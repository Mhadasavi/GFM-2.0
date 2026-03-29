import logging
import os
import csv
from datetime import datetime
from typing import Dict, Set, Tuple, List
from domain.models import FileRecord
from domain.interfaces import FileRepositoryInterface

logger = logging.getLogger(__name__)


class ComparisonService:
    def __init__(self, repo: FileRepositoryInterface):
        self.repo = repo
        self.audit_log_path = "logs/audit.csv"

    def run_comparison(self) -> Dict[str, int]:
        """
        Compare Drive files against Local inventory using Hash + Size.
        Calculates confidence score (0-100) based on:
        - Hash Match: 70%
        - Size Match: 20%
        - Extension Match: 5%
        - Filename Match: 5%

        Updates statuses and scores in the database.
        Logs decisions to audit.csv.
        """
        logger.info("Starting comparison with Confidence Scoring Engine...")

        # Ensure log directory exists
        os.makedirs(os.path.dirname(self.audit_log_path), exist_ok=True)

        # 1. Load Local inventory into a lookup (Hash -> List of Records)
        local_lookup: Dict[str, List[FileRecord]] = {}
        local_records = self._get_records_by_source("local")
        for record in local_records:
            if record.hash:
                if record.hash not in local_lookup:
                    local_lookup[record.hash] = []
                local_lookup[record.hash].append(record)

        logger.info(f"Loaded {len(local_lookup)} local hash groups.")

        # 2. Iterate through Drive records
        drive_records = self._get_records_by_source("drive")

        summary = {
            "DUPLICATE": 0,
            "UNIQUE": 0,
            "UNVERIFIED": self._count_unverified_by_source("drive"),
            "TOTAL_VERIFIABLE": len(drive_records),
        }

        audit_data = []

        for drive_rec in drive_records:
            status = "UNIQUE"
            max_score = 0

            # (Note: Unverified are already in their own table,
            # so we only process files that actually have hashes here)
            if not drive_rec.hash:
                continue

            # Find candidates in local inventory by hash
            candidates = local_lookup.get(drive_rec.hash, [])

            if not candidates:
                # No hash match at all
                self.repo.update_status_and_score(drive_rec.source_id, "UNIQUE", 0)
                summary["UNIQUE"] += 1
                continue

            # Calculate score against each candidate and keep the best one
            for local_rec in candidates:
                current_score = self._calculate_confidence(drive_rec, local_rec)
                if current_score > max_score:
                    max_score = current_score

            # Threshold Check (Dev 6 AC: Only >= 90 is DUPLICATE)
            if max_score >= 90:
                status = "DUPLICATE"
            else:
                status = "UNIQUE"

            self.repo.update_status_and_score(drive_rec.source_id, status, max_score)
            summary[status] += 1

            # Record for audit
            audit_data.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "drive_id": drive_rec.source_id,
                    "drive_name": drive_rec.name,
                    "score": max_score,
                    "status": status,
                    "hash": drive_rec.hash,
                }
            )

        self._write_audit_log(audit_data)
        logger.info(f"Comparison complete: {summary}")
        return summary

    def _calculate_confidence(self, drive: FileRecord, local: FileRecord) -> int:
        score = 0
        # Hash Match (Mandatory implicitly as we only compare hash-matches here)
        if drive.hash == local.hash:
            score += 70
        # Size Match (Mandatory check)
        if drive.size == local.size:
            score += 20
        # Extension Match
        if (
            drive.extension
            and local.extension
            and drive.extension.lower() == local.extension.lower()
        ):
            score += 5
        # Filename Match
        if drive.name == local.name:
            score += 5
        return score

    def _write_audit_log(self, data: List[Dict]):
        if not data:
            return
        file_exists = os.path.isfile(self.audit_log_path)
        keys = ["timestamp", "drive_id", "drive_name", "score", "status", "hash"]
        with open(
            self.audit_log_path, "a", newline="", encoding="utf-8"
        ) as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            if not file_exists:
                dict_writer.writeheader()
            dict_writer.writerows(data)

    def _get_records_by_source(self, source: str) -> List[FileRecord]:
        return self.repo.get_all_by_source(source)

    def _count_unverified_by_source(self, source: str) -> int:
        return self.repo.count_unverified_by_source(source)
