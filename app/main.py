import os
import sys
import logging
from pymongo import MongoClient
from app.config import Config
from infrastructure.local.local_scanner import LocalScanner
from services.hashing_service import HashingService
from infrastructure.persistence.mongo_hash_repo import MongoHashRepository
from services.inventory_runner import InventoryRunner

from infrastructure.drive.drive_client import DriveClient
from infrastructure.drive.drive_scanner import DriveScanner
from infrastructure.persistence.mongo_drive_repo import MongoDriveRepository
from infrastructure.persistence.mongo_scan_state_repo import MongoScanStateRepository
from services.drive_inventory_runner import DriveInventoryRunner

from utils.logging import get_logger

def run_local_inventory(config, logger):
    logger.info("Starting local inventory run...")
    scanner = LocalScanner()
    hashing_service = HashingService(chunk_size=1024*1024)
    hash_repo = MongoHashRepository(
        connection_string=config.MONGO_CONNECTION_STRING,
        db_name=config.DB_NAME,
        collection_name='file_hashes'
    )
    
    inventory_runner = InventoryRunner(
        scanner=scanner,
        hashing_service=hashing_service,
        hash_repo=hash_repo,
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
    client = MongoClient(config.MONGO_URI)
    db = client[config.DB_NAME]

    state_repo = MongoScanStateRepository(db)
    last_scan = state_repo.get_last_scan_time("drive")

    drive_client = DriveClient(
        credentials_path=config.CREDENTIALS_PATH,
        token_path=config.TOKEN_PATH
    )

    scanner = DriveScanner(drive_client, last_scan)
    drive_repo = MongoDriveRepository(db)

    runner = DriveInventoryRunner(scanner, drive_repo, state_repo)
    runner.run()

def main():
    logger = get_logger(__name__)
    config = Config()

    if len(sys.argv) < 2:
        print("Usage: python -m app.main [local|drive|all]")
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

if __name__ == "__main__":
    main()
