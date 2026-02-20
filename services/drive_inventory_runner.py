import time
import logging
import json

logger = logging.getLogger(__name__)


class DriveInventoryRunner:
    def __init__(self, scanner, drive_repo, state_repo):
        self.scanner = scanner
        self.drive_repo = drive_repo
        self.state_repo = state_repo

    def run(self):
        start_time = time.time()
        records = list(self.scanner.scan())

        self.drive_repo.upsert_many(records)

        now = int(time.time())
        self.state_repo.update_last_scan_time("drive", now)

        logger.info(json.dumps({
            "event": "drive_scan_completed",
            "total_records": len(records),
            "duration_sec": round(time.time() - start_time, 2)
        }))
