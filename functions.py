


import base64
import ctypes
from datetime import date, datetime, timedelta
import json
import logging
import multiprocessing
import os
import threading
import time
import tkinter as tk
from tkinter import Tk, messagebox
import lib.constants
import tkinter
# import image
from cryptography.fernet import Fernet
from PIL import Image, ImageSequence, ImageTk

from lib import constants
from lib.import_export_data import *

def login(mobile_number, password):
    # mobile_number = mobile_entry.get()
    # password = password_entry.get()
    if len(mobile_number) != 10 or str(mobile_number).isdigit() == False:
        messagebox.showerror("Login Failed", "Invalid Mobile number")
        return 0
    elif len(password)<1:
        messagebox.showerror("Login Failed", "Invalid Password")
        return 0
    else:
    # Implement your login logic here
    # For demonstration, just check for specific mobile number and password
        res = send_login_request(mobile_number, password)
        # print('➡ login.py:89 res:', res)
        # logging.info(res)
        
        if "status_code" in res.keys() and res['status_code'] in [1,'1']:
            if_chain_pharmacy = res["data"]["business_details"]["is_chain_business"]
            # print('➡ login.py:94 if_chain_pharmacy:', if_chain_pharmacy)
            # messagebox.showinfo("Login", "Login Successful")
            # print(res["data"])
            constants.COMPANY_MAPPING = res["data"]["business_details"]["company_mapping_details"]
            if "accesstoken" in res["data"]:
                constants.ACCESS_TOKEN = res["data"]["accesstoken"]
            if "apikey" in res["data"]:

                constants.EVITAL_RX_API_KEY = res["data"]["apikey"]
            # constants.ACCESS_TOKEN = res["data"]["accesstoken"]
            
            data = {
                "login_response" : constants.LOGIN_RESPONSE,
                "company_mapping" : res["data"]["business_details"]["company_mapping_details"]
            }
            # with open("./lib/app_cache.txt", "w") as json_file:
            #     json.dump(data, json_file)
            with open("./lib/app_cache.txt", "w") as json_file:
                # json.dump(data, json_file)
                json_file.write(encrypt_data(data))
            already_mapped = True if len(res["data"]["business_details"]["company_mapping_details"]) > 0 else False
            
            # get_all_mapping_details()
            # if already_mapped:
            #     # login_window.destroy()
            #     main_thread()
            # else:
            #     if if_chain_pharmacy:
            #         # print()
            #         # if if_chain_pharmacy:
            #         if_ho = res["data"]["business_details"]["logged_in_business"]["is_HO"]
            #         if if_ho:
            #             ask_account_type()
            #         else:
            #             show_single_account_selection(login_window)
                        
            #     else:
            #         show_single_account_selection(login_window)
            return 1
        elif "status_code" in res.keys() and res['status_code'] in [0,'0']:
            # messagebox.showerror("Login Error", res["status_message"])
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

    constants.MAPPING_HISTORY = []
    constants.ONE_SYNC = []
    constants.LAST_SYNCED = ""
    constants.MOBILE = ""
    constants.MOBILE_VAR = None
    constants.CURRENT_BRANCH_SYNC = None
    constants.LAST_SYNC_VAR = None
    constants.REQUIRE_REBOOT = False
    constants.SYNC_TIMER = 0
    constants.CURRENT_BRANCH_SYNC_JSON = {}
    # root.destroy()
    
def get_all_mapping_details():
    res = get_mapping_details()
    if "status_code" in res and res["status_code"] in [1, '1']:
        constants.MAPPING_HISTORY = res["data"]
        # if constants.LAST_SYNC_VAR is not None:
        #     last_time = [str()]
        #     constants.LAST_SYNC_VAR.set()
    print('➡ functions.py:85 res:', res)
    
    
