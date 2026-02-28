import logging
import json
from typing import List, Dict
from pymongo import ASCENDING

logger = logging.getLogger(__name__)


class ComparisonService:
    def __init__(self, local_collection, drive_collection):
        self.local = local_collection
        self.drive = drive_collection

    def find_hash_duplicates(self) -> List[Dict]:
        """
        Find exact duplicates using hash + size.
        Only considers files eligible for deduplication.
        """

        pipeline = [
            {
                "$match": {
                    "hash": {"$ne": None},
                    "eligible_for_dedup": True
                }
            },
            {
                "$lookup": {
                    "from": "local_files",
                    "localField": "hash",
                    "foreignField": "hash",
                    "as": "local_matches"
                }
            },
            {
                "$match": {
                    "local_matches.0": {"$exists": True}
                }
            }
        ]

        results = list(self.drive.aggregate(pipeline))

        logger.info(json.dumps({
            "event": "hash_duplicate_detection_completed",
            "matches_found": len(results)
        }))

        return results
