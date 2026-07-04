import base64
import ctypes
from datetime import datetime
import json
import multiprocessing
import threading
import time
import tkinter as tk
from tkinter import messagebox

# import image
from cryptography.fernet import Fernet
from PIL import Image, ImageSequence, ImageTk

from lib import constants
from lib.import_export_data import *
from lib.tally_service import TallyService


def login(mobile_number, password, entity="chemist"):
    if len(mobile_number) != 10 or str(mobile_number).isdigit() == False:
        messagebox.showerror("Login Failed", "Invalid Mobile number")
        return 0
    elif len(password) < 1:
        messagebox.showerror("Login Failed", "Invalid Password")
        return 0
    else:
        res = send_login_request(mobile_number, password, entity)
        # print(res)

        if "status_code" in res.keys() and res["status_code"] in [1, "1"]:
            if_chain_pharmacy = res["data"]["business_details"]["is_chain_business"]
            LogManagerObj.write_log(res.get("status_message", ""))

            constants.COMPANY_MAPPING = []
            if (
                len(
                    res["data"]["business_details"]["logged_in_business"][
                        "tally_mapping_details"
                    ]
                )
                > 0
            ):
                constants.COMPANY_MAPPING.append(
                    res["data"]["business_details"]["logged_in_business"][
                        "tally_mapping_details"
                    ][0]
                )

            if len(res["data"]["business_details"].get("child_businesses", [])) > 0:
                for x in res["data"]["business_details"]["child_businesses"]:
                    if len(x["tally_mapping_details"]) > 0:
                        constants.COMPANY_MAPPING.append(x["tally_mapping_details"][0])

            if "accesstoken" in res["data"]["business_details"]["logged_in_business"]:
                constants.ACCESS_TOKEN = res["data"]["business_details"][
                    "logged_in_business"
                ]["accesstoken"]
            if "apikey" in res["data"]["business_details"]["logged_in_business"]:
                constants.EVITAL_RX_API_KEY = res["data"]["business_details"][
                    "logged_in_business"
                ]["apikey"]

            data = {
                "login_response": constants.LOGIN_RESPONSE,
                "company_mapping": constants.COMPANY_MAPPING,
            }
            with open("./lib/app_cache.txt", "w") as json_file:
                json_file.write(encrypt_data(data))

            return 1
        elif "status_code" in res.keys() and res["status_code"] in [0, "0"]:
            LogManagerObj.write_log("Login Failed")
            LogManagerObj.write_log(res.get("status_message", ""))

            return 0


def logout():
    # with open("./lib/app_cache.txt", "w") as json_file:
    #     json.dump({}, json_file)
    with open("./lib/app_cache.txt", "w") as json_file:
        # json.dump(data, json_file)
        json_file.write(encrypt_data({}))
    constants.COMPANY_MAPPING = {}
    constants.MAPPING_HISTORY = {}
    constants.EVITAL_RX_API_KEY = ""
    constants.LOGIN_RESPONSE = {}
    constants.IS_LOGIN = False
    constants.RX_ACCOUNTS = []
    # constants.TALLY_ACCOUNTS = []
    constants.TALLY_RESPONSE = []
    constants.COMPANY_MAPPING = []
    constants.MAPPING_TYPE = ""
    constants.ACCESS_TOKEN = ""
    constants.THREAD = None
    constants.STOP_THREAD = False
    constants.DISPLAY_SYNC_LOADER = False

    constants.MAPPING_HISTORY = {}
    constants.ONE_SYNC = []
    constants.LAST_SYNCED = ""
    constants.MOBILE = ""
    constants.MOBILE_VAR = None
    constants.CURRENT_BRANCH_SYNC = None
    constants.LAST_SYNC_VAR = None
    constants.REQUIRE_REBOOT = False
    constants.SYNC_TIMER = 0
    constants.CURRENT_BRANCH_SYNC_JSON = {}
    constants.SYNC_STAGE = 0
    # SYNC_STAGE = 0
    constants.SYNC_BTN_TEXT = "Next"
    constants.LAST_SYNC_HEADER_VAR = ""
    constants.SYNC_START_DATE = ""
    constants.SYNC_END_DATE = ""
    LogManagerObj.write_log("Logout Successful")
    # root.destroy()


def get_all_mapping_details():
    res = get_mapping_details()
    print(res, "mapping res")
    if "status_code" in res and res["status_code"] in [1, "1"]:
        constants.MAPPING_HISTORY = res["data"]


