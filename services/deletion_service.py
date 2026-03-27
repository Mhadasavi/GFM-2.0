import os
import csv
import logging
import json
from datetime import datetime
from typing import List, Dict
from domain.interfaces import FileRepositoryInterface
from infrastructure.drive.drive_client import DriveClient
from infrastructure.persistence.sqlite_repo import SQLiteFileRepository

logger = logging.getLogger(__name__)


class DeletionService:
    def __init__(self, repo: FileRepositoryInterface, drive_client: DriveClient):
        self.repo = repo
        self.drive_client = drive_client

    def run_deletion(
        self, dry_run: bool = True, output_report_path: str = "logs/deletion_report.csv"
    ) -> Dict[str, int]:
        """
        Processes Drive duplicates for deletion.
        If dry_run=True, only generates a report.
        If dry_run=False, performs deletions and updates the database.
        """
        logger.info(
            f"Starting deletion process (dry_run={dry_run}, report={output_report_path})"
        )

        # 1. Fetch Drive records from repository
        drive_records = self._get_drive_records()
        logger.info(f"Retrieved {len(drive_records)} Drive records from inventory.")

        # 2. Prepare report data
        report_data = []
        summary = {"proposed_deletions": 0, "proposed_keeps": 0, "actual_deletions": 0}

        for record in drive_records:
            # We only propose deletion for those marked DUPLICATE (score >= 90)
            proposed_action = "DELETE" if record.status == "DUPLICATE" else "KEEP"

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
                }
            )

        # 3. Export report
        self._export_report(report_data, output_report_path)

        # 4. Perform actual deletions if not dry-run
        if not dry_run:
            for item in report_data:
                if item["Proposed action"] == "DELETE":
                    file_id = item["Drive file ID"]
                    try:
                        self.drive_client.delete_file(file_id)
                        # Update status in repository
                        self.repo.update_status_and_score(file_id, "DELETED", item["Confidence score"])
                        summary["actual_deletions"] += 1
                        logger.info(f"Deleted and updated: {file_id}")
                    except Exception as e:
                        logger.error(f"Failed to delete {file_id}: {e}")

        logger.info(f"Deletion summary: {summary}")
        return summary

    def _get_drive_records(self):
        # Using the same logic as ComparisonService to fetch drive records
        if isinstance(self.repo, SQLiteFileRepository):
            with self.repo._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT source_id, name, size, source, hash, hash_algo, extension, last_modified, status, confidence_score FROM file_records WHERE source = 'drive'"
                )
                return [self.repo._row_to_record(row) for row in cursor.fetchall()]
        return []

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
