import os
from pymongo import MongoClient
from dotenv import load_dotenv


def setup_mongo():
    # Load .env from the mongo-prod-setup directory
    env_path = os.path.join("mongo-prod-setup", ".env")
    load_dotenv(env_path)

    user = os.getenv("MONGO_ROOT_USER", "admin")
    password = os.getenv("MONGO_ROOT_PASSWORD", "StrongPassword123!")
    db_name = os.getenv("MONGO_DB", "inventory")

    # Connection string for a local mongo with auth
    # Added directConnection=true to bypass replica set discovery for single-node local setup
    connection_string = f"mongodb://{user}:{password}@localhost:27017/?authSource=admin&directConnection=true"

    print(f"Connecting to MongoDB at localhost:27017...")
    client = MongoClient(connection_string)

    db = client[db_name]

    print(f"Creating collections in '{db_name}'...")
    collections = ["local_files", "drive_files", "deletion_batches"]
    for col in collections:
        if col not in db.list_collection_names():
            db.create_collection(col)
            print(f"  Created collection: {col}")
        else:
            print(f"  Collection already exists: {col}")

    print("Adding indexes...")

    # Local Files Indexes
    db.local_files.create_index([("size", 1), ("hash", 1)])
    db.local_files.create_index([("path", 1)], unique=True)

    # Drive Files Indexes
    db.drive_files.create_index([("size", 1), ("hash", 1)])
    db.drive_files.create_index([("drive_file_id", 1)], unique=True)

    print("MongoDB setup completed successfully.")


if __name__ == "__main__":
    setup_mongo()
