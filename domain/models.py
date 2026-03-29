from sqlalchemy import String, BigInteger, Float, Integer, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import Optional


class Base(DeclarativeBase):
    pass


class FileRecord(Base):
    __tablename__ = "file_records"

    # Use a surrogate ID for primary key, but keep source_id unique
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(String, unique=True, index=True)  # Path for local, Drive ID for drive
    name: Mapped[str] = mapped_column(String)
    size: Mapped[int] = mapped_column(BigInteger, index=True)
    source: Mapped[str] = mapped_column(String, index=True)  # 'local' or 'drive'
    hash: Mapped[Optional[str]] = mapped_column(String, index=True)
    hash_algo: Mapped[Optional[str]] = mapped_column(String)
    extension: Mapped[Optional[str]] = mapped_column(String)
    last_modified: Mapped[Optional[float]] = mapped_column(Float)
    status: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)  # 'DUPLICATE', 'UNIQUE', 'UNVERIFIED'
    confidence_score: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)

    # Composite index for size and hash as used in Mongo
    __table_args__ = (
        Index("ix_file_records_size_hash", "size", "hash"),
    )

    def to_dict(self):
        return {
            "source_id": self.source_id,
            "name": self.name,
            "size": self.size,
            "source": self.source,
            "hash": self.hash,
            "hash_algo": self.hash_algo,
            "extension": self.extension,
            "last_modified": self.last_modified,
            "status": self.status,
            "confidence_score": self.confidence_score,
        }


class DriveFile(Base):
    __tablename__ = "drive_files"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    drive_file_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    size: Mapped[int] = mapped_column(BigInteger, index=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String)
    hash: Mapped[Optional[str]] = mapped_column(String, index=True)
    last_modified: Mapped[Optional[float]] = mapped_column(Float)
    eligible_for_dedup: Mapped[bool] = mapped_column(default=True, index=True)
    parent_id: Mapped[Optional[str]] = mapped_column(String)
    path: Mapped[Optional[str]] = mapped_column(String)

    __table_args__ = (
        Index("ix_drive_files_size_hash", "size", "hash"),
    )


class ScanState(Base):
    __tablename__ = "scan_state"

    source: Mapped[str] = mapped_column(String, primary_key=True)
    last_successful_scan_time: Mapped[int] = mapped_column(BigInteger)
