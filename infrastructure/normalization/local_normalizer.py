from domain.interfaces import NormalizerInterface
from domain.models import FileRecord
import os


class LocalNormalizer(NormalizerInterface):
    def normalize(self, raw_data: dict) -> FileRecord:
        """
        raw_data expected: {'path': ..., 'name': ..., 'size': ..., 'last_modified': ...}
        """
        path = raw_data["path"]
        name = raw_data["name"]
        size = raw_data["size"]
        last_modified = raw_data["last_modified"]
        extension = name.split(".")[-1].lower() if "." in name else None

        return FileRecord(
            source_id=path,
            name=name,
            size=size,
            source="local",
            extension=extension,
            last_modified=last_modified,
            confidence_score=0
        )
