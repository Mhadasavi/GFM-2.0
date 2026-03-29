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
from infrastructure.persistence.sqlalchemy_repo import (
    SQLAlchemyFileRepository,
    SQLAlchemyScanStateRepository,
    SQLAlchemyDriveRepository
)
from services.inventory_runner import InventoryRunner

from infrastructure.drive.drive_client import DriveClient
from infrastructure.drive.drive_scanner import DriveScanner
from infrastructure.normalization.drive_normalizer import DriveNormalizer
from services.drive_inventory_runner import DriveInventoryRunner
from services.duplicate_detection_runner import DuplicateDetectionRunner
from services.deletion_service import DeletionService

from utils.logging import get_logger


def run_local_inventory(config, logger, file_repo, state_repo):
    logger.info("Starting local inventory run...")
    scanner = LocalScanner()
    normalizer = LocalNormalizer()
    hashing_service = HashingService(chunk_size=1024 * 1024)

    inventory_runner = InventoryRunner(
        scanner=scanner,
        normalizer=normalizer,
        hashing_service=hashing_service,
        file_repo=file_repo,
        state_repo=state_repo,
        max_workers=config.MAX_WORKERS,
        hash_algo=config.HASH_ALGO,
    )

    scan_path = config.SCAN_DIRECTORY
    if not os.path.isdir(scan_path):
        logger.error(f"Scan directory not found: {scan_path}")
        return

    inventory_runner.run(scan_path)


def run_drive_inventory(config, logger, file_repo, drive_repo, state_repo):
    logger.info("Starting drive inventory run...")

    try:
        drive_client = DriveClient(
            credentials_path=config.CREDENTIALS_PATH, token_path=config.TOKEN_PATH
        )
    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
        return

    # Enable incremental scanning if we have a last scan time
    last_scan_time = state_repo.get_last_scan_time("drive")
    if last_scan_time:
        logger.info(f"Using incremental scan from timestamp: {last_scan_time}")

    scanner = DriveScanner(drive_client, last_scan_time=last_scan_time)
    normalizer = DriveNormalizer()

    runner = DriveInventoryRunner(scanner, normalizer, file_repo, drive_repo, state_repo)
    runner.run()


def run_duplicate_detection(config, logger, file_repo):
    logger.info("Starting duplicate detection (PostgreSQL)...")

    runner = DuplicateDetectionRunner(file_repo)
    summary = runner.run()

    logger.info(f"Duplicate detection summary: {summary}")


def run_deletion(config, logger, file_repo, dry_run=True):
    logger.info(f"Initiating deletion flow (dry_run={dry_run})...")
    
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

    # Shared repository instances
    file_repo = SQLAlchemyFileRepository(config.DATABASE_URL)
    state_repo = SQLAlchemyScanStateRepository(config.DATABASE_URL)
    drive_repo = SQLAlchemyDriveRepository(config.DATABASE_URL)

    if len(sys.argv) < 2:
        print("Usage: python -m app.main [local|drive|compare|delete|all] [--force]")
        return

    command = sys.argv[1].lower()
    force_delete = "--force" in sys.argv

    if command in ["local", "all"]:
        try:
            run_local_inventory(config, logger, file_repo, state_repo)
        except Exception as e:
            logger.error(f"Local inventory failed: {e}", exc_info=True)

    if command in ["drive", "all"]:
        try:
            run_drive_inventory(config, logger, file_repo, drive_repo, state_repo)
        except Exception as e:
            logger.error(f"Drive inventory failed: {e}", exc_info=True)

    if command in ["compare", "all"]:
        try:
            run_duplicate_detection(config, logger, file_repo)
        except Exception as e:
            logger.error(f"Duplicate detection failed: {e}", exc_info=True)

    if command == "delete":
        try:
            run_deletion(config, logger, file_repo, dry_run=(not force_delete))
        except Exception as e:
            logger.error(f"Deletion process failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()
