import os
from app.config import Config
from infrastructure.local.local_scanner import LocalScanner
from services.hashing_service import HashingService
from infrastructure.persistence.mongo_hash_repo import MongoHashRepository
from services.inventory_runner import InventoryRunner
from utils.logging import get_logger

def main():
    """
    Main entry point for the application.
    Initializes and runs the inventory process.
    """
    logger = get_logger(__name__)
    logger.info("Application starting...")

    # Configuration
    config = Config()
    
    # Dependency Injection / Wiring
    scanner = LocalScanner()
    hashing_service = HashingService(chunk_size=1024*1024) # 1MB chunks
    hash_repo = MongoHashRepository(
        connection_string=config.MONGO_CONNECTION_STRING,
        db_name='gfm_dev',
        collection_name='file_hashes'
    )
    
    inventory_runner = InventoryRunner(
        scanner=scanner,
        hashing_service=hashing_service,
        hash_repo=hash_repo,
        max_workers=config.MAX_WORKERS,
        hash_algo=config.HASH_ALGO
    )

    # Execution
    scan_path = config.SCAN_DIRECTORY
    if not os.path.isdir(scan_path):
        logger.error(f"Scan directory not found: {scan_path}")
        return

    try:
        inventory_runner.run(scan_path)
    except Exception as e:
        logger.critical(f"A critical error occurred: {e}", exc_info=True)

    logger.info("Application finished.")

if __name__ == "__main__":
    main()
