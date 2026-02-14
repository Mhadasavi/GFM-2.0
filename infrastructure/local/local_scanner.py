import os
from typing import List
from domain.models import FileRecord
from domain.interfaces import ScannerInterface

class LocalScanner(ScannerInterface):
    def __init__(self, supported_extensions: List[str] = None):
        self.supported_extensions = supported_extensions or ['jpg', 'png', 'jpeg', 'heic', 'webp']

    def scan(self, dir_path: str) -> List[FileRecord]:
        records = []
        for root, _, files in os.walk(dir_path):
            for file in files:
                extension = file.split('.')[-1].lower()
                if extension in self.supported_extensions:
                    path = os.path.join(root, file)
                    size = os.path.getsize(path)
                    last_modified = os.path.getmtime(path)
                    records.append(
                        FileRecord(
                            path=path,
                            name=file,
                            extension=extension,
                            size=size,
                            last_modified=last_modified,
                            hash=None,
                            hash_algo='',
                            source='local'
                        )
                    )
        return records
