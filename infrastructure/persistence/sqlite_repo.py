import sqlite3
import json
from typing import List, Optional
from domain.models import FileRecord
from domain.interfaces import FileRepositoryInterface


class SQLiteFileRepository(FileRepositoryInterface):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            # Main table for verifiable files
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS file_records (
                    source_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    hash TEXT,
                    hash_algo TEXT,
                    extension TEXT,
                    last_modified REAL,
                    status TEXT
                )
            """
            )
            # Separate table for unverified files (missing hash)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS unverified_files (
                    source_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    extension TEXT,
                    last_modified REAL,
                    reason TEXT
                )
            """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_hash ON file_records (hash)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_source ON file_records (source)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_unverified_source ON unverified_files (source)"
            )

            # Migration: Ensure status column exists if it was created previously without it
            try:
                conn.execute("ALTER TABLE file_records ADD COLUMN status TEXT")
            except sqlite3.OperationalError:
                # Column already exists
                pass

            conn.commit()

    def upsert(self, record: FileRecord):
        # If hash is missing and it's from Drive, it goes to unverified_files
        if not record.hash and record.source == "drive":
            self.upsert_unverified(record, "Missing Hash")
            return

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO file_records (source_id, name, size, source, hash, hash_algo, extension, last_modified, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    name=excluded.name,
                    size=excluded.size,
                    source=excluded.source,
                    hash=excluded.hash,
                    hash_algo=excluded.hash_algo,
                    extension=excluded.extension,
                    last_modified=excluded.last_modified,
                    status=excluded.status
            """,
                (
                    record.source_id,
                    record.name,
                    record.size,
                    record.source,
                    record.hash,
                    record.hash_algo,
                    record.extension,
                    record.last_modified,
                    record.status,
                ),
            )
            conn.commit()

    def upsert_unverified(self, record: FileRecord, reason: str = "Unknown"):
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO unverified_files (source_id, name, size, source, extension, last_modified, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    name=excluded.name,
                    size=excluded.size,
                    source=excluded.source,
                    extension=excluded.extension,
                    last_modified=excluded.last_modified,
                    reason=excluded.reason
            """,
                (
                    record.source_id,
                    record.name,
                    record.size,
                    record.source,
                    record.extension,
                    record.last_modified,
                    reason,
                ),
            )
            conn.commit()

    def get_by_source_id(self, source_id: str) -> Optional[FileRecord]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT source_id, name, size, source, hash, hash_algo, extension, last_modified, status FROM file_records WHERE source_id = ?",
                (source_id,),
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_record(row)

            # Check unverified if not found in main
            cursor = conn.execute(
                "SELECT source_id, name, size, source, NULL, NULL, extension, last_modified, 'UNVERIFIED' FROM unverified_files WHERE source_id = ?",
                (source_id,),
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_record(row)

        return None

    def find_duplicates_by_hash(self) -> List[FileRecord]:
        """
        Finds all files that share a hash and size with at least one other file.
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT source_id, name, size, source, hash, hash_algo, extension, last_modified, status
                FROM file_records
                WHERE (hash, size) IN (
                    SELECT hash, size FROM file_records WHERE hash IS NOT NULL GROUP BY hash, size HAVING COUNT(*) > 1
                )
                ORDER BY hash, size
            """
            )
            return [self._row_to_record(row) for row in cursor.fetchall()]

    def update_status(self, source_id: str, status: str):
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE file_records SET status = ? WHERE source_id = ?",
                (status, source_id),
            )
            conn.commit()

    def _row_to_record(self, row: tuple) -> FileRecord:
        return FileRecord(
            source_id=row[0],
            name=row[1],
            size=row[2],
            source=row[3],
            hash=row[4],
            hash_algo=row[5],
            extension=row[6],
            last_modified=row[7],
            status=row[8],
        )
