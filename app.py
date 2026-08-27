from lib import constants

constants.LOAD_COMPLETE = False

import multiprocessing
import sys
import threading
import traceback
from pathlib import Path
import pyglet
from functions import (
    decrypt_data,
    LogManagerObj,
    log_business_apikey_status,
)
from lib.import_export_data import get_tally_companies, is_tally_reachable
from tkinter import messagebox
from tk_screen import App
import ctypes


# Cleanup leftover files from a previous update
# Handles crash recovery: if process died mid-update, restore the old exe
try:
    _app_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
    _marker = _app_dir / "_update_in_progress"

    if _marker.exists():
        LogManagerObj.write_log("[Startup] Update marker found — recovering from crash")
        _old_files = list(_app_dir.glob("*.old"))
        if _old_files:
            _current_exe = Path(sys.executable) if getattr(sys, "frozen", False) else None
            _new_in_place = _current_exe and _current_exe.exists() and _current_exe.stat().st_size > 1024 * 1024
            if not _new_in_place:
                for _old in _old_files:
                    _original_name = _old.name.rsplit(".old", 1)[0]
                    _original = _app_dir / _original_name
                    if not _original.exists():
                        _old.rename(_original)
                        LogManagerObj.write_log(f"[Startup] Restored {_original_name} from .old")
        _marker.unlink(missing_ok=True)

    # Try direct deletion with retries
    import time as _cleanup_time
    _cleanup_time.sleep(2)
    _remaining = []
    for _attempt in range(3):
        _remaining = []
        for _cleanup in _app_dir.glob("*.old"):
            try:
                _cleanup.unlink(missing_ok=True)
            except OSError:
                _remaining.append(_cleanup)
        _debug_log = _app_dir / "_update_debug.log"
        if _debug_log.exists():
            try:
                _debug_log.unlink(missing_ok=True)
            except OSError:
                _remaining.append(_debug_log)
        if not _remaining:
            break
        _cleanup_time.sleep(2)

    # Fallback: detached PowerShell cleanup for anything still locked
    if _remaining:
        try:
            _paths = ";".join(str(f) for f in _remaining)
            _ps_cmd = (
                "Start-Sleep -Seconds 8; "
                f"$paths = '{_paths}' -split ';'; "
                "foreach ($p in $paths) { "
                "  if (Test-Path $p) { "
                "    try { Remove-Item -Path $p -Force -ErrorAction Stop } "
                "    catch { Start-Sleep -Seconds 5; Remove-Item -Path $p -Force -ErrorAction SilentlyContinue } "
                "  } "
                "}"
            )
            import subprocess as _cleanup_subprocess
            _cleanup_subprocess.Popen(
                ["powershell", "-WindowStyle", "Hidden", "-Command", _ps_cmd],
                creationflags=0x08000000,
                close_fds=True,
            )
        except Exception:
            pass

    # Clean up any leftover .cmd scripts from older update versions
    for _old_cmd in _app_dir.glob("_update_cleanup.cmd"):
        try:
            _old_cmd.unlink(missing_ok=True)
        except OSError:
            pass
except Exception:
    pass

try:  # >= win 8.1
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:  # win 8.0 or less
    ctypes.windll.user32.SetProcessDPIAware()

# spalsh comment
try:
    import pyi_splash
    pyi_splash.update_text('UI Loaded ...')
    pyi_splash.close()
except ImportError:
    print("No Splash Screen Found")

pyglet.options["win32_gdi_font"] = True
fontpath = "./lib/fonts/static/Manrope-Regular.ttf"
try:
    pyglet.font.add_file(str(fontpath))
except Exception:
    pass  # Use default font if custom font cannot be loaded

LogManagerObj.clear_logs()
LogManagerObj.write_log("Application started")


my_file = Path("./lib/app_cache.txt")
appObj = App()


_force_check_retries = [0]

def _startup_force_check():
    """Check for force updates on startup. Shows the update dialog if required."""
    import updater
    def _check():
        try:
            result = updater.check_for_updates()
            if result.get("force") and result.get("update_available"):
                LogManagerObj.write_log("[Startup] Force update detected")
                if hasattr(appObj, "_on_check_updates"):
                    appObj.after(0, lambda: appObj._on_check_updates())
                elif _force_check_retries[0] < 15:
                    _force_check_retries[0] += 1
                    appObj.after(2000, _startup_force_check)
            elif result.get("error"):
                LogManagerObj.write_log(f"[Startup] Update check error: {result['error']}")
        except Exception as e:
            LogManagerObj.write_log(f"[Startup] Force check failed: {e}")
    threading.Thread(target=_check, daemon=True).start()


def finish_startup_restore():
    """Runs on a worker thread while the Loading screen stays painted
    and responsive. UI switches are marshaled back via after()."""
    if not is_tally_reachable():
        LogManagerObj.write_log("Tally is not running.")

        def show_offline_error():
            messagebox.showerror("Tally Company", "Tally is not running.")
            appObj.destroy()

        appObj.after(0, show_offline_error)
        return

    try:
        get_tally_companies()
    except SystemExit:
        pass
    except Exception:
        LogManagerObj.write_log(traceback.format_exc())

    appObj.after(0, lambda: appObj.show_frame("Dashboard"))
    appObj.after(1000, _startup_force_check)


if my_file.is_file():
    json_data = {}
    try:
        json_data = decrypt_data(my_file.read_bytes())
    except Exception:
        LogManagerObj.write_log(traceback.format_exc())
    if isinstance(json_data, dict) and "login_response" in json_data.keys() and json_data["login_response"][
        "status_code"
    ] in [1, "1"]:
        LogManagerObj.write_log("Previous Login Found.")
        constants.LOGIN_RESPONSE = json_data["login_response"]
        if "mobile" in json_data.keys():
            constants.MOBILE = json_data["mobile"]
            constants.TALLY_PORT = json_data.get("tally_port", 9000)
            constants.HOST = json_data.get("tally_host", "localhost")
            if constants.MOBILE_VAR is not None:
                constants.MOBILE_VAR.set(constants.MOBILE)
        if (
            "accesstoken"
            in json_data["login_response"]["data"]["business_details"][
                "logged_in_business"
            ]
        ):
            constants.ACCESS_TOKEN = json_data["login_response"]["data"][
                "business_details"
            ]["logged_in_business"]["accesstoken"]
        if (
            "apikey"
            in json_data["login_response"]["data"]["business_details"][
                "logged_in_business"
            ]
        ):
            constants.EVITAL_RX_API_KEY = json_data["login_response"]["data"][
                "business_details"
            ]["logged_in_business"]["apikey"]

        log_business_apikey_status()

        # Show the loading placeholder immediately, then do the slow
        # Tally check / company fetch off the UI thread.
        appObj.show_frame("LoadingScreen")
        threading.Thread(target=finish_startup_restore, daemon=True).start()
    else:
        appObj.show_frame("LoginScreen")
        appObj.after(1000, _startup_force_check)

else:
    LogManagerObj.write_log("Login Details Not found.")
    appObj.show_frame("LoginScreen")
    appObj.after(1000, _startup_force_check)

if __name__ == "__main__":
    constants.LOAD_COMPLETE = True
    appObj.mainloop()
    multiprocessing.freeze_support()
