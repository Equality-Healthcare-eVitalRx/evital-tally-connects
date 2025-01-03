import json
from pathlib import Path
from main import main_thread
from login import login_thread  
from lib import constants
import logging
import ctypes, tkinter
try: # >= win 8.1
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except: # win 8.0 or less
    ctypes.windll.user32.SetProcessDPIAware()
## spalsh comment
# import pyi_splash
# pyi_splash.update_text('UI Loaded ...')
# pyi_splash.close()

from datetime import datetime
log_filename = f"./lib/app_logs.txt"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logging.info("Application started.")

my_file = Path("./lib/credentials.json")
print('➡ app.py:7 my_file:', my_file)
if my_file.is_file():

    json_data = json.load(open("./lib/credentials.json", "rb"))
    if "login_response" in json_data.keys() and json_data["login_response"]["status_code"] in [1,'1'] and ( 
        "company_mapping" in json_data.keys() and len(json_data["company_mapping"]) > 0 
    ):
        logging.info("Previous Login Found.")
        constants.RX_ACCOUNTS = list([{key:value for key,value in json_data["login_response"]["data"]["pharmacy_details"]["logged_in_pharmacy"].items()}])
        if "child_pharmacies" in json_data["login_response"]["data"]["pharmacy_details"].keys() and json_data["login_response"]["data"]["pharmacy_details"]["logged_in_pharmacy"]["is_HO"]:
            constants.RX_ACCOUNTS += [x for x in json_data["login_response"]["data"]["pharmacy_details"]["child_pharmacies"]]
        if "HO_pharmacy" in json_data["login_response"]["data"]["pharmacy_details"].keys():
            constants.RX_ACCOUNTS += list([{key:value for key,value in json_data["login_response"]["data"]["pharmacy_details"]["HO_pharmacy"].items()}])            
        if "is_HO" in json_data["login_response"]["data"]["pharmacy_details"]["logged_in_pharmacy"].keys():
            # constants.COMPANY_MAPPING = x for key, value in json_data["company_mapping"].items() if 
            ho_id = json_data["login_response"]["data"]["pharmacy_details"]["logged_in_pharmacy"]["id"]
            is_ho_present = False
            constants.COMPANY_MAPPING = json_data["company_mapping"]
            for x in json_data["company_mapping"]:
                if ho_id == x["chemist_id"]:
                    is_ho_present = True
            if not is_ho_present:
                logging.info("HO Details Not Found in login.")
                constants.COMPANY_MAPPING = {}
                login_thread()   
        else:
            constants.COMPANY_MAPPING = json_data["company_mapping"]
        constants.MAPPING_TYPE = json_data["company_mapping"][0]["mapping_type"]
        constants.LOGIN_RESPONSE = json_data["login_response"]
        if "accesstoken" in json_data["login_response"]["data"]:
            constants.ACCESS_TOKEN = json_data["login_response"]["data"]["accesstoken"]
        if "apikey" in json_data["login_response"]["data"]:
            constants.EVITAL_RX_API_KEY = json_data["login_response"]["data"]["apikey"]
        main_thread()
    else:
        login_thread()
    print('➡ app.py:9 json_data:', json_data)
else:
    print("no file")
    logging.info("Login Details Not found.")
    
    login_thread()