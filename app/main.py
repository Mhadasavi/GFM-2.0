import os
import sys
import logging

from dotenv import load_dotenv

# Load .env before importing Config to ensure it picks up the environment variables
load_dotenv(override=True)

from sqlalchemy import create_engine
from domain.models import Base
from app.config import Config
from infrastructure.local.local_scanner import LocalScanner
from infrastructure.normalization.local_normalizer import LocalNormalizer
from services.hashing_service import HashingService
from infrastructure.persistence.sqlalchemy_repo import (
    SQLAlchemyFileRepository,
    SQLAlchemyScanStateRepository,
    SQLAlchemyDriveRepository,
)
from services.inventory_runner import InventoryRunner

from infrastructure.drive.drive_client import DriveClient
from infrastructure.drive.drive_scanner import DriveScanner
from infrastructure.normalization.drive_normalizer import DriveNormalizer
from services.drive_inventory_runner import DriveInventoryRunner
from services.duplicate_detection_runner import DuplicateDetectionRunner
from services.deletion_service import DeletionService

from utils.logging import get_logger


def run_local_inventory(config, logger, file_repo, state_repo, limit=None):
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

    # Add limit support to local scan (we'll modify runner slightly if needed)
    inventory_runner.run(scan_path)


def run_drive_inventory(
    config, logger, file_repo, drive_repo, state_repo, folder_id=None, limit=None
):
    logger.info(
        f"Starting drive inventory run (folder_id={folder_id}, limit={limit})..."
    )

    try:
        drive_client = DriveClient(
            credentials_path=config.CREDENTIALS_PATH, token_path=config.TOKEN_PATH
        )
    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
        return

    # Enable incremental scanning if we have a last scan time AND no limit/folder is forced
    last_scan_time = None
    if not folder_id and not limit:
        last_scan_time = state_repo.get_last_scan_time("drive")
        if last_scan_time:
            logger.info(f"Using incremental scan from timestamp: {last_scan_time}")

    scanner = DriveScanner(drive_client, last_scan_time=last_scan_time)
    normalizer = DriveNormalizer()

    runner = DriveInventoryRunner(
        scanner, normalizer, file_repo, drive_repo, state_repo
    )
    runner.run(source_path=folder_id, limit=limit)


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

    # Create tables once
    engine = create_engine(config.DATABASE_URL)
    Base.metadata.create_all(engine)

    # Shared repository instances
    file_repo = SQLAlchemyFileRepository(engine)
    state_repo = SQLAlchemyScanStateRepository(engine)
    drive_repo = SQLAlchemyDriveRepository(engine)

    if len(sys.argv) < 2:
        print(
            "Usage: python -m app.main [local|drive|compare|delete|all] [folder_id] [--limit N] [--force]"
        )
        return

    command = sys.argv[1].lower()

    # Simple argument parsing
    folder_id = None
    limit = None
    force_delete = "--force" in sys.argv

    if "--limit" in sys.argv:
        try:
            limit_idx = sys.argv.index("--limit")
            limit = int(sys.argv[limit_idx + 1])
        except (ValueError, IndexError):
            logger.warning("Invalid limit provided, ignoring.")

    # If the second argument is not a flag, treat it as a folder_id
    if len(sys.argv) > 2 and not sys.argv[2].startswith("--"):
        folder_id = sys.argv[2]

    if command in ["local", "all"]:
        try:
            # Note: local runner doesn't have limit implemented yet, but we'll add it if needed
            run_local_inventory(config, logger, file_repo, state_repo, limit=limit)
        except Exception as e:
            logger.error(f"Local inventory failed: {e}", exc_info=True)

    if command in ["drive", "all"]:
        try:
            run_drive_inventory(
                config,
                logger,
                file_repo,
                drive_repo,
                state_repo,
                folder_id=folder_id,
                limit=limit,
            )
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
