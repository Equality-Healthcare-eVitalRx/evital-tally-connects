import ctypes
import json
import multiprocessing
from multiprocessing.dummy import freeze_support
import multiprocessing.process
import threading
import time
import tkinter as tk
from tkinter import font, ttk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageSequence
from tkinter import Tk
from functions import login, logout, get_all_mapping_details, constants, start_background_thread, start_thread, map_rx_companies, startprocess
# from lib.import_export_data import get_tally_companies, check_if_tally_running


try: # >= win 8.1
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except: # win 8.0 or less
    ctypes.windll.user32.SetProcessDPIAware()



class App(tk.Tk):
    def __init__(self):
        super().__init__()
        constants.LOAD_COMPLETE = True            

        # Draggable functionality for the window
        # def start_move(event):
        #     self.x = event.x
        #     self.y = event.y

        # def stop_move(event):
        #     self.x = None
        #     self.y = None

        # def do_move(event):
        #     # print("-"*50)
        #     # print("x",self.winfo_pointerx())
        #     # print("y",self.winfo_pointery())
        #     # print("new x",self.x)
        #     # print("new y",self.y)
            
        #     # print(self.winfo_geometry())
            
        #     x = self.winfo_pointerx() - self.x
        #     y = self.winfo_pointery() - self.y
            
        #     current_x = int(str(self.winfo_geometry()).split('+')[1])
        #     current_y = int(str(self.winfo_geometry()).split('+')[2])
        #     if current_x == 0:
        #         current_x = 1
        #     if current_y == 0:
        #         current_y = 1
        #     # print(current_x, current_y)
            
        #     if x / current_x < 1.15 and y / current_y < 1.15:
            
        #         self.geometry(f"+{x}+{y}")
            
            
        def start_move(event):
            """Store the initial mouse position relative to the window (absolute position)."""
            self.x_offset = event.x_root - self.winfo_x()
            self.y_offset = event.y_root - self.winfo_y()

        def do_move(event):
            """Move the window smoothly based on absolute pointer position."""
            x = event.x_root - self.x_offset
            y = event.y_root - self.y_offset
            self.geometry(f"+{x}+{y}")
            
        def on_closing():
            self.destroy()
        # self.title("Multi-Screen App")
        # self.geometry("600x400")
        
        # Dictionary to store frames
        self.frames = {}
        
        # Initialize all screens
        
        # Show the first screen
        
        # self.title("Sync Utility Login")
        self.geometry("900x600")
        self.configure(bg="#044C9D")  # Set background to blue
        self.overrideredirect(True)
        # self.geometry(f'+300+200')
        
        user32 = ctypes.windll.user32
        x ,y = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        x = (x - 900) // 2
        y = (y - 600) // 2
        
        self.geometry(f'+{str(int(x))}+{str(int(y))}')
        
        self.resizable(0,0)
        self.iconbitmap("./lib/images/logo2.ico")
        self.title("Login Screen")
        # self.config(
        #     background='black'
        #     # borderwidth=2, relief="solid"
        # )
        
        self.bind("<Button-1>", start_move)
        # self.bind("<ButtonRelease-1>", stop_move)
        self.bind("<B1-Motion>", do_move)
        
        self.protocol("WM_DELETE_WINDOW", on_closing)
        # Ensure the window appears in the taskbar and Alt+Tab
        # self.attributes("-topmost", True)  # Always on top
        self.attributes("-toolwindow", False)  # Make it appear in Alt+Tab
        self.wm_attributes("-toolwindow", False)  # Make it appear in Alt+Tab
        self.attributes("-fullscreen", False)  # Prevent full-screen mode
        # self.attributes()
        
        # login_window = self
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, 0x00000000)

        # hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
        # Set the window style to make it appear in the taskbar
        # ctypes.windll.user32.SetWindowLongW(hwnd, -8, 0)  # GWLP_HWNDPARENT = -8

        # menubar = Menu(root)
        # menubar.add_command(label="File")
        # menubar.add_command(label="Quit", command=root.quit())

        # root.config(menu=menubar)
        # root.wm_attributes('-fullscreen','true')
        # root.resizable(0)

        # Custom font
        # header_font = font.Font(family="Arial", size=14, weight="bold")
        # header_font1 = font.Font(family="Arial", size=14)
        self.initialize_screens()

        # self.show_frame("Dashboard")
        self.show_frame("LoginScreen")
    
    def close_window(self):
        self.destroy()

    def initialize_screens(self):
        # Add frames to the dictionary
        self.frames["LoginScreen"] = LoginScreen(self, self)
        self.frames["Dashboard"] = Dashboard(self, self)
        
        # Pack all frames but keep them hidden initially
        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

    def show_frame(self, frame_name, **kwargs):
        """Show a frame by name."""
        print("frame called")
        frame = self.frames[frame_name]
        if hasattr(frame, "update_content"):  # Check if the frame supports dynamic updates
            frame.update_content(**kwargs)
        frame.tkraise()
        # if frame_name == "Dashboard":
        #     frame.create_main_content()

class LoginScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller
        parent.title = "Login"

        def close_window():
            self.destroy()
            parent.destroy()
        
        def check_login():
            res = login(mobile_entry.get(), password_entry.get())
            # print(constants.EVITAL_RX_API_KEY)
            # print('➡ tk_screen.py:112 res:', res)
            # res = 1
            if res == 1:
                constants.MOBILE = mobile_entry.get()
                
                with open("./lib/credentials.json") as data_file:
                        data = json.load(data_file)
                data["mobile"] = constants.MOBILE
                with open("./lib/credentials.json", "w") as json_file:
                        json.dump(data, json_file)
                # print('➡ tk_screen.py:129 constants.MOBILE:', constants.MOBILE)
                if constants.MOBILE_VAR is not None:
                    constants.MOBILE_VAR.set(constants.MOBILE)
                get_all_mapping_details()
                parent.show_frame("Dashboard")
            # if res = 0


        # Left panel
        left_panel = tk.Frame(self, bg="#044C9D")
        left_panel.pack(side=tk.LEFT, fill=tk.Y)
        
            # Add static image to the left panel
        image = Image.open("./lib/images/login_panel.PNG")  # Replace with your image path
        image = image.resize((500, 600), Image.Resampling.LANCZOS)  # Resize image to fit the panel
        # print('➡ tk_screen.py:162 image:', image)
        image_tk = ImageTk.PhotoImage(image)
        # print('➡ tk_screen.py:163 image_tk:', image_tk)

        image_label = tk.Label(left_panel, image=image_tk, bg="#004BA8")
        image_label.image = image_tk  # Keep a reference to avoid garbage collection
        image_label.pack(pady=(0, 10))

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
        title_bar = tk.Frame(self, width=900, bg="white")
        title_bar.pack(fill=tk.X)
        
        header_font = font.Font(family="Arial", size=14, weight="bold")
        header_font1 = font.Font(family="Arial", size=14)
        header_font2 = font.Font(family="Arial", size=13)


        close_button = tk.Button(title_bar, text='x', font=header_font, command=close_window, bg='white', fg='#044C9D', borderwidth=0, relief=tk.SUNKEN)
        close_button.pack(side=tk.RIGHT, padx=20, pady=15)

        right_panel = tk.Frame(self, bg="white", width=400 , height=470)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        right_panel.pack_propagate(False)

        login_label = tk.Label(right_panel, text="Login with your", bg="white", font=header_font1, justify=tk.LEFT)
        login_label.pack(pady=(45, 0), padx=50, anchor=tk.W)
        login_label = tk.Label(right_panel, text="eVitalRx account", bg="white", font=header_font, justify=tk.LEFT)
        login_label.pack(pady=(0, 30), padx=50, anchor=tk.W)

        mobile_label = tk.Label(right_panel, text="Mobile Number", bg="white", fg="#044C9D", font=header_font2)
        mobile_label.pack(pady=(20, 0), padx=50, anchor=tk.W)

        mobile_entry = tk.Entry(right_panel, bg="white", font=header_font1, bd=0, width=40)
        mobile_entry.pack(pady=4, padx=53, anchor=tk.W)
        mobile_line = tk.Canvas(right_panel, width=280, height=1, bg="#004BA8", highlightthickness=0)
        mobile_line.pack(pady=(0, 10), padx=(53,40), anchor=tk.W)
        # mobile_entry.insert(0, "9876543210")  # Placeholder value
        mobile_entry.propagate(False)

        password_label = tk.Label(right_panel, text="Password", bg="white", fg="#044C9D", font=header_font2, width=40, justify=tk.LEFT, anchor="w")
        password_label.pack(pady=(20, 0), padx=50, anchor=tk.W)

        password_entry = tk.Entry(right_panel, bg="white", font=header_font1, bd=0, show="*")
        password_entry.pack(pady=4, padx=53, anchor=tk.W, fill=tk.X)
        password_line = tk.Canvas(right_panel, width=280, height=1, bg="#004BA8", highlightthickness=0)
        password_line.pack(pady=(0, 20), padx=(53, 40), anchor=tk.W)

        login_button = tk.Button(right_panel, text="Login", bg="#0CA1F6", fg="white", font=header_font, relief=tk.FLAT, height=1, width=20, command=check_login)
        login_button.pack(pady=20, padx=(0, 15))


