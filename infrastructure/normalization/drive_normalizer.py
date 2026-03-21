from domain.interfaces import NormalizerInterface
from domain.models import FileRecord
import time


class DriveNormalizer(NormalizerInterface):
    def normalize(self, raw_data: dict) -> FileRecord:
        """
        raw_data expected: Google Drive API file metadata dict
        """
        name = raw_data.get("name", "")
        extension = name.split(".")[-1].lower() if "." in name else None
        size = int(raw_data.get("size", 0)) if raw_data.get("size") else 0
        md5 = raw_data.get("md5Checksum")

        # Modified time in ISO format (YYYY-MM-DDTHH:MM:SS.mmmZ)
        # We'll just store the string or convert to timestamp if needed
        # AC says "No timestamps are used for identity", so we just keep it for info.

        return FileRecord(
            source_id=raw_data["id"],
            name=name,
            size=size,
            source="drive",
            hash=md5,
            hash_algo="md5" if md5 else None,
            extension=extension,
            # We skip last_modified for identity as per AC, but could add it for cache invalidation
        )
