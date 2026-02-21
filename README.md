# GFM 2.0 (Google File Manager)

A robust tool to synchronize, deduplicate, and manage files between local storage and Google Drive. GFM 2.0 identifies exact duplicates using content-based hashing to safely manage your cloud storage.

## Features

- **Local Inventory:** Recursively scans local directories and computes content hashes (SHA-256) for image files.
- **Drive Inventory:** Fetches Google Drive metadata and MD5 checksums incrementally to minimize API calls.
- **Duplicate Detection:** Compares local and Drive inventories to identify exact duplicates safely for deletion.
- **Persistence:** Uses MongoDB for efficient storage and querying of file metadata and scan states.

## Prerequisites

- **Python 3.8+**
- **MongoDB:** A running instance (local or Atlas).
- **Google Cloud Project:** With Drive API enabled and OAuth 2.0 credentials.

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
| `MONGO_CONNECTION_STRING` | MongoDB connection URI | `mongodb://localhost:27017/` |
| `DB_NAME` | Database name | `gfm_dev` |
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
