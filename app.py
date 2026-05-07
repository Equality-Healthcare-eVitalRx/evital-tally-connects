
import multiprocessing
from pathlib import Path
import pyglet
from functions import decrypt_data, LogManagerObj
from lib.import_export_data import get_tally_companies
from lib import constants
from tk_screen import App
import ctypes

try: # >= win 8.1
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except: # win 8.0 or less
    ctypes.windll.user32.SetProcessDPIAware()


# spalsh comment
# import pyi_splash
# pyi_splash.update_text('UI Loaded ...')
# pyi_splash.close()


pyglet.options['win32_gdi_font'] = True
fontpath = './lib/fonts/static/Manrope-Regular.ttf'
pyglet.font.add_file(str(fontpath))

LogManagerObj.clear_logs()
LogManagerObj.write_log("Application started")

get_tally_companies()

my_file = Path("./lib/app_cache.txt")
appObj = App()
if my_file.is_file():

    json_data = open("./lib/app_cache.txt", "rb")
    json_data = decrypt_data(json_data.read())
    if "login_response" in json_data.keys() and json_data["login_response"]["status_code"] in [1,'1'] :
        LogManagerObj.write_log("Previous Login Found.")
        constants.LOGIN_RESPONSE = json_data["login_response"]
        if "mobile" in json_data.keys():
            constants.MOBILE = json_data["mobile"]
            constants.TALLY_PORT = json_data.get("tally_port", 9000)
            constants.HOST = json_data.get("tally_host", "localhost")
            constants.MOBILE_VAR.set(constants.MOBILE)
        if "accesstoken" in json_data["login_response"]["data"]["business_details"]["logged_in_business"]:
            constants.ACCESS_TOKEN = json_data["login_response"]["data"]["business_details"]["logged_in_business"]["accesstoken"]
        if "apikey" in json_data["login_response"]["data"]["business_details"]["logged_in_business"]:
            constants.EVITAL_RX_API_KEY = json_data["login_response"]["data"]["business_details"]["logged_in_business"]["apikey"]
            
        appObj.show_frame("Dashboard")
    else:
        appObj.show_frame("LoginScreen")

else:
    LogManagerObj.write_log("Login Details Not found.")
    appObj.show_frame("LoginScreen")
    
if __name__ == "__main__":

    appObj.mainloop()
    multiprocessing.freeze_support()