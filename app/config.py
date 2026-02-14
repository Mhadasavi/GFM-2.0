import os

class Config:
    MONGO_CONNECTION_STRING = os.environ.get("MONGO_CONNECTION_STRING", "mongodb://localhost:27017/")
    SCAN_DIRECTORY = os.environ.get("SCAN_DIRECTORY", "D:\study\Repo\GFM2.0") #Defaulting to the project folder
    HASH_ALGO = os.environ.get("HASH_ALGO", "sha256")
    MAX_WORKERS = int(os.environ.get("MAX_WORKERS", 4))
