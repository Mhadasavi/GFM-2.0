from pymongo import MongoClient
from domain.models import FileRecord
from domain.interfaces import HashRepositoryInterface

class MongoHashRepository(HashRepositoryInterface):
    def __init__(self, connection_string: str, db_name: str = 'gfm', collection_name: str = 'hashes'):
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.collection.create_index([('path', 1), ('last_modified', 1)], unique=True)
        self.collection.create_index([('hash', 1)])

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
            {'path': record.path, 'last_modified': record.last_modified},
            {'$set': record_dict},
            upsert=True
        )

    def get(self, file_path: str, last_modified: float) -> FileRecord:
        doc = self.collection.find_one({'path': file_path, 'last_modified': last_modified})
        if doc:
            # Remove MongoDB's internal '_id' before creating the FileRecord
            doc.pop('_id', None)
            return FileRecord(**doc)
        return None
