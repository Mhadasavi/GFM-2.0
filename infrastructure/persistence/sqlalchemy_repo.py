import logging
from typing import List, Optional
from sqlalchemy import create_engine, select, update, func, and_
from sqlalchemy.orm import sessionmaker, Session
from domain.models import Base, FileRecord, DriveFile, ScanState
from domain.interfaces import (
    FileRepositoryInterface,
    HashRepositoryInterface,
    ScanStateRepositoryInterface,
    DriveRepositoryInterface,
)

logger = logging.getLogger(__name__)


class SQLAlchemyFileRepository(FileRepositoryInterface, HashRepositoryInterface):
    def __init__(self, engine):
        self.engine = engine
        self.Session = sessionmaker(bind=self.engine)

    def upsert(self, record: FileRecord):
        with self.Session() as session:
            try:
                # Merge is basically UPSERT based on the primary key,
                # but our primary key is a surrogate 'id'.
                # We want to UPSERT based on 'source_id'.
                stmt = select(FileRecord).where(
                    FileRecord.source_id == record.source_id
                )
                existing = session.execute(stmt).scalar_one_or_none()

                if existing:
                    # Update fields manually to avoid changing 'id'
                    existing.name = record.name
                    existing.size = record.size
                    existing.source = record.source
                    existing.hash = record.hash
                    existing.hash_algo = record.hash_algo
                    existing.extension = record.extension
                    existing.mime_type = record.mime_type
                    existing.last_modified = record.last_modified
                    existing.status = record.status or existing.status
                    existing.confidence_score = (
                        record.confidence_score
                        if record.confidence_score is not None
                        else 0
                    )
                else:
                    # Ensure confidence_score is never None on new records
                    if record.confidence_score is None:
                        record.confidence_score = 0
                    session.add(record)

                session.commit()
            except Exception as e:
                session.rollback()
                logger.error(f"Error in upsert: {e}")
                raise

    def get_by_source_id(self, source_id: str) -> Optional[FileRecord]:
        with self.Session() as session:
            stmt = select(FileRecord).where(FileRecord.source_id == source_id)
            return session.execute(stmt).scalar_one_or_none()

    def get(self, file_path: str) -> Optional[FileRecord]:
        """Implementation for HashRepositoryInterface (uses path/source_id)"""
        return self.get_by_source_id(file_path)

    def find_duplicates_by_hash(self) -> List[FileRecord]:
        with self.Session() as session:
            # Find hashes that appear more than once with the same size
            subq = (
                select(FileRecord.hash, FileRecord.size)
                .where(FileRecord.hash.is_not(None))
                .group_by(FileRecord.hash, FileRecord.size)
                .having(func.count(FileRecord.id) > 1)
                .subquery()
            )

            stmt = (
                select(FileRecord)
                .join(
                    subq,
                    and_(
                        FileRecord.hash == subq.c.hash, FileRecord.size == subq.c.size
                    ),
                )
                .order_by(FileRecord.hash, FileRecord.size)
            )
            return list(session.execute(stmt).scalars().all())

    def update_status_and_score(
        self, source_id: str, status: str, confidence_score: int
    ):
        with self.Session() as session:
            stmt = (
                update(FileRecord)
                .where(FileRecord.source_id == source_id)
                .values(status=status, confidence_score=confidence_score)
            )
            session.execute(stmt)
            session.commit()

    def get_all_by_source(self, source: str) -> List[FileRecord]:
        with self.Session() as session:
            stmt = select(FileRecord).where(FileRecord.source == source)
            return list(session.execute(stmt).scalars().all())

    def count_unverified_by_source(self, source: str) -> int:
        with self.Session() as session:
            stmt = select(func.count(FileRecord.id)).where(
                and_(FileRecord.source == source, FileRecord.status == "UNVERIFIED")
            )
            return session.execute(stmt).scalar() or 0

    def upsert_unverified(self, record: FileRecord, reason: str = "Unknown"):
        # We can just use status='UNVERIFIED' in the main table for simplicity
        # or add a 'reason' field if needed.
        # Current SQLite implementation had a separate table.
        # Let's just set the status to UNVERIFIED and store it in the main table.
        record.status = "UNVERIFIED"
        self.upsert(record)


class SQLAlchemyScanStateRepository(ScanStateRepositoryInterface):
    def __init__(self, engine):
        self.engine = engine
        self.Session = sessionmaker(bind=self.engine)

    def get_last_scan_time(self, source: str) -> Optional[int]:
        with self.Session() as session:
            stmt = select(ScanState).where(ScanState.source == source)
            state = session.execute(stmt).scalar_one_or_none()
            return state.last_successful_scan_time if state else None

    def update_last_scan_time(self, source: str, timestamp: int):
        with self.Session() as session:
            stmt = select(ScanState).where(ScanState.source == source)
            existing = session.execute(stmt).scalar_one_or_none()
            if existing:
                existing.last_successful_scan_time = timestamp
            else:
                session.add(
                    ScanState(source=source, last_successful_scan_time=timestamp)
                )
            session.commit()


class SQLAlchemyDriveRepository(DriveRepositoryInterface):
    def __init__(self, engine):
        self.engine = engine
        self.Session = sessionmaker(bind=self.engine)

    def upsert(self, record: DriveFile):
        with self.Session() as session:
            try:
                stmt = select(DriveFile).where(
                    DriveFile.drive_file_id == record.drive_file_id
                )
                existing = session.execute(stmt).scalar_one_or_none()

                if existing:
                    existing.name = record.name
                    existing.size = record.size
                    existing.mime_type = record.mime_type
                    existing.hash = record.hash
                    existing.last_modified = record.last_modified
                    existing.eligible_for_dedup = record.eligible_for_dedup
                    existing.parent_id = record.parent_id
                    existing.path = record.path
                else:
                    session.add(record)

                session.commit()
            except Exception as e:
                session.rollback()
                logger.error(f"Error in Drive upsert: {e}")
                raise

    def get_by_id(self, drive_file_id: str) -> Optional[DriveFile]:
        with self.Session() as session:
            stmt = select(DriveFile).where(DriveFile.drive_file_id == drive_file_id)
            return session.execute(stmt).scalar_one_or_none()
