from lib import constants

constants.LOAD_COMPLETE = False

import multiprocessing
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

else:
    LogManagerObj.write_log("Login Details Not found.")
    appObj.show_frame("LoginScreen")

if __name__ == "__main__":
    constants.LOAD_COMPLETE = True
    appObj.mainloop()
    multiprocessing.freeze_support()
