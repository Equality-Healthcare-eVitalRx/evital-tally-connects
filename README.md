# eVitalConnects (eVital<>Tally Connects)

A desktop application that synchronizes accounting data between **TallyPrime** (an Indian accounting software) and the **eVitalRx / eVitalSupply** cloud platform. It extracts financial reports and vouchers from Tally, transforms them, and pushes them to the eVitalRx API — and vice-versa for importing eVitalRx data back into Tally.

---

## Table of Contents

- [Overview](#overview)
- [How the App Works](#how-the-app-works)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Running the App (Development)](#running-the-app-development)
- [Building the App](#building-the-app)
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

---

## How the App Works

### Entry Point & Startup Flow

The application starts at **`app.py`**, which orchestrates the initial setup:

1. **DPI Awareness** — Sets Windows DPI awareness so the UI renders correctly on high-DPI displays.
2. **Splash Screen** — If running as a PyInstaller bundle, the splash screen is updated and closed.
3. **Font Loading** — Loads the custom `Manrope` font via `pyglet`.
4. **Logging** — Initializes the `LogManager` (from `log.py`) which writes encrypted log entries to `lib/app_logs.txt` and auto-clears logs daily.
5. **Cache Check** — Reads `lib/app_cache.txt` (encrypted with Fernet). If a valid cached login exists:
   - Restores login response, API keys, access tokens, and Tally connection settings.
   - Fetches the list of Tally companies.
   - Shows the **Dashboard** screen.
   - If no valid cache exists, shows the **LoginScreen**.
6. **Main Loop** — Starts the Tkinter event loop (`appObj.mainloop()`).

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

---

## Project Structure

```
py-extract-tally/
├── app.py                      # Entry point — startup, cache check, launches UI
├── build.py                    # Build automation script (PyInstaller + zip packaging)
├── app.spec                    # PyInstaller spec file
├── version.txt                 # PyInstaller version info (currently v0.3.10.8)
├── pyproject.toml              # Project metadata & dependencies (uv)
├── requirements.txt            # Pinned dependencies (auto-generated by uv)
├── README.md                   # This file
├── .gitignore
├──
├── tk_screen.py                # Main UI — App, LoginScreen, Dashboard, LogViewer
├── login.py                    # Legacy login screen (older UI implementation)
├── main.py                     # Legacy main dashboard (older UI implementation)
├── functions.py                # Core business logic — login, sync, encryption, data extraction
├── api_client.py               # API client wrapper (multi-key sync helper)
├── log.py                      # Encrypted logging with daily rotation
│
├── lib/
│   ├── constants.py            # All app constants, config, XML templates, runtime state
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

1. Reads the current version from `version.txt`.
2. For each environment:
   - Temporarily sets `envtype` in `lib/constants.py` to the target environment.
   - Runs PyInstaller with the configured arguments (one-file, windowed, no console, version file, icon, splash, fonts, babel).
   - Creates a versioned zip archive: `evital-tally-connects-v{version}-{env}.zip` in `dist/`.
   - Restores the original `envtype` in `lib/constants.py`.
3. Prints a summary of all created archives.

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
uv run pyinstaller.exe --noconsole --onefile --windowed --clean --version-file="version.txt" --icon=./lib/images/logo2.ico --add-data "lib/fonts/static/Manrope-Regular.ttf;lib/fonts/static/" --add-data "lib/fonts/breeze/breeze.tcl;lib/fonts/breeze" --add-data "lib/fonts/breeze/breeze/*.png;lib/fonts/breeze/breeze" --splash "./lib/images/login_panel.jpg" --collect-all babel app.py

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

- **Encryption Key:** Stored in `lib/constants.py` as `ENCRYPTION_KEY` (Fernet key).
- **Cache File:** `lib/app_cache.txt` — stores login response, API keys, company mappings, and Tally settings (encrypted).
- **Log File:** `lib/app_logs.txt` — all log entries are encrypted.