def startprocess(one_sync=False):
    constants.DISPLAY_SYNC_LOADER = True
    time.sleep(1)
    # animation_thread = threading.Thread(target=show_animation, daemon=True)
    # animation_thread.start()
    # show_animation()
    
    #print('➡ main.py:97 constants.LOGIN_RESPONSE:', constants.LOGIN_RESPONSE)
    # if constants.MAPPING_TYPE == "single" and constants.LOGIN_RESPONSE["data"]["business_details"]["is_chain_business"] and constants.LOGIN_RESPONSE["data"]["business_details"]["logged_in_business"]["is_HO"]:
    #     #print("Sdsdgf")
    #     #print('➡ main.py:99 constants.COMPANY_MAPPING:', constants.COMPANY_MAPPING)
    #     #print('➡ main.py:101 constants.RX_ACCOUNTS:', constants.RX_ACCOUNTS)
    #     companies = [
    #         {"chemist_id": x["id"], "company_name": m["company_name"], "company_guid": m["company_guid"]}
    #         for m in constants.COMPANY_MAPPING
    #         for x in constants.RX_ACCOUNTS 
    #     ]
    # else:
    #     companies = constants.COMPANY_MAPPING
    
    # print("1234")
    get_tally_companies()
    # print("1234")
    # print(constants.MAPPING_HISTORY)
    if not one_sync:
        companies = [
            {"chemist_id" : x["entity_id"], "company_name":x["tally_company_name"], "company_guid":x["tally_company_guid"], "branch_name":x["branch_name"]}
            for x in constants.MAPPING_HISTORY["results"] if x["is_mapped"] in ['true', True, 'True']
        ]
    else:
        companies = constants.ONE_SYNC
    # #print('➡ main.py:102 companies:', companies)
    # #print(dfgdg)
    #print(select_software_dropdown.get())
    current_time = datetime.now()
    current_year = current_time.year if current_time.month > 3 else current_time.year - 1
    from_date = date(current_year,int(4),1)
    
    to_date = date(current_year+1,3,31)
    
    request_array = []
    init_data_array = []
    if len(companies) <= 0:
        messagebox.showerror("Tally Sync", "Please Map Your Company First.")
        constants.STOP_THREAD = True
        return 0
    for company in companies:
        if constants.CURRENT_BRANCH_SYNC is not None:
        
            constants.CURRENT_BRANCH_SYNC.set(
                company["branch_name"]
            )
        #print('➡ main.py:141 company:', company)
        data_list = {
            "list_of_companies": {},
            "active_company": {},
            "balance_sheet": {},
            "profit_and_loss": {},
            "ratio_analysis": {},
            
        }
        init_data_list = {
            "ledgers_data" : {},
            "groups_data" : {}
        }
        
        for key, value in constants.REQUEST_FORMATS.items():
            if constants.CURRENT_BRANCH_SYNC is not None:
            
                constants.CURRENT_BRANCH_SYNC.set(
                    company["branch_name"]
                )
            #print('➡ main.py:141 company:', company)
            print('➡ func.py:208 key:', key)
            
            if key != "list_of_companies":
                request_str = str(value)
                request_str = request_str.replace("company_name", company["company_name"])
                # request_str = request_str.replace("company_name", "company")
                # request_str = request_str.replace("company_name", "Smit Pharmacy")
                request_str = request_str.replace("from_date", from_date.strftime("%Y%m%d"))
                request_str = request_str.replace("to_date", to_date.strftime("%Y%m%d"))
                # #print('➡ main.py:25 request_str:', request_str)
                
                parsed_data =  send_request_to_tally(request_str, key)
                
                # if key == "groups_data":
                #     print('➡ main.py:206 parsed_data:', parsed_data)
                
                if key in data_list.keys():
                    #print("yes")
                    data_list[key] = json.loads(parsed_data)
                else:
                    #print("no")
                    init_data_list[key] = json.loads(parsed_data)
            elif key == "list_of_companies":
                    request_str = str(value)
                    parsed_data =  send_request_to_tally(request_str, key)
                    print('➡ functions.py:217 parsed_data:', parsed_data)
                    data_list[key] = json.loads(parsed_data)
            # if key == 'profit_and_loss':
                # print('➡ functions.py:157 parsed_data:', parsed_data)
                
        # #print('➡ main.py:210 data_list:', data_list)
        # #print('➡ main.py:213 init_data_list:', init_data_list)
                
        init_data_list["start_date"] = from_date.strftime("%Y-%m-%d")
        init_data_list["end_date"] = to_date.strftime("%Y-%m-%d")
        init_data_list["chemist_id"] = company["chemist_id"]
        
        tally_data = {
            "start_date" : from_date.strftime("%Y-%m-%d"),
            "end_date" : to_date.strftime("%Y-%m-%d"),
            "chemist_id" : company["chemist_id"],
            "json_data" : data_list,
        }
        # logging.info(encrypt_data(tally_data))
        LogManagerObj.write_log(tally_data)
        # print('➡ functions.py:245 cipher_text(json.dumps(tally_data):', cipher_text(json.dumps(tally_data), 15))
        # print('➡ functions.py:246 15):', 15))
        # logging.info(encrypt_data(init_data_list))
        LogManagerObj.write_log(init_data_list)
        request_array.append(tally_data)
        init_data_array.append(init_data_list)
        
        if constants.STOP_THREAD:
            print("thread stopped abnormally")
            constants.STOP_THREAD = False
            return 0
    #print('➡ main.py:226 request_array:', request_array)
        # #print('➡ main.py:228 init_data_array:', init_data_array)
    if constants.STOP_THREAD:   
        print("thread stopped abnormally")
        constants.STOP_THREAD = False
        return 0
    res = send_data_to_evitalrx(request_array)
    print('➡ functions.py:186 res:', res)
    init_response = send_init_data_to_evital_rx(init_data_array, from_date.strftime("%Y-%m-%d"), to_date.strftime("%Y-%m-%d"))    
    print('➡ functions.py:188 init_response:', init_response)
    # message_label.config(text=res["status_message"])
    print('➡ main.py:168 constants.DISPLAY_SYNC_LOADER:', constants.DISPLAY_SYNC_LOADER)
    
    if not ('status_code' in res.keys() and res["status_code"] != 1):
        messagebox.showerror("Tally Sync", "Unable to sync data.")
    elif not ('status_code' in init_response.keys() and init_response["status_code"] != 1):
        messagebox.showerror("Sync Issue", "Unable to sync data.")
    # elif constants.THREAD is None:
    #     messagebox.showinfo("Tally Data Export",str(res["status_message"]).replace("_", " "))
    
    # message_label.config(text=str(res["status_message"]).replace("_", " ").title())
    constants.DISPLAY_SYNC_LOADER = False

    constants.LAST_SYNCED = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if one_sync:
        constants.STOP_THREAD = True
    else:
        constants.REQUIRE_REBOOT = True
        
    # if parent is not None:
    #     parent.__init__(parent.parent, parent.controller)
    # additional_message_label.config(text="Last Syncd : "+constants.LAST_SYNCED)
    # print('➡ main.py:168 constants.DISPLAY_SYNC_LOADER:', constants.DISPLAY_SYNC_LOADER)

    
