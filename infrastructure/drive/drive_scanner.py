import time
import logging
import json
from typing import Dict, Generator, Any, Optional

logger = logging.getLogger(__name__)


class DriveScanner:
    def __init__(self, drive_client, last_scan_time: Optional[int] = None):
        self.drive_client = drive_client
        self.last_scan_time = last_scan_time

    def _build_query(self) -> str:
        base_query = "trashed = false"

        if self.last_scan_time:
            iso_time = time.strftime(
                "%Y-%m-%dT%H:%M:%SZ",
                time.gmtime(self.last_scan_time)
            )
            return f"{base_query} and modifiedTime > '{iso_time}'"

        return base_query

    def scan(self) -> Generator[Dict[str, Any], None, None]:
        query = self._build_query()

        logger.info(json.dumps({
            "event": "drive_scan_started",
            "query": query
        }))

        for file in self.drive_client.list_files(query=query):
            yield self._normalize(file)

    def _normalize(self, file: Dict[str, Any]) -> Dict[str, Any]:
        name = file.get("name", "")
        extension = name.split(".")[-1].lower() if "." in name else None
        size = int(file.get("size", 0)) if file.get("size") else None
        md5 = file.get("md5Checksum")

        return {
            "drive_file_id": file["id"],
            "name": name,
            "extension": extension,
            "size": size,
            "last_modified": file.get("modifiedTime"),
            "hash": md5,
            "hash_algo": "md5" if md5 else None,
            "source": "drive",
            "mime_type": file.get("mimeType"),
            "parents": file.get("parents", []),
            "eligible_for_dedup": bool(md5),
            "scanned_at": int(time.time())
        }
