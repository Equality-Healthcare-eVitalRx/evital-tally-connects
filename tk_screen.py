import ctypes
from ctypes import wintypes
import json
import multiprocessing
from multiprocessing.dummy import freeze_support
import multiprocessing.process
import threading
import time
import tkinter as tk
from tkinter import font, ttk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageSequence, ImageGrab, ImageFilter
from tkinter import Tk
from functions import login, logout, get_all_mapping_details, constants, start_background_thread, start_thread, map_rx_companies, startprocess
# from lib.import_export_data import get_tally_companies, check_if_tally_running


try: # >= win 8.1
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except: # win 8.0 or less
    ctypes.windll.user32.SetProcessDPIAware()
# import pyglet
# pyglet.font.add_file('lib/fonts/static/Manrope-Medium.ttf') 

class MARGINS(ctypes.Structure):
    _fields_ = [("cxLeftWidth", wintypes.INT),
                ("cxRightWidth", wintypes.INT),
                ("cyTopHeight", wintypes.INT),
                ("cyBottomHeight", wintypes.INT)]

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
            
            
        # def start_move(event):
        #     """Store the initial mouse position relative to the window (absolute position)."""
        #     self.x_offset = event.x_root - self.winfo_x()
        #     self.y_offset = event.y_root - self.winfo_y()

        # def do_move(event):
        #     """Move the window smoothly based on absolute pointer position."""
        #     x = event.x_root - self.x_offset
        #     y = event.y_root - self.y_offset
        #     self.geometry(f"+{x}+{y}")
            
    
        def start_move(event):
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 2, ctypes.byref(ctypes.c_int(0)), ctypes.sizeof(ctypes.c_int(0)))
            
            self.x_offset = event.x_root - self.winfo_x()
            self.y_offset = event.y_root - self.winfo_y()

        def stop_move(event):
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 2, ctypes.byref(ctypes.c_int(2)), ctypes.sizeof(ctypes.c_int(2)))

        def do_move(event):
            x = event.x_root - self.x_offset
            y = event.y_root - self.y_offset
            self.geometry(f"+{x}+{y}")

            
        def on_closing():
            self.destroy()
        
        self.frames = {}
        
        self.geometry("900x600")
        self.configure(bg="#044C9D")  # Set background to blue
        self.overrideredirect(True)
        
        user32 = ctypes.windll.user32
        x ,y = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        x = (x - 900) // 2
        y = (y - 600) // 2
        
        self.geometry(f'+{str(int(x))}+{str(int(y))}')
        
        self.resizable(0,0)
        self.iconbitmap("./lib/images/logo2.ico")
        self.title("Login Screen")
        # self.bind("<Button-1>", start_move)
        # self.bind("<ButtonRelease-1>", stop_move)
        # self.bind("<B1-Motion>", do_move)
        
        self.protocol("WM_DELETE_WINDOW", on_closing)
        self.attributes("-toolwindow", False)  # Make it appear in Alt+Tab
        self.wm_attributes("-toolwindow", False)  # Make it appear in Alt+Tab
        self.attributes("-fullscreen", False)  # Prevent full-screen mode
        self.attributes("-transparentcolor", "white") 
        
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, 0x00000000)
        
        self.add_shadow()
        # self.update_idletasks()

        # hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
        # Set the window style to make it appear in the taskbar
        # ctypes.windll.user32.SetWindowLongW(hwnd, -8, 0)  # GWLP_HWNDPARENT = -8

        self.initialize_screens()
        # self.show_frame("Dashboard")
        self.show_frame("LoginScreen")
        
 
    def add_shadow(self):
        """Applies a drop shadow effect to the window without making it fully white."""
        import ctypes

        # Reduce flickering
        # HWND = ctypes.windll.user32.GetParent(self.winfo_id())
        # style = ctypes.windll.user32.GetWindowLongW(HWND, -20)
        # ctypes.windll.user32.SetWindowLongW(HWND, -20, style | 0x02000000)  # WS_EX_COMPOSITED

        
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        # hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
        style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)  # GWL_EXSTYLE
        style |= 0x00020000  # WS_EX_LAYERED (For transparency)
        style |= 0x00010000  # WS_EX_TRANSPARENT (Prevents white screen issue)
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, style)

        # Apply the shadow effect
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 1, ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int(1))
        )
        
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
            if res == 1:
                constants.MOBILE = mobile_entry.get()
                
                with open("./lib/credentials.json") as data_file:
                        data = json.load(data_file)
                data["mobile"] = constants.MOBILE
                with open("./lib/credentials.json", "w") as json_file:
                        json.dump(data, json_file)
                if constants.MOBILE_VAR is not None:
                    constants.MOBILE_VAR.set(constants.MOBILE)
                get_all_mapping_details()
                parent.show_frame("Dashboard")
            

        # Left panel
        left_panel = tk.Frame(self, bg="#044C9D")
        left_panel.pack(side=tk.LEFT, fill=tk.Y)
        
        image = Image.open("./lib/images/login_panel.PNG")  # Replace with your image path
        image = image.resize((500, 600), Image.Resampling.LANCZOS)  # Resize image to fit the panel
        image_tk = ImageTk.PhotoImage(image)
        
        image_label = tk.Label(left_panel, image=image_tk, bg="#004BA8")
        image_label.image = image_tk  # Keep a reference to avoid garbage collection
        image_label.pack(pady=(0, 10))

        title_bar = tk.Frame(self, width=900, bg="white")
        title_bar.pack(fill=tk.X)
        
        header_font = font.Font(family="Manrope", size=14, weight="bold")
        header_font1 = font.Font(family="Manrope", size=14)
        header_font2 = font.Font(family="Manrope", size=13)


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
            last_sync_label.pack(pady=(10, 0), padx=30, anchor=tk.W)
            
            if len(constants.MAPPING_HISTORY) > 0 and 'login_entity_last_synced' in constants.MAPPING_HISTORY.keys() and constants.MAPPING_HISTORY["login_entity_last_synced"] != "":
                constants.LAST_SYNC_VAR.set(constants.MAPPING_HISTORY["login_entity_last_synced"])

            last_sync_time = tk.Label(top_left_panel, textvariable=constants.LAST_SYNC_VAR, bg="#E7F6FF", fg="#004BA8", font=label_font2, justify=tk.LEFT)
            last_sync_time.pack(pady=(0, 10), padx=30, anchor=tk.W)

            
            sync_all_button = tk.Button(top_right_panel, text="Sync all", bg="#0CA1F6", fg="white", font=label_font2, relief=tk.FLAT, height=1, width=11, command=show_sync_frame)
            sync_all_button.pack(pady=(15,20), padx=40, anchor=tk.E)

            # Lower right panel (contains branch data)
            lower_right_panel = tk.Frame(right_panel, bg="white")
            lower_right_panel.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=30, pady=(10, 0))
            

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
            # print('➡ tk_screen.py:336 branches:', branches)

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
            
            canvas = tk.Canvas(lower_right_panel, bg="white", bd=0, highlightthickness=0, relief='ridge')
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
                if len(branches) > 4:
                    if event.delta:  # Windows scrolling
                        canvas.yview_scroll(-1 * (event.delta // 120), "units")
                    elif event.num == 4:  # Linux scroll up
                        canvas.yview_scroll(-1, "units")
                    elif event.num == 5:  # Linux scroll down
                        canvas.yview_scroll(1, "units")
                        
            def rotate_image(canvas2, size, image_tk, angle):
                while not constants.STOP_THREAD:
                    # Rotate image smoothly
                    rotated_image = branch_image.rotate(angle, resample=Image.BICUBIC, expand=True)

                    # Create a transparent background to prevent jiggling
                    background = Image.new("RGBA", (size, size), (255, 255, 255, 0))
                    offset = (
                        int((size - rotated_image.width) / 2),
                        int((size - rotated_image.height) / 2)
                    )
                    background.paste(rotated_image, offset, rotated_image)

                    # Update the image on canvas
                    image_tk = ImageTk.PhotoImage(background)
                    canvas2.itemconfig(image_id, image=image_tk)

                    # Increment angle for rotation
                    angle = (angle - 15) % 360
                    time.sleep(0.05)
                re_create_main_content()

            def toggle_rotation(event, branch_data, canvas2, size, image_tk, angle=0):
                # print('➡ tk_screen.py:528 toggle_rotation:')
                # print(event)
                print(branch_data)
                sync_single_branch(branch_data)
                if not constants.STOP_THREAD:
                    threading.Thread(target=rotate_image, args=(canvas2, size, image_tk, angle), daemon=True).start()
                    
            
            def show_map_menu(event, branch_data):
                # Capture the screen
                constants.CURRENT_BRANCH_SYNC_JSON = branch_data
                x = self.winfo_rootx()
                y = self.winfo_rooty()
                w = self.winfo_width()
                h = self.winfo_height()
                print(x, y)
                
                # Capture the screen area
                screen = ImageGrab.grab(bbox=(x, y, x + w, y + h))
                blurred_screen = screen.filter(ImageFilter.GaussianBlur(5))

                # Create overlay window
                overlay = tk.Toplevel(self)
                overlay.geometry(f"{w}x{h}+{x}+{y}")
                overlay.overrideredirect(True)

                # Display blurred background
                bg_image = ImageTk.PhotoImage(blurred_screen)
                bg_label = tk.Label(overlay, image=bg_image)
                bg_label.image = bg_image
                bg_label.pack(fill="both", expand=True)

                # Centered menu
                menu_frame = tk.Frame(overlay, bg="white", bd=2, relief="ridge")
                menu_frame.place(relx=0.5, rely=0.5, anchor="center")

                tk.Label(menu_frame, text="Auto Sync", font=header_font, bg="white").pack(pady=(10, 5), padx=30)
                tk.Label(menu_frame, text="Map Now", font=label_font2, bg="white").pack(pady=(10, 5), padx=30)

                options = remaining_branch
                
                s = ttk.Style()                     # Creating style element
                s.configure('Wild.TRadiobutton',    # First argument is the name of style. Needs to end with: .TRadiobutton
                        background="white",         # Setting background to our specified color above
                        foreground='black',
                        font=label_font) 
            
                selected = tk.StringVar(value="")
                
                for option in options:
                    rb = ttk.Radiobutton(menu_frame, text=option, value=option, variable=selected, style = 'Wild.TRadiobutton', command= lambda opt=option, overlay=overlay: map_branch_action(opt, overlay))
                    rb.pack(anchor="w", padx=(40,20), pady=5, ipadx=20)
                    
                # Function to close the overlay when clicking outside
                def on_click_outside(event):
                    # Only destroy if click is outside of both the overlay and the menu_frame
                    if not overlay.winfo_containing(event.x_root, event.y_root) == overlay and \
                    event.widget not in menu_frame.winfo_children():
                        overlay.destroy()

                # Bind click outside the menu to close the overlay
                overlay.bind("<Button-1>", on_click_outside)

            
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
                        test_button.bind("<Button-1>", lambda event, branch_data=branch: show_map_menu(event, branch_data))

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
                    
                branch_right_frame = tk.Frame(branch_frame, bg="white")
                branch_right_frame.pack(side=tk.RIGHT, fill=tk.X, padx=(custom_padding,0))

                if branch["time"] != "No Sync":
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
                
                try:
                    branch_image = Image.open(branch_image_path).convert("RGBA")
                    branch_image = branch_image.resize((20, 20), Image.Resampling.LANCZOS)  # Resize for better visibility
                    branch_image_tk = ImageTk.PhotoImage(branch_image)
                            # Load the original image
                    # self.original_image = Image.open("lib\images\sync_btn.png").convert("RGBA")
                    
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
                    if "Map Now" not in branch["status"]:
                    
                        size = int(max(branch_image.size) * 1.5)  # Add padding for smooth rotation

                        # Create canvas
                        canvas2 = tk.Canvas(branch_right_frame, width=size, height=size, bg="white", highlightthickness=0)
                        canvas2.pack(anchor=tk.E, padx=(10,0), side=tk.LEFT)

                        # Center coordinates
                        center_x = size // 2
                        center_y = size // 2

                        # Display the image
                        image_tk = ImageTk.PhotoImage(branch_image)
                        image_id = canvas2.create_image(center_x, center_y, image=image_tk)

                        # Bind click event to the image
                        canvas2.tag_bind(image_id, "<Button-1>", lambda event,branch_data=branch, x=canvas2, size=size,image_tk=image_tk, angle=0: toggle_rotation(event,branch_data, x, size, image_tk, angle))

                    
                    # else:
                    #     branch_image_button = tk.Label(
                    #         branch_right_frame,
                    #         image=branch_image_tk2,  # Set the image on the button
                    #         bg="white",
                    #         borderwidth=0,
                    #         # relief=tk.FLAT,
                    #         # command=lambda: print(f"Clicked image button for branch")  # Example command
                    #         # command=lambda x=True:show_sync_frame(x)
                    #     )
                    #     branch_image_button.image = branch_image_tk2
                    #     branch_image_button.pack(anchor=tk.E, padx=(10,0), side=tk.LEFT)
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
            thread1 = threading.Thread(
                target=start_background_thread,
                args=(True,True),
                daemon=True
            )
            thread1.start()
            
            # thread1 = threading.Thread(
            #     target=check_thread_status,
            #     daemon=True
            # )
            # thread1.start()
            # show_sync_frame(True)
            
            
            
        def map_branch_action(branch_name, overlay, branch={}):
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
            overlay.destroy()
            create_main_content()
            
        def re_create_main_content():
            constants.STOP_THREAD = True
            self.after_cancel(animate_gif)
            create_main_content()
        
        def logout_account():
            logout()
            parent.show_frame("LoginScreen")
                 
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
            def auto_sync_option_selected(option,overlay):
                auto_sync_var.set(option)  # Update the label text
                constants.SYNC_TIMER = 0 if str(option) == 'Off' else int(str(option).replace(" minutes","").replace(" min",""))
                if constants.SYNC_TIMER == 0:
                    constants.STOP_THREAD = True
                start_thread(False, False)
                thread1 = threading.Thread(
                    target=check_if_require_reboot,
                    # args=(False, False),
                    daemon=True
                )
                thread1.start()
                
                
                print(f"Auto Sync Option Selected: {option}")
                overlay.destroy()

            # Auto Sync Dropdown (No Down Arrow)
            auto_sync_var = tk.StringVar(value="Off")
            auto_sync_var.set("off")

            # Label styled to look like plain text
            auto_sync_label = tk.Label(
                auto_sync_frame2,
                textvariable=auto_sync_var,
                bg="#004BA8",
                fg="#7E878C",
                font=label_font,
                justify=tk.LEFT
            )
            def show_sync_menu(event):
                # Capture the screen
                x = self.winfo_rootx()
                y = self.winfo_rooty()
                w = self.winfo_width()
                h = self.winfo_height()
                print(x, y)
                
                # Capture the screen area
                screen = ImageGrab.grab(bbox=(x, y, x + w, y + h))
                blurred_screen = screen.filter(ImageFilter.GaussianBlur(5))

                # Create overlay window
                overlay = tk.Toplevel(self)
                overlay.geometry(f"{w}x{h}+{x}+{y}")
                overlay.overrideredirect(True)

                # Display blurred background
                bg_image = ImageTk.PhotoImage(blurred_screen)
                bg_label = tk.Label(overlay, image=bg_image)
                bg_label.image = bg_image
                bg_label.pack(fill="both", expand=True)

                # Centered menu
                menu_frame = tk.Frame(overlay, bg="white", bd=2, relief="ridge")
                menu_frame.place(relx=0.5, rely=0.5, anchor="center")

                tk.Label(menu_frame, text="Auto Sync", font=header_font, bg="white").pack(pady=(10, 5), padx=30)

                options = ["Off", "30 min", "60 min", "90 min", "120 min", "180 min"]
                
                s = ttk.Style()                     # Creating style element
                s.configure('Wild.TRadiobutton',    # First argument is the name of style. Needs to end with: .TRadiobutton
                        background="white",         # Setting background to our specified color above
                        foreground='black',
                        font=label_font) 
                
                for option in options:
                    rb = ttk.Radiobutton(menu_frame, text=option, value=option, variable=auto_sync_var, style = 'Wild.TRadiobutton', command= lambda opt=option, indicatoron=0, overlay=overlay:auto_sync_option_selected(opt, overlay))
                    rb.pack(anchor="w", padx=(40,20), pady=5, ipadx=20)
                    
                # Function to close the overlay when clicking outside
                def on_click_outside(event):
                    # Only destroy if click is outside of both the overlay and the menu_frame
                    if not overlay.winfo_containing(event.x_root, event.y_root) == overlay and \
                    event.widget not in menu_frame.winfo_children():
                        overlay.destroy()

                # Bind click outside the menu to close the overlay
                overlay.bind("<Button-1>", on_click_outside)

            # auto_sync_label.pack(pady=(0, 20), padx=10, anchor=tk.W)
            auto_sync_label.pack(padx=(20, 0), pady=(30, 20),side=tk.LEFT, anchor=tk.W)

            # Dropdown menu
            # auto_sync_menu = tk.Menu(auto_sync_frame2, tearoff=0, bg="white", fg="black", font=label_font)
            # for option in ["Off",
            #                 # "1 min",
            #                 "30 min", "60 min", "90 min", "120 min", "180 min"]:
            #     auto_sync_menu.add_command(label=option, command=lambda opt=option: auto_sync_option_selected(opt))

            # Bind right-click or left-click to show the menu
            # auto_sync_label.bind("<Button-1>", lambda e: auto_sync_menu.post(e.x_root, e.y_root))
            auto_sync_label.bind("<Button-1>", show_sync_menu)

            auto_sync_label = tk.Label(auto_sync_frame2, text=">", bg="#004BA8", fg="#7E878C", font=header_font2)
            auto_sync_label.pack(padx=(5, 15), pady=(30, 20),side=tk.RIGHT, anchor=tk.E)


            lower_left_panel.pack_propagate(False)

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

        

    
            
# Run the application
if __name__ == "__main__":
    app = App()
    app.mainloop()
    freeze_support()
