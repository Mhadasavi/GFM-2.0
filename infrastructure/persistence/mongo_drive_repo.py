import logging
import json
from pymongo import UpdateOne

logger = logging.getLogger(__name__)


class MongoDriveRepository:
    def __init__(self, db):
        self.collection = db["drive_files"]
        self._ensure_indexes()

    def _ensure_indexes(self):
        self.collection.create_index("drive_file_id", unique=True)
        self.collection.create_index("hash")
        self.collection.create_index("last_modified")
        self.collection.create_index("eligible_for_dedup")

    def upsert_many(self, records):
        operations = [
            UpdateOne(
                {"drive_file_id": record["drive_file_id"]},
                {"$set": record},
                upsert=True
            )
            for record in records
        ]

        if operations:
            result = self.collection.bulk_write(operations)
            logger.info(json.dumps({
                "event": "drive_bulk_upsert",
                "inserted": result.upserted_count,
                "modified": result.modified_count
            }))
