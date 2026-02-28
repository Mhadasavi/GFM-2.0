import os

class Config:
    MONGO_CONNECTION_STRING = os.environ.get("MONGO_CONNECTION_STRING", "mongodb://admin:StrongPassword123!@localhost:27017/?authSource=admin&directConnection=true")
    MONGO_URI = MONGO_CONNECTION_STRING # Alias for convenience
    DB_NAME = os.environ.get("DB_NAME", "inventory")
    SCAN_DIRECTORY = os.environ.get("SCAN_DIRECTORY", "D:\\Media\\MahadevsWorld\\extra\\img")
    HASH_ALGO = os.environ.get("HASH_ALGO", "sha256")
    MAX_WORKERS = int(os.environ.get("MAX_WORKERS", 4))
    CREDENTIALS_PATH = os.environ.get("CREDENTIALS_PATH", "credentials/credentials.json")
    TOKEN_PATH = os.environ.get("TOKEN_PATH", "credentials/token.json")
