import os

class Config:
    SQLITE_DB_PATH = os.environ.get("SQLITE_DB_PATH", "inventory.db")
    MONGO_CONNECTION_STRING = os.environ.get("MONGO_CONNECTION_STRING", "mongodb://admin:StrongPassword123!@localhost:27017/?authSource=admin&directConnection=true")
    MONGO_URI = MONGO_CONNECTION_STRING # Alias for convenience
    DB_NAME = os.environ.get("DB_NAME", "inventory")
    SCAN_DIRECTORY = os.environ.get("SCAN_DIRECTORY", "D:\\Media\\MahadevsWorld\\extra")
    HASH_ALGO = os.environ.get("HASH_ALGO", "sha256")
    MAX_WORKERS = int(os.environ.get("MAX_WORKERS", 4))
    CREDENTIALS_PATH = os.environ.get("CREDENTIALS_PATH", "credentials/credentials.json")
    TOKEN_PATH = os.environ.get("TOKEN_PATH", "credentials/token.json")
    LOG_PATH = os.environ.get("LOG_PATH", "logs/app.log")
    DELETE_OLD_LOGS = os.environ.get("DELETE_OLD_LOGS", "False").lower() == "true"
    LOG_RETENTION_DAYS = int(os.environ.get("LOG_RETENTION_DAYS", 30))
