import time
import logging
import json
from domain.interfaces import ScannerInterface, NormalizerInterface, FileRepositoryInterface

logger = logging.getLogger(__name__)


class DriveInventoryRunner:
    def __init__(self, scanner: ScannerInterface, normalizer: NormalizerInterface, file_repo: FileRepositoryInterface, state_repo=None):
        self.scanner = scanner
        self.normalizer = normalizer
        self.file_repo = file_repo
        self.state_repo = state_repo

    def run(self, source_path: str = None):
        start_time = time.time()
        count = 0
        for raw_data in self.scanner.scan(source_path):
            record = self.normalizer.normalize(raw_data)
            self.file_repo.upsert(record)
            count += 1

        if self.state_repo:
            now = int(time.time())
            self.state_repo.update_last_scan_time("drive", now)

        logger.info(json.dumps({
            "event": "drive_scan_completed",
            "total_records": count,
            "duration_sec": round(time.time() - start_time, 2)
        }))
