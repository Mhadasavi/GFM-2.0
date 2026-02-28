# GFM 2.0 (Google File Manager)

A robust tool to synchronize, deduplicate, and manage files between local storage and Google Drive. GFM 2.0 identifies exact duplicates using content-based hashing to safely manage your cloud storage.

## Features

- **Local Inventory:** Recursively scans local directories and computes content hashes (SHA-256) for image files.
- **Drive Inventory:** Fetches Google Drive metadata and MD5 checksums incrementally to minimize API calls.
- **Duplicate Detection:** Compares local and Drive inventories to identify exact duplicates safely for deletion.
- **Persistence:** Uses MongoDB for efficient storage and querying of file metadata and scan states.

## Prerequisites

- **Python 3.8+**
- **Docker & Docker Compose:** For a production-like MongoDB setup.
- **Google Cloud Project:** With Drive API enabled and OAuth 2.0 credentials.

## MongoDB Setup

GFM 2.0 uses a production-style MongoDB configuration with replica sets and authentication for high availability and performance.

### 1. Initialize MongoDB with Docker

Go to the `mongo-prod-setup` directory and start the container:

```bash
cd mongo-prod-setup
docker-compose up -d
```

### 2. Initialize Replica Set and Admin User

Enter the MongoDB container:

```bash
docker exec -it mongodb mongosh
```

Inside the `mongosh` prompt, initialize the replica set:

```javascript
rs.initiate()
```

Wait a few seconds for it to become Primary (check with `rs.status()`), then create the admin user:

```javascript
db.getSiblingDB("admin").createUser({
  user: "admin",
  pwd: "StrongPassword123!",
  roles: [{ role: "root", db: "admin" }]
})
```

### 3. Setup Database and Collections

You can use the provided setup script to create collections and indexes automatically:

```bash
# From the project root
python setup_mongo.py
```

Alternatively, you can manually set them up in `mongosh`:

```javascript
use inventory

db.createCollection("local_files")
db.createCollection("drive_files")
db.createCollection("deletion_batches")

// Critical indexes for scale
db.local_files.createIndex({ size: 1, hash: 1 })
db.drive_files.createIndex({ size: 1, hash: 1 })
db.local_files.createIndex({ path: 1 }, { unique: true })
db.drive_files.createIndex({ drive_file_id: 1 }, { unique: true })
```

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-repo/gfm2.0.git
   cd gfm2.0
   ```

2. **Set up a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Google Drive Credentials:**
   Place your `credentials.json` in the `credentials/` directory. On the first run, the application will prompt for authentication and save a `token.json`.

## Configuration

The application is configured via environment variables. You can set these in your shell or use a `.env` file.

| Variable | Description | Default |
| :--- | :--- | :--- |
| `MONGO_CONNECTION_STRING` | MongoDB connection URI | `mongodb://admin:StrongPassword123!@localhost:27017/?authSource=admin&directConnection=true` |
| `DB_NAME` | Database name | `inventory` |
| `SCAN_DIRECTORY` | Local directory to scan | (Project root) |
| `HASH_ALGO` | Hash algorithm for local files | `sha256` |
| `MAX_WORKERS` | Parallel workers for hashing | `4` |
| `CREDENTIALS_PATH` | Path to Google Drive credentials | `credentials/credentials.json` |
| `TOKEN_PATH` | Path to Google Drive token | `credentials/token.json` |

## Usage

Run the application using the following commands:

### 1. Scan Local Files
Builds an inventory of local images and their hashes.
```bash
python -m app.main local
```

### 2. Scan Google Drive
Fetches metadata and MD5 checksums for Drive files.
```bash
python -m app.main drive
```

### 3. Detect Duplicates
Compares local and Drive records to find safe-to-delete duplicates.
```bash
python -m app.main compare
```

### 4. Run All Steps
Executes local scan, Drive scan, and duplicate detection sequentially.
```bash
python -m app.main all
```

## Project Structure

- `app/`: Application entry point and configuration.
- `services/`: Core business logic and runners.
- `infrastructure/`: External integrations (Drive, Local FS, MongoDB).
- `domain/`: Business models and interfaces.
- `utils/`: Shared utilities like logging and validation.

## Safety Rules

- Only files with matching hashes and sizes are marked for deletion.
- Files must be explicitly marked as `eligible_for_dedup` (e.g., binary images with valid checksums).
- No actual deletion occurs in the current version; results are stored in the `duplicate_results` collection for review.

## License

MIT
