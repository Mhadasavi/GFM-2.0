import hashlib
from domain.interfaces import HashingServiceInterface

class HashingService(HashingServiceInterface):
    def __init__(self, chunk_size=1024*1024):
        self.chunk_size = chunk_size

    def stream_hash(self, file_path: str, algorithm: str = 'sha256') -> str:
        hasher = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(self.chunk_size), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
