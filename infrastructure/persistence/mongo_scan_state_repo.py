class MongoScanStateRepository:
    def __init__(self, db):
        self.collection = db["scan_state"]

    def get_last_scan_time(self, source: str):
        doc = self.collection.find_one({"source": source})
        return doc["last_successful_scan_time"] if doc else None

    def update_last_scan_time(self, source: str, timestamp: int):
        self.collection.update_one(
            {"source": source},
            {"$set": {"last_successful_scan_time": timestamp}},
            upsert=True
        )
