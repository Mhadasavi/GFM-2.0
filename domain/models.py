from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class FileRecord:
    path: str
    name: str
    extension: str
    size: int
    last_modified: float
    hash: Optional[str]
    hash_algo: str
    source: str = "local"  # or "drive"
