import json
import multiprocessing
import multiprocessing.process
from pathlib import Path
import time

import pyglet
from main import main_thread
from login import login_thread
from functions import get_all_mapping_details, play_loading_animation, decrypt_data, LogManagerObj
from lib.import_export_data import get_tally_companies
from lib import constants
from tk_screen import App
import logging
import ctypes, tkinter
from tkinter import font

try: # >= win 8.1
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except: # win 8.0 or less
    ctypes.windll.user32.SetProcessDPIAware()


# spalsh comment
# import pyi_splash
# pyi_splash.update_text('UI Loaded ...')
# pyi_splash.close()


pyglet.options['win32_gdi_font'] = True
# fontpath = Path(__file__).parent / 
fontpath = './lib/fonts/static/Manrope-Regular.ttf'
# pyglet.font.add_file(str(fontpath))
print(fontpath)
pyglet.font.add_file(str(fontpath))
# pyglet.font.add_file('./lib/fonts/static/Manrope-Bold.ttf')
# pyglet.font.add_file('./lib/fonts/static/Manrope-ExtraBold.ttf')
# pyglet.font.add_file('./lib/fonts/static/Manrope-Light.ttf')
# pyglet.font.add_file('./lib/fonts/static/Manrope-Regular.ttf')
# pyglet.font.add_file('./lib/fonts/static/Manrope-SemiBold.ttf')
# pyglet.font.add_file('lib/fonts/static/Manrope-SemiBold.ttf')

from datetime import datetime

LogManagerObj.write_log("Application started")
# log_filename = f"./lib/app_logs.txt"
# logging.basicConfig(
#     filename=log_filename,
#     level=logging.INFO,
#     format="\n%(asctime)s  -  %(levelname)s  -  %(message)s",
# )
# logging.info("Application started.")

get_tally_companies()

# play_loading_animation()

# import threading
# thread101 = threading.Thread(
#     target=play_loading_animation,
#     daemon=True
# )
# if __name__ == "__main__":
#     print("main")
#     thread101.start()
#     time.sleep(5)

my_file = Path("./lib/app_cache.txt")
print('➡ app.py:7 my_file:', my_file)
appObj = App()
if my_file.is_file():

    json_data = open("./lib/app_cache.txt", "rb")
    json_data = decrypt_data(json_data.read())
    print('➡ app.py:75 json_data:', json_data)
    if "login_response" in json_data.keys() and json_data["login_response"]["status_code"] in [1,'1'] :
    # and ( 
    #     "company_mapping" in json_data.keys() and len(json_data["company_mapping"]) > 0 
    # )
    # :
        # logging.info("Previous Login Found.")
        LogManagerObj.write_log("Previous Login Found.")
        # constants.RX_ACCOUNTS = list([{key:value for key,value in json_data["login_response"]["data"]["pharmacy_details"]["logged_in_business"].items()}])
        # if "child_businesses" in json_data["login_response"]["data"]["pharmacy_details"].keys() and json_data["login_response"]["data"]["pharmacy_details"]["logged_in_business"]["is_HO"]:
        #     constants.RX_ACCOUNTS += [x for x in json_data["login_response"]["data"]["pharmacy_details"]["child_businesses"]]
        # if "HO_pharmacy" in json_data["login_response"]["data"]["pharmacy_details"].keys():
        #     constants.RX_ACCOUNTS += list([{key:value for key,value in json_data["login_response"]["data"]["pharmacy_details"]["HO_pharmacy"].items()}])            
        # if "is_HO" in json_data["login_response"]["data"]["pharmacy_details"]["logged_in_business"].keys():
        #     # constants.COMPANY_MAPPING = x for key, value in json_data["company_mapping"].items() if 
        #     ho_id = json_data["login_response"]["data"]["pharmacy_details"]["logged_in_business"]["id"]
        #     is_ho_present = False
            # constants.COMPANY_MAPPING = json_data["company_mapping"]
            # for x in json_data["company_mapping"]:
            #     if ho_id == x["chemist_id"]:
            #         is_ho_present = True
            # if not is_ho_present:
            #     logging.info("HO Details Not Found in login.")
            #     # constants.COMPANY_MAPPING = {}
            #     # login_thread()
                
            #     # appObj = App()
            #     appObj.show_frame("LoginScreen")
            #     pass
                 
        # else:
        #     constants.COMPANY_MAPPING = json_data["company_mapping"]
        # constants.MAPPING_TYPE = json_data["company_mapping"][0]["mapping_type"]
        constants.LOGIN_RESPONSE = json_data["login_response"]
        if "mobile" in json_data.keys():
            constants.MOBILE = json_data["mobile"]
            constants.TALLY_PORT = json_data.get("tally_port", 9000)
            constants.MOBILE_VAR.set(constants.MOBILE)
        if "accesstoken" in json_data["login_response"]["data"]:
            constants.ACCESS_TOKEN = json_data["login_response"]["data"]["accesstoken"]
        if "apikey" in json_data["login_response"]["data"]:
            constants.EVITAL_RX_API_KEY = json_data["login_response"]["data"]["apikey"]
            
        # list_of_dates = [x["synced_timestamp"] for x in json_data["data"]["last_synced_history"]]
        # if len(list_of_dates) > 0:
        #     constants.LAST_SYNCED = max(list_of_dates)
        
        # print('➡ app.py:71 json_data:', json_data)
        # print('➡ app.py:72 constants.EVITAL_RX_API_KEY:', constants.EVITAL_RX_API_KEY)
        # main_thread()
        # get_all_mapping_details()
        
        # thread101.join()
        
        appObj.show_frame("Dashboard")
    else:
        # thread101.join()
        # login_thread()
        
        appObj.show_frame("LoginScreen")
                
    # print('➡ app.py:9 json_data:', json_data)
else:
    print("no file")
    # logging.info("Login Details Not found.")
    LogManagerObj.write_log("Login Details Not found.")
    appObj.show_frame("LoginScreen")
    
if __name__ == "__main__":
    # appObj.update()
    # appObj.update_idletasks()
    # available_fonts = list(font.families())

    # for f in available_fonts:
    #     print(f)
        
    # appObj.option_add("*Font", "Manrope 14 bold")
    appObj.mainloop()
    multiprocessing.freeze_support()
    # login_thread()