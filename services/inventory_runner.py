from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List
from domain.interfaces import ScannerInterface, HashingServiceInterface, HashRepositoryInterface
from domain.models import FileRecord
from utils.logging import get_logger

logger = get_logger(__name__)

class InventoryRunner:
    def __init__(
        self,
        scanner: ScannerInterface,
        hashing_service: HashingServiceInterface,
        hash_repo: HashRepositoryInterface,
        max_workers: int = 4,
        hash_algo: str = 'sha256'
    ):
        self.scanner = scanner
        self.hashing_service = hashing_service
        self.hash_repo = hash_repo
        self.max_workers = max_workers
        self.hash_algo = hash_algo

    def run(self, dir_path: str):
        logger.info(f"Starting inventory run for directory: {dir_path}")
        files_to_process = self._get_files_to_process(dir_path)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._process_file, file): file for file in files_to_process}
            for future in as_completed(futures):
                file = futures[future]
                try:
                    future.result()
                except Exception as exc:
                    logger.error(f'{file.path} generated an exception: {exc}')
        
        logger.info("Inventory run completed.")

    def _get_files_to_process(self, dir_path: str) -> List[FileRecord]:
        all_files = self.scanner.scan(dir_path)
        files_to_process = []
        for file in all_files:
            cached_file = self.hash_repo.get(file.path, file.last_modified)
            if not cached_file or not cached_file.hash:
                files_to_process.append(file)
            else:
                logger.debug(f"Cache hit for {file.path}. Skipping hashing.")
                # If we have a cached record, we can upsert it to update other metadata if needed
                # For now, we assume if it's cached, it's fine.
                pass
        
        logger.info(f"Found {len(all_files)} files, {len(files_to_process)} need processing.")
        return files_to_process

    def _process_file(self, file: FileRecord):
        logger.info(f"Processing file: {file.path}")
        try:
            hash_value = self.hashing_service.stream_hash(file.path, self.hash_algo)
            
            # Create a new FileRecord with the hash
            hashed_record = FileRecord(
                path=file.path,
                name=file.name,
                extension=file.extension,
                size=file.size,
                last_modified=file.last_modified,
                hash=hash_value,
                hash_algo=self.hash_algo,
                source=file.source
            )
            
            self.hash_repo.upsert(hashed_record)
            logger.info(f"Successfully processed and stored hash for {file.path}")
        except Exception as e:
            logger.error(f"Failed to process file {file.path}: {e}")
            # Optionally, you could store a record with an error state
            # in the database to avoid retrying problematic files.
