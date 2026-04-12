import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional
from app.config import Config
from domain.interfaces import (
    ScannerInterface,
    HashingServiceInterface,
    FileRepositoryInterface,
    NormalizerInterface,
    ScanStateRepositoryInterface
)
from domain.models import FileRecord
from utils.logging import get_logger

logger = get_logger(__name__)


class InventoryRunner:
    def __init__(
        self,
        scanner: ScannerInterface,
        normalizer: NormalizerInterface,
        hashing_service: HashingServiceInterface,
        file_repo: FileRepositoryInterface,
        state_repo: Optional[ScanStateRepositoryInterface] = None,
        max_workers: int = Config.MAX_WORKERS,
        hash_algo: str = Config.HASH_ALGO,
    ):
        self.scanner = scanner
        self.normalizer = normalizer
        self.hashing_service = hashing_service
        self.file_repo = file_repo
        self.state_repo = state_repo
        self.max_workers = max_workers
        self.hash_algo = hash_algo

    def run(self, dir_path: str):
        logger.info(f"Starting inventory run for directory: {dir_path}")

        # We need to collect files that need hashing
        files_to_hash = []
        for raw_data in self.scanner.scan(dir_path):
            record = self.normalizer.normalize(raw_data)
            cached_record = self.file_repo.get_by_source_id(record.source_id)

            if (
                not cached_record
                or cached_record.last_modified != record.last_modified
                or not cached_record.hash
            ):
                files_to_hash.append(record)
            else:
                logger.debug(f"Cache hit for {record.source_id}. Skipping hashing.")

        logger.info(f"Found files, {len(files_to_hash)} need hashing.")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._process_file, record): record
                for record in files_to_hash
            }
            for future in as_completed(futures):
                record = futures[future]
                try:
                    future.result()
                except Exception as exc:
                    logger.error(f"{record.source_id} generated an exception: {exc}")

        # Update scan state after successful run
        if self.state_repo:
            now = int(time.time())
            self.state_repo.update_last_scan_time("local", now)

        logger.info("Inventory run completed.")

    def _process_file(self, record: FileRecord):
        logger.info(f"Processing file: {record.source_id}")
        try:
            # For local files, source_id is the path
            hash_value = self.hashing_service.stream_hash(
                record.source_id, self.hash_algo
            )

            # Create a new FileRecord with the hash
            hashed_record = FileRecord(
                source_id=record.source_id,
                name=record.name,
                size=record.size,
                source=record.source,
                hash=hash_value,
                hash_algo=self.hash_algo,
                extension=record.extension,
                last_modified=record.last_modified,
                confidence_score=0
            )

            self.file_repo.upsert(hashed_record)
            logger.info(
                f"Successfully processed and stored hash for {record.source_id}"
            )
        except Exception as e:
            logger.error(f"Failed to process file {record.source_id}: {e}")
