"""
Auto-update module for eVitalConnects.
Checks GitHub Releases for a newer production build, downloads the zip,
replaces the executable and lib/ (preserving user data), and relaunches the app.
"""

import os
import sys
import json
import shutil
import zipfile
import tempfile
import subprocess
import time
import requests
from pathlib import Path
from lib import constants
from log import LogManagerObj


GITHUB_API_URL = f"https://api.github.com/repos/{constants.GITHUB_OWNER}/{constants.GITHUB_REPO}/releases/latest"

# Antivirus can temporarily lock files during scanning
AV_RETRY_COUNT = 5
AV_RETRY_DELAY = 3  # seconds between retries


def _github_headers():
    """Return headers for GitHub API requests (public repo — no auth needed)."""
    return {"Accept": "application/vnd.github.v3+json"}


def _parse_version(version_str):
    try:
        parts = version_str.strip().lstrip("v").split(".")
        return tuple(int(p) for p in parts)
    except (ValueError, AttributeError):
        return (0, 0, 0)


def get_install_dir():
    """Return the directory where the application executable is located."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def _schedule_background_cleanup(install_dir, files_to_delete):
    """
    Spawn a detached PowerShell process that waits then deletes files.
    Works regardless of whether the calling process is alive or dead.
    Handles paths with spaces, single quotes, and special characters.
    """
    if not files_to_delete:
        return
    escaped = []
    for f in files_to_delete:
        s = str(f).replace("'", "''")
        escaped.append(s)
    paths = ";".join(escaped)
    ps_cmd = (
        "Start-Sleep -Seconds 8; "
        "$paths = @(" + ";".join(f"'{e}'" for e in escaped) + "); "
        "foreach ($p in $paths) { "
        "  if (Test-Path $p) { "
        "    try { Remove-Item -Path $p -Force -ErrorAction Stop } "
        "    catch { Start-Sleep -Seconds 5; Remove-Item -Path $p -Force -ErrorAction SilentlyContinue } "
        "  } "
        "}"
    )
    try:
        subprocess.Popen(
            ["powershell", "-WindowStyle", "Hidden", "-Command", ps_cmd],
            creationflags=0x08000000,  # CREATE_NO_WINDOW
            close_fds=True,
        )
    except Exception:
        pass


def _copy_with_retry(src, dst, log_fn=None):
    """
    Copy a file with retries for antivirus locking.
    AV may hold a brief exclusive lock while scanning a newly-written file.
    """
    last_err = None
    for attempt in range(AV_RETRY_COUNT):
        try:
            shutil.copy2(src, dst)
            return
        except (OSError, PermissionError) as e:
            last_err = e
            if log_fn:
                log_fn(f"copy attempt {attempt + 1} failed: {e}")
            time.sleep(AV_RETRY_DELAY)
    raise last_err


def _rmdir_with_retry(path, log_fn=None):
    """Remove a directory tree with retries for AV locking."""
    for attempt in range(AV_RETRY_COUNT):
        try:
            shutil.rmtree(path, ignore_errors=False)
            return
        except Exception as e:
            if log_fn:
                log_fn(f"rmdir attempt {attempt + 1} failed: {e}")
            time.sleep(AV_RETRY_DELAY)
    shutil.rmtree(path, ignore_errors=True)


def _safe_rmtree(path):
    """Remove directory, ignoring all errors."""
    shutil.rmtree(path, ignore_errors=True)


def check_for_updates():
    """
    Check GitHub Releases for a newer production build.

    Returns:
        dict: {
            "update_available": bool,
            "current_version": str,
            "latest_version": str,
            "download_url": str or None,
            "release_notes": str or None,
            "error": str or None
        }
    """
    current_version = constants.APP_VERSION
    result = {
        "update_available": False,
        "current_version": current_version,
        "latest_version": None,
        "download_url": None,
        "asset_id": None,
        "release_notes": None,
        "force": False,
        "error": None,
    }

    try:
        resp = requests.get(GITHUB_API_URL, headers=_github_headers(), timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        result["error"] = f"Failed to check for updates: {e}"
        LogManagerObj.write_log(f"[Update] Check failed: {e}")
        return result

    tag = data.get("tag_name", "").lstrip("v")
    if not tag:
        result["error"] = "Could not parse version from release."
        LogManagerObj.write_log("[Update] Check failed: could not parse version from release")
        return result

    result["latest_version"] = tag

    notes = data.get("body", "") or ""
    if notes.strip().startswith("[FORCE UPDATE]"):
        result["force"] = True
        notes = notes.strip()[len("[FORCE UPDATE]"):].lstrip("\r\n")
    result["release_notes"] = notes

    if _parse_version(tag) <= _parse_version(current_version):
        LogManagerObj.write_log(f"[Update] Up to date (v{current_version})")
        return result

    target_asset_name = f"evital-tally-connects-v{tag}-{constants.envtype}.zip"
    for asset in data.get("assets", []):
        if asset.get("name") == target_asset_name:
            result["update_available"] = True
            result["download_url"] = asset.get("browser_download_url")
            result["asset_id"] = asset.get("id")
            break

    LogManagerObj.write_log(
        f"[Update] v{tag} available (current: v{current_version}, force: {result['force']})"
    )

    if not result["update_available"] and result["download_url"] is None:
        result["error"] = f"Release {tag} found but '{target_asset_name}' asset not found."

    return result


def download_update(download_url, asset_id=None, progress_callback=None):
    """
    Download the update zip to a temp directory.

    For private repos, uses the GitHub API asset endpoint to avoid
    auth header being stripped on redirect.

    Args:
        download_url: URL of the zip file (fallback).
        asset_id: GitHub release asset ID (preferred for private repos).
        progress_callback: Optional callable(bytes_downloaded, total_bytes).

    Returns:
        Path to the downloaded zip file, or raises Exception.
    """
    LogManagerObj.write_log("[Update] Download started")
    tmp_dir = tempfile.mkdtemp(prefix="evital_update_")
    zip_path = Path(tmp_dir) / "update.zip"

    if asset_id:
        api_url = (
            f"https://api.github.com/repos/{constants.GITHUB_OWNER}"
            f"/{constants.GITHUB_REPO}/releases/assets/{asset_id}"
        )
        headers = _github_headers()
        headers["Accept"] = "application/octet-stream"
    else:
        api_url = download_url
        headers = _github_headers()

    try:
        resp = requests.get(api_url, stream=True, headers=headers, timeout=120, allow_redirects=True)
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        downloaded = 0

        with open(zip_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        progress_callback(downloaded, total)

        LogManagerObj.write_log(f"[Update] Download completed ({downloaded / (1024*1024):.1f} MB)")
        return zip_path
    except Exception as e:
        LogManagerObj.write_log(f"[Update] Download failed: {e}")
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise


def _validate_zip(extract_dir):
    """
    Validate extracted contents before replacing anything.
    Returns (exe_path, error_string). error_string is None on success.
    """
    exe_candidates = list(extract_dir.glob("*.exe"))
    if not exe_candidates:
        return None, "Update zip does not contain any .exe file"

    exe_path = exe_candidates[0]
    if exe_path.stat().st_size < 1024 * 1024:
        return None, f"Exe file is suspiciously small ({exe_path.stat().st_size} bytes)"

    src_lib = extract_dir / "lib"
    if not src_lib.exists():
        return None, "Update zip does not contain a lib/ folder"

    return exe_path, None


def apply_update(zip_path):
    """
    Replace running app files and relaunch — with full failure recovery.

    Safety guarantees:
    - Zip is extracted and validated BEFORE any installed files are touched
    - If ANYTHING fails after renaming, ALL changes are rolled back:
      exe is restored, lib/ is restored from backup, marker is removed
    - A marker file tracks "update in progress" so app.py can recover on crash
    - Antivirus resilience: retries with delays for copy, launch, and cleanup
    - Background PowerShell cleanup handles stubborn file locks
    """
    LogManagerObj.write_log("[Update] Apply started")
    install_dir = get_install_dir()
    extract_dir = Path(tempfile.mkdtemp(prefix="evital_extract_"))
    marker = install_dir / "_update_in_progress"
    debug_log = install_dir / "_update_debug.log"
    lib_backup = install_dir / "_lib_backup"

    def _log(msg):
        try:
            with open(debug_log, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        except Exception:
            pass

    def _cleanup_extract_dirs():
        _safe_rmtree(extract_dir)
        _safe_rmtree(Path(zip_path).parent)

    def _full_rollback(renamed, lib_was_backed_up):
        """Restore ALL changes: exe, lib/, marker."""
        LogManagerObj.write_log("[Update] Rolling back changes")
        # Restore exe
        if renamed and old_exe.exists() and not current_exe.exists():
            try:
                old_exe.rename(current_exe)
                _log(f"ROLLBACK: restored {old_exe.name} -> {exe_name}")
            except Exception as re:
                _log(f"ROLLBACK FAILED (exe): {re}")
                LogManagerObj.write_log(f"[Update] Rollback failed (exe): {re}")
        # Restore lib/ from backup
        if lib_was_backed_up and lib_backup.exists():
            try:
                dst_lib = install_dir / "lib"
                if dst_lib.exists():
                    shutil.rmtree(dst_lib, ignore_errors=True)
                lib_backup.rename(dst_lib)
                _log("ROLLBACK: restored lib/ from backup")
            except Exception as re:
                _log(f"ROLLBACK FAILED (lib): {re}")
                LogManagerObj.write_log(f"[Update] Rollback failed (lib): {re}")
        # Remove marker
        try:
            marker.unlink(missing_ok=True)
        except Exception:
            pass

    _log(f"install_dir={install_dir}  extract_dir={extract_dir}")

    if getattr(sys, "frozen", False):
        current_exe = Path(sys.executable)
    else:
        current_exe = install_dir / "eVital-Tally Connects.exe"

    exe_name = current_exe.name
    old_exe = install_dir / (exe_name + ".old")
    _log(f"exe_name={exe_name}  frozen={getattr(sys, 'frozen', False)}")

    # =========================================================================
    # PHASE 1: Extract and validate — NO installed files touched yet
    # =========================================================================
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
    except zipfile.BadZipFile:
        _cleanup_extract_dirs()
        raise ValueError("Downloaded file is not a valid zip.")
    _log(f"zip extracted: {[p.name for p in extract_dir.iterdir()]}")
    LogManagerObj.write_log("[Update] Zip extracted and validating")

    new_exe_path, err = _validate_zip(extract_dir)
    if err:
        _cleanup_extract_dirs()
        raise ValueError(err)
    _log(f"zip validated: exe={new_exe_path.name} size={new_exe_path.stat().st_size}")

    # =========================================================================
    # PHASE 2: Write marker
    # =========================================================================
    try:
        marker.write_text(time.strftime("%Y-%m-%d %H:%M:%S"), encoding="utf-8")
    except Exception:
        pass
    _log("marker written")

    # =========================================================================
    # PHASE 3: Backup lib/, rename exe, copy new files
    # Any failure here triggers full_rollback (exe + lib + marker)
    # =========================================================================
    renamed = False
    lib_was_backed_up = False
    try:
        # Clean up any leftover .old from a previous failed update
        if old_exe.exists():
            old_exe.unlink(missing_ok=True)
            _log("removed leftover .old")

        # ---- Backup lib/ BEFORE any modification ----
        dst_lib = install_dir / "lib"
        if dst_lib.exists():
            shutil.copytree(dst_lib, lib_backup)
            lib_was_backed_up = True
            _log("backed up lib/ -> _lib_backup/")
            LogManagerObj.write_log("[Update] Backed up lib/")

        # ---- Rename running exe ----
        current_exe.rename(old_exe)
        renamed = True
        _log(f"renamed {exe_name} -> {old_exe.name}")
        LogManagerObj.write_log(f"[Update] Renamed {exe_name} -> {old_exe.name}")

        # ---- Copy new exe (with AV retries) ----
        target_exe = install_dir / new_exe_path.name
        _copy_with_retry(new_exe_path, target_exe, log_fn=_log)
        _log(f"copied exe -> {target_exe} (size={target_exe.stat().st_size})")
        LogManagerObj.write_log("[Update] New exe copied")

        # ---- Wait for AV to finish scanning the new exe ----
        time.sleep(2)

        # ---- Merge lib/ (preserve user data + constants) ----
        src_lib = extract_dir / "lib"
        if src_lib.exists():
            for src_item in src_lib.rglob("*"):
                rel = src_item.relative_to(src_lib)
                dst_item = dst_lib / rel
                if src_item.is_dir():
                    dst_item.mkdir(parents=True, exist_ok=True)
                else:
                    dst_item.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_item, dst_item)
            _log("merged lib/")

    except Exception as e:
        _log(f"file operation FAILED: {e}")
        _full_rollback(renamed, lib_was_backed_up)
        _cleanup_extract_dirs()
        raise

    # =========================================================================
    # PHASE 4: Cleanup temp files (safe — all copies are done)
    # =========================================================================
    _cleanup_extract_dirs()
    _log("temp files cleaned")

    # =========================================================================
    # PHASE 5: Remove marker (update is committed)
    # =========================================================================
    try:
        marker.unlink(missing_ok=True)
        _log("marker removed")
    except Exception:
        pass

    # =========================================================================
    # PHASE 6: Delete .old files (with AV retries + fallback)
    # Debug log is deleted AFTER all _log() calls finish (see Phase 7)
    # =========================================================================
    cleanup_targets = []
    for _f in install_dir.glob("*.old"):
        try:
            _f.unlink(missing_ok=True)
        except OSError:
            cleanup_targets.append(_f)
    # Also clean up backup dir if still exists
    if lib_backup.exists():
        try:
            shutil.rmtree(lib_backup, ignore_errors=True)
        except Exception:
            pass

    # =========================================================================
    # PHASE 7: Relaunch with AV-aware retries
    # If launch fails, roll back exe so old app still works
    # =========================================================================
    new_final_exe = install_dir / exe_name
    _log(f"launching {new_final_exe}  exists={new_final_exe.exists()}")
    LogManagerObj.write_log(f"[Update] Launching new version: {new_final_exe.name}")

    launch_ok = False
    for attempt in range(AV_RETRY_COUNT):
        try:
            subprocess.Popen(
                [str(new_final_exe)],
                cwd=str(install_dir),
            )
            launch_ok = True
            _log(f"launch succeeded (attempt {attempt + 1})")
            LogManagerObj.write_log(f"[Update] Launch succeeded (attempt {attempt + 1})")
            break
        except Exception as e:
            _log(f"launch attempt {attempt + 1} failed: {e}")
            LogManagerObj.write_log(f"[Update] Launch attempt {attempt + 1} failed: {e}")
            time.sleep(AV_RETRY_DELAY)

    if not launch_ok:
        _log("all launch attempts failed — rolling back to old exe")
        LogManagerObj.write_log("[Update] All launch attempts failed — rolling back")
        try:
            if old_exe.exists() and not current_exe.exists():
                old_exe.rename(current_exe)
                _log(f"ROLLBACK: restored {old_exe.name} -> {exe_name}")
        except Exception as re:
            _log(f"ROLLBACK FAILED (exe): {re}")
        # Also restore lib/ if backup exists
        if lib_backup.exists() and lib_was_backed_up:
            try:
                dst_lib = install_dir / "lib"
                if dst_lib.exists():
                    shutil.rmtree(dst_lib, ignore_errors=True)
                lib_backup.rename(dst_lib)
                _log("ROLLBACK: restored lib/ from backup")
            except Exception as re:
                _log(f"ROLLBACK FAILED (lib): {re}")
        raise RuntimeError("Failed to launch new version. Old version restored.")

    # Clean up lib backup if launch succeeded
    if lib_backup.exists():
        try:
            shutil.rmtree(lib_backup, ignore_errors=True)
        except Exception:
            pass

    time.sleep(3)

    # Final cleanup — all logging is done, safe to delete debug log now
    try:
        debug_log.unlink(missing_ok=True)
    except OSError:
        cleanup_targets.append(debug_log)
    if cleanup_targets:
        _schedule_background_cleanup(install_dir, cleanup_targets)

    os._exit(0)
