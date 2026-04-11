from domain.interfaces import NormalizerInterface
from domain.models import FileRecord, DriveFile
from datetime import datetime


class DriveNormalizer(NormalizerInterface):
    def normalize(self, raw_data: dict) -> FileRecord:
        """
        raw_data expected: Google Drive API file metadata dict
        """
        name = raw_data.get("name", "")
        extension = name.split(".")[-1].lower() if "." in name else None
        size = int(raw_data.get("size", 0)) if raw_data.get("size") else 0
        md5 = raw_data.get("md5Checksum")

        modified_time_str = raw_data.get("modifiedTime")
        last_modified = None
        if modified_time_str:
            # Drive API returns ISO strings ending in Z or .mmmZ
            # Replace Z with +00:00 for fromisoformat or handle manually
            iso_str = modified_time_str.replace("Z", "+00:00")
            try:
                last_modified = datetime.fromisoformat(iso_str)
            except ValueError:
                pass

        return FileRecord(
            source_id=raw_data["id"],
            name=name,
            size=size,
            source="drive",
            hash=md5,
            hash_algo="md5" if md5 else None,
            extension=extension,
            mime_type=raw_data.get("mimeType"),
            last_modified=last_modified,
            confidence_score=0,
        )

    def to_drive_file(self, raw_data: dict) -> DriveFile:
        """
        Extract detailed cloud metadata.
        """
        name = raw_data.get("name", "")
        size = int(raw_data.get("size", 0)) if raw_data.get("size") else 0
        md5 = raw_data.get("md5Checksum")
        parents = raw_data.get("parents", [])
        parent_id = parents[0] if parents else None

        modified_time_str = raw_data.get("modifiedTime")
        last_modified = None
        if modified_time_str:
            iso_str = modified_time_str.replace("Z", "+00:00")
            try:
                last_modified = datetime.fromisoformat(iso_str)
            except ValueError:
                pass

        return DriveFile(
            drive_file_id=raw_data["id"],
            name=name,
            size=size,
            mime_type=raw_data.get("mimeType"),
            hash=md5,
            last_modified=last_modified,
            parent_id=parent_id,
            eligible_for_dedup=True,
        )
