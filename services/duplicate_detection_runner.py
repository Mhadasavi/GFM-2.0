import time
import logging
import json

logger = logging.getLogger(__name__)


class DuplicateDetectionRunner:
    def __init__(self, comparison_service, result_collection):
        self.comparison_service = comparison_service
        self.result_collection = result_collection

    def run(self):
        start = time.time()

        duplicates = self.comparison_service.find_hash_duplicates()

        records = []
        for drive_doc in duplicates:
            for local_doc in drive_doc["local_matches"]:

                records.append({
                    "drive_file_id": drive_doc["drive_file_id"],
                    "local_file_id": local_doc.get("_id"),
                    "hash": drive_doc["hash"],
                    "size": drive_doc["size"],
                    "confidence": 1.0,
                    "decision": "SAFE_DELETE",
                    "created_at": int(time.time())
                })

        if records:
            self.result_collection.insert_many(records)

        logger.info(json.dumps({
            "event": "duplicate_detection_completed",
            "total_duplicates": len(records),
            "duration_sec": round(time.time() - start, 2)
        }))
