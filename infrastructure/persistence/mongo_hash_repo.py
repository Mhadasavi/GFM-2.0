from pymongo import MongoClient
from domain.models import FileRecord
from domain.interfaces import HashRepositoryInterface

class MongoHashRepository(HashRepositoryInterface):
    def __init__(self, connection_string: str, db_name: str = 'inventory', collection_name: str = 'local_files'):
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.collection.create_index("path", unique=True)
        self.collection.create_index([("size", 1), ("hash", 1)])
        self.collection.create_index("hash")

    def upsert(self, record: FileRecord):
        # Convert FileRecord to dict for MongoDB
        record_dict = {
            'path': record.path,
            'name': record.name,
            'extension': record.extension,
            'size': record.size,
            'last_modified': record.last_modified,
            'hash': record.hash,
            'hash_algo': record.hash_algo,
            'source': record.source
        }
        self.collection.update_one(
            {'path': record.path},
            {'$set': record_dict},
            upsert=True
        )

    def get(self, file_path: str) -> FileRecord:
        doc = self.collection.find_one({'path': file_path})
        if doc:
            # Remove MongoDB's internal '_id' before creating the FileRecord
            doc.pop('_id', None)
            return FileRecord(**doc)
        return None
