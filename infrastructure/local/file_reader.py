import hashlib

CHUNK_SIZE = 1024 * 1024  # 1MB

def stream_hash(file_path: str, algo: str = "sha256") -> str:
    hasher = hashlib.new(algo)

    with open(file_path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            hasher.update(chunk)

    return hasher.hexdigest()
