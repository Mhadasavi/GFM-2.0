import os
from typing import Generator, Dict, Any, List
from domain.interfaces import ScannerInterface


class LocalScanner(ScannerInterface):
    def __init__(self, supported_extensions: List[str] = None):
        self.supported_extensions = supported_extensions or [
            "jpg",
            "png",
            "jpeg",
            "heic",
            "webp",
        ]

    def scan(self, dir_path: str) -> Generator[Dict[str, Any], None, None]:
        for root, _, files in os.walk(dir_path):
            for file in files:
                extension = file.split(".")[-1].lower()
                if extension in self.supported_extensions:
                    path = os.path.abspath(os.path.join(root, file))
                    try:
                        stat = os.stat(path)
                        yield {
                            "path": path,
                            "name": file,
                            "size": stat.st_size,
                            "last_modified": stat.st_mtime,
                        }
                    except (OSError, PermissionError) as e:
                        # Log error if needed
                        continue
