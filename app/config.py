import os

class Config:
    MONGO_CONNECTION_STRING = os.environ.get("MONGO_CONNECTION_STRING", "mongodb://localhost:27017/")
    MONGO_URI = MONGO_CONNECTION_STRING # Alias for convenience
    DB_NAME = os.environ.get("DB_NAME", "gfm_dev")
    SCAN_DIRECTORY = os.environ.get("SCAN_DIRECTORY", "D:\\study\\Repo\\GFM2.0")
    HASH_ALGO = os.environ.get("HASH_ALGO", "sha256")
    MAX_WORKERS = int(os.environ.get("MAX_WORKERS", 4))
    CREDENTIALS_PATH = os.environ.get("CREDENTIALS_PATH", "credentials/credentials.json")
    TOKEN_PATH = os.environ.get("TOKEN_PATH", "credentials/token.json")
