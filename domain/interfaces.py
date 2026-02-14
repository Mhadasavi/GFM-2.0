from abc import ABC, abstractmethod
from typing import List
from domain.models import FileRecord

class HashingServiceInterface(ABC):
    @abstractmethod
    def stream_hash(self, file_path: str, algorithm: str = 'sha256') -> str:
        pass

class ScannerInterface(ABC):
    @abstractmethod
    def scan(self, dir_path: str) -> List[FileRecord]:
        pass

class HashRepositoryInterface(ABC):
    @abstractmethod
    def upsert(self, record: FileRecord):
        pass

    @abstractmethod
    def get(self, file_path: str, last_modified: float) -> FileRecord:
        pass