def start_background_thread(start_now=False, one_sync=False):
    while not constants.STOP_THREAD:
        
        #print("Running background task...")
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
            messagebox.showerror("Tally is Not Open","Make Sure Tally is Running.")
            return 0
    if constants.THREAD is None:
        background_thread = threading.Thread(target=start_background_thread, args=(start_now,one_sync), daemon=True)
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
        
        current_time = time.time()
        if current_time - start_time >= 3:
            print("stop")
            constants.LOAD_COMPLETE = True
            self.after_cancel(animate_gif)
            self.destroy()
            return 0
        
        # time.sleep(0.5)
        # print(frames)
        frame = frames[index]
        sync_label.configure(image=frame)
        next_index = (index + 3) % len(frames)
        self.after(300, animate_gif, self, sync_label, frames, next_index)

        
    
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
    
    root = Tk()
    root.overrideredirect(True)
    
    user32 = ctypes.windll.user32
    x ,y = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    x = (x - 600) // 2
    y = (y - 600) // 2
    
    root.geometry(f'+{str(int(x))}+{str(int(y))}')
    root.geometry("600x600")
    root.attributes("-toolwindow", False)  # Make it appear in Alt+Tab
    root.attributes("-fullscreen", False)  # Prevent full-screen mode
    root.resizable(0,0)
        
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
  
    root.mainloop()
    
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
        
        if (char.isupper()):
            result += chr((ord(char) + s-65) % 26 + 65)
        # Encrypt lowercase characters in plain text
        else:
            result += chr((ord(char) + s - 97) % 26 + 97)
    return result

