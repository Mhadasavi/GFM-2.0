import time
import logging
from infrastructure.persistence.sqlite_repo import SQLiteFileRepository
from services.comparison_service import ComparisonService

logger = logging.getLogger(__name__)


class DuplicateDetectionRunner:
    def __init__(self, repo: SQLiteFileRepository):
        self.repo = repo
        self.comparison_service = ComparisonService(repo)

    def run(self):
        """
        Runs the comparison engine to mark duplicates.
        """
        start = time.time()
        logger.info("Starting duplicate detection engine...")

        try:
            summary = self.comparison_service.run_comparison()

            duration = round(time.time() - start, 2)
            logger.info(f"Duplicate detection completed in {duration}s.")
            logger.info(f"Summary: {summary}")

            return summary

        except Exception as e:
            logger.error(f"Duplicate detection failed: {e}", exc_info=True)
            raise
