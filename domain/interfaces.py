from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generator, Optional
from domain.models import FileRecord, DriveFile


class HashingServiceInterface(ABC):
    @abstractmethod
    def stream_hash(self, file_path: str, algorithm: str) -> str:
        pass


class NormalizerInterface(ABC):
    @abstractmethod
    def normalize(self, raw_data: Any) -> FileRecord:
        pass


class ScannerInterface(ABC):
    @abstractmethod
    def scan(self, source_path: str) -> Generator[Any, None, None]:
        pass


class FileRepositoryInterface(ABC):
    @abstractmethod
    def upsert(self, record: FileRecord):
        pass

    @abstractmethod
    def get_by_source_id(self, source_id: str) -> Optional[FileRecord]:
        pass

    @abstractmethod
    def find_duplicates_by_hash(self) -> List[FileRecord]:
        pass

    @abstractmethod
    def update_status_and_score(
        self, source_id: str, status: str, confidence_score: int
    ):
        pass

    @abstractmethod
    def get_all_by_source(self, source: str) -> List[FileRecord]:
        pass

    @abstractmethod
    def count_unverified_by_source(self, source: str) -> int:
        pass


class HashRepositoryInterface(ABC):
    @abstractmethod
    def upsert(self, record: FileRecord):
        pass

    @abstractmethod
    def get(self, file_path: str) -> Optional[FileRecord]:
        pass


class ScanStateRepositoryInterface(ABC):
    @abstractmethod
    def get_last_scan_time(self, source: str) -> Optional[int]:
        pass

    @abstractmethod
    def update_last_scan_time(self, source: str, timestamp: int):
        pass


class DriveRepositoryInterface(ABC):
    @abstractmethod
    def upsert(self, record: DriveFile):
        pass

    @abstractmethod
    def get_by_id(self, drive_file_id: str) -> Optional[DriveFile]:
        pass
