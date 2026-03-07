import os
import sys
import logging
from app.config import Config
from infrastructure.local.local_scanner import LocalScanner
from infrastructure.normalization.local_normalizer import LocalNormalizer
from services.hashing_service import HashingService
from infrastructure.persistence.sqlite_repo import SQLiteFileRepository
from services.inventory_runner import InventoryRunner

from infrastructure.drive.drive_client import DriveClient
from infrastructure.drive.drive_scanner import DriveScanner
from infrastructure.normalization.drive_normalizer import DriveNormalizer
from services.drive_inventory_runner import DriveInventoryRunner
# from services.comparison_service import ComparisonService # Needs refactoring for SQLite
# from services.duplicate_detection_runner import DuplicateDetectionRunner

from utils.logging import get_logger

def run_local_inventory(config, logger):
    logger.info("Starting local inventory run...")
    scanner = LocalScanner()
    normalizer = LocalNormalizer()
    hashing_service = HashingService(chunk_size=1024*1024)
    file_repo = SQLiteFileRepository(config.SQLITE_DB_PATH)
    
    inventory_runner = InventoryRunner(
        scanner=scanner,
        normalizer=normalizer,
        hashing_service=hashing_service,
        file_repo=file_repo,
        max_workers=config.MAX_WORKERS,
        hash_algo=config.HASH_ALGO
    )

    scan_path = config.SCAN_DIRECTORY
    if not os.path.isdir(scan_path):
        logger.error(f"Scan directory not found: {scan_path}")
        return

    inventory_runner.run(scan_path)

def run_drive_inventory(config, logger):
    logger.info("Starting drive inventory run...")
    file_repo = SQLiteFileRepository(config.SQLITE_DB_PATH)

    drive_client = DriveClient(
        credentials_path=config.CREDENTIALS_PATH,
        token_path=config.TOKEN_PATH
    )

    scanner = DriveScanner(drive_client)
    normalizer = DriveNormalizer()

    runner = DriveInventoryRunner(scanner, normalizer, file_repo)
    runner.run()

def run_duplicate_detection(config, logger):
    logger.info("Starting duplicate detection (SQLite)...")
    file_repo = SQLiteFileRepository(config.SQLITE_DB_PATH)
    duplicates = file_repo.find_duplicates_by_hash()
    
    logger.info(f"Found {len(duplicates)} duplicate records across all sources.")
    # For now, just log some info. In a full implementation, we'd output to CSV/Excel as per AC.
    for record in duplicates[:10]: # Log first 10
        logger.info(f"Duplicate: {record.name} ({record.source_id}) - Hash: {record.hash}")

def main():
    logger = get_logger(__name__)
    config = Config()

    if len(sys.argv) < 2:
        print("Usage: python -m app.main [local|drive|compare|all]")
        return

    command = sys.argv[1].lower()

    if command in ['local', 'all']:
        try:
            run_local_inventory(config, logger)
        except Exception as e:
            logger.error(f"Local inventory failed: {e}", exc_info=True)

    if command in ['drive', 'all']:
        try:
            run_drive_inventory(config, logger)
        except Exception as e:
            logger.error(f"Drive inventory failed: {e}", exc_info=True)

    if command in ['compare', 'all']:
        try:
            run_duplicate_detection(config, logger)
        except Exception as e:
            logger.error(f"Duplicate detection failed: {e}", exc_info=True)

if __name__ == "__main__":
    main()