def startprocess(one_sync=False):
    constants.DISPLAY_SYNC_LOADER = True
    time.sleep(1)
    tallyObj = TallyService()

    get_tally_companies()

    if not one_sync:
        company_options = {
            x["company_guid"]: x["company_name"] for x in constants.TALLY_ACCOUNTS
        }
        tally_guids = list(company_options.keys())
        companies = [
            {
                "chemist_id": x["entity_id"],
                "company_name": x["tally_company_name"],
                "company_guid": x["tally_company_guid"],
                "branch_name": x["branch_name"],
            }
            for x in constants.MAPPING_HISTORY["results"]
            if x["is_mapped"] in ["true", True, "True"]
            and x["tally_company_guid"] in tally_guids
            # if x["tally_company_name"] == constants.COMPANY_NAME
        ]
    else:
        companies = [
            {
                "chemist_id": x["entity_id"],
                "company_name": x["tally_company_name"],
                "company_guid": x["tally_company_guid"],
                "branch_name": x["branch_name"],
            }
            for x in constants.MAPPING_HISTORY["results"]
            if x["is_mapped"] in ["true", True, "True"]
            if x["tally_company_name"] == constants.COMPANY_NAME
        ]

    if len(companies) <= 0:
        messagebox.showerror("Tally Sync", "Please Map Your Company First.")
        constants.STOP_THREAD = True
        return 0

    request_array = []
    init_data_array = []
    for company in companies:
        if constants.STOP_THREAD:
            print("thread stopped abnormally")
            LogManagerObj.write_log("thread stopped abnormally")
            LogManagerObj.write_log("+" * 50)
            constants.STOP_THREAD = False
            return 0
        LogManagerObj.write_log("+" * 50)
        LogManagerObj.write_log(
            f"🔑 Syncing {company['company_name']} from {company['branch_name']}"
        )

        current_apikey = ""
        current_from_date = ""
        if (
            constants.LOGIN_RESPONSE["data"]["business_details"]["logged_in_business"][
                "id"
            ]
            == company["chemist_id"]
            and constants.LOGIN_RESPONSE["data"]["business_details"][
                "logged_in_business"
            ]["apikey"]
            != ""
        ):
            current_apikey = constants.LOGIN_RESPONSE["data"]["business_details"][
                "logged_in_business"
            ]["apikey"]

        if current_apikey == "":
            for x in constants.LOGIN_RESPONSE["data"]["business_details"][
                "child_businesses"
            ]:
                if x["id"] == company["chemist_id"] and x["apikey"] != "":
                    current_apikey = x["apikey"]

        print(current_apikey, "Api key")
        if current_apikey == "":
            print("No Api key found")
            LogManagerObj.write_log("No Api key found")
            LogManagerObj.write_log("+" * 50)
            continue
        # continue
        # return 0
        
        current_company_data = filter(lambda x: x["company_guid"] == company["company_guid"], constants.TALLY_ACCOUNTS)
        if current_company_data:
            for z in current_company_data:
                current_from_date = z["starting_from"]
                break

        from_date = datetime.strptime(constants.SYNC_START_DATE.get(), "%d-%m-%y")
        to_date = datetime.strptime(constants.SYNC_END_DATE.get(), "%d-%m-%y")
        if "Ledgers" in constants.SELECTED_MODULES:
            if constants.CURRENT_BRANCH_SYNC is not None:
                constants.CURRENT_BRANCH_SYNC.set("Syncing Ledgers")
            ledgers_selected = True
            current_from_date = datetime.strptime(current_from_date, "%Y%m%d").strftime("%Y-%m-%d")
            data = get_data_from_evitalrx(
                from_date.strftime("%Y-%m-%d"),
                to_date.strftime("%Y-%m-%d"),
                current_apikey,
                "Accounts",
                current_from_date
            )
            # print(data)
            vouchers = extract_vouchers(data, ledgers_selected)
            if not vouchers:
                print("⚠️ No Ledger records found across all keys.")
                LogManagerObj.write_log("No Ledger records found across all keys.")
            else:
                print(f"🚀 Found {len(vouchers)} Ledger records. Importing...")
                LogManagerObj.write_log(
                    f"🚀 Found {len(vouchers)} Ledger records. Importing..."
                )
                tallyObj.push_batch(
                    vouchers,
                    report_name="All Masters",
                    company_name=company["company_name"],
                )
        for x in constants.SELECTED_MODULES:
            if x in ["ledgers", "Ledgers"]:
                continue
            LogManagerObj.write_log("=" * 50)
            LogManagerObj.write_log("-" * 50)
            if constants.STOP_THREAD:
                print("thread stopped abnormally")
                LogManagerObj.write_log("thread stopped abnormally")
                LogManagerObj.write_log("+" * 50)
                constants.STOP_THREAD = False
                return 0
            if constants.CURRENT_BRANCH_SYNC is not None:
                constants.CURRENT_BRANCH_SYNC.set(f"Syncing {x}")
            ledgers_selected = False
            data = get_data_from_evitalrx(
                from_date.strftime("%Y-%m-%d"),
                to_date.strftime("%Y-%m-%d"),
                current_apikey,
                x,
            )
            # print(data)
            
            vouchers = extract_party_xmls(data)
            if not vouchers:
                print("⚠️ No Party XML records found across all keys.")
                LogManagerObj.write_log("⚠️ No Party XML records found across all keys.")
            else:
                print(f"🚀 Found {len(vouchers)} Party XML records. Importing...")
                LogManagerObj.write_log(
                    f"🚀 Found {len(vouchers)} Party XML records. Importing..."
                )
                tallyObj.push_batch(
                    vouchers,
                    company_name=company["company_name"],
                )
            
            vouchers = extract_vouchers(data, ledgers_selected)
            if not vouchers:
                LogManagerObj.write_log(f"⚠️ No {x} records found across all keys.")
                print(f"⚠️ No {x} records found across all keys.")
            else:
                print(f"🚀 Found {len(vouchers)} {x} records. Importing...")
                LogManagerObj.write_log(
                    f"🚀 Found {len(vouchers)} {x} records. Importing..."
                )
                tallyObj.push_batch(
                    vouchers,
                    company_name=company["company_name"],
                    fetch_voucher_numbers=True,
                )
        
        if constants.CURRENT_BRANCH_SYNC is not None:
            constants.CURRENT_BRANCH_SYNC.set("Exporting Reconciliation Data")
        txt_data = tallyObj.export_voucher_register(
            from_date=from_date.strftime("%Y-%m-%d"),
            to_date=to_date.strftime("%Y-%m-%d"),
            company_name=company["company_name"],
        )

        # ── Call ERP reconciliation API ────────────────────────────
        print("🔄 Organizing reconciliation data..")
        LogManagerObj.write_log("🔄 Organizing reconciliation data..")

        results = send_reconciliation(
            file_content=txt_data,
            start_date=from_date.strftime("%Y-%m-%d"),
            end_date=to_date.strftime("%Y-%m-%d"),
            api_keys=[current_apikey],
        )

        for _, res in results.items():
            if "error" in res:
                print(f"❌ Reconciliation failed: {res['error']}")
                LogManagerObj.write_log(f"❌ Reconciliation failed: {res['error']}")
            else:
                LogManagerObj.write_log("✅ Reconciliation successful.")
                print("✅ Reconciliation successful.")

        if constants.CURRENT_BRANCH_SYNC is not None:
            constants.CURRENT_BRANCH_SYNC.set("Exporting Balance Sheet")
        data_list = {
            "list_of_companies": {},
            "active_company": {},
            "balance_sheet": {},
            "profit_and_loss": {},
            "ratio_analysis": {},
        }
        init_data_list = {"ledgers_data": {}, "groups_data": {}}

        current_date = datetime.now()
        start_date = from_date.strftime("%Y%m%d")
        end_date = to_date.strftime("%Y%m%d")

        if current_date.month > 3:
            start_date = str(current_date.year) + "0401"
            end_date = str(current_date.year + 1) + "0331"
        else:
            start_date = str(current_date.year - 1) + "0401"
            end_date = str(current_date.year - 1) + "0331"

        for key, value in constants.REQUEST_FORMATS.items():
            if constants.STOP_THREAD:
                print("thread stopped abnormally")
                LogManagerObj.write_log("thread stopped abnormally")
                LogManagerObj.write_log("+" * 50)
                constants.STOP_THREAD = False
                return 0

            if key != "list_of_companies":
                request_str = str(value)
                request_str = request_str.replace(
                    "company_name", company["company_name"]
                )
                # request_str = request_str.replace("company_name", "company")
                # request_str = request_str.replace("company_name", "Smit Pharmacy")

                request_str = request_str.replace("from_date", start_date)
                request_str = request_str.replace("to_date", end_date)
                # #print('➡ main.py:25 request_str:', request_str)

                parsed_data = send_request_to_tally(request_str, key)

                # if key == "groups_data":
                #     print('➡ main.py:206 parsed_data:', parsed_data)

                if key in data_list.keys():
                    # print("yes")
                    data_list[key] = json.loads(parsed_data)
                else:
                    # print("no")
                    init_data_list[key] = json.loads(parsed_data)
            elif key == "list_of_companies":
                request_str = str(value)
                parsed_data = send_request_to_tally(request_str, key)
                # print('➡ functions.py:217 parsed_data:', parsed_data)
                data_list[key] = json.loads(parsed_data)
            # if key == 'profit_and_loss':
            # print('➡ functions.py:157 parsed_data:', parsed_data)

        # #print('➡ main.py:210 data_list:', data_list)
        # #print('➡ main.py:213 init_data_list:', init_data_list)

        new_start_date = datetime.strptime(start_date, "%Y%m%d").strftime("%Y-%m-%d")
        new_end_date = datetime.strptime(end_date, "%Y%m%d").strftime("%Y-%m-%d")
        init_data_list["start_date"] = new_start_date
        init_data_list["end_date"] = new_end_date
        init_data_list["chemist_id"] = company["chemist_id"]

        tally_data = {
            "start_date": new_start_date,
            "end_date": new_end_date,
            "chemist_id": company["chemist_id"],
            "json_data": data_list,
        }
        request_array.append(tally_data)
        init_data_array.append(init_data_list)

        if constants.STOP_THREAD:
            print("thread stopped abnormally")
            LogManagerObj.write_log("thread stopped abnormally")
            LogManagerObj.write_log("+" * 50)
            constants.STOP_THREAD = False
            return 0

    LogManagerObj.write_log("+" * 50)

    if constants.STOP_THREAD:
        print("thread stopped abnormally")
        LogManagerObj.write_log("thread stopped abnormally")
        LogManagerObj.write_log("+" * 50)
        constants.STOP_THREAD = False
        return 0
    LogManagerObj.write_log("Sending tally data to eVitalRx")
    res = send_data_to_evitalrx(request_array)
    LogManagerObj.write_log(res)

    init_response = send_init_data_to_evital_rx(
        init_data_array, from_date.strftime("%Y-%m-%d"), to_date.strftime("%Y-%m-%d")
    )
    LogManagerObj.write_log(init_response)

    if not ("status_code" in res.keys() and res["status_code"] != 1):
        messagebox.showerror("Tally Sync", "Unable to sync data.")
    elif not (
        "status_code" in init_response.keys() and init_response["status_code"] != 1
    ):
        messagebox.showerror("Sync Issue", "Unable to sync data.")
    # elif constants.THREAD is None:
    #     messagebox.showinfo("Tally Data Export",str(res["status_message"]).replace("_", " "))
    constants.ANIMATION_AFTER_ID = None
    # message_label.config(text=str(res["status_message"]).replace("_", " ").title())
    constants.DISPLAY_SYNC_LOADER = False

    constants.LAST_SYNC_HEADER_VAR = ""
    constants.SYNC_START_DATE = ""
    constants.SYNC_END_DATE = ""
    constants.SELECTED_MODULES = []
    constants.STOP_THREAD = True

    constants.LAST_SYNCED = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if one_sync:
        constants.STOP_THREAD = True
    print("stopped")


