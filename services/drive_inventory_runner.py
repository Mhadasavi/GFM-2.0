import time
import logging
import json
from domain.interfaces import (
    ScannerInterface,
    NormalizerInterface,
    FileRepositoryInterface,
    DriveRepositoryInterface
)

logger = logging.getLogger(__name__)


class DriveInventoryRunner:
    def __init__(
        self,
        scanner: ScannerInterface,
        normalizer: NormalizerInterface,
        file_repo: FileRepositoryInterface,
        drive_repo: DriveRepositoryInterface,
        state_repo=None,
    ):
        self.scanner = scanner
        self.normalizer = normalizer
        self.file_repo = file_repo
        self.drive_repo = drive_repo
        self.state_repo = state_repo

    def run(self, source_path: str = None):
        start_time = time.time()
        count = 0
        logger.info(json.dumps({"event": "drive_inventory_run_started"}))
        for raw_data in self.scanner.scan(source_path):
            # 1. Update basic comparison inventory (file_records table)
            record = self.normalizer.normalize(raw_data)
            self.file_repo.upsert(record)
            
            # 2. Update cloud-specific inventory (drive_files table)
            if hasattr(self.normalizer, "to_drive_file"):
                drive_file_meta = self.normalizer.to_drive_file(raw_data)
                self.drive_repo.upsert(drive_file_meta)
            
            count += 1
            if count % 1000 == 0:
                logger.info(
                    json.dumps(
                        {
                            "event": "drive_inventory_progress",
                            "records_processed": count,
                            "elapsed_sec": round(time.time() - start_time, 2),
                        }
                    )
                )

        if self.state_repo:
            now = int(time.time())
            self.state_repo.update_last_scan_time("drive", now)

        logger.info(
            json.dumps(
                {
                    "event": "drive_scan_completed",
                    "total_records": count,
                    "duration_sec": round(time.time() - start_time, 2),
                }
            )
        )
