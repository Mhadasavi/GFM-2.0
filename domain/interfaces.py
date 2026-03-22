from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generator
from domain.models import FileRecord


class HashingServiceInterface(ABC):
    @abstractmethod
    def stream_hash(self, file_path: str, algorithm: str = "sha256") -> str:
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
    def get_by_source_id(self, source_id: str) -> FileRecord:
        pass

    @abstractmethod
    def find_duplicates_by_hash(self) -> List[FileRecord]:
        pass

    @abstractmethod
    def update_status_and_score(
        self, source_id: str, status: str, confidence_score: int
    ):
        pass