class Dashboard(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#004BA8")
        for widget in self.winfo_children():
            widget.destroy()
        self.controller = controller
        self.parent = parent
        parent.title = "Tally Sync"

        # self.config(borderwidth=1, relief="solid")
    
        # self.animation_running = False
             
        def create_main_content():

            constants.STOP_THREAD = True
            right_panel.configure(background="white")
            for widget in right_panel.winfo_children():
                widget.destroy()
                
            constants.STOP_THREAD = False

            title_bar = tk.Frame(right_panel, width=900, bg="#E7F6FF")
            title_bar.pack(fill=tk.X)
            close_button = tk.Button(title_bar, text='x', font=header_font, command=close_window, bg='#E7F6FF', fg='#044C9D', borderwidth=0, relief=tk.SUNKEN)
            close_button.pack(side=tk.RIGHT, padx=20, pady=(10,5))
            get_all_mapping_details()

            # Upper right panel (contains last sync and button)
            upper_right_panel = tk.Frame(right_panel, bg="#E7F6FF")
            upper_right_panel.pack(side=tk.TOP, fill=tk.X)
            

            # Left and right sections inside the upper panel
            top_left_panel = tk.Frame(upper_right_panel, bg="#E7F6FF")
            top_left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            top_right_panel = tk.Frame(upper_right_panel, bg="#E7F6FF")
            top_right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

            # Last Sync header and time
            constants.LAST_SYNC_VAR = tk.StringVar(value="No Sync")
            
            last_sync_label = tk.Label(top_left_panel, text="Last Sync", bg="#E7F6FF", fg="#7E878C", font=label_font2, justify=tk.LEFT)
            last_sync_label.pack(pady=(15, 0), padx=30, anchor=tk.W)
            
            if len(constants.MAPPING_HISTORY) > 0 and 'login_entity_last_synced' in constants.MAPPING_HISTORY.keys() and constants.MAPPING_HISTORY["login_entity_last_synced"] != "":
                constants.LAST_SYNC_VAR.set(constants.MAPPING_HISTORY["login_entity_last_synced"])

            last_sync_time = tk.Label(top_left_panel, textvariable=constants.LAST_SYNC_VAR, bg="#E7F6FF", fg="#004BA8", font=label_font2, justify=tk.LEFT)
            last_sync_time.pack(pady=(0, 20), padx=30, anchor=tk.W)

            # Sync all button
            # style = ttk.Style()
            # style.configure("Rounded.TButton", 
            #                 font=label_font2,
            #                 background="#0CA1F6",
            #                 foreground="white",
            #                 borderwidth=0,
            #                 padding=10)
            # style.theme_use("clam")
        #     style.map("Custom.TButton",
        #   background=[("active", "darkblue"), ("pressed", "navy")],  # Color when hovered/pressed
        #   foreground=[("active", "white"), ("pressed", "white")])
            # sync_all_button = ttk.Button(top_right_panel, text="Sync all", style="Rounded.TButton", command=show_sync_frame)

            sync_all_button = tk.Button(top_right_panel, text="Sync all", bg="#0CA1F6", fg="white", font=label_font2, relief=tk.FLAT, height=1, width=11, command=show_sync_frame)
            sync_all_button.pack(pady=(15,20), padx=40, anchor=tk.E)

            # Lower right panel (contains branch data)
            lower_right_panel = tk.Frame(right_panel, bg="white")
            lower_right_panel.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=30, pady=(10, 0))
            



            # print("ASfg4e", constants.MAPPING_HISTORY)
