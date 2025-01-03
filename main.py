import itertools
import json
import threading
from tkinter import *
from lib import constants
from tkinter import messagebox
from lib.import_export_data import send_request_to_tally,send_data_to_evitalrx,reset_mapping_from_rx,check_if_tally_running,send_init_data_to_evital_rx
from tkinter.ttk import Combobox, Labelframe
import os
from ttkthemes import ThemedTk
from tkcalendar import Calendar, DateEntry
from datetime import datetime, date
import time

spinner_loader =itertools.cycle(['⬤       ', '     ⬤  ', '       ⬤', '  ⬤     '])  # Larger symbols for circular pattern
    

def add_labels(files_list_frame):
    for index, value in enumerate(constants.IMPORTED_FIELDS):
        child_label = Label(files_list_frame, text=str('\u2022'+"  "+value).replace('_',' ').title(), anchor='w')
        child_label.pack(padx=2, pady=5, fill='both')
    
    
    # pass
            
def main_thread():
    def show_animation():
        
        spinner = ['|', '/', '---', '\\']  # Symbols for the spinner
        spinner_index = 0
        while constants.DISPLAY_SYNC_LOADER == True:
            # print("spin")
            # message_label.config(text="Processing\t"+next(spinner_loader))
            # message_label.config(text=f"\rLoading... {symbol}")
            message_label.config(text=f"\rProcessing... {spinner[spinner_index]}")
            spinner_index += 1
            if spinner_index >= len(spinner):
                spinner_index = 0
            
            time.sleep(0.2)
            # for symbol in spinner:
                # if constants.DISPLAY_SYNC_LOADER != True:
                #     break
            

    
            
    root = ThemedTk(theme='breeze')
    root.resizable(0,0)
    root.iconbitmap("./lib/images/logo2.ico")
    root.title("Import Tally Data to eVitalRx")
    root.geometry("500x400")

    thisyear = datetime.now().year
    
    #print(constants.LOGIN_RESPONSE)
    list_of_dates = [x["synced_timestamp"] for x in constants.LOGIN_RESPONSE["data"]["last_synced_history"]]
    #print('➡ main.py:29 list_of_dates:', list_of_dates)
    # #print(max(list_of_dates))
    if len(list_of_dates) > 0:
        constants.LAST_SYNCED = max(list_of_dates)

    # Header frame
    header_frame = Frame(root, bg="#75a8f0")
    header_frame.pack(side='top', fill='x', pady=10)

    header = Label(header_frame, text="Fetch Tally Data", font=("calibri", 20, 'bold'), anchor='center')
    header.pack(fill='x')

    # Select software frame
    select_software_frame = Frame(root,  bg="#75a8f0", highlightbackground="#280754", highlightcolor="#280754", highlightthickness=1)
    select_software_frame.pack(side='top', pady=10, padx=20, fill='x')

    select_software_label = Label(select_software_frame, text="Select Financial Year:", font=('calibri', 12), fg="white", anchor='center', bg="#75a8f0")
    select_software_label.pack(side='left', padx=10, pady=10, expand=True)

    combo_box_text = StringVar()
    select_software_dropdown = Combobox(select_software_frame, width=30, textvariable=combo_box_text)
    select_software_dropdown['values'] = (
        f"{thisyear}-{thisyear+1}",
        f"{thisyear-1}-{thisyear}",
        f"{thisyear-2}-{thisyear-1}",
        f"{thisyear-3}-{thisyear-2}",
    )
    select_software_dropdown['state'] = 'readonly'
    select_software_dropdown.pack(side='left', padx=10, pady=10)
    select_software_dropdown.current(0)

    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    # Split master frame
    split_frame = Frame(root, bg="#75a8f0", highlightbackground="#280754", highlightcolor="#280754", highlightthickness=1)
    split_frame.pack(padx=10, pady=10, fill='both', expand=True)

    # Left frame for buttons and controls
    left_frame = Frame(split_frame, bg="#F0F0F0", bd=1, relief='solid')
    left_frame.pack(padx=10, pady=10, side='left', fill='y')

    # Get files frame
    get_files_frame = Frame(left_frame, bg="#F0F0F0")
    get_files_frame.pack(padx=10, pady=10)

    # Right frame
    right_frame = Frame(split_frame, bg="#F0F0F0", highlightbackground="#280754", highlightcolor="#280754", highlightthickness=1)
    right_frame.pack(padx=10, pady=10, side='right', fill='both', expand=True)

    # Files list frame
    files_list_frame = Frame(right_frame, bg="#F0F0F0", relief='solid')
    files_list_frame.pack(padx=10, pady=10, side='top', fill='both', expand=True)

    # Message frame
    message_frame = Frame(right_frame, bg="#F0F0F0")
    message_frame.pack(side='top', fill='x', expand=True)

    message_label = Label(message_frame, text='', font=('Helvetica', 10), bg="#F0F0F0")
    message_label.pack(fill='x', padx=5, pady=2)
   
    # loading_message_frame = Frame(right_frame, bg="#F0F0F0")
    # loading_message_frame.pack(side='top', fill='x', pady=10, expand=True)
    
    # loading_message_label = Label(loading_message_frame, text="", font=('Helvetica', 10), bg="#F0F0F0")
    # loading_message_label.pack(fill='x', padx=5, pady=2)
    
    # if not constants.FIRST_LOADER_INIT:
    #     loading_message_label.config(te)
    
    # Additional message frame
    additional_message_frame = Frame(right_frame, bg="#F0F0F0")
    additional_message_frame.pack(side='top', fill='x', pady=10, expand=True)

    additional_message_label = Label(additional_message_frame, text='', font=('Helvetica', 10), bg="#F0F0F0")
    additional_message_label.pack(fill='x', padx=5, pady=2)
    
    if constants.LAST_SYNCED != "":
        additional_message_label.config(text="Last Syncd : "+constants.LAST_SYNCED)
    
    # if constants.DISPLAY_SYNC_LOADER == True:
    #     print("spin")
    #     additional_message_label.config(text=next(spinner_loader))

    
    def logout():
        with open("./lib/credentials.json", "w") as json_file:
            json.dump({}, json_file)
        constants.COMPANY_MAPPING = {}
        root.destroy()
        
    def reset_mapping():
        response = reset_mapping_from_rx()
        with open("./lib/credentials.json", "w") as json_file:
            json.dump({}, json_file)
        constants.COMPANY_MAPPING = {}
        root.destroy()
        
    def stop_background_thread():
        constants.STOP_THREAD = True
        if constants.THREAD is not None:
            constants.THREAD.join()
            #print("Background thread stopped.")
        
    def background_sync(start_now = False):
        while not constants.STOP_THREAD:
            
            #print("Running background task...")
            tally_status = check_if_tally_running()
            if tally_status == True:
                if not start_now:
                    time.sleep(3 * 60 * 60)
                    # time.sleep(3 * 1)
                startprocess()
                if start_now:
                    break
                    # constants.STOP_THREAD = True
            else:
                time.sleep(15 * 60)
        # constants.STOP_THREAD = False
    
    def start_thread(start_now=False):
        if start_now:            
            tally_status = check_if_tally_running()
            if tally_status != True:
                messagebox.showerror("Tally is Not Open","Make Sure Tally is Running.")
                return 0
        if constants.THREAD is None:
            background_thread = threading.Thread(target=background_sync, args=(start_now,), daemon=True)
            background_thread.start()
            print("Background thread started.")
        else:
            print("Background thread is already running.")
            
    def on_closing():
        stop_background_thread()
        root.destroy()
    
    def startprocess():
        constants.DISPLAY_SYNC_LOADER = True
        animation_thread = threading.Thread(target=show_animation, daemon=True)
        animation_thread.start()
        # show_animation()
        
        #print('➡ main.py:97 constants.LOGIN_RESPONSE:', constants.LOGIN_RESPONSE)
        if constants.MAPPING_TYPE == "single" and constants.LOGIN_RESPONSE["data"]["pharmacy_details"]["is_chain_pharmacy"] and constants.LOGIN_RESPONSE["data"]["pharmacy_details"]["logged_in_pharmacy"]["is_HO"]:
            #print("Sdsdgf")
            #print('➡ main.py:99 constants.COMPANY_MAPPING:', constants.COMPANY_MAPPING)
            #print('➡ main.py:101 constants.RX_ACCOUNTS:', constants.RX_ACCOUNTS)
            companies = [
                {"chemist_id": x["id"], "company_name": m["company_name"], "company_guid": m["company_guid"]}
                for m in constants.COMPANY_MAPPING
                for x in constants.RX_ACCOUNTS 
            ]
        else:
            companies = constants.COMPANY_MAPPING
        # #print('➡ main.py:102 companies:', companies)
        # #print(dfgdg)
        #print(select_software_dropdown.get())
        from_date = date(
                int(str(select_software_dropdown.get()).split("-")[0]),int(4),1
            )
        to_date = date(
                int(str(select_software_dropdown.get()).split("-")[1]),3,31
            )
        
        request_array = []
        init_data_array = []
        for company in companies:
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
                #print('➡ main.py:208 key:', key)
                
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
            request_array.append(tally_data)
            init_data_array.append(init_data_list)
        #print('➡ main.py:226 request_array:', request_array)
            # #print('➡ main.py:228 init_data_array:', init_data_array)
                
        
        res = send_data_to_evitalrx(request_array)
        init_response = send_init_data_to_evital_rx(init_data_array, from_date.strftime("%Y-%m-%d"), to_date.strftime("%Y-%m-%d"))    
        # message_label.config(text=res["status_message"])
        print('➡ main.py:168 constants.DISPLAY_SYNC_LOADER:', constants.DISPLAY_SYNC_LOADER)
        message_label.config(text=str(res["status_message"]).replace("_", " ").title())
        constants.DISPLAY_SYNC_LOADER = False

        print('➡ main.py:168 constants.DISPLAY_SYNC_LOADER:', constants.DISPLAY_SYNC_LOADER)
        if constants.THREAD is None:
            messagebox.showinfo("Tally Data Export",str(res["status_message"]).replace("_", " ").title())
        constants.LAST_SYNCED = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        additional_message_label.config(text="Last Syncd : "+constants.LAST_SYNCED)
        print('➡ main.py:168 constants.DISPLAY_SYNC_LOADER:', constants.DISPLAY_SYNC_LOADER)
        
    # def 

    get_files_button = Button(get_files_frame, text="Sync Data",width = 8,fg='white', bg = "#75a8f0" , font=("calibri", 10, 'bold'), command=lambda :start_thread(True))
    get_files_button.grid(row=0, column=0, padx=10, pady=20)
    get_files_button = Button(get_files_frame, text="Reset",width = 8, fg='white', bg = "#75a8f0", font=("calibri", 10, 'bold'), command=reset_mapping)
    get_files_button.grid(row=1, column=0, padx=10, pady=(30, 10))
    get_files_button = Button(get_files_frame, text="Logout",width = 8, fg='white', bg = "#75a8f0", font=("calibri", 10, 'bold'), command=logout)
    get_files_button.grid(row=2, column=0, padx=10, pady=(10,30))

    if constants.DISPLAY_SYNC_LOADER == True:
        print("spin")
        message_label.config(text=next(spinner_loader))
        time.sleep(2)
    add_labels(files_list_frame)
    start_thread()
    import atexit    
    root.protocol("WM_DELETE_WINDOW", on_closing)
# atexit.register(stop_background_thread)
    atexit.register(stop_background_thread)
    
    root.mainloop()
    
# main_thread()