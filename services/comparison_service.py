import logging
from typing import Dict, Set, Tuple
from infrastructure.persistence.sqlite_repo import SQLiteFileRepository

logger = logging.getLogger(__name__)

class ComparisonService:
    def __init__(self, repo: SQLiteFileRepository):
        self.repo = repo

    def run_comparison(self) -> Dict[str, int]:
        """
        Compare Drive files against Local inventory using Hash + Size.
        Updates statuses in the database: DUPLICATE, UNIQUE, UNVERIFIED.
        Returns a summary of the results.
        """
        logger.info("Starting comparison: Drive vs Local...")
        
        # 1. Load all Local hashes into an O(1) lookup structure
        # We only care about (hash, size) pairs for exact duplicates
        local_lookup: Set[Tuple[str, int]] = set()
        
        # We need a way to get all records from a source. 
        # I'll add a helper method to the repository for this.
        local_records = self._get_records_by_source('local')
        for record in local_records:
            if record.hash:
                local_lookup.add((record.hash, record.size))
        
        logger.info(f"Loaded {len(local_lookup)} unique local hash/size pairs.")

        # 2. Iterate through Drive records and mark status
        drive_records = self._get_records_by_source('drive')
        
        summary = {
            "DUPLICATE": 0,
            "UNIQUE": 0,
            "UNVERIFIED": 0,
            "TOTAL": len(drive_records)
        }

        for record in drive_records:
            status = "UNIQUE"
            
            if not record.hash:
                status = "UNVERIFIED"
            elif (record.hash, record.size) in local_lookup:
                status = "DUPLICATE"
            
            self.repo.update_status(record.source_id, status)
            summary[status] += 1

        logger.info(f"Comparison complete: {summary}")
        return summary

    def _get_records_by_source(self, source: str):
        # Temporary internal helper until I add it to the repo properly
        with self.repo._get_connection() as conn:
            cursor = conn.execute(
                "SELECT source_id, name, size, source, hash, hash_algo, extension, last_modified, status FROM file_records WHERE source = ?",
                (source,)
            )
            return [self.repo._row_to_record(row) for row in cursor.fetchall()]