#             response_josn = {
#     "status_code": "1",
#     "status_message": "Tally Company mappings fetched successfully",
#     "datetime": "2025-01-16 15:29:54",
#     "data": {
#         "login_entity_last_synced": "11 days ago",
#         "results": [
#             {
#                 "chemist_id": "rM9k/ftzTZOC2y9KFKF5Vg==",
#                 "evitalrx_branch_name": "Smit Pharmacy, Ahmedabad",
#                 "tally_company_name": "Smit Pharmacy",
#                 "tally_company_guid": "rtetgfdgsd4546",
#                 "last_synced": "11 days ago",
#                 "is_mapped": "true"
#             },
#             {
#                 "chemist_id": "4rCzgqEKT1jjLrpV/6xShg==",
#                 "evitalrx_branch_name": "Shyam Pharmacy, Ahmedabad",
#                 "tally_company_name": "EvitalRx Smit",
#                 "tally_company_guid": "hnfe5tge43dcds",
#                 "last_synced": "11 days ago",
#                 "is_mapped": "true"
#             }
#         ]
#     }
# }           
            # if "data" in response_josn.keys():
            #     constants.MAPPING_HISTORY = response_josn["data"]
            # Example Branch Data
            # branches = [
            #     {"name": "Amin Pharmacy, Chandkheda", "status": "Mapped as Chandkheda branch", "time": "25 mins ago"},
            #     {"name": "Lorem Ipsum Pharmacy, Chandkheda", "status": "Mapped as Chandkheda branch", "time": "2 hrs ago"},
            #     {"name": "Shree Anupam Medical", "status": "Mapped as Chandkheda branch", "time": "85 mins ago"},
            #     {"name": "Amin Pharmacy, Chandkheda", "status": "Map Now", "time": "No Sync"},
            #     {"name": "Amin Pharmacy, Chandkheda", "status": "Mapped as Chandkheda branch", "time": "5 hrs ago"},
            # ]

            # constants.MAPPING_HISTORY
            # print("main content")
            # print(constants.MAPPING_HISTORY)
            # print(type(constants.MAPPING_HISTORY))
            branches = [] if constants.EVITAL_RX_API_KEY == "" else [
                {
                    "name":x["evitalrx_branch_name"], 
                    "status":"Map Now" if x["tally_company_name"] =="" else str("Mapped as ")+str(x["tally_company_name"]), 
                    "time" : "No Sync" if x["last_synced"]=="" else x["last_synced"],
                    "chemist_id" : x["chemist_id"],
                    "company_guid" : x["tally_company_guid"]
                } 
                for x in constants.MAPPING_HISTORY["results"]
            ]
            print('➡ tk_screen.py:336 branches:', branches)

            remaining_branch = [
                x["company_name"] for x in constants.TALLY_ACCOUNTS if x["company_name"] not in [
                    str(y["status"]).replace('Mapped as ','') for y in branches
                ]
            ]
            custom_padding = 30
            if len(branches) > 0:
                max_branch = max([len(str(x["name"])) for x in  branches])
                custom_padding = 120 if max_branch < 30 else 30
            
            branches_label = tk.Label(lower_right_panel, text=str(len(branches))+" Branches", bg="white", fg="#A9A9A9", font=label_font, justify=tk.LEFT)
            branches_label.pack(pady=(30, 5), padx=5, anchor=tk.W)
            
            # style = ttk.Style()
            # style.theme_use("clam")  # Ensure we can modify the scrollbar


            # style.configure("Custom.Vertical.TScrollbar",
            #     background="white",  # Background color of scrollbar
            #     troughcolor="blue",  # Track color
            #     arrowcolor="blue",  # Arrow color
            #     bordercolor="blue",  # Border color
            #     relief="flat") 
          # Create a canvas and a scrollbar
            canvas = tk.Canvas(lower_right_panel, bg="white")
            # scrollbar = ttk.Scrollbar(lower_right_panel, orient="vertical", command=canvas.yview, style="Custom.Vertical.TScrollbar")
            scrollbar = ttk.Scrollbar(lower_right_panel, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg="white")

            # Configure the canvas
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            # Pack canvas and scrollbar
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            def on_scroll(event):
                """Enable scrolling inside the frame without dragging the app."""
                if len(branches) > 5:
                    if event.delta:  # Windows scrolling
                        canvas.yview_scroll(-1 * (event.delta // 120), "units")
                    elif event.num == 4:  # Linux scroll up
                        canvas.yview_scroll(-1, "units")
                    elif event.num == 5:  # Linux scroll down
                        canvas.yview_scroll(1, "units")
            
            # Bind scrolling to the canvas
            canvas.bind_all("<MouseWheel>", on_scroll)  # Windows
            canvas.bind_all("<Button-4>", on_scroll)  # Linux Scroll Up
            canvas.bind_all("<Button-5>", on_scroll)  # Linux Scroll Down
            
            for branch in branches:
                # Main frame for each branch
                branch_frame = tk.Frame(scrollable_frame, bg="white")
                branch_frame.pack(fill=tk.X, pady=10)

                # Left frame for chemist details
                branch_left_frame = tk.Frame(branch_frame, bg="white")
                branch_left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

                # Subframe 1: Chemist's name
                chemist_name = tk.Label(
                    branch_left_frame,
                    text=branch["name"],
                    bg="white",
                    fg="black",
                    font=label_font2,
                    justify=tk.LEFT
                )
                chemist_name.pack(anchor=tk.W, padx=5)

                branch_left_frame2 = tk.Frame(branch_frame, bg='white')
                branch_left_frame2.pack(side=tk.LEFT, fill=tk.X, expand=True)
                
                
                if "Map Now" in branch["status"]:
                    def test_menu(branch_data, event):
                        constants.CURRENT_BRANCH_SYNC_JSON = branch_data
                        print('➡ tk_screen.py:403 constants.CURRENT_BRANCH_SYNC_JSON:', constants.CURRENT_BRANCH_SYNC_JSON)
                    
                        # Get the clicked widget's position on the screen
                        x = event.widget.winfo_rootx()
                        y = event.widget.winfo_rooty() + event.widget.winfo_height()

                        print(f"Placing menu at ({x}, {y})")  # Debugging info

                        # Ensure menu does not go outside the application window
                        if x < 0: x = 0
                        if y < 0: y = 0

                        # Show menu at the correct location
                        map_menu.post(x, y)

                    if len(remaining_branch) > 0:
                        test_button = tk.Label(branch_left_frame, text="Map Now >", fg='red', bg='white', font=label_font)
                        test_button.pack(anchor=tk.E, padx=(10,5), fill=tk.X, side=tk.LEFT)
                        test_button.bind("<Button-1>", lambda event, branch_data=branch: test_menu(branch_data, event))

                        # test_button.pack_info()
                    else:
                        test_button = tk.Label(branch_left_frame, text="Tally company not available", fg='red', bg='white', font=label_font)
                        test_button.pack(anchor=tk.E, padx=(10, 5), fill=tk.X, side=tk.LEFT)

                    

                    map_menu = tk.Menu(branch_left_frame2, tearoff=0, bg="white", fg="black", font=label_font)
                    for option in remaining_branch:
                        # map_menu.add_command(label=option, command=lambda opt=option: map_branch_action(opt))
                        map_menu.add_radiobutton(label=option, command=lambda opt=option: map_branch_action(opt,))
                        # map_menu.add_separator()

                else:
                    mapped_status = tk.Label(
                        branch_left_frame,
                        text="Mapped as:",
                        bg="white",
                        fg="#7E878C",
                        font=label_font,
                        justify=tk.LEFT
                    )
                    mapped_status.pack(anchor=tk.W, padx=(10,0), side=tk.LEFT)
                    mapped_status = tk.Label(
                        branch_left_frame,
                        text=branch["status"].replace("Mapped as", ""),
                        bg="white",
                        fg="black",
                        font=label_font,
                        justify=tk.LEFT
                    )
                    mapped_status.pack(anchor=tk.W, padx=(5,10), side=tk.LEFT)  
                    
                # custom_padding = 30 if len(str(branch["name"])) > 30 else 100
                # custom_padding = 120 if len(str(branch["name"])) < 30 else 0
                print('➡ tk_screen.py:534 custom_padding:', custom_padding)
                # # custom_padding = len(str(branch["name"])) + 110

                # Right frame for time and image
                branch_right_frame = tk.Frame(branch_frame, bg="white")
                branch_right_frame.pack(side=tk.RIGHT, fill=tk.X, padx=(custom_padding,0))

                # Subframe 1: Time
                if branch["time"] == "No Sync":
                    branch_time = tk.Label(
                        branch_right_frame,
                        text=branch["time"],
                        bg="white",
                        fg="#7E878C",
                        font=label_font,
                        justify=tk.RIGHT
                    )
                    branch_time.pack(anchor=tk.E, padx=(10,0), side=tk.LEFT)
                    
                else:
                    branch_time = tk.Label(
                        branch_right_frame,
                        text=branch["time"],
                        bg="white",
                        fg="#004BA8",
                        font=label_font,
                        justify=tk.RIGHT
                    )
                    branch_time.pack(anchor=tk.E, padx=(10,0), side=tk.LEFT)
                branch_image_path = ".\\lib\\images\\sync_btn.png"
                branch_image_path2 = ".\\lib\\images\\sync_btn2.png"
                # image = Image.open(branch_image_path).resize((20, 20), Image.Resampling.LANCZOS)
                # branch_image = ImageTk.PhotoImage(image)
                
                # print('➡ tk_screen.py:418 branch_image:', branch_image)
                # Subframe 2: Image (placeholder)
                # branch_image = tk.PhotoImage(file=branch_image_path)
                try:
                    branch_image = Image.open(branch_image_path)
                    branch_image = branch_image.resize((20, 20), Image.Resampling.LANCZOS)  # Resize for better visibility
                    branch_image_tk = ImageTk.PhotoImage(branch_image)
                except Exception as e:
                    print(f"Error loading image: {e}")
                    branch_image_tk = None
                try:
                    branch_image2 = Image.open(branch_image_path2)
                    branch_image2 = branch_image2.resize((20, 20), Image.Resampling.LANCZOS)  # Resize for better visibility
                    branch_image_tk2 = ImageTk.PhotoImage(branch_image2)
                except Exception as e:
                    print(f"Error loading image: {e}")
                    branch_image_tk2 = None

                if branch_image:
                    # constants.ONE_SYNC = [
                    #     {
                    #         "chemist_id" : branch["chemist_id"],
                    #         "tally_company_guid" : branch["company_guid"],
                    #         "company_name" : str(branch).replace("Mapped as ", "")
                    #     }
                    # ]
                    if "Map Now" not in branch["status"]:
                        branch_image_button = tk.Button(
                            branch_right_frame,
                            image=branch_image_tk,  # Set the image on the button
                            bg="white",
                            borderwidth=0,
                            relief=tk.FLAT,
                            # command=lambda: print(f"Clicked image button for branch")  # Example command
                            command=lambda x=branch:sync_single_branch(x),
                        )
                        branch_image_button.image = branch_image_tk
                        branch_image_button.pack(anchor=tk.E, padx=(10,0), side=tk.LEFT)
                    else:
                        branch_image_button = tk.Label(
                            branch_right_frame,
                            image=branch_image_tk2,  # Set the image on the button
                            bg="white",
                            borderwidth=0,
                            # relief=tk.FLAT,
                            # command=lambda: print(f"Clicked image button for branch")  # Example command
                            # command=lambda x=True:show_sync_frame(x)
                        )
                        branch_image_button.image = branch_image_tk2
                        branch_image_button.pack(anchor=tk.E, padx=(10,0), side=tk.LEFT)
                else:
                    branch_image_label = tk.Label(
                        branch_right_frame,
                        text="[IMG]",
                        bg="white",
                        fg="black",
                        font=label_font,
                        justify=tk.RIGHT
                    )
                    branch_image_label.pack(anchor=tk.E, padx=(10, 0), side=tk.LEFT)
                    
            
            # Tk().update()
            # Tk().update_idletasks()
            
            # def configure_scroll_region(event):
            #     canvas.configure(scrollregion=canvas.bbox("all"))

            
            # frame_container.bind("<Configure>", configure_scroll_region)
            # canvas.update_idletasks()  # Forces a layout update before starting the mainloop
            # canvas.configure(scrollregion=canvas.bbox("all"))
            
            # self.update()
            self.update_idletasks()
       
        
        def close_window():
            self.destroy()
            parent.destroy()
            
        def sync_single_branch(data):
        
            constants.ONE_SYNC = [
                {
                    "chemist_id" : data["chemist_id"],
                    "tally_company_guid" : data["company_guid"],
                    "company_name" : str(data["status"]).replace("Mapped as ", ""),
                    "branch_name" : data["name"]
                }
            ]
            show_sync_frame(True)
            
            
            
        def map_branch_action(branch_name, branch={}):
            company_guid = '' 
            if branch == {}:
                branch = constants.CURRENT_BRANCH_SYNC_JSON
            for x in constants.TALLY_ACCOUNTS:
                if x["company_name"] == branch_name:
                    company_guid = x["company_guid"]
            print('➡ tk_screen.py:599 company_guid:', company_guid)
            constants.COMPANY_MAPPING = [
                        {"chemist_id": branch["chemist_id"], "company_name": branch_name, "company_guid": company_guid, "mapping_type":"single"}
            ]
            print('➡ tk_screen.py:605 constants.COMPANY_MAPPING:', constants.COMPANY_MAPPING)
            map_rx_companies()
            
            self.update()
            self.update_idletasks()
            print(f"Mapping branch: {branch_name}")
            
            create_main_content()
            
        def re_create_main_content():
            constants.STOP_THREAD = True
            self.after_cancel(animate_gif)
            create_main_content()
        
        def logout_account():
            logout()
            parent.show_frame("LoginScreen")
            
        # def sync_single_branch():
        #     show_sync_frame(one_sync=False)
            
            
        # def create_process_thread():
            
            

        # def show_sync_frame():
        #     for widget in right_panel.winfo_children():
        #         widget.destroy()

        #     sync_frame = tk.Frame(right_panel, bg="white")
        #     sync_frame.pack(fill=tk.BOTH, expand=True)

        #     sync_label = tk.Label(sync_frame, text="Syncing Data...", bg="white", fg="#004BA8", font=header_font)
        #     sync_label.pack(pady=20)

        #     progress = ttk.Progressbar(sync_frame, orient=tk.HORIZONTAL, length=300, mode="indeterminate")
        #     progress.pack(pady=20)
        #     progress.start()

        #     # Back button
        #     back_button = tk.Button(sync_frame, text="Back", bg="#004BA8", fg="white", font=label_font, relief=tk.FLAT, command=create_main_content)
        #     back_button.pack(pady=20)
        #     # Add your branch mapping logic here (e.g., API call, database update)
            # messagebox.showinfo("Map Branch", f"Branch '{branch_name}' mapped successfully!")

            # Function to animate GIF
        # def check_thread_status():
            
        #     print("maing ", constants.STOP_THREAD)
        #     time.sleep(30)
        #     if not constants.STOP_THREAD:
        #         # gif_animation.destroy()
        #         create_main_content()
        #     else:
        #         self.after(500, check_thread_status)
            
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
            
        def animate_gif(sync_label, frames, index=0):
            frame = frames[index]
            sync_label.configure(image=frame)
            next_index = (index + 3) % len(frames)
            if not constants.STOP_THREAD:
                self.after(100, animate_gif, sync_label, frames, next_index)

        def check_thread_status():
            while not constants.STOP_THREAD:
                time.sleep(0.1)
            re_create_main_content()

        def check_if_require_reboot():
            while not constants.REQUIRE_REBOOT:
                time.sleep(1)
            create_main_content()
            constants.REQUIRE_REBOOT = False
            check_if_require_reboot()
        
        def show_sync_frame(one_sync = False):
            def stop_thread_process():
                messagebox.showerror("Tally Sync", "Sync Stopped Abnormally !!")
                re_create_main_content()
            # print('➡ tk_screen.py:565 one_sync:', one_sync)
            # startprocess(one_sync=one_sync)
            
            thread1 = threading.Thread(
                target=start_background_thread,
                args=(True,one_sync),
                daemon=True
            )
            # check_thread_status()
            thread1.start()
            
            for widget in right_panel.winfo_children():
                widget.destroy()
                
            # print()
            thread1 = threading.Thread(
                target=check_thread_status,
                daemon=True
            )
            # check_thread_status()
            thread1.start()


            right_panel.config(background="#E7F6FF")
            title_bar = tk.Frame(right_panel, width=900, bg="#E7F6FF")
            title_bar.pack(fill=tk.X)
            close_button = tk.Button(title_bar, text='x', font=header_font, command=close_window, bg='#E7F6FF', fg='#044C9D', borderwidth=0, relief=tk.SUNKEN)
            close_button.pack(side=tk.RIGHT, padx=20, pady=(10,5))
            # sync_frame = tk.Frame(right_panel, bg="white")
            # sync_frame.pack(fill=tk.BOTH, expand=True, pady=0)

            # Load GIF and create frames
            gif_path = "lib\images\GIF.gif"  # Update with your gif path
            try:
                gif = Image.open(gif_path)
                frames = []
                size = (350, 350)  # Set your desired size (width, height)
                for frame in ImageSequence.Iterator(gif):
                    processed_frame = process_frame(frame, size)
                    tk_frame = ImageTk.PhotoImage(processed_frame)
                    frames.append(tk_frame)
                # animate_gif(sync_frame, frames)
            except Exception as e:
                print(f"Error loading GIF: {e}")
                # root.destroy()
                # retu
            
            gif_label = tk.Label(right_panel, bg="#E7F6FF")
            gif_label.pack(expand=True, anchor=tk.N, pady=(10, 0))
            
            
            # gif_label = tk.Label(right_panel, bg="white")
            # gif_label.pack(expand=True, anchor=tk.N, pady=0)
            
            constants.CURRENT_BRANCH_SYNC = tk.StringVar(value="")
            print('➡ tk_screen.py:731 constants.CURRENT_BRANCH_SYNC:', constants.CURRENT_BRANCH_SYNC)
            version_label = tk.Label(right_panel, textvariable=constants.CURRENT_BRANCH_SYNC, bg="#E7F6FF", fg="Black", font=header_font2)
            version_label.pack(pady=(0, 20), padx=40, anchor=tk.N)

            
            sync_all_button = tk.Button(right_panel, text="Stop", bg="#ED5A4A", fg="white", font=header_font, relief=tk.FLAT, height=1, width=7, command=stop_thread_process)
            sync_all_button.pack(pady=(10, 120), padx=40, anchor=tk.N)
            # sync_all_button.config(r)


            # Start animation
            animate_gif(gif_label, frames)
            
        def check_login_status():
            # print("sleep 123")
            while constants.MOBILE == "":
                # print("sleep")
                time.sleep(0.1)
            re_create_main_content()
                
        

        # Custom fonts
        header_font = font.Font(family="Manrope", size=14, weight="bold")
        header_font2 = font.Font(family="Manrope", size=12, weight="bold")
        label_font = font.Font(family="Manrope", size=10)
        label_font2 = font.Font(family="Manrope", size=12)
        small_font = font.Font(family="Manrope", size=9)

        
        # Add a title label to the custom title bar
        # title_label = tk.Label(title_bar, text="Custom Title Bar - Approach 3", bg='gray', fg='white')
        # title_label.pack(side=tk.LEFT, padx=10)

        # Add a close button to the custom title bar

        def create_left_content():
            # Left Panel
            # left_panel.configure(background="#004BA8")
            for widget in left_panel.winfo_children():
                widget.destroy()
            
            upper_left_panel = tk.Frame(left_panel, bg="#033D7E", height=150, width=270)
            upper_left_panel.pack(anchor=tk.N, fill=tk.X)

            # Tally Sync Utility header
            header_label = tk.Label(upper_left_panel, text="Tally Sync", bg="#033D7E", fg="white", font=header_font, justify=tk.LEFT)
            header_label.pack(pady=(35, 0), padx=30, anchor=tk.W)
            header_label = tk.Label(upper_left_panel, text="Utility", bg="#033D7E", fg="white", font=header_font, justify=tk.LEFT)
            header_label.pack(pady=(0, 5), padx=30, anchor=tk.W)

            version_label = tk.Label(upper_left_panel, text="Version 2.0", bg="#033D7E", fg="#7E878C", font=small_font)
            version_label.pack(pady=(0, 20), padx=30, anchor=tk.W)
            upper_left_panel.pack_propagate(False)

            lower_left_panel = tk.Frame(left_panel, bg="#004BA8", height=150, width=270)
            lower_left_panel.pack(anchor=tk.W)
            # Auto Sync Section
            # auto_sync_label = tk.Label(lower_left_panel, text="Auto Sync", bg="#004BA8", fg="white", font=label_font, justify=tk.LEFT)
            # auto_sync_label.pack(pady=(20, 5), padx=(10, 20), anchor=tk.W)
                # Auto Sync Section
            
            auto_sync_frame = tk.Frame(lower_left_panel, bg="#004BA8", height=150, width=270)
            auto_sync_frame.pack(pady=(10, 20), padx=0, fill=tk.X)

            auto_sync_label = tk.Label(auto_sync_frame, text="Auto Sync", bg="#004BA8", fg="white", font=header_font2)
            auto_sync_label.pack(padx=(30, 20), pady=(10, 20),side=tk.LEFT, anchor=tk.W)

            # auto_sync_status = tk.Label(auto_sync_frame, text="Off >", bg="#004BA8", fg="white", font=header_font2)
            # auto_sync_status.pack(padx=(20, 30), pady=(30, 20),side=tk.RIGHT, anchor=tk.E)
            
            auto_sync_frame2 = tk.Frame(auto_sync_frame, bg="#004BA8", height=150, width=270)
            auto_sync_frame2.pack(pady=(0, 20), padx=0, fill=tk.X, side=tk.RIGHT)

            # Function to handle menu selection
            def auto_sync_option_selected(option):
                auto_sync_var.set(option)  # Update the label text
                # print('➡ tk_screen.py:790 constants.THREAD:', constants.THREAD)
                # if constants.THREAD is not None:
                #     print("yes")
                    # constants.THREAD.kill()
                    # constants.THREAD = None
                constants.SYNC_TIMER = 0 if str(option) == 'Off' else int(str(option).replace(" min",""))
                if constants.SYNC_TIMER == 0:
                    constants.STOP_THREAD = True
                start_thread(False, False)
                thread1 = threading.Thread(
                    target=check_if_require_reboot,
                    # args=(False, False),
                    daemon=True
                )
                thread1.start()
                
                # constants.THREAD = thread1
                # print('➡ tk_screen.py:800 constants.THREAD:', constants.THREAD)
                
                # # check_thread_status()
                
                print(f"Auto Sync Option Selected: {option}")

            # Auto Sync Dropdown (No Down Arrow)
            auto_sync_var = tk.StringVar(value="Off")

            # Label styled to look like plain text
            auto_sync_label = tk.Label(
                auto_sync_frame2,
                textvariable=auto_sync_var,
                bg="#004BA8",
                fg="#7E878C",
                font=label_font,
                justify=tk.LEFT
            )
            # auto_sync_label.pack(pady=(0, 20), padx=10, anchor=tk.W)
            auto_sync_label.pack(padx=(20, 0), pady=(30, 20),side=tk.LEFT, anchor=tk.W)

            # Dropdown menu
            auto_sync_menu = tk.Menu(auto_sync_frame2, tearoff=0, bg="white", fg="black", font=label_font)
            for option in ["Off",
                            # "1 min",
                            "30 min", "60 min", "90 min", "120 min", "180 min"]:
                auto_sync_menu.add_command(label=option, command=lambda opt=option: auto_sync_option_selected(opt))

            # Bind right-click or left-click to show the menu
            auto_sync_label.bind("<Button-1>", lambda e: auto_sync_menu.post(e.x_root, e.y_root))

            auto_sync_label = tk.Label(auto_sync_frame2, text=">", bg="#004BA8", fg="#7E878C", font=header_font2)
            auto_sync_label.pack(padx=(5, 15), pady=(30, 20),side=tk.RIGHT, anchor=tk.E)


            lower_left_panel.pack_propagate(False)

        # auto_sync_status = tk.Label(lower_left_panel, text="Off >", bg="#004BA8", fg="white", font=label_font, justify=tk.LEFT)
        # auto_sync_status.pack(pady=(0, 20), padx=30, anchor=tk.W)

            # Dotted Line above Logout
        # dotted_line = tk.Canvas(left_panel, bg="#004BA8", highlightthickness=0, height=2)
        # dotted_line.pack(fill=tk.X, padx=0, pady=(0, 10))
        # for i in range(2, 270, 10):  # Adjust range and step for dotted effect
        #     dotted_line.create_line(i, 1, i + 5, 1, fill="white", width=0.4)


            # User Info Section
            constants.MOBILE_VAR = tk.StringVar(value=constants.MOBILE)
            user_label = tk.Label(left_panel, textvariable=constants.MOBILE_VAR, bg="#004BA8", fg="white", font=header_font2, justify=tk.LEFT)
            user_label.pack(pady=(185, 5), padx=30, anchor=tk.W)

            logout_label = tk.Button(left_panel, text="Logout >", bg="#004BA8", fg="white",
                                    highlightbackground='#004BA8', highlightcolor='#004BA8', borderwidth=0,font=label_font2, justify=tk.LEFT, relief=tk.SUNKEN, command=logout_account)
            logout_label.pack(pady=(0, 20), padx=25, anchor=tk.W)

            left_panel.pack_propagate(False)
            
            
        left_panel = tk.Frame(self, bg="#004BA8", width=270, height=600)
        left_panel.pack(side=tk.LEFT, fill=tk.Y)
        
        
        left_panel.pack_propagate(False)
        right_panel = tk.Frame(self, bg="white", width=600, height=600)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
            
        create_left_content()
        create_main_content()
        
        if constants.MOBILE == "":
            thread1 = threading.Thread(
                target=check_login_status,
                daemon=True
            )
            # check_thread_status()
            thread1.start()
            
        
        
        # start_thread(False, False)
        # thread1 = multiprocessing.Process(
        #     target=start_thread,
        #     args=(False, False),
        #     daemon=True
        # )
        # constants.THREAD = thread1
        # # check_thread_status()
        # thread1.start()

        

    
            
# Run the application
if __name__ == "__main__":
    app = App()
    app.mainloop()
    freeze_support()
