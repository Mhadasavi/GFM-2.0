# GFM 2.0 (Google File Manager)

A robust tool to synchronize, deduplicate, and manage files between local storage and Google Drive. GFM 2.0 identifies exact duplicates using content-based hashing to safely manage your cloud storage.

## Features

- **Local Inventory:** Recursively scans local directories and computes content hashes (SHA-256) for image files.
- **Drive Inventory:** Fetches Google Drive metadata and MD5 checksums incrementally to minimize API calls.
- **Duplicate Detection (Engine):**
    - **O(n) Comparison:** High-speed lookup using memory-efficient sets.
    - **Hash + Size Match:** Strictly identifies duplicates based on both content hash and file size.
    - **Status Tracking:** Automatically marks files as `DUPLICATE`, `UNIQUE`, or `UNVERIFIED` in the database.
- **Unverified Files Handling:** Automatically moves files without MD5 hashes (like Google-native Docs/Sheets) to a separate table for safety.
- **Persistence:** Uses SQLite for primary inventory and duplicate tracking. (Legacy support for MongoDB available).
- **Daily Rotating Logs:** Built-in logging with daily rollover and configurable retention.

## Prerequisites

- **Python 3.8+**
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
| `SQLITE_DB_PATH` | SQLite database file path | `inventory.db` |
| `SCAN_DIRECTORY` | Local directory to scan | (See config.py) |
| `HASH_ALGO` | Hash algorithm for local files | `sha256` |
| `MAX_WORKERS` | Parallel workers for hashing | `4` |
| `LOG_PATH` | Path to the application log file | `logs/app.log` |
| `DELETE_OLD_LOGS` | Whether to delete logs older than retention | `False` |
| `LOG_RETENTION_DAYS` | Number of days to keep log files | `30` |
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

## Logging

GFM 2.0 uses a **Timed Rotating File Handler** for logging:
- **Daily Rotation:** A new log file is created at midnight every day.
- **Retention:** By default, it keeps logs forever (`DELETE_OLD_LOGS=False`). If enabled, it will maintain a rolling window of the last `LOG_RETENTION_DAYS` (default: 30).
- **Console & File:** Logs are simultaneously printed to the console and saved to disk.

## Safety Rules

- **Hash Match (Mandatory):** No file is ever considered a duplicate without an exact hash match.
- **Size Match (Mandatory):** Adds an extra layer of security before marking for deletion.
- **Unverified Isolation:** Files missing MD5 hashes (mostly Google Docs) are moved to the `unverified_files` table and never marked as duplicates automatically.
- **Local Confirmation:** A Drive file is only marked `DUPLICATE` if a confirmed copy exists in your local inventory.

## Project Structure

- `app/`: Application entry point and configuration.
- `services/`: Core business logic (comparison engine, runners).
- `infrastructure/`: External integrations (Drive, Local FS, Persistence).
- `domain/`: Business models, interfaces, and rules.
- `utils/`: Shared utilities (logging, validation).
- `logs/`: Automatically created directory for daily logs.

## License

MIT
