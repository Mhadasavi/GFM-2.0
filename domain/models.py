from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FileRecord:
    source_id: str  # Path for local, Drive ID for drive
    name: str
    size: int
    source: str  # 'local' or 'drive'
    hash: Optional[str] = None
    hash_algo: Optional[str] = None
    extension: Optional[str] = None
    last_modified: Optional[float] = None
    status: Optional[str] = None  # 'DUPLICATE', 'UNIQUE', 'UNVERIFIED'
    confidence_score: int = 0  # 0-100