def start_background_thread(start_now=False, one_sync=False):
    while not constants.STOP_THREAD:
        # print("Running background task...")
        tally_status = check_if_tally_running()
        if tally_status == True:
            if not start_now:
                if constants.SYNC_TIMER == 0:
                    constants.STOP_THREAD = True
                    break
                print("sleep")
                time.sleep(constants.SYNC_TIMER * 60)
                # time.sleep(3 * 1)
            if constants.STOP_THREAD:
                print("background thread killed")
                break
            startprocess(one_sync=one_sync)
            if start_now:
                constants.STOP_THREAD = True
                break

        else:
            time.sleep(15 * 60)
    # constants.STOP_THREAD = False


def start_thread(start_now=False, one_sync=False):
    if start_now:
        tally_status = check_if_tally_running()
        if tally_status != True:
            messagebox.showerror("Tally is Not Open", "Make Sure Tally is Running.")
            return 0
    if constants.THREAD is None:
        background_thread = threading.Thread(
            target=start_background_thread, args=(start_now, one_sync), daemon=True
        )
        background_thread.start()
        constants.THREAD = background_thread
        print("Background thread started.")
    else:
        print("Background thread is already running.")


def play_loading_animation():

    current_frame = 0
    frames = []
    start_time = time.time()

    def animate_gif(self, sync_label, frames, index=0):
        if not sync_label.winfo_exists():
            return  # STOP if widget is gone

        current_time = time.time()
        if current_time - start_time >= 3:
            print("stop")
            constants.LOAD_COMPLETE = True
            self.after_cancel(animate_gif)
            self.withdraw()
            try:
                self.destroy()  # Properly destroy the window
            except:
                pass
            return 0

        # time.sleep(0.5)
        # print(frames)
        frame = frames[index]
        sync_label.configure(image=frame)
        next_index = (index + 3) % len(frames)
        self.after(100, animate_gif, self, sync_label, frames, next_index)

    def process_frame(frame, size):
        # Convert the frame to RGBA
        frame = frame.convert("RGBA")
        data = frame.getdata()

        # Make black background transparent
        new_data = []
        for item in data:
            # If the pixel is black, make it transparent
            if item[:3] == (0, 0, 0):
                new_data.append((0, 0, 0, 0))  # Transparent
            else:
                new_data.append(item)
        frame.putdata(new_data)

        # Resize the frame
        frame = frame.resize(size, Image.Resampling.LANCZOS)
        return frame

    root = tk.Toplevel()
    root.overrideredirect(True)

    user32 = ctypes.windll.user32
    x, y = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    x = (x - 600) // 2
    y = (y - 600) // 2

    root.geometry(f"+{str(int(x))}+{str(int(y))}")
    root.geometry("600x600")
    root.attributes("-toolwindow", False)  # Make it appear in Alt+Tab
    root.attributes("-fullscreen", False)  # Prevent full-screen mode
    root.resizable(0, 0)

    root.iconbitmap("./lib/images/logo2.ico")
    root.title("Tally Sync")

    hwnd = ctypes.windll.user32.GetForegroundWindow()
    ctypes.windll.user32.SetWindowLongW(hwnd, -20, 0x00000000)

    gif_path = "lib\images\TallySyncSplash.gif"  # Update with your gif path

    gif_label = tk.Label(root, bg="white")
    gif_label.pack(expand=True)

    gif = Image.open(gif_path)
    # frames = [ImageTk.PhotoImage(gif.copy().seek(i)) for i in range(gif.n_frames)]

    size = (600, 600)  # Set your desired size (width, height)
    for frame in ImageSequence.Iterator(gif):
        processed_frame = process_frame(frame, size)
        tk_frame = ImageTk.PhotoImage(processed_frame)
        frames.append(tk_frame)

    animate_gif(root, gif_label, frames, current_frame)

    multiprocessing.freeze_support()

    # root.mainloop()


