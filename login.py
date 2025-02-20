import ctypes
import json
import tkinter as tk
from tkinter import Menu, messagebox
from tkinter import ttk
from tkinter.ttk import Button, Style
from PIL import Image, ImageTk
from tkinter import font
from ttkthemes import ThemedTk
from functions import decrypt_data, encrypt_data
from main import main_thread
from lib.import_export_data import send_login_request, get_tally_companies, map_rx_companies, check_if_tally_running
from lib import constants
from ctypes import windll
# from app import logging
import logging


def login_thread():

    def show_mapping_screen(account_window):
        tally_status = check_if_tally_running()
        if tally_status == False:
            messagebox.showerror("Tally is offline", "Make sure tally is running.")
            logging.error("Tally is offline on mapping")
            return 0
        get_tally_companies()
        account_window.destroy()
        mapping_window = ThemedTk(theme='breeze')
        mapping_window.resizable(0,0)
        mapping_window.iconbitmap("./lib/images/logo2.ico")
        mapping_window.title("Account Mapping")
        mapping_window.geometry("600x550")
        mapping_window.configure(bg="#F0F0F0")

        label_instruction = tk.Label(mapping_window, text="Map your eVital accounts with unique Tally Companies:", font=("Helvetica", 14, "bold"), bg="#F0F0F0")
        label_instruction.bind('<Configure>', lambda e: label_instruction.config(wraplength=label_instruction.winfo_width()))
        label_instruction.pack(pady=30)

        accounts = [x["pharmacy_name"] for x in constants.RX_ACCOUNTS]  # Example accounts
        categories = [x["company_name"] for x in constants.TALLY_ACCOUNTS]  # Example categories

        mapping_entries = []
        selected_categories = {}
    
        def update_options():
            used_categories = set(selected_categories.values())
            available_categories = [cat for cat in categories if cat not in used_categories]
            for account, combobox in mapping_entries:
                current_selection = combobox.get()
                combobox["values"] = available_categories + ([current_selection] if current_selection else [])

        def reset_comboboxes():
            selected_categories.clear()
            for account, combobox in mapping_entries:
                combobox.set('')
            update_options()

        def category_selected(event, account):
            combobox = event.widget
            selected_categories[account] = combobox.get()
            update_options()
        
        
        # import tkinter as tk
        # from tkinter import ttk

        # # Initialize main window
        # root = tk.Tk()
        # root.geometry("600x400")
        # root.title("Mapping Window")

        # Create a canvas with a scrollbar
        canvas = tk.Canvas(mapping_window, bg="#F0F0F0")
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)


        # Create a frame inside the canvas
        frame_container = tk.Frame(canvas, bg="#F0F0F0")
        canvas.create_window((0, 0), window=frame_container, anchor="nw")

        scrollbar = ttk.Scrollbar(mapping_window, orient="vertical", command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        # Example account list
        # accounts = ["Account 1", "Account 2", "Account 3", "Account 4", "Account 5", "Account 6", "Account 7"]

        # Header Frame for Titles
        header_frame = tk.Frame(frame_container, bg="#F0F0F0")
        header_frame.pack(pady=10, padx=20, fill='x')

        label_account = tk.Label(header_frame, text="eVital Accounts", font=("Helvetica", 12), bg="#F0F0F0")
        label_account.pack(side=tk.LEFT, padx=20)
        label_tally = tk.Label(header_frame, text="Tally Companies", font=("Helvetica", 12), bg="#F0F0F0")
        label_tally.pack(side=tk.RIGHT, padx=20)

        # separator = ttk.Separator(header_frame, orient='vertical')
        # separator.pack(side=tk.LEFT, padx=10, pady=5, fill='y')

        # # List to hold mapping entries
        # mapping_entries = []

        # Loop to create the mapping rows
        for account in accounts:
            frame = tk.Frame(frame_container, bg="#F0F0F0")
            frame.pack(pady=10, padx=20, fill='x')

            label_account = tk.Label(frame, text=account + ":", font=("Helvetica", 12), bg="#F0F0F0")
            label_account.pack(side=tk.LEFT, padx=20)

            combobox = ttk.Combobox(frame, state='readonly', font=("Helvetica", 12))
            combobox.pack(side=tk.RIGHT, padx=20, fill='x')
            combobox.bind("<<ComboboxSelected>>", lambda event, a=account: category_selected(event, a))
            mapping_entries.append((account, combobox))

        # def category_selected(event, account):
        #     selected_value = event.widget.get()
        #     print(f"Selected {selected_value} for {account}")

        # Start the Tkinter main loop
        # root.mainloop()

        
        # frame = tk.Frame(mapping_window, bg="#F0F0F0")
        # frame.pack(pady=10, padx=20, fill='x')

        # label_account = tk.Label(frame, text="eVital Accounts", font=("Helvetica", 12), bg="#F0F0F0")
        # label_account.pack(side=tk.LEFT, padx=20)
        # label_account = tk.Label(frame, text="Tally Companies", font=("Helvetica", 12), bg="#F0F0F0")
        # label_account.pack(side=tk.RIGHT, padx=20)

        # separator = ttk.Separator(frame, orient='vertical')
        # separator.place(relx=0.47, rely=0, relwidth=0.2, relheight=1)
        # for account in accounts:
        #     frame = tk.Frame(mapping_window, bg="#F0F0F0")
        #     frame.pack(pady=10, padx=20, fill='x')

        #     label_account = tk.Label(frame, text=account + ":", font=("Helvetica", 12), bg="#F0F0F0")
        #     label_account.pack(side=tk.LEFT, padx=20)

        #     combobox = ttk.Combobox(frame, state='readonly', font=("Helvetica", 12))
        #     combobox.pack(side=tk.RIGHT, padx=20, fill='x')
        #     combobox.bind("<<ComboboxSelected>>", lambda event, a=account: category_selected(event, a))
        #     mapping_entries.append((account, combobox))

        update_options()  # Initialize options for the comboboxes

        def submit_mapping(account_window):
            # mapping_result = {account: combobox.get() for account, combobox in mapping_entries}
            # messagebox.showinfo("Mapping Result", f"Account Mapping: {mapping_result}")
            constants.COMPANY_MAPPING = [
                {"chemist_id": x["id"], "company_name": combobox.get(), "company_guid": y["company_guid"], "mapping_type":"multiple"}
                for account, combobox in mapping_entries
                for x in constants.RX_ACCOUNTS if x["pharmacy_name"] == account
                for y in constants.TALLY_ACCOUNTS if y["company_name"] == combobox.get()
            ]
            print('➡ login.py:56 COMPANY_MAPPING:', constants.COMPANY_MAPPING)
            logging.info("commpany mapping : "+str(constants.COMPANY_MAPPING))
            if len(constants.COMPANY_MAPPING)<1:
                messagebox.showinfo("Map Tally Companies", "Please select atleast one company")
            else:   
                res = map_rx_companies()
                if res not in [0] and ("status_code" in res.keys() and res["status_code"] in [1, "1", '1.0']):
                    mapping_window.destroy()
                    account_window.destroy()
                    data = {}
                    # with open("./lib/app_cache.txt") as data_file:
                    #     data = json.load(data_file)
                    with open("./lib/app_cache.txt") as data_file:
                        # data = json.load(data_file)
                        data = decrypt_data(data_file.read())
                    data["company_mapping"] = constants.COMPANY_MAPPING
                    # data["mapping_type"] = "multi"
                    # constants.MAPPING_TYPE = "multi"

                    # with open("./lib/app_cache.txt", "w") as json_file:
                    #     json.dump(data, json_file)
                    with open("./lib/app_cache.txt", "w") as json_file:
                        # json.dump(data, json_file)
                        json_file.write(encrypt_data(data))
                    main_thread()
                else:
                    print(res)
                    messagebox.showerror("Map Companies","Error while mapping companies.")
        
        # Create the scrollbar
        # scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
        # scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        

        button_frame = tk.Frame(frame_container, bg="#F0F0F0")
        button_frame.pack(pady=20)

        button_submit = tk.Button(button_frame, text="Submit", font=("Helvetica", 12), bg="#4CAF50", fg="white", command=lambda a=account_window: submit_mapping(a))
        button_submit.pack(side=tk.LEFT, padx=20)

        button_reset = tk.Button(button_frame, text="Reset", font=("Helvetica", 12), bg="#F44336", fg="white", command=reset_comboboxes)
        button_reset.pack(side=tk.LEFT, padx=20)
        
        frame_container.bind("<Configure>", configure_scroll_region)
        canvas.update_idletasks()  # Forces a layout update before starting the mainloop
        canvas.configure(scrollregion=canvas.bbox("all"))

        mapping_window.mainloop()

    def show_single_account_selection(account_window):
        tally_status = check_if_tally_running()
        if tally_status == False:
            messagebox.showerror("Tally is offline", "Make sure tally is running.")
            return 0
        get_tally_companies()
        account_window.destroy()
        single_account_window = ThemedTk(theme='breeze')
        single_account_window.resizable(0,0)
        single_account_window.iconbitmap("./lib/images/logo2.ico")
        single_account_window.title("Single Account Selection")
        single_account_window.geometry("400x200")
        single_account_window.configure(bg="#F0F0F0")

        label_instruction = tk.Label(single_account_window, text="Select your single Tally Company:", font=("Helvetica", 14, "bold"), bg="#F0F0F0")
        label_instruction.pack(pady=20)

        accounts = [x["company_name"] for x in constants.TALLY_ACCOUNTS]  # Example accounts
        print('➡ login.py:106 accounts:', accounts)

        account_var = tk.StringVar()
        combobox_account = ttk.Combobox(single_account_window, textvariable=account_var, state='readonly', font=("Helvetica", 12))
        combobox_account['values'] = accounts
        combobox_account.pack(pady=10, padx=20)
        combobox_account.current(0)

        def submit_single_account():
            
            # selected_account = combobox_account.get()
            # messagebox.showinfo("Selected COmpany", f"You selected: {selected_account}")
            # Save the selected account to a file
            data = {}
            if constants.LOGIN_RESPONSE["data"]["pharmacy_details"]["is_chain_pharmacy"]:
                # if constants.LOGIN_RESPONSE["data"]["pharmacy_details"]["logged_in_pharmacy"]["is_HO"]:
                constants.COMPANY_MAPPING = [
                    {"chemist_id": x["id"] , "company_name": combobox_account.get(), "company_guid": y["company_guid"], "mapping_type":"single"}
                    for x in constants.RX_ACCOUNTS if x["pharmacy_name"] == constants.LOGIN_RESPONSE["data"]["pharmacy_details"]["logged_in_pharmacy"]["pharmacy_name"]
                    for y in constants.TALLY_ACCOUNTS if y["company_name"] == combobox_account.get()
                ]
                # else:
                #     print(constants.RX_ACCOUNTS)
                #     print(constants.TALLY_ACCOUNTS)
                #     constants.COMPANY_MAPPING = [
                #         {"chemist_id": x["id"] , "company_name": combobox_account.get(), "company_guid": y["company_guid"]}
                #         for x in constants.RX_ACCOUNTS if x["pharmacy_name"] == constants.LOGIN_RESPONSE["data"]["pharmacy_details"]["logged_in_pharmacy"]["pharmacy_name"]
                #         for y in constants.TALLY_ACCOUNTS if y["company_name"] == combobox_account.get()
                #     ]
                #     print('➡ login.py:136 COMPANY_MAPPING:', constants.COMPANY_MAPPING)
                    # pass
            else:
                constants.COMPANY_MAPPING = [
                    {"chemist_id": x["id"] , "company_name": combobox_account.get(), "company_guid": y["company_guid"], "mapping_type":"single"}
                    for x in constants.RX_ACCOUNTS
                    for y in constants.TALLY_ACCOUNTS if y["company_name"] == combobox_account.get()
                ]
            data["mapping_type"] = "single"
            # constants.MAPPING_TYPE = "multi"
            # map_rx_companies()
            res = map_rx_companies()
            print('➡ login.py:260 res:', res)
            if res not in [0] and ("status_code" in res.keys() and res["status_code"] in [1, "1", '1.0']):
                # with open("./lib/app_cache.txt") as data_file:
                #     data = json.load(data_file)
                
                with open("./lib/app_cache.txt") as data_file:
                    # data = json.load(data_file)
                    data = decrypt_data(data_file.read())

                data["company_mapping"] = constants.COMPANY_MAPPING

                # with open("./lib/app_cache.txt", "w") as json_file:
                #     json.dump(data, json_file)
                
                with open("./lib/app_cache.txt", "w") as json_file:
                    # json.dump(data, json_file)
                    # json.dump(encrypt_data(data), json_file)
                    json_file.write(encrypt_data(data))

                single_account_window.destroy()
                main_thread()  # Proceed with the main logic
            else:
                # print(res)
                messagebox.showerror("Map Companies","Error while mapping companies.")


        button_submit = tk.Button(single_account_window, text="Submit", font=("Helvetica", 12), bg="#4CAF50", fg="white", command=submit_single_account)
        button_submit.pack(pady=20)

        single_account_window.mainloop()
        
        
    def ask_account_type():
        login_window.destroy()
        
        account_window = ThemedTk(theme='breeze')
        account_window.resizable(0,0)
        account_window.iconbitmap("./lib/images/logo2.ico")
        account_window.title("Account Type")
        account_window.geometry("500x300")
        account_window.configure(bg="#F0F0F0")

        sub_panel = tk.Frame(account_window, bg="#F0F0F0")
        sub_panel.pack(pady=30, padx=30, fill='both', expand=True)

        label_question = tk.Label(sub_panel, text="Do you have a single Tally Company for all your evital Accounts?", wraplength=400, font=("Helvetica", 16, "bold"), bg="#F0F0F0")
        label_question.pack(pady=20, padx=20)

        button_single = tk.Button(sub_panel, text="Single Company", font=("Helvetica", 12), bg="#4CAF50", fg="white", width=20, command=lambda: account_selected("Single", account_window))
        button_single.pack(pady=10, padx=10)

        button_multiple = tk.Button(sub_panel, text="Multiple Companies", font=("Helvetica", 12), bg="#2196F3", fg="white", width=20, command=lambda: account_selected("Multiple", account_window))
        button_multiple.pack(pady=10, padx=10)

        # Add padding and expand options to the buttons to improve layout
        for widget in sub_panel.winfo_children():
            widget.pack_configure(pady=10, padx=10)

        account_window.mainloop()
        
    def clear_frame(frame):
        for widget in frame.winfo_children():
            widget.destroy()
        

    def account_selected(account_type, account_window):
        if account_type == "Multiple":
            show_mapping_screen(account_window)
        else:
            show_single_account_selection(account_window)
        # You can add more logic here based on the account type selection

    def login():
        mobile_number = mobile_entry.get()
        password = password_entry.get()
        if len(mobile_number) != 10 and str(mobile_number).isdigit() == False:
            messagebox.showerror("Login Failed", "Invalid Mobile number")
        elif len(password)<1:
            messagebox.showerror("Login Failed", "Invalid Password")
        else:
        # Implement your login logic here
        # For demonstration, just check for specific mobile number and password
            res = send_login_request(mobile_number, password)
            print('➡ login.py:89 res:', res)
            logging.info(res)
            
            if "status_code" in res.keys() and res['status_code'] in [1,'1']:
                if_chain_pharmacy = res["data"]["pharmacy_details"]["is_chain_pharmacy"]
                # print('➡ login.py:94 if_chain_pharmacy:', if_chain_pharmacy)
                messagebox.showinfo("Login", "Login Successful")
                # print(res["data"])
                constants.COMPANY_MAPPING = res["data"]["pharmacy_details"]["company_mapping_details"]
                if "accesstoken" in res["data"]:
                    constants.ACCESS_TOKEN = res["data"]["accesstoken"]
                if "apikey" in res["data"]:
    
                    constants.EVITAL_RX_API_KEY = res["data"]["apikey"]
                # constants.ACCESS_TOKEN = res["data"]["accesstoken"]
                
                data = {
                    "login_response" : constants.LOGIN_RESPONSE,
                    "company_mapping" : res["data"]["pharmacy_details"]["company_mapping_details"]
                }
                # with open("./lib/app_cache.txt", "w") as json_file:
                #     json.dump(data, json_file)
                with open("./lib/app_cache.txt", "w") as json_file:
                    # json.dump(data, json_file)
                    json_file.write(encrypt_data(data))
                already_mapped = True if len(res["data"]["pharmacy_details"]["company_mapping_details"]) > 0 else False
                if already_mapped:
                    # login_window.destroy()
                    main_thread()
                else:
                    if if_chain_pharmacy:
                        # print()
                        # if if_chain_pharmacy:
                        if_ho = res["data"]["pharmacy_details"]["logged_in_pharmacy"]["is_HO"]
                        if if_ho:
                            ask_account_type()
                        else:
                            show_single_account_selection(login_window)
                            
                    else:
                        show_single_account_selection(login_window)
            elif "status_code" in res.keys() and res['status_code'] in [0,'0']:
                messagebox.showerror("Login Error", res["status_message"])
        # ask_account_type()
            
    # login_window = ThemedTk(theme='breeze', bg="#044C9D")
    # login_window.title("Login Screen")
    # login_window.geometry("800x400")
    # login_window.configure(bg="#F0F0F0")

    # # Load and display the image
    # photo = ImageTk.PhotoImage(image)

    # # label_image = tk.Label(login_window, height=100, width=100, bg="#044C9D")
    # # label_image.grid(row=0, column=0, rowspan=6, padx=0, pady=0, sticky='w')
    
        # Function to move the window
    def move_window(event):
        root.geometry(f'+{event.x_root}+{event.y_root}')
        
    def close_window():
        root.destroy()
        
    
    # Draggable functionality for the window
    def start_move(event):
        root.x = event.x
        root.y = event.y

    def stop_move(event):
        root.x = None
        root.y = None

    def do_move(event):
        x = root.winfo_pointerx() - root.x
        y = root.winfo_pointery() - root.y
        root.geometry(f"+{x}+{y}")



    # Bind the title bar to the move window function
    root = tk.Tk()
    root.title("Sync Utility Login")
    root.geometry("900x600")
    root.configure(bg="#044C9D")  # Set background to blue
    root.overrideredirect(True)
    root.geometry(f'+300+200')
    root.resizable(0,0)
    root.iconbitmap("./lib/images/logo2.ico")
    root.title("Login Screen")
    
    root.bind("<Button-1>", start_move)
    root.bind("<ButtonRelease-1>", stop_move)
    root.bind("<B1-Motion>", do_move)
    
    # Ensure the window appears in the taskbar and Alt+Tab
    # root.attributes("-topmost", True)  # Always on top
    root.attributes("-toolwindow", False)  # Make it appear in Alt+Tab
    root.attributes("-fullscreen", False)  # Prevent full-screen mode
    
    login_window = root
    hwnd = ctypes.windll.user32.GetForegroundWindow()
    ctypes.windll.user32.SetWindowLongW(hwnd, -20, 0x00000000)

    # hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
    # Set the window style to make it appear in the taskbar
    # ctypes.windll.user32.SetWindowLongW(hwnd, -8, 0)  # GWLP_HWNDPARENT = -8

    # menubar = Menu(root)
    # menubar.add_command(label="File")
    # menubar.add_command(label="Quit", command=root.quit())

    # root.config(menu=menubar)
    # root.wm_attributes('-fullscreen','true')
    # root.resizable(0)

    # Custom font
    header_font = font.Font(family="Arial", size=14, weight="bold")
    header_font1 = font.Font(family="Arial", size=14)
    # label_font = font.Font(family="Arial", size=14)
    # label_font1 = font.Font(family="Arial", size=14)

    # Left panel
    left_panel = tk.Frame(root, bg="#044C9D")
    left_panel.pack(side=tk.LEFT, fill=tk.Y)
    
        # Add static image to the left panel
    image = Image.open("./lib/images/login_panel.PNG")  # Replace with your image path
    image = image.resize((500, 600), Image.Resampling.LANCZOS)  # Resize image to fit the panel
    image_tk = ImageTk.PhotoImage(image)

    image_label = tk.Label(left_panel, image=image_tk, bg="#004BA8")
    image_label.image = image_tk  # Keep a reference to avoid garbage collection
    image_label.pack(pady=(30, 10))

    # Icons on the left panel
    # tally_logo = tk.Label(left_panel, text="Tally", bg="#044C9D", fg="white", font=header_font)
    # tally_logo.pack(pady=(80, 10))

    # connector = tk.Label(left_panel, text=". . . . .", bg="#044C9D", fg="white", font=header_font)
    # connector.pack()

    # evital_logo = tk.Label(left_panel, text="eVitalRx", bg="#044C9D", fg="white", font=header_font)
    # evital_logo.pack(pady=(10, 80))

    # version_label = tk.Label(left_panel, text="Sync Utility", bg="#044C9D", fg="white", font=header_font, justify=tk.CENTER)
    # version_label.pack()
    # version_label = tk.Label(left_panel, text="Version 2.0", bg="#044C9D", fg="white", font=header_font1, justify=tk.CENTER)
    # version_label.pack()

    # Right panel    # Create a custom title bar
    title_bar = tk.Frame(root, width=900, bg="white")
    title_bar.pack(fill=tk.X)

    # Add a title label to the custom title bar
    # title_label = tk.Label(title_bar, text="Custom Title Bar - Approach 3", bg='gray', fg='white')
    # title_label.pack(side=tk.LEFT, padx=10)

    # Add a close button to the custom title bar
    close_button = tk.Button(title_bar, text='x', font=header_font, command=close_window, bg='white', fg='#044C9D', borderwidth=0, relief=tk.SUNKEN)
    close_button.pack(side=tk.RIGHT, padx=20, pady=15)

    right_panel = tk.Frame(root, bg="white", width=400 , height=480)
    right_panel.pack(side=tk.RIGHT, fill=tk.Y)
    right_panel.pack_propagate(False)

    login_label = tk.Label(right_panel, text="Login with your", bg="white", font=header_font1, justify=tk.LEFT)
    login_label.pack(pady=(45, 0), padx=50, anchor=tk.W)
    login_label = tk.Label(right_panel, text="eVitalRx account", bg="white", font=header_font, justify=tk.LEFT)
    login_label.pack(pady=(0, 30), padx=50, anchor=tk.W)

    mobile_label = tk.Label(right_panel, text="Mobile Number", bg="white", fg="#044C9D", font=header_font1)
    mobile_label.pack(pady=(20, 0), padx=50, anchor=tk.W)

    mobile_entry = tk.Entry(right_panel, bg="white", font=header_font1, bd=0, width=40)
    mobile_entry.pack(pady=4, padx=53, anchor=tk.W)
    mobile_line = tk.Canvas(right_panel, width=280, height=1, bg="#004BA8", highlightthickness=0)
    mobile_line.pack(pady=(0, 10), padx=(53,40), anchor=tk.W)
    mobile_entry.insert(0, "9876543210")  # Placeholder value
    mobile_entry.propagate(False)

    password_label = tk.Label(right_panel, text="Password", bg="white", fg="#044C9D", font=header_font1, width=40, justify=tk.LEFT, anchor="w")
    password_label.pack(pady=(20, 0), padx=50, anchor=tk.W)

    password_entry = tk.Entry(right_panel, bg="white", font=header_font1, bd=0, show="*")
    password_entry.pack(pady=4, padx=53, anchor=tk.W, fill=tk.X)
    password_line = tk.Canvas(right_panel, width=280, height=1, bg="#004BA8", highlightthickness=0)
    password_line.pack(pady=(0, 20), padx=(53, 40), anchor=tk.W)

    login_button = tk.Button(right_panel, text="Login", bg="#0CA1F6", fg="white", font=header_font, relief=tk.FLAT, height=1, width=20, command=login)
    login_button.pack(pady=20, padx=(0, 15))

    # GWL_EXSTYLE = -20
    # WS_EX_APPWINDOW = 0x00040000
    # WS_EX_TOOLWINDOW = 0x00000080
    # right_panel.bind('<B1-Motion>', move_window)
    
    # def set_appwindow(mainWindow):
    # # Honestly forgot what most of this stuff does. I think it's so that you can see
    # # the program in the task bar while using overridedirect. Most of it is taken
    #     # from a post I found on stackoverflow.
    #     hwnd = windll.user32.GetParent(mainWindow.winfo_id())
    #     stylew = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    #     stylew = stylew & ~WS_EX_TOOLWINDOW
    #     stylew = stylew | WS_EX_APPWINDOW
    #     res = windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, stylew)
    #     # re-assert the new window style
    #     mainWindow.wm_withdraw()
    #     mainWindow.after(10, lambda: mainWindow.wm_deiconify())
        
    # def frameMapped(event=None):
    #     global z
    #     root.overrideredirect(True)
    #     root.iconbitmap("./lib/images/logo2.ico")
    #     if z == 1:
    #         set_appwindow(root)
    #         z = 0
            
    # root.bind("<Map>", frameMapped) 
    root.mainloop()

            
#     login_window = ThemedTk(theme='breeze')
#     login_window.resizable(0,0)
#     login_window.iconbitmap("./lib/images/logo2.ico")
#     login_window.title("Login Screen")
#     login_window.geometry("800x400")
#     login_window.configure(bg="#F0F0F0")

#     # Create a plain blue screen on the left
#     label_image = tk.Label(login_window, height=30, width=65, bg="#000078")
#     label_image.grid(row=0, column=0, rowspan=6, padx=0, pady=0, sticky='nsew')

#     # Load and display the logo
#     image_path = "./lib/images/logo.png"  # Replace with your image path
#     image = Image.open(image_path)
#     image = image.resize((180, 45))
#     photo = ImageTk.PhotoImage(image)

#     image_frame = tk.Label(label_image, image=photo, bg="#000078")
#     image_frame.place(relx=0.2, rely=0.1, anchor='center')

#     # Create a label for "Login" text
#     label_login = tk.Label(login_window, text="Login", font=("Manrope", 24, "bold"), bg="#F0F0F0")
#     label_login.grid(row=0, column=1, padx=40, pady=(0, 0), sticky='w')

#     # Frame for form elements
#     form_frame = tk.Frame(login_window, bg="#F0F0F0")
#     form_frame.grid(row=1, column=1, rowspan=6, columnspan=3, pady=0, sticky='n')

#     # Create labels and entries for mobile number and password in a single row
#     label_mobile = tk.Label(form_frame, text="Mobile Number", font=("Manrope", 11), bg="#F0F0F0")
#     label_mobile.grid(row=0, column=0, padx=40, pady=(0, 5), sticky='w')
#     entry_mobile = tk.Entry(form_frame, font=("Manrope", 11))
#     entry_mobile.grid(row=1, column=0, padx=40, pady=(0, 25), sticky='w')

#     label_password = tk.Label(form_frame, text="Password", font=("Manrope", 11), bg="#F0F0F0")
#     label_password.grid(row=2, column=0, padx=40, pady=(0, 5), sticky='w')
#     entry_password = tk.Entry(form_frame, show="*", font=("Manrope", 11))
#     entry_password.grid(row=3, column=0, padx=40, pady=(0, 25), sticky='w')

# #     style = Style()
#     # Define a style
#     style = ttk.Style(login_window)
      
#     style.theme_use("clam") 
#     style.configure('Blue.TButton', background='#000070', foreground='white', font=('Helvetica', 12))
#     style.map('Blue.TButton',
#             background=[('active', '#005BB5'), ('pressed', '#003E8B')],
#             foreground=[('active', 'white'), ('pressed', 'white')])
 
# # # Will add style to every available button 
# # # even though we are not passing style
# # # to every button widget.
# #     style.configure('TButton', font =
# #         ('calibri', 10, 'bold'),
# #             foreground = 'whilte', background='#000078', width=20)
#     # Create the login button
#     button_login = ttk.Button(form_frame, text="Login", command=login, style='Blue.TButton')
#     button_login.grid(row=4, column=0, pady=10, sticky='n')
#     login_window.mainloop()