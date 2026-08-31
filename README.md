# eVitalConnects (eVital<>Tally Connects)

A desktop application that synchronizes accounting data between **TallyPrime** (an Indian accounting software) and the **eVitalRx / eVitalSupply** cloud platform. It extracts financial reports and vouchers from Tally, transforms them, and pushes them to the eVitalRx API — and vice-versa for importing eVitalRx data back into Tally.

---

## Table of Contents

- [Overview](#overview)
- [How the App Works](#how-the-app-works)
- [Auto-Update System](#auto-update-system)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Running the App (Development)](#running-the-app-development)
- [Building the App](#building-the-app)
- [Publishing a Release](#publishing-a-release)
- [Build Commands Reference](#build-commands-reference)
- [Configuration](#configuration)
- [Environment Variables](#environment-variables)

---

## Overview

eVitalConnects is a Tkinter-based desktop utility that bridges **TallyPrime** (running locally on port 9000) and the **eVitalRx** API (cloud-hosted). The app:

1. **Authenticates** the user against the eVitalRx API using a mobile number and password.
2. **Maps** eVitalRx business accounts to Tally companies (single or multiple mapping).
3. **Extracts** financial data (ledgers, groups, balance sheet, P&L, ratio analysis, vouchers) from Tally via its XML API.
4. **Imports** eVitalRx data (accounts, sales, purchases, payments, receipts, contra) back into Tally as XML vouchers.
5. **Reconciles** transactions between the two systems.
6. **Logs** all activity to an encrypted log file (`lib/app_logs.txt`).
7. **Auto-updates** — checks GitHub Releases for new builds, downloads the zip, swaps the executable + `lib/`, and relaunches itself.

---

## How the App Works

### Entry Point & Startup Flow

The application starts at **`app.py`**, which orchestrates the initial setup:

1. **DPI Awareness** — Sets Windows DPI awareness so the UI renders correctly on high-DPI displays.
2. **Splash Screen** — If running as a PyInstaller bundle, the splash screen is updated and closed.
3. **Font Loading** — Loads the custom `Manrope` font via `pyglet`.
4. **Logging** — Initializes the `LogManager` (from `log.py`) which writes encrypted log entries to `lib/app_logs.txt` and auto-clears logs daily.
5. **Crash Recovery (update leftovers)** — If a previous update was interrupted:
   - If an `_update_in_progress` marker file is found, the app restores any `*.old` executables left behind by a half-finished update.
   - Leftover `*.old` / `_update_debug.log` files are deleted (with retries to survive antivirus locks), falling back to a detached PowerShell cleanup process.
6. **Cache Check** — Reads `lib/app_cache.txt` (encrypted with Fernet). If a valid cached login exists:
   - Restores login response, API keys, access tokens, and Tally connection settings.
   - Fetches the list of Tally companies.
   - Shows the **Dashboard** screen.
   - If no valid cache exists, shows the **LoginScreen**.
7. **Startup Update Check** — In the background, `_startup_force_check()` queries GitHub Releases. If a **force update** is pending, the mandatory-update dialog is shown as soon as the UI is ready (retried until the Dashboard exists).
8. **Main Loop** — Starts the Tkinter event loop (`appObj.mainloop()`).

### UI Layer (`tk_screen.py`)

The UI is built with **Tkinter** + **ttkthemes** (breeze theme) + **customtkinter** for modern buttons. The `App` class (subclass of `tk.Tk`) manages two screens via a frame-stacking pattern:

- **LoginScreen** — Login form with:
  - Mobile number & password fields (with input validation).
  - Entity type selector (eVitalRx / eVitalSupply radio buttons).
  - A "Tally Configuration" popup (appears after successful login) to set the Tally host and port.
  - Ctrl+D shortcut to toggle a log viewer window.

- **Dashboard** — Main sync interface with:
  - A scrollable list of branches showing mapping status ("Map Now" or "Mapped as [Company]").
  - A "Sync" button to trigger data synchronization.
  - Last sync timestamp display.
  - Per-branch context menu for mapping individual companies.
  - A "Check for Updates" button (bottom-left) that opens the update dialog with release notes.

### Authentication & Company Mapping (`login.py` / `functions.py`)

- **`login()`** (in `functions.py`) sends a POST request to the eVitalRx API (`/v2/master/tally_data/v3/login`) with the mobile number, password, and entity type.
- On success, it stores the login response, API keys, and access tokens in `constants.py` and caches them encrypted in `lib/app_cache.txt`.
- If the business is a **chain pharmacy** (head office), the user is prompted to choose between **single company** or **multiple company** mapping.
- **`map_rx_companies()`** sends the company mapping to the eVitalRx API so eVitalRx knows which Tally company corresponds to which eVitalRx account.

### Data Synchronization (`functions.py` → `startprocess()`)

The core sync logic lives in `startprocess()` in `functions.py`. It runs in a **background thread** (via `start_thread()` / `start_background_thread()`):

1. **Check Tally is running** — Pings Tally on the configured port.
2. **Get Tally companies** — Fetches the list of companies from Tally.
3. **For each mapped company:**
   - **Import eVitalRx → Tally:**
     - Fetches data from eVitalRx API for selected modules (Accounts, Sales, Credit Note, Purchase, Debit Note, Wholesale, Wholesale Return, Payment, Receipt, Contra).
     - Extracts XML voucher strings from the API response.
     - Pushes vouchers to Tally in **adaptive batches** (10–100 records per batch) via `TallyService.push_batch()`, with retry logic on timeouts.
   - **Export Tally → eVitalRx:**
     - Sends Tally XML requests for Balance Sheet, Profit & Loss, Ratio Analysis, and List of Companies.
     - Parses the XML responses (using `xmltodict`) and converts them to JSON.
     - Sends the consolidated data to eVitalRx via `send_data_to_evitalrx()`.
   - **Reconciliation:**
     - Exports the voucher register from Tally.
     - Sends it to eVitalRx's reconciliation API.
4. **Background sync** — After the initial sync, the background thread can be configured to re-run at intervals (default: every 3 hours) or wait for Tally to come online.

### Tally Communication (`lib/tally_service.py`)

The `TallyService` class handles all communication with TallyPrime:

- **`push_batch()`** — Sends XML voucher data to Tally in batches. Uses adaptive batch sizing (10–100) and adaptive timeouts. On timeout, retries with smaller sub-batches. Tracks CREATED, ALTERED, and ERROR counts from Tally's response.
- **`export_voucher_register()`** — Exports a voucher register report from Tally using a custom TDL (Tally Definition Language) XML template.
- **`get_companies()`** — Retrieves the list of companies from Tally.
- **`check_tally_alive()`** — Simple health check to see if Tally is responding.

### eVitalRx API Communication (`lib/import_export_data.py`)

This module contains all HTTP communication with both Tally and eVitalRx:

- **`send_request_to_tally()`** — Sends XML requests to Tally's HTTP API (port 9000). Parses XML responses with `xmltodict` and cleans the data.
- **`send_data_to_evitalrx()`** — POSTs consolidated Tally data to eVitalRx's `/v2/master/tally_data/v3/import_reports_data` endpoint.
- **`send_login_request()`** — Authenticates with eVitalRx and populates `constants.LOGIN_RESPONSE`, `constants.RX_ACCOUNTS`, etc.
- **`get_tally_companies()`** — Fetches companies from Tally and populates `constants.TALLY_ACCOUNTS`.
- **`map_rx_companies()`** — Sends company mapping to eVitalRx.
- **`reset_mapping_from_rx()`** — Resets all company mappings on the eVitalRx side.
- **`get_mapping_details()`** — Fetches the mapping history (which eVitalRx accounts are mapped to which Tally companies).
- **`get_data_from_evitalrx()`** — Fetches accounts/transactions from eVitalRx for import into Tally.
- **`send_reconciliation()`** — Sends reconciliation data (voucher register) to eVitalRx.

### Encryption & Caching (`functions.py`)

- **`encrypt_data()`** / **`decrypt_data()`** — Uses Fernet symmetric encryption (key stored in `constants.ENCRYPTION_KEY`) to encrypt/decrypt the app cache file (`lib/app_cache.txt`). This stores login credentials, API keys, company mappings, and Tally connection settings securely.

### Logging (`log.py`)

- **`LogManager`** — Writes encrypted log entries to `lib/app_logs.txt`. A background thread checks daily and clears old logs. Logs can be viewed in-app via Ctrl+D.

### Constants & Configuration (`lib/constants.py`)

Central configuration hub containing:
- **Tally connection settings** (host, port — default `localhost:9000`).
- **Environment configs** for 4 environments: `local`, `staging`, `beta`, `production` — each with different eVitalRx API URLs.
- **Tally XML request templates** (`REQUEST_FORMATS`) — pre-built XML envelopes for Balance Sheet, Profit & Loss, Ratio Analysis, List of Companies, Ledgers, and Groups.
- **Runtime state variables** — login response, company mappings, sync state, thread control flags, etc.
- **Encryption key** for cache and log files.
- **GitHub repo details** (`GITHUB_OWNER`, `GITHUB_REPO`) used by the auto-updater. The repo is **public**, so no token is needed for the Releases API.

---

## Auto-Update System

The app can update itself from **GitHub Releases** on the **private** repository `evital-smit/py-extract-tally`. All logic lives in **`updater.py`**.

### How it works

1. **`check_for_updates()`** calls the GitHub API (`/releases/latest`). Release tags must follow semantic versioning (e.g. `3.11.0`). The release **body is plain-text/Markdown release notes**.
2. The version is compared against `constants.APP_VERSION` (read from the bundled `VERSION` file — the single source of truth, managed separately from `version.txt` used for the Windows executable metadata).
3. If a newer version exists, the updater looks for a release asset named:
   ```
   evital-tally-connects-v{version}-{envtype}.zip
   ```
   The `{envtype}` is read from `constants.envtype`, so each installed environment (local / staging / beta / production) downloads **its own matching zip** automatically.
4. **`download_update()`** downloads the asset. For private repos the `Authorization` header is stripped on redirected `browser_download_url` requests, so the updater uses the **GitHub API asset endpoint** (`/releases/assets/{asset_id}` with `Accept: application/octet-stream`) instead. A progress callback drives the UI progress bar.
5. **`apply_update()`** extracts the zip, validating that it contains an `.exe` and a `lib/` folder, then:
   - Backs up the existing `lib/` to `_lib_backup/`.
   - Renames the running exe to `*.old` (Windows cannot overwrite a running exe).
   - Copies the new exe into place, then merges the new `lib/` over the old.
   - Writes an `_update_in_progress` marker before starting, so a crash mid-update is recoverable.
   - Launches the new exe via `subprocess.Popen` and terminates the old process.
6. **Failure handling** — if any step fails (including antivirus locking), the app rolls back both the exe and `lib/` from the backup. Antivirus resilience is built in: retries (5x, 3s apart) for file copies and process launches. All steps are logged via `LogManagerObj`.

### Force (mandatory) updates

A release is **mandatory** when its body starts with the line `[FORCE UPDATE]`:

```
[FORCE UPDATE]
Here are the release notes...
```

- The marker is stripped from the displayed release notes.
- On startup, `app.py` runs `_startup_force_check()` in the background and shows the dialog as soon as the UI is ready.
- The update dialog becomes **non-dismissible** for force updates:
  - No Cancel button, `WM_DELETE_WINDOW` blocked, Escape/click-outside blocked.
  - Header reads **"Mandatory Update"**, the button is a red **"Update Now"**, and failures show **"Retry"**.
  - The dialog stays topmost while it is active; the user can still open the **log viewer (Ctrl+D)** to watch update progress.

### Update dialog

The "Check for Updates" button (and the startup force check) opens a blurred, darkened overlay dialog (`tk_screen.py`) containing:

- A blue header bar ("Version Update" / "Mandatory Update").
- Status + detail labels (checking → downloading with % progress → installing → restarting).
- **Markdown-rendered release notes** (headings, bold, and bullet points) in a scrollable, non-selectable "What's new" box.
- Buttons: **Update Now** / **Cancel** (regular), or **Update Now** only (mandatory).

### Z-order & window behaviour

- **Force updates**: the overlay stays above the main window. Dragging the main window moves the overlay with it. Opening the log viewer (Ctrl+D) raises it above the overlay so the user can read logs; focusing the app again demotes it back.
- **Regular updates**: the overlay is a normal dialog; the log viewer and other windows can be raised above it freely.

### Failure / crash recovery on startup

- If the process dies mid-update, a `_update_in_progress` marker remains. On next launch `app.py` detects it, restores any `*.old` executable back to its original name, and cleans up remaining artifacts.

---

## Project Structure

```
py-extract-tally/
├── app.py                      # Entry point — startup, crash recovery, cache check, force-update check
├── build.py                    # Build automation script (PyInstaller + zip packaging)
├── updater.py                  # Auto-update module — GitHub Releases check, download, apply, rollback
├── app.spec                    # PyInstaller spec file
├── VERSION                     # Single source of truth for app version (e.g. 3.11.0), bundled
├── version.txt                 # PyInstaller Windows version metadata (FileVersion)
├── pyproject.toml              # Project metadata & dependencies (uv)
├── requirements.txt            # Pinned dependencies (auto-generated by uv)
├── README.md                   # This file
├── .gitignore
├──
├── tk_screen.py                # Main UI — App, LoginScreen, Dashboard, LogViewer, update dialog
├── login.py                    # Legacy login screen (older UI implementation)
├── main.py                     # Legacy main dashboard (older UI implementation)
├── functions.py                # Core business logic — login, sync, encryption, data extraction
├── api_client.py               # API client wrapper (multi-key sync helper)
├── log.py                      # Encrypted logging with daily rotation
│
├── lib/
│   ├── constants.py            # All app constants, config, XML templates, runtime state, GITHUB_*
│   ├── secrets.py              # (gitignored) ENCRYPTION_KEY — copy from secrets.py.example
│   ├── secrets.py.example      # Template for lib/secrets.py
│   ├── import_export_data.py   # HTTP communication with Tally & eVitalRx APIs
│   ├── tally_service.py        # TallyService class — XML voucher push, export, batch handling
│   ├── app_cache.txt           # Encrypted cache (login, API keys, mappings)
│   ├── app_logs.txt            # Encrypted application logs
│   ├── credentials.json        # Credentials file
│   ├── data2.json              # Sample/test data
│   ├── test.py                 # Test script
│   ├── fonts/                  # Custom fonts (Manrope, breeze theme)
│   │   ├── static/Manrope-Regular.ttf
│   │   └── breeze/             # ttk breeze theme files
│   └── images/                 # App icons, splash, GIFs
│       ├── logo2.ico           # App icon
│       ├── login_panel.jpg     # Splash/login panel image
│       ├── TallySyncSplash.gif # Loading animation
│       └── sync_btn.png        # Sync button icon
```

---

## Prerequisites

- **Python 3.11+**
- **uv** (recommended package manager) — [install uv](https://docs.astral.sh/uv/)
- **TallyPrime** running locally on port 9000 (default)
- **Windows** (the app uses Windows-specific APIs for DPI awareness, window shadows, and screen capture)

---

## Running the App (Development)

```bash
# Install dependencies
uv sync

# Run the app
uv run python app.py
```

---

## Building the App

The project uses **`build.py`** — a build automation script that wraps PyInstaller and produces versioned, environment-specific zip archives.

### Quick Build (All Environments)

```bash
uv run python build.py
```

This builds **all 4 environments** (local, staging, beta, production), each with the correct `envtype` set in `lib/constants.py`, and packages them as versioned zip files in `dist/`.

### Build a Single Environment

```bash
uv run python build.py --env staging
```

Valid environments: `local`, `staging`, `beta`, `production`.

### Build Without Zipping

```bash
uv run python build.py --skip-zip
```

Skips the zip archive step — useful for testing the raw executable.

### Clean Before Building

```bash
uv run python build.py --clean
```

Removes `build/` and `dist/` directories before starting.

### Combined Flags

```bash
uv run python build.py --env local --skip-zip --clean
```

### What `build.py` Does

1. Reads the current version from the **`VERSION`** file.
2. For each environment:
   - Temporarily sets `envtype` in `lib/constants.py` to the target environment.
   - Runs PyInstaller with the configured arguments (one-file, windowed, no console, version file, icon, splash, fonts, babel, and `VERSION` bundled as `--add-data "VERSION;."` so the running exe knows its own version).
   - Creates a versioned zip archive: `evital-tally-connects-v{version}-{env}.zip` in `dist/`.
   - Restores the original `envtype` in `lib/constants.py`.
3. Prints a summary of all created archives.

> **Note:** The `VERSION` file (plain version text, bundled into the exe — used by the auto-updater) and `version.txt` (PyInstaller Windows FileVersion metadata) are **separate** files. Bump `VERSION` when cutting a new release; both are read by `build.py`.

---

## Publishing a Release

The auto-updater pulls from the **latest GitHub Release** on `evital-smit/py-extract-tally` (private). To ship a new version:

1. **Bump the version** in the `VERSION` file (e.g. `3.10.10`).
2. **Build** the environment(s) you need:
   ```bash
   uv run python build.py --env production
   ```
   This produces `dist/evital-tally-connects-v3.10.10-production.zip` (repeat for any other environments).
3. **Create a GitHub release**:
   - **Tag**: the plain version, e.g. `3.10.10` (the updater strips a leading `v` if present).
   - **Title**: anything readable (e.g. `v3.10.10`).
   - **Body**: Markdown release notes. Prefix with `[FORCE UPDATE]` on the first line to make it **mandatory** for all users.
   - **Assets**: attach the environment zip(s). Name them exactly `evital-tally-connects-v{version}-{env}.zip` — the updater picks the asset matching the user's `envtype`.
4. Users with auto-update or force-update will pick up the release on next startup / on the "Check for Updates" button.

Below is an example release body:

```
[FORCE UPDATE]
## Highlights

- Fixed sync timeout on large batches
- Improved reconciliation accuracy

**Note:** this update adds new voucher handling for Wholesale returns.
```

---

## Build Commands Reference

### Using `build.py` (Recommended)

| Command | Description |
|---|---|
| `uv run python build.py` | Build all 4 environments (local, staging, beta, production) |
| `uv run python build.py --env staging` | Build only the staging environment |
| `uv run python build.py --skip-zip` | Build without creating zip archives |
| `uv run python build.py --clean` | Clean `build/` and `dist/` before building |
| `uv run python build.py --env local --skip-zip --clean` | Combined flags |

### Manual PyInstaller (Alternative)

```bash
# Using uv
uv run pyinstaller.exe --noconsole --onefile --windowed --clean --version-file="version.txt" --icon=./lib/images/logo2.ico --add-data "lib/fonts/static/Manrope-Regular.ttf;lib/fonts/static/" --add-data "lib/fonts/breeze/breeze.tcl;lib/fonts/breeze" --add-data "lib/fonts/breeze/breeze/*.png;lib/fonts/breeze/breeze" --add-data "VERSION;." --splash "./lib/images/login_panel.jpg" --collect-all babel app.py

# Using uvx
uvx pyinstaller.exe --noconsole --onefile --windowed --icon=./lib/images/logo2.ico --add-data "lib/fonts/static/Manrope-Regular.ttf;lib/fonts/static/" --add-data "lib/fonts/breeze/breeze.tcl;lib/fonts/breeze" --add-data "lib/fonts/breeze/breeze/*.png;lib/fonts/breeze/breeze" --splash "./lib/images/login_panel.PNG" app.py

# Direct pyinstaller
pyinstaller.exe --noconsole --onefile --windowed --icon=./lib/images/logo2.ico --add-data "lib/fonts/static/Manrope-Regular.ttf;lib/fonts/static/" --add-data "lib/fonts/breeze/breeze.tcl;lib/fonts/breeze" --add-data "lib/fonts/breeze/breeze/*.png;lib/fonts/breeze/breeze" --splash "./lib/images/login_panel.PNG" app.py
```

### Regenerating requirements.txt

```bash
uv export --project . --format requirements-txt --output-file requirements.txt
```

---

## Configuration

### Tally Connection

- **Host:** `localhost` (configurable in the Tally Configuration popup)
- **Port:** `9000` (configurable in the Tally Configuration popup)

### Environment Configuration

The `envtype` variable in `lib/constants.py` controls which eVitalRx API endpoints are used:

| Environment | eVitalRx Host | eVitalRx URL |
|---|---|---|
| `local` | `localhost` | `http://localhost:4000/` |
| `staging` | `dev-api.evitalrx.in` | `https://ews-staging-api-product.portal-evital.com/` |
| `beta` | `beta-api.evitalrx.in` | `https://beta-api.evitalrx.in/` |
| `production` | `api.evitalrx.in` | `https://api.evitalrx.in:4050/` |

The `build.py` script automatically sets the correct `envtype` for each environment build.

### Encryption

- **Encryption Key:** Stored in `lib/secrets.py` as `ENCRYPTION_KEY` (Fernet key). `lib/constants.py` imports it. **`lib/secrets.py` is gitignored** — copy `lib/secrets.py.example` and fill in real values; keep the file out of version control.
- **Cache File:** `lib/app_cache.txt` — stores login response, API keys, company mappings, and Tally settings (encrypted).
- **Log File:** `lib/app_logs.txt` — all log entries are encrypted.

### GitHub Auto-Update & Secrets

- **`lib/secrets.py`** stores only the encryption key:
  ```python
  ENCRYPTION_KEY = "..."
  ```
  `constants.py` reads `GITHUB_OWNER` / `GITHUB_REPO` directly. **No GitHub personal access token is embedded in the repo.**
- The repo & owner are configured in `lib/constants.py` (`GITHUB_OWNER = "evital-smit"`, `GITHUB_REPO = "py-extract-tally"`). The repo is **public**, so the auto-updater calls the GitHub Releases API **without any authentication**.
- **Git operations** (clone / fetch / push) on the build machine use an **SSH deploy key** — the remote URL is `git@github.com:<owner>/<repo>.git` and the deploy key's public key is authorized in the repo's Settings → Deploy keys.
- For downloads, the updater uses the GitHub **API asset endpoint** (`/releases/assets/{asset_id}` with `Accept: application/octet-stream`) because the `Authorization`-independent redirect of `browser_download_url` is not needed for a public repo.

---

## Environment Variables

| Variable | Purpose | Required? |
|---|---|---|
| `ENCRYPTION_KEY` | Fernet key for cache and log encryption (usually set in `lib/secrets.py`, not an env var). | No (comes from `lib/secrets.py`) |

> GitHub updates use a **public** repo, so no token is required. Git operations on the build machine use an SSH deploy key.
