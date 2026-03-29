# GFM 2.0 (Google File Manager)

A robust tool to synchronize, deduplicate, and manage files between local storage and Google Drive. GFM 2.0 identifies exact duplicates using content-based hashing to safely manage your cloud storage.

## Features

- **Local Inventory:** Recursively scans local directories and computes content hashes (SHA-256) for image files.
- **Drive Inventory:** Fetches Google Drive metadata and MD5 checksums incrementally to minimize API calls.
- **Duplicate Detection (Engine):**
    - **O(n) Comparison:** High-speed lookup using memory-efficient dictionaries.
    - **Status Tracking:** Automatically marks files as `DUPLICATE`, `UNIQUE`, or `UNVERIFIED`.
- **Confidence Scoring Engine:**
    - **Defense-in-Depth:** Every potential duplicate is assigned a score (0-100).
    - **Weighted Scoring:**
        - Hash Match: **70%**
        - Size Match: **20%**
        - Extension Match: **5%**
        - Filename Match: **5%**
    - **Safety Threshold:** Only files with a score **≥ 90** are marked for deletion.
- **Auditable Decisions:** Every scoring decision is recorded in `logs/audit.csv` with detailed metadata.
- **Unverified Files Handling:** Google-native files (Docs, Sheets) or files missing hashes are isolated in a separate `unverified_files` table.
- **Persistence:** Uses SQLite for primary inventory and duplicate tracking.
- **Daily Rotating Logs:** Built-in logging with daily rollover and configurable retention.
- **Dry-Run Deletion (Safety-First):**
    - **Default Mode:** Every deletion command runs in dry-run mode by default.
    - **Move to Trash:** Files are moved to the Google Drive Trash (not permanently deleted), allowing for easy recovery.
    - **Rate-Limited API:** Built-in delays to respect Google Drive API quotas.
    - **Detailed Action Reports:** Generates a `logs/deletion_report.csv` with the final status of every file.

## Prerequisites

- **Python 3.8+**
- **Google Cloud Project:** With Drive API enabled and OAuth 2.0 credentials.

### Getting Google Drive Credentials

To use the Google Drive features, you must provide a `credentials.json` file:

1.  **Go to the [Google Cloud Console](https://console.cloud.google.com/).**
2.  **Create a New Project** (or select an existing one).
3.  **Enable the Drive API:**
    - Go to **APIs & Services > Library**.
    - Search for "Google Drive API" and click **Enable**.
4.  **Configure OAuth Consent Screen:**
    - Go to **APIs & Services > OAuth consent screen**.
    - Select **External** (or Internal if you have a Workspace) and click **Create**.
    - Fill in the required app information (App name, User support email, Developer contact info).
    - Add the scope: `.../auth/drive` (or simply `https://www.googleapis.com/auth/drive`).
    - Add your email to **Test users** (CRITICAL: while in "Testing" mode, only these users can log in).
5.  **Create Credentials:**
    - Go to **APIs & Services > Credentials**.
    - Click **+ CREATE CREDENTIALS** and select **OAuth client ID**.
    - Set **Application type** to **Desktop app**.
    - Give it a name (e.g., "GFM 2.0") and click **Create**.
6.  **Download JSON:**
    - Find your new credential under **OAuth 2.0 Client IDs**.
    - Click the **Download JSON** icon (down arrow) on the right.
    - Rename the downloaded file to `credentials.json`.
7.  **Place the file:**
    - Move `credentials.json` into the `credentials/` directory of this project.

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

### 3. Detect Duplicates & Score
```bash
python -m app.main compare
```

### 4. Delete Verified Duplicates (Safety Mode)
Generates a report of files marked for deletion. Moves files to trash only with `--force`.
```bash
python -m app.main delete
```

### 5. Execute Deletion (Permanent Action)
Moves all verified duplicates (score ≥ 90) to the Google Drive Trash.
```bash
python -m app.main delete --force
```

### 6. Run All Steps
Executes local scan, Drive scan, and duplicate detection sequentially.
```bash
python -m app.main all
```

## Logging & Auditing

- **App Logs (`logs/app.log`):** Daily rotating system logs for debugging and monitoring. Actions like moving a file to trash are logged with timestamps and file hashes.
- **Audit Logs (`logs/audit.csv`):** Permanent record of every duplicate decision, including the specific confidence score and hash.
- **Deletion Reports (`logs/deletion_report.csv`):** Detailed CSV generated after every deletion run (dry-run or force). Includes Drive ID, Name, Score, Hash, and Final Status (e.g., `TRASHED_SUCCESS`, `SKIPPED_DRY_RUN`).

## Safety Rules (Confidence Engine)

- **Mandatory Match:** No file is marked as a duplicate without matching both Hash and Size (minimum score of 90).
- **Explicit Thresholds:** Files with a score below 90 (e.g., matching hash but different size) are marked `UNIQUE` and kept safe.
- **Unverified Isolation:** Files without checksums are NEVER automatically marked for deletion.

## Project Structure

- `app/`: Application entry point and configuration.
- `services/`: Core business logic (Comparison & Confidence Engine).
- `infrastructure/`: External integrations (Drive, Local FS, SQLite).
- `domain/`: Business models, interfaces, and rules.
- `utils/`: Shared utilities (logging, validation).
- `logs/`: Automatically created directory for daily logs.

## License

MIT