def encrypt_data(data):
    key = constants.ENCRYPTION_KEY
    f = Fernet(key)
    data = json.dumps(data)
    encrypted_data = f.encrypt(data.encode())
    return base64.b64encode(encrypted_data).decode()  # Convert to Base64 string


# Decrypt data
def decrypt_data(encrypted_base64):
    key = constants.ENCRYPTION_KEY
    f = Fernet(key)
    encrypted_data = base64.b64decode(encrypted_base64)  # Decode from Base64
    try:
        decrypted_data = f.decrypt(encrypted_data).decode()
    except:
        decrypted_data = "{}"
    return json.loads(decrypted_data)


def cipher_text(text, s):
    result = ""
    # transverse the plain text
    for i in range(len(text)):
        char = text[i]
        # Encrypt uppercase characters in plain text

        if char.isupper():
            result += chr((ord(char) + s - 65) % 26 + 65)
        # Encrypt lowercase characters in plain text
        else:
            result += chr((ord(char) + s - 97) % 26 + 97)
    return result


def extract_vouchers(multi_key_response: dict, ledgers_selected: bool) -> list:
    """
    Accepts the multi-key response dict  { api_key: response, ... }
    and returns a flat, deduplicated list of XML voucher strings across
    all keys, with optional ledger-XML filtering applied.
    """
    seen = set()
    vouchers = []

    for api_key, response in multi_key_response.items():
        # Skip failed keys
        if "error" in response:
            # self.log_msg(f"  ⚠️  Key {api_key} failed: {response['error']}")
            continue

        # print(response)
        data = response.get("data") or {}
        xmls = data.get("voucher_xmls") or data.get("import_xmls") or []

        for xml in xmls:
            # if not ledgers_selected and "<LEDGER " in xml:
            #     continue  # filter out ledger XMLs when not requested
            if xml not in seen:
                seen.add(xml)
                vouchers.append(xml)

    return vouchers

def extract_party_xmls(multi_key_response:dict) -> list:
    seen = set()
    vouchers = []

    for api_key, response in multi_key_response.items():
        # Skip failed keys
        if "error" in response:
            # self.log_msg(f"  ⚠️  Key {api_key} failed: {response['error']}")
            continue

        # print(response)
        data = response.get("data") or {}
        xmls = data.get("party_import_xmls") or []

        for xml in xmls:
            if xml not in seen:
                seen.add(xml)
                vouchers.append(xml)

    return vouchers
    

from log import LogManagerObj
