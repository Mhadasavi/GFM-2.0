import os
import csv
import logging
import json
import time
from datetime import datetime
from typing import List, Dict
from domain.interfaces import FileRepositoryInterface
from infrastructure.drive.drive_client import DriveClient
logger = logging.getLogger(__name__)

class DeletionService:
    def __init__(self, repo: FileRepositoryInterface, drive_client: DriveClient):
        self.repo = repo
        self.drive_client = drive_client

    def run_deletion(
        self, dry_run: bool = True, output_report_path: str = "logs/deletion_report.csv"
    ) -> Dict[str, int]:
        """
        Processes Drive duplicates for deletion (trashing).
        If dry_run=True, only generates a report.
        If dry_run=False, performs trashing and updates the database.
        """
        logger.info(
            f"Starting deletion process (dry_run={dry_run}, report={output_report_path})"
        )

        # 1. Fetch Drive records from repository
        drive_records = self._get_drive_records()
        logger.info(json.dumps({
            "event": "deletion_scan_start",
            "scanned_file_count": len(drive_records)
        }))

        # 2. Prepare report data
        report_data = []
        summary = {
            "scanned_files": len(drive_records),
            "duplicates_found": 0,
            "proposed_deletions": 0,
            "proposed_keeps": 0,
            "actual_deletions": 0,
            "errors": 0
        }

        for record in drive_records:
            is_duplicate = (record.status == "DUPLICATE")
            if is_duplicate:
                summary["duplicates_found"] += 1

            # AC: Only files marked DELETE with confidence >= 90 are removed
            should_delete = (is_duplicate and record.confidence_score >= 90)
            proposed_action = "DELETE" if should_delete else "KEEP"

            if proposed_action == "DELETE":
                summary["proposed_deletions"] += 1
            else:
                summary["proposed_keeps"] += 1

            report_data.append(
                {
                    "Drive file ID": record.source_id,
                    "Name": record.name,
                    "Confidence score": record.confidence_score,
                    "Proposed action": proposed_action,
                    "Hash": record.hash,
                    "Status": "PENDING"
                }
            )

        # 3. Perform actual trashing if not dry-run
        if not dry_run:
            for item in report_data:
                if item["Proposed action"] == "DELETE":
                    file_id = item["Drive file ID"]
                    file_hash = item["Hash"]
                    try:
                        # Rate-limiting: Small delay between API calls
                        time.sleep(0.1)

                        self.drive_client.delete_file(file_id)

                        # AC: Deletion is logged with timestamp, file ID, hash
                        logger.info(json.dumps({
                            "event": "file_trashed_action",
                            "timestamp": datetime.now().isoformat(),
                            "file_id": file_id,
                            "hash": file_hash,
                            "status": "SUCCESS"
                        }))

                        # Update status in repository
                        self.repo.update_status_and_score(file_id, "DELETED", item["Confidence score"])
                        summary["actual_deletions"] += 1
                        item["Status"] = "TRASHED_SUCCESS"
                    except Exception as e:
                        summary["errors"] += 1
                        item["Status"] = f"FAILED: {str(e)}"
                        logger.error(json.dumps({
                            "event": "file_trash_failed",
                            "file_id": file_id,
                            "error": str(e),
                            "action": "trash"
                        }))
                else:
                    item["Status"] = "SKIPPED_KEEP"
        else:
            for item in report_data:
                item["Status"] = "SKIPPED_DRY_RUN"

        # 4. Export report (Full visibility into actions taken)
        self._export_report(report_data, output_report_path)

        logger.info(json.dumps({
            "event": "deletion_process_summary",
            "summary": summary,
            "dry_run": dry_run
        }))
        return summary

    def _get_drive_records(self):
        return self.repo.get_all_by_source("drive")

    def _export_report(self, data: List[Dict], path: str):
        if not data:
            logger.warning("No data to export to report.")
            return

        os.makedirs(os.path.dirname(path), exist_ok=True)
        keys = data[0].keys()
        with open(path, "w", newline="", encoding="utf-8") as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(data)
        logger.info(f"Report exported to {path}")
