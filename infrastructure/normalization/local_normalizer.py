from domain.interfaces import NormalizerInterface
from domain.models import FileRecord
import os
import mimetypes
from datetime import datetime


class LocalNormalizer(NormalizerInterface):
    def normalize(self, raw_data: dict) -> FileRecord:
        """
        raw_data expected: {'path': ..., 'name': ..., 'size': ..., 'last_modified': ...}
        """
        path = raw_data["path"]
        name = raw_data["name"]
        size = raw_data["size"]
        last_modified_float = raw_data["last_modified"]
        last_modified = datetime.fromtimestamp(last_modified_float)
        extension = name.split(".")[-1].lower() if "." in name else None
        mime_type, _ = mimetypes.guess_type(path)

        return FileRecord(
            source_id=path,
            name=name,
            size=size,
            source="local",
            extension=extension,
            mime_type=mime_type,
            last_modified=last_modified,
            confidence_score=0,
        )
