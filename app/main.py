import os
import sys
import logging

from dotenv import load_dotenv

# Load .env before importing Config to ensure it picks up the environment variables
load_dotenv(override=True)

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
from services.duplicate_detection_runner import DuplicateDetectionRunner
from services.deletion_service import DeletionService

from utils.logging import get_logger


def run_local_inventory(config, logger):
    logger.info("Starting local inventory run...")
    scanner = LocalScanner()
    normalizer = LocalNormalizer()
    hashing_service = HashingService(chunk_size=1024 * 1024)
    file_repo = SQLiteFileRepository(config.SQLITE_DB_PATH)

    inventory_runner = InventoryRunner(
        scanner=scanner,
        normalizer=normalizer,
        hashing_service=hashing_service,
        file_repo=file_repo,
        max_workers=config.MAX_WORKERS,
        hash_algo=config.HASH_ALGO,
    )

    scan_path = config.SCAN_DIRECTORY
    if not os.path.isdir(scan_path):
        logger.error(f"Scan directory not found: {scan_path}")
        return

    inventory_runner.run(scan_path)


def run_drive_inventory(config, logger):
    logger.info("Starting drive inventory run...")
    file_repo = SQLiteFileRepository(config.SQLITE_DB_PATH)

    try:
        drive_client = DriveClient(
            credentials_path=config.CREDENTIALS_PATH, token_path=config.TOKEN_PATH
        )
    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
        return

    scanner = DriveScanner(drive_client)
    normalizer = DriveNormalizer()

    runner = DriveInventoryRunner(scanner, normalizer, file_repo)
    runner.run()


def run_duplicate_detection(config, logger):
    logger.info("Starting duplicate detection (SQLite)...")
    file_repo = SQLiteFileRepository(config.SQLITE_DB_PATH)

    runner = DuplicateDetectionRunner(file_repo)
    summary = runner.run()

    logger.info(f"Duplicate detection summary: {summary}")


def run_deletion(config, logger, dry_run=True):
    logger.info(f"Initiating deletion flow (dry_run={dry_run})...")
    file_repo = SQLiteFileRepository(config.SQLITE_DB_PATH)
    drive_client = DriveClient(
        credentials_path=config.CREDENTIALS_PATH, token_path=config.TOKEN_PATH
    )

    service = DeletionService(file_repo, drive_client)
    summary = service.run_deletion(dry_run=dry_run)

    logger.info(f"Deletion flow completed. Summary: {summary}")
    if dry_run:
        print("\n[DRY RUN] Report generated at logs/deletion_report.csv")
        print(f"[DRY RUN] Proposed deletions: {summary['proposed_deletions']}")
    else:
        print("\n[FORCE DELETE] Action completed.")
        print(f"[FORCE DELETE] Files deleted: {summary['actual_deletions']}")


def run_deletion(config, logger, dry_run=True):
    logger.info(f"Initiating deletion flow (dry_run={dry_run})...")
    file_repo = SQLiteFileRepository(config.SQLITE_DB_PATH)

    try:
        drive_client = DriveClient(
            credentials_path=config.CREDENTIALS_PATH, token_path=config.TOKEN_PATH
        )
    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
        return

    service = DeletionService(file_repo, drive_client)
    summary = service.run_deletion(dry_run=dry_run)

    logger.info(f"Deletion flow completed. Summary: {summary}")
    if dry_run:
        print("\n[DRY RUN] Report generated at logs/deletion_report.csv")
        print(f"[DRY RUN] Proposed deletions: {summary['proposed_deletions']}")
    else:
        print("\n[FORCE DELETE] Action completed.")
        print(f"[FORCE DELETE] Files deleted: {summary['actual_deletions']}")


def main():
    logger = get_logger(__name__)
    config = Config()

    if len(sys.argv) < 2:
        print("Usage: python -m app.main [local|drive|compare|delete|all] [--force]")
        return

    command = sys.argv[1].lower()
    force_delete = "--force" in sys.argv

    if command in ["local", "all"]:
        try:
            run_local_inventory(config, logger)
        except Exception as e:
            logger.error(f"Local inventory failed: {e}", exc_info=True)

    if command in ["drive", "all"]:
        try:
            run_drive_inventory(config, logger)
        except Exception as e:
            logger.error(f"Drive inventory failed: {e}", exc_info=True)

    if command in ["compare", "all"]:
        try:
            run_duplicate_detection(config, logger)
        except Exception as e:
            logger.error(f"Duplicate detection failed: {e}", exc_info=True)

    if command == "delete":
        try:
            run_deletion(config, logger, dry_run=(not force_delete))
        except Exception as e:
            logger.error(f"Deletion process failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()
