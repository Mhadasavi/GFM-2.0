from domain.interfaces import NormalizerInterface
from domain.models import FileRecord, DriveFile
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

        return FileRecord(
            source_id=raw_data["id"],
            name=name,
            size=size,
            source="drive",
            hash=md5,
            hash_algo="md5" if md5 else None,
            extension=extension,
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
        
        # Drive gives ISO strings for modifiedTime
        # We can store it as a float for consistency with other models
        # but the model says Float so we should convert it.
        modified_time_str = raw_data.get("modifiedTime")
        last_modified = None
        if modified_time_str:
            try:
                # Basic conversion, could be more robust
                struct_time = time.strptime(modified_time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                last_modified = float(time.mktime(struct_time))
            except ValueError:
                try:
                     struct_time = time.strptime(modified_time_str, "%Y-%m-%dT%H:%M:%SZ")
                     last_modified = float(time.mktime(struct_time))
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
            # Path can be reconstructed later or fetched if needed
            eligible_for_dedup=True 
        )