class LogManager:
    def __init__(self, log_file="./lib/app_logs.txt"):
        self.log_file = log_file
        self.last_clear_date = self._get_last_clear_date()
        
        # Start the log clearing thread
        self.clear_thread = threading.Thread(target=self._monitor_for_clearing, daemon=True)
        self.clear_thread.start()

    def _get_last_clear_date(self):
        """Extract the date when the log was created from the first line of the log file"""
        if not os.path.exists(self.log_file):
            return date.today() - timedelta(days=1)  # Default to yesterday
        
        try:
            with open(self.log_file, "rb") as f:
                first_line = f.readline().strip()
                if first_line.startswith(b'# Log file created on'):
                    # Try to decrypt if it's encrypted
                    try:
                        key = constants.ENCRYPTION_KEY
                        fernet = Fernet(key)
                        line = fernet.decrypt(first_line).decode('utf-8')
                    except:
                        # Not encrypted, just decode
                        line = first_line.decode('utf-8')
                    
                    # Extract date using regex
                    match = re.search(r'created on (\d{4}-\d{2}-\d{2})', line)
                    if match:
                        date_str = match.group(1)
                        return datetime.strptime(date_str, "%Y-%m-%d").date()
                
                # If we get here, check the timestamps in the logs
                self._rewind_file(f)
                latest_date = None
                
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        # Try to decrypt the line
                        key = self._get_key()
                        fernet = Fernet(key)
                        decrypted = fernet.decrypt(line).decode('utf-8')
                        
                        # Extract timestamp
                        match = re.search(r'\[(\d{4}-\d{2}-\d{2})', decrypted)
                        if match:
                            date_str = match.group(1)
                            log_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                            if latest_date is None or log_date > latest_date:
                                latest_date = log_date
                    except:
                        pass
                
                if latest_date:
                    return latest_date
                
            # Default to yesterday if we couldn't find a date
            return date.today() - timedelta(days=1)
        except Exception as e:
            print(f"Error determining last clear date: {e}")
            return date.today() - timedelta(days=1)
    
    def _update_last_clear_date(self):
        """Update the date of the last log clearing"""
        metadata_file = "log_metadata.txt"
        with open(metadata_file, "w") as f:
            f.write(date.today().strftime("%Y-%m-%d"))
        self.last_clear_date = date.today()
    
    def _monitor_for_clearing(self):
        """Thread function to check for daily log clearing"""
        while True:
            today = date.today()
            last_clear_date = self._get_last_clear_date()
            
            if today > last_clear_date:
                self.clear_logs()
            
            # Check every hour
            time.sleep(3600)
    
    def clear_logs(self):
        """Clear the log file and update the clear date"""
        try:
            creation_date = datetime.now()
            header = f"# Log file created on {creation_date.strftime('%Y-%m-%d %H:%M:%S')}"
            
            with open(self.log_file, "w") as f:
                f.write(header + "\n")
            
            return True
        except Exception as e:
            print(f"Error clearing logs: {e}")
            return False
    
    def write_log(self, message):
        """Write an encrypted log entry"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {message}"
            
            # Encrypt the log entry
            # key = self._get_key()
            key = constants.ENCRYPTION_KEY
            fernet = Fernet(key)
            encrypted_entry = fernet.encrypt(log_entry.encode())
            
            with open(self.log_file, "ab") as f:
                f.write(encrypted_entry + b"\n")
            
            return True
        except Exception as e:
            print(f"Error writing log: {e}")
            return False
    
    def read_logs(self):
        """Read and decrypt all log entries"""
        if not os.path.exists(self.log_file):
            return []
        
        try:
            # key = self._get_key()
            key = constants.ENCRYPTION_KEY
            fernet = Fernet(key)
            
            logs = []
            with open(self.log_file, "rb") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            decrypted_line = fernet.decrypt(line).decode('utf-8')
                            logs.append(decrypted_line)
                        except:
                            # Skip lines that can't be decrypted (could be plain text headers)
                            if line.startswith(b'#'):
                                logs.append(line.decode('utf-8'))
            
            return logs
        except Exception as e:
            print(f"Error reading logs: {e}")
            return [f"Error: {e}"]
        
    def get_last_clear_date_formatted(self):
        """Get the formatted last clear date for display"""
        return self._get_last_clear_date().strftime("%Y-%m-%d")

LogManagerObj = LogManager()