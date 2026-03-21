import time
import logging
import json
from typing import Generator, Dict, Any, Optional
from domain.interfaces import ScannerInterface

logger = logging.getLogger(__name__)


class DriveScanner(ScannerInterface):
    def __init__(self, drive_client, last_scan_time: Optional[int] = None):
        self.drive_client = drive_client
        self.last_scan_time = last_scan_time

    def _build_query(self) -> str:
        base_query = "trashed = false"

        if self.last_scan_time:
            iso_time = time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.last_scan_time)
            )
            return f"{base_query} and modifiedTime > '{iso_time}'"

        return base_query

    def scan(self, source_path: str = None) -> Generator[Dict[str, Any], None, None]:
        # source_path can be used as a folder ID if needed, otherwise it scans all accessible
        query = self._build_query()
        if source_path:
            query = f"'{source_path}' in parents and {query}"

        logger.info(json.dumps({"event": "drive_scan_started", "query": query}))

        for file in self.drive_client.list_files(query=query):
            yield file
