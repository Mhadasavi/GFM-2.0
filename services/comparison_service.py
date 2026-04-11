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

        # 1. Load Local inventory into lookups
        local_lookup: Dict[str, List[FileRecord]] = {}
        local_name_lookup: Dict[str, List[FileRecord]] = {}
        local_records = self._get_records_by_source("local")
        for record in local_records:
            # Hash lookup
            if record.hash:
                if record.hash not in local_lookup:
                    local_lookup[record.hash] = []
                local_lookup[record.hash].append(record)

            # Name lookup (case-insensitive, no extension)
            base_name = (
                record.name.rsplit(".", 1)[0].lower()
                if "." in record.name
                else record.name.lower()
            )
            if base_name not in local_name_lookup:
                local_name_lookup[base_name] = []
            local_name_lookup[base_name].append(record)

        logger.info(
            f"Loaded {len(local_lookup)} hash groups and {len(local_name_lookup)} name groups from local."
        )

        # 2. Iterate through Drive records
        drive_records = self._get_records_by_source("drive")

        summary = {
            "DUPLICATE": 0,
            "UNIQUE": 0,
            "UNVERIFIED": self._count_unverified_by_source("drive"),
            "TOTAL_VERIFIABLE": len(drive_records),
        }

        audit_data = []

        # Google Doc mime types that don't have hashes
        GOOGLE_DOC_MIMETYPES = {
            "application/vnd.google-apps.document",
            "application/vnd.google-apps.spreadsheet",
            "application/vnd.google-apps.presentation",
        }

        for drive_rec in drive_records:
            status = "UNIQUE"
            max_score = 0
            candidates = []

            if drive_rec.hash:
                # Find candidates in local inventory by hash
                candidates = local_lookup.get(drive_rec.hash, [])
            elif drive_rec.mime_type in GOOGLE_DOC_MIMETYPES:
                # For Google Docs without hashes, try name-based matching
                base_name = (
                    drive_rec.name.lower()
                )  # Google Docs usually don't have extension in name
                candidates = local_name_lookup.get(base_name, [])
            else:
                # Other files without hashes (e.g. shortcuts, folders) - skip for now
                continue

            if not candidates:
                # No match at all
                self.repo.update_status_and_score(drive_rec.source_id, "UNIQUE", 0)
                summary["UNIQUE"] += 1
                continue

            # Calculate score against each candidate and keep the best one
            for local_rec in candidates:
                if drive_rec.hash:
                    current_score = self._calculate_confidence(drive_rec, local_rec)
                else:
                    current_score = self._calculate_fuzzy_confidence(
                        drive_rec, local_rec
                    )

                if current_score > max_score:
                    max_score = current_score

            # Threshold Check (Dev 6 AC: Only >= 90 is DUPLICATE)
            # For fuzzy matches, we might want a slightly different threshold or just use the same
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
                    "hash": drive_rec.hash or "N/A (Google Doc)",
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

    def _calculate_fuzzy_confidence(self, drive: FileRecord, local: FileRecord) -> int:
        """
        Confidence calculation for files without hashes (Google Docs).
        Since there's no hash or size match, we rely on Name, Extension (inferred), and MimeType.
        """
        score = 0

        # 1. Filename Match (ignoring extension) - 60%
        drive_name_lower = drive.name.lower()
        local_base_name = (
            local.name.rsplit(".", 1)[0].lower()
            if "." in local.name
            else local.name.lower()
        )

        if drive_name_lower == local_base_name:
            score += 60

        # 2. Mime Type Correlation - 30%
        # Map Google Doc types to common extensions
        MIME_MAP = {
            "application/vnd.google-apps.document": [".docx", ".doc", ".rtf", ".odt"],
            "application/vnd.google-apps.spreadsheet": [
                ".xlsx",
                ".xls",
                ".csv",
                ".ods",
            ],
            "application/vnd.google-apps.presentation": [".pptx", ".ppt", ".odp"],
        }

        if drive.mime_type in MIME_MAP:
            expected_extensions = MIME_MAP[drive.mime_type]
            local_ext = "." + local.extension.lower() if local.extension else ""
            if local_ext in expected_extensions:
                score += 30

        # 3. Exact Name Match (unlikely for Google Docs vs local docx, but possible) - 10%
        if drive.name == local.name:
            score += 10

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
