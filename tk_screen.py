import ctypes
from ctypes import wintypes
from datetime import datetime, timedelta
import json
import multiprocessing
from multiprocessing.dummy import freeze_support
import multiprocessing.process
from pathlib import Path
import threading
import time
import tkinter as tk
from tkinter import font, ttk
from tkinter import messagebox
from tkinter import scrolledtext
import traceback
from PIL import Image, ImageTk, ImageSequence, ImageGrab, ImageFilter
from customtkinter import CTkButton, CTkFont
import pyglet
import keyboard
from tkcalendar import Calendar, DateEntry
from ttkthemes import ThemedStyle
from functions import login, logout, get_all_mapping_details, constants, start_background_thread, start_thread, map_rx_companies, startprocess, encrypt_data,decrypt_data, LogManagerObj
pyglet.options['win32_gdi_font'] = True
fontpath = Path(__file__).parent / 'lib/fonts/static/Manrope-Regular.ttf'
themepath = Path(__file__).parent / "lib/fonts/breeze/breeze.tcl"
print(fontpath)
pyglet.font.add_file(str(fontpath))
try: # >= win 8.1
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except: # win 8.0 or less
    ctypes.windll.user32.SetProcessDPIAware()

import ctypes

class MARGINS(ctypes.Structure):
    _fields_ = [("cxLeftWidth", wintypes.INT),
                ("cxRightWidth", wintypes.INT),
                ("cyTopHeight", wintypes.INT),
                ("cyBottomHeight", wintypes.INT)]
    

def open_log_window(parent, event):
    print("ctrl d")
    # logObj = LogManagerObj()
    LogViewerAppObj = LogViewerApp(parent)
    # parent.log_window = 
    LogViewerAppObj.show_log_viewer()
    

class App(tk.Tk):
    def __init__(self):
        
        super().__init__()
        # Store reference to root window for thread-safe operations
        constants.ROOT_WINDOW = self
        constants.ANIMATION_AFTER_ID = None
        # self.log_viewer = LogViewerApp(self)
        constants.LOAD_COMPLETE = True
        self.log_window = None



        def start_move(event):
            self.x_offset = event.x_root - self.winfo_x()
            self.y_offset = event.y_root - self.winfo_y()

        def do_move(event):
            x = event.x_root - self.x_offset
            y = event.y_root - self.y_offset

            hwnd = ctypes.windll.user32.GetForegroundWindow()
            ctypes.windll.user32.SetWindowPos(hwnd, None, x, y, 0, 0, 0x0001 | 0x0004)

        def stop_move(event):
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            ctypes.windll.user32.SendMessageW(hwnd, 0x000B, True, 0)   # WM_SETREDRAW = 0x000B
            ctypes.windll.user32.RedrawWindow(hwnd, None, None, 0x85)  # RDW_INVALIDATE | RDW_UPDATENOW | RDW_ALLCHILDREN

        def close_window():
            """Close the application."""
            self.destroy()
            
        def on_closing():
            self.destroy()
        
        self.frames = {}
        
        self.geometry("950x650")
        self.configure(bg="#044C9D")  # Set background to blue
        self.overrideredirect(True)
        
        hwnd = self.winfo_id()
        
        # Ensure the window has a taskbar presence
        ctypes.windll.user32.SetWindowLongW(hwnd, -8, 0)  # Set parent to None (GWLP_HWNDPARENT = -8)
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, 
                                            ctypes.windll.user32.GetWindowLongW(hwnd, -20) & ~0x00000080)  # Remove WS_EX_TOOLWINDOW
        ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0020)  # Apply changes (SWP_FRAMECHANGED)

        
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
        # self.attributes("-transparentcolor", "white") 
        
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, 0x00000000)
        
        self.add_shadow()
        # self.update_idletasks()

        self.initialize_screens()
        self.show_frame("LoginScreen")
        
        hwnd = self.winfo_id()
        
        # Ensure the window has a taskbar presence
        ctypes.windll.user32.SetWindowLongW(hwnd, -8, 0)  # Set parent to None (GWLP_HWNDPARENT = -8)
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, 
                                            ctypes.windll.user32.GetWindowLongW(hwnd, -20) & ~0x00000080)  # Remove WS_EX_TOOLWINDOW
        ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0020)  # Apply changes (SWP_FRAMECHANGED)

        user32 = ctypes.windll.user32
        
        self.update()
        self.update_idletasks()
        
    def start_move(self, event):
        self.x_offset = event.x_root - self.winfo_x()
        self.y_offset = event.y_root - self.winfo_y()

    def do_move(self, event):
        x = event.x_root - self.x_offset
        y = event.y_root - self.y_offset

        hwnd = ctypes.windll.user32.GetForegroundWindow()
        ctypes.windll.user32.SetWindowPos(hwnd, None, x, y, 0, 0, 0x0001 | 0x0004)

    def stop_move(self, event):
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        ctypes.windll.user32.SendMessageW(hwnd, 0x000B, True, 0)   # WM_SETREDRAW = 0x000B
        ctypes.windll.user32.RedrawWindow(hwnd, None, None, 0x85)  # RDW_INVALIDATE | RDW_UPDATENOW | RDW_ALLCHILDREN

    
    def add_shadow(self):
        """Applies a drop shadow effect to the window without making it fully white."""
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)  # GWL_EXSTYLE
        style |= 0x00020000  # WS_EX_LAYERED (For transparency)
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, style)

        # Apply the shadow effect
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 2, ctypes.byref(ctypes.c_int(2)), ctypes.sizeof(ctypes.c_int(2))
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
        if frame_name in self.frames:
            self.frames[frame_name].destroy()
            del self.frames[frame_name]
        
        if frame_name == "LoginScreen":
            self.frames[frame_name] = LoginScreen(self, self)
        elif frame_name == "Dashboard":
            self.frames[frame_name] = Dashboard(self, self)
        
        frame = self.frames[frame_name]
        # frame.tkraise()
        # frame.update_idletasks() 
        
        frame.grid(row=0, column=0, sticky="nsew")

        # Raise the new frame to the front
        frame.tkraise()
        frame.update_idletasks()  # Force UI update
        
                    
    def clear_frame_inputs(self, frame):
        """Clear all Entry, Text, and selected values in Checkbuttons/Radiobuttons inside a frame."""
        for widget in frame.winfo_children():
            if isinstance(widget, tk.Entry):
                widget.delete(0, tk.END)  # Clear text entry fields
            elif isinstance(widget, tk.Text):
                widget.delete("1.0", tk.END)  # Clear text area
            elif isinstance(widget, tk.Checkbutton):
                widget.deselect()  # Uncheck checkbuttons
            elif isinstance(widget, tk.Radiobutton):
                widget.deselect()  # Unselect radiobuttons
            elif isinstance(widget, tk.OptionMenu):
                widget.set("")  # Reset dropdown selection if applicable
            elif isinstance(widget, tk.Frame):
                self.clear_frame_inputs(widget)  # Recursively clear nested frames

class LoginScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller
        parent.title = "Login"
        
        self.bind_all("<Control-d>", lambda e: open_log_window(parent, e))


        header_font = font.Font(family="Manrope", size=14, weight="bold")
        header_font1 = font.Font(family="Manrope", size=14)
        header_font2 = font.Font(family="Manrope", size=13)
        header_font2b = font.Font(family="Manrope", size=13, weight="bold")
        header_font3 = font.Font(family="Manrope", size=12)
        header_font4 = font.Font(family="Manrope", size=11)
        header_font4b = font.Font(family="Manrope", size=11, weight="bold")
        header_font5b = font.Font(family="Manrope", size=8, weight="bold")
        
        
        def close_window():
            self.destroy()
            parent.destroy()
        
        def check_login():
            entity = "chemist" if str(selected_entity.get()) == "eVitalRx" else "distributor"
            res = login(mobile_entry.get(), password_entry.get(), entity)
            print(res, "login response")
            if res == 1:
                show_port_popup()
                constants.MOBILE = mobile_entry.get()
                
                with open("./lib/app_cache.txt") as data_file:
                        # data = json.load(data_file)
                        data = decrypt_data(data_file.read())
                data["mobile"] = constants.MOBILE
                data["tally_port"] = constants.TALLY_PORT
                data["tally_host"] = constants.HOST
                with open("./lib/app_cache.txt", "w") as json_file:
                        # json.dump(data, json_file)
                        json_file.write(encrypt_data(data))
                if constants.MOBILE_VAR is not None:
                    constants.MOBILE_VAR.set(constants.MOBILE)
                get_all_mapping_details()
                parent.show_frame("Dashboard")
                
        def update_tally_port(overlay, port, host):
            constants.TALLY_PORT = port
            constants.HOST = host
            overlay.destroy()
            [widget.delete(0, tk.END) for widget in parent.winfo_children() if isinstance(widget, tk.Entry)]
        
            
        def show_port_popup():
            x = self.winfo_rootx()
            y = self.winfo_rooty()
            w = self.winfo_width()
            h = self.winfo_height()
            
            def validate(action, index, value_if_allowed,
                prior_value, text, validation_type, trigger_type, widget_name):
                if value_if_allowed == "":
                    return True
                if value_if_allowed:
                    try:
                        float(value_if_allowed)
                        return True
                    except ValueError:
                        return False
                else:
                    return False
            
            vcmd = (self.register(validate),
                        '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
            
            # Capture the screen area
            screen = ImageGrab.grab(bbox=(x, y, x + w, y + h))
            blurred_screen = screen.filter(ImageFilter.GaussianBlur(4))

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
            menu_frame = tk.Frame(overlay, bg="white", bd=2, relief="ridge", padx=10, pady=10)
            menu_frame.place(relx=0.5, rely=0.5, anchor="center")

            tk.Label(menu_frame, text="Tally Configuration",
                    font=header_font2, bg="white").pack(pady=(20, 20), padx=40)
            
            
            # host Entry
            button_frame2 = tk.Frame(menu_frame, bg="white")
            button_frame2.pack(pady=(7,15))
            
            host_label = tk.Label(button_frame2, text="Tally Host", font=header_font4, bg="white")
            host_label.pack(pady=(0, 10), padx=(10, 20), side=tk.LEFT)
            
            tally_host_var = tk.StringVar(value=constants.HOST)
            host_entry = tk.Entry(button_frame2, textvariable=tally_host_var, font=header_font3, validate='key', validatecommand=vcmd, width=13, justify="center", bd=1, relief="solid")
            host_entry.pack(pady=(0, 10), padx=(10, 20), side=tk.RIGHT)
            host_entry.pack_propagate(False)
            
            # Port Entry
            button_frame = tk.Frame(menu_frame, bg="white")
            button_frame.pack(pady=(7,15))
            
            tally_port_var = tk.StringVar(value=constants.TALLY_PORT)
            port_label = tk.Label(button_frame, text="Tally Port", font=header_font4, bg="white")
            port_label.pack(pady=(0, 10), padx=(10, 20), side=tk.LEFT)
            
            port_entry = tk.Entry(button_frame, textvariable=tally_port_var, font=header_font3, validate='key', validatecommand=vcmd, width=13, justify="center", bd=1, relief="solid")
            port_entry.pack(pady=(0, 10), padx=(10, 20), side=tk.RIGHT)
            port_entry.pack_propagate(False)
            
            
            # YES button - Blue background with white text
            yes_button2 = tk.Button(menu_frame, text="Update", width=8, bg="#007BFF", fg="white",
                                activebackground="#0056b3", activeforeground="white",
                                relief="flat", font=header_font4,
                                command=lambda x=overlay,y=tally_port_var.get(),z=tally_host_var.get():update_tally_port(x,y,z))
            yes_button2.pack(pady=(0, 10), side="left", padx=20, fill=tk.X, expand=True)


            # Function to close the overlay when clicking outside
            def on_click_outside(event):
                if not overlay.winfo_containing(event.x_root, event.y_root):
                    overlay.destroy()

            # Bind click outside the menu to close the overlay
            overlay.bind("<Button-1>", on_click_outside)
        
        drag_layer = tk.Frame(
            self,
            # bg="#0CA1F6",
            bg="white",
            height=35
        )
        drag_layer.pack(side=tk.TOP, fill=tk.X)
        
        # Load and display icon in title bar
        icon_path = "./lib/images/logo2.ico"  # or use .png
        try:
            icon_image = Image.open(icon_path)
            icon_image = icon_image.resize((20, 20), Image.Resampling.LANCZOS)
            icon_image_tk = ImageTk.PhotoImage(icon_image)
            
            icon_label = tk.Label(
                drag_layer,
                image=icon_image_tk,
                bg="white"
            )
            icon_label.image = icon_image_tk  # Keep reference
            icon_label.pack(side=tk.LEFT, padx=(15, 5), pady=(3, 3))
            print("Title bar icon loaded")
        except Exception as e:
            print(f"Error loading title bar icon: {e}")

        # Title (left side)
        title_label = tk.Label(
            drag_layer,
            text="Tally Sync Utility",
            # bg="#0CA1F6",
            bg="white",
            # fg="white",
            fg="black",
            font=header_font5b
        )
        title_label.pack(side=tk.LEFT, padx=(5, 0), pady=(3,0))

        # Close button (right side)
        close_button = tk.Label(
            drag_layer,
            text="✕",
            # bg="#0CA1F6",
            bg="white",
            # fg="white",
            fg="black",
            font=("Segoe UI", 8, "bold"),
            cursor="hand2"
        )
        close_button.pack(side=tk.RIGHT, padx=15, pady=3)
    
        def on_close_enter(e):
            close_button.config(bg="#E81123")  # Windows red

        def on_close_leave(e):
            # close_button.config(bg="#0CA1F6")
            close_button.config(bg="white")

        close_button.bind("<Enter>", on_close_enter)
        close_button.bind("<Leave>", on_close_leave)

        drag_layer.bind("<Button-1>", self.controller.start_move)
        drag_layer.bind("<B1-Motion>", self.controller.do_move)

        # Also allow dragging from title text
        title_label.bind("<Button-1>", self.controller.start_move)
        title_label.bind("<B1-Motion>", self.controller.do_move)
        
        close_button.bind("<Button-1>", lambda e: close_window())

        # Left panel
        left_panel = tk.Frame(self, bg="#044C9D")
        left_panel.pack(side=tk.LEFT, fill=tk.Y)
        
        image = Image.open("./lib/images/login_panel.jpg")  # Replace with your image path
        image = image.resize((500, 600), Image.Resampling.LANCZOS)  # Resize image to fit the panel
        image_tk = ImageTk.PhotoImage(image)
        
        image_label = tk.Label(left_panel, image=image_tk, bg="#004BA8")
        image_label.image = image_tk  # Keep a reference to avoid garbage collection
        image_label.pack(pady=(0, 10))

        # title_bar = tk.Frame(self, width=900, bg="white")
        # title_bar.pack(fill=tk.X)

    
        # close_button = tk.Button(title_bar, text='x', font=header_font, command=close_window, bg='white', fg='#044C9D', borderwidth=0, relief=tk.SUNKEN)
        # close_button.pack(side=tk.RIGHT, padx=20, pady=15)

        right_panel = tk.Frame(self, bg="white", width=450 , height=650)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        right_panel.pack_propagate(False)

        login_label = tk.Label(right_panel, text="Login with", bg="white", font=header_font2b, justify=tk.LEFT)
        login_label.pack(pady=(75, 0), padx=(60,55), anchor=tk.W)
        
        entity_selection_frame = tk.Frame(right_panel, bg="white")
        entity_selection_frame.pack(pady=(5, 20), padx=(60,55), anchor=tk.W)
        
        entity_button_theme = ttk.Style()
        if "breeze" not in entity_button_theme.theme_names():
            self.tk.call('source',themepath)
    
        entity_button_theme.configure("TLabel", foreground="black")         # Label text color
        entity_button_theme.configure("TButton", foreground="black")        # Button text color
        entity_button_theme.configure("TRadiobutton", foreground="black")   # Radiobutton text color
        entity_button_theme.configure("TCheckbutton", foreground="black")   # Checkbutton text color
        
        entity_button_theme.configure('breeze.TRadiobutton',# First argument is the name of style. Needs to end with: .TRadiobutton
        background = "white",focuscolor="white", highlightthickness=0, borderwidth=0)         # You can define colors like this also
        entity_button_theme.theme_use("breeze")
        
        selected_color = "#044C9D"  # Blue color for selected text
        default_color = "black"

        def update_color():
            if selected_entity.get() == "eVitalRx":
                label1.config(fg=selected_color, font=header_font4b)
                label2.config(fg=default_color, font=header_font4b)
            else:
                label1.config(fg=default_color, font=header_font4b)
                label2.config(fg=selected_color, font=header_font4b)
        
        selected_entity = tk.StringVar(value="eVitalRx")
        
        rb1 = ttk.Radiobutton(entity_selection_frame, style="breeze.TRadiobutton", variable=selected_entity, value="eVitalRx",command=update_color)
        rb1.pack(side="left")

        label1 = tk.Label(entity_selection_frame, text="eVitalRx", font=header_font4b, fg=selected_color, background='white')
        label1.pack(side="left")

        rb2 = ttk.Radiobutton(entity_selection_frame, style="breeze.TRadiobutton", variable=selected_entity, value="eVitalSupply",command=update_color)
        rb2.pack(side="left", padx=(30, 0))

        label2 = tk.Label(entity_selection_frame, text="eVitalSupply", font=header_font4b, fg=default_color, background='white')
        label2.pack(side="left")

        def validate(action, index, value_if_allowed,
                        prior_value, text, validation_type, trigger_type, widget_name):
            if value_if_allowed == "":
                return True
            if value_if_allowed:
                if len(str(value_if_allowed)) > 10:
                    return False
                try:
                    float(value_if_allowed)
                    return True
                except ValueError:
                    return False
            else:
                return False
        
        vcmd = (self.register(validate),
                    '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
            
        
        mobile_label = tk.Label(right_panel, text="Mobile Number", bg="white", fg="#044C9D", font=header_font3)
        mobile_label.pack(pady=(20, 0), padx=(60,55), anchor=tk.W)

        mobile_entry = tk.Entry(right_panel, bg="white", font=header_font2, bd=0, width=40, validate='key' , validatecommand=vcmd)
        mobile_entry.pack(pady=4, padx=65, anchor=tk.W)
        mobile_line = tk.Canvas(right_panel, width=280, height=1, bg="#004BA8", highlightthickness=0)
        mobile_line.pack(pady=(0, 10), padx=(65,35), anchor=tk.W)
        mobile_entry.propagate(False)

        password_label = tk.Label(right_panel, text="Password", bg="white", fg="#044C9D", font=header_font3, width=40, justify=tk.LEFT, anchor="w")
        password_label.pack(pady=(10, 0), padx=(60,55), anchor=tk.W)

        password_entry = tk.Entry(right_panel, bg="white", font=header_font2, bd=0, show="*")
        password_entry.pack(pady=4, padx=65, anchor=tk.W, fill=tk.X)
        password_line = tk.Canvas(right_panel, width=280, height=1, bg="#004BA8", highlightthickness=0)
        password_line.pack(pady=(0, 20), padx=(65, 35), anchor=tk.W)
        
        password_entry.bind("<Return>", lambda e: login_button.invoke())
        
        login_button = CTkButton(right_panel, text="Login", hover_color='#033D7E', text_color='white', fg_color="#0CA1F6", font=CTkFont(family='Manrope', size=16, weight='bold'), height=42, width=230, corner_radius=4, command=check_login)
        login_button.pack(pady=20, padx=(20, 50))
        

class Dashboard(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#004BA8")
        for widget in self.winfo_children():
            if widget.winfo_exists():
                widget.destroy()
        self.controller = controller
        self.parent = parent
        parent.title = "Tally Sync"
        self.checkbox_vars = {}
        header_font5b = font.Font(family="Manrope", size=8, weight="bold")
        
        # def open_log_window()
        
        self.bind_all("<Control-d>", lambda e: open_log_window(parent, e))


        def create_main_content():

            constants.STOP_THREAD = False
            if right_panel.winfo_exists():  # Ensures widget exists before calling winfo_children()
                for widget in right_panel.winfo_children():
                    if widget.winfo_exists():
                        widget.destroy()

            get_all_mapping_details()
            all_mapped = False
            mapres1 = constants.MAPPING_HISTORY["results"] if isinstance(constants.MAPPING_HISTORY, dict) and "results" in constants.MAPPING_HISTORY.keys() else []
            mapres = [x for x in mapres1 if x["is_mapped"] in ["False", False, 'false', ""]]
            
            available_companies = constants.TALLY_ACCOUNTS.copy()
            for x in constants.TALLY_ACCOUNTS:
                for j in constants.MAPPING_HISTORY.get("results", []):
                    if x["company_guid"] == j["tally_company_guid"] and x in available_companies:
                        available_companies.remove(x)
            all_mapped = len(available_companies) == 0 or len(mapres) == 0
            if all_mapped and len(mapres1) > 0:
                constants.SYNC_STAGE = 1
                constants.SYNC_BTN_TEXT = "Sync All"
                print("stage 1")
                
            # print(constants.MAPPING_HISTORY, "mapping history in dashboard")
            # # print(constants.COMPANY_MAPPING, "company mapping in dashboard")
            
            style = ttk.Style()
            style.configure("TLabel", foreground="black")         # Label text color
            style.configure("TButton", foreground="black")        # Button text color
            style.configure("TRadiobutton", foreground="black")   # Radiobutton text color
            style.configure("TCheckbutton", foreground="black")   # Checkbutton text color

            # Upper right panel (contains last sync and button)
            upper_right_panel = tk.Frame(right_panel, bg="#E7F6FF")
            upper_right_panel.pack(side=tk.TOP, fill=tk.X)
            

            # Left and right sections inside the upper panel
            top_left_panel = tk.Frame(upper_right_panel, bg="#E7F6FF")
            top_left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(50, 15))
            
            top_right_panel = tk.Frame(upper_right_panel, bg="#E7F6FF")
            top_right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, pady=(60, 5), padx=(0,20))

            # Last Sync header and time
            constants.LAST_SYNC_VAR = tk.StringVar(value="" if constants.SYNC_STAGE == 0 else "No Sync")
            
            constants.LAST_SYNC_HEADER_VAR = tk.StringVar(value="Map Your Tally Companies" if constants.SYNC_STAGE == 0 else "Last Sync")
            last_sync_label = tk.Label(top_left_panel, textvariable=constants.LAST_SYNC_HEADER_VAR, bg="#E7F6FF", fg="#7E878C", font=label_font2, justify=tk.LEFT)
            last_sync_label.pack(pady=(10, 0), padx=30, anchor=tk.W)
            
            if constants.SYNC_STAGE == 1 and constants.MAPPING_HISTORY is not None and len(constants.MAPPING_HISTORY) > 0 and 'login_entity_last_synced' in constants.MAPPING_HISTORY.keys() and constants.MAPPING_HISTORY["login_entity_last_synced"] != "":
                constants.LAST_SYNC_VAR.set(constants.MAPPING_HISTORY["login_entity_last_synced"])


            last_sync_time = tk.Label(top_left_panel, textvariable=constants.LAST_SYNC_VAR, bg="#E7F6FF", fg="#004BA8", font=label_font2, justify=tk.LEFT)
            last_sync_time.pack(pady=(0, 10), padx=30, anchor=tk.W)

            sync_all_button = CTkButton(top_right_panel, text=constants.SYNC_BTN_TEXT, hover_color='#033D7E' , font=CTkFont(family='Manrope', size=16, weight='bold'), text_color='white', fg_color="#0CA1F6", height=42, width=120, corner_radius=4, command=show_sync_frame)
            sync_all_button.pack(pady=(5,20), padx=40, anchor=tk.E)

            # Lower right panel (contains branch data)
            lower_right_panel = tk.Frame(right_panel, bg="white")
            lower_right_panel.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=30, pady=(10, 0))
            
            if constants.SYNC_STAGE == 0:

                branches = [] if constants.EVITAL_RX_API_KEY == "" or constants.MAPPING_HISTORY is None else [
                    {
                        "name":x["branch_name"], 
                        "status":"Map Now" if x["tally_company_name"] =="" else str("Mapped as ")+str(x["tally_company_name"]), 
                        "time" : "No Sync" if x["last_synced"]=="" else x["last_synced"],
                        "chemist_id" : x["entity_id"],
                        "company_guid" : x["tally_company_guid"]
                    } 
                    for x in constants.MAPPING_HISTORY["results"]
                ]
                remaining_branch = [
                    x["company_name"] for x in constants.TALLY_ACCOUNTS         
                ]
                custom_padding = 100
                if len(branches) > 0:
                    max_branch = max([len(str(x["name"])) for x in  branches])
                    max_branch_time = max([len(str(x["time"])) for x in  branches])
                    
                    custom_padding = 280 - ((max_branch+max_branch_time)) if max_branch + max_branch_time < 34 else ((280 - ((max_branch+max_branch_time) * 3.5 )) if max_branch+max_branch_time < 45 else (280 - ((max_branch+max_branch_time) * 4.5 )))
                custom_padding = custom_padding if custom_padding > 0 else 0
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
                    # print(branch_data)
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
                    menu_frame = tk.Frame(overlay, bg="white", bd=2, relief="ridge", pady=20)
                    menu_frame.place(relx=0.5, rely=0.5, anchor="center")

                    # print(branch_data)
                    tk.Label(menu_frame, text=branch_data["name"], font=header_font, bg="white").pack(pady=(10, 5), padx=20)
                    # tk.Label(menu_frame, text="Arkham sylum batman joker harley quinn aquamna cyborg flash", font=header_font, bg="white").pack(pady=(20, 5), padx=20)
                    tk.Label(menu_frame, text="Map With", font=label_font2, bg="white").pack(anchor='n',pady=(0, 20), padx=20)

                    options = remaining_branch

                    if len(options) > 10:
                        canvas2 = tk.Canvas(menu_frame, bg="white", bd=0, highlightthickness=0, relief='ridge')
                        # scrollbar = ttk.Scrollbar(menu_frame, orient="vertical", command=canvas.yview, style="Custom.Vertical.TScrollbar")
                        scrollbar2 = ttk.Scrollbar(menu_frame, orient="vertical", command=canvas2.yview)
                        scrollable_frame2 = tk.Frame(canvas2, bg="white")

                        # Configure the canvas
                        scrollable_frame2.bind(
                            "<Configure>",
                            lambda e: canvas2.configure(scrollregion=canvas2.bbox("all"))
                        )

                        canvas2.create_window((0, 0), window=scrollable_frame2, anchor="nw")
                        canvas2.configure(yscrollcommand=scrollbar2.set)

                        # Pack canvas and scrollbar
                        canvas2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)
                    else:
                        scrollable_frame2 = menu_frame
                    def on_scroll2(event):
                        """Enable scrolling inside the frame without dragging the app."""
                        if len(options) > 10:
                            if event.delta:  # Windows scrolling
                                canvas2.yview_scroll(-1 * (event.delta // 120), "units")
                            elif event.num == 4:  # Linux scroll up
                                canvas2.yview_scroll(-1, "units")
                            elif event.num == 5:  # Linux scroll down
                                canvas2.yview_scroll(1, "units")
                    
                    s = ttk.Style()                     # Creating style element
                    s.configure('Wild.TRadiobutton',    # First argument is the name of style. Needs to end with: .TRadiobutton
                            background="white",         # Setting background to our specified color above
                            foreground='black',
                            indicatormargin=100,
                            # padding=(10,5),
                            font=label_font) 
                
                    selected = tk.StringVar(value="")
                    
                    for option in options:
                        rb = ttk.Radiobutton(scrollable_frame2, text=option, value=option, variable=selected, style = 'Wild.TRadiobutton', command= lambda opt=option, overlay=overlay: map_branch_action(opt, overlay))
                        rb.pack(anchor="w", padx=(80,20), pady=5, fill="x")
                        
                    # Function to close the overlay when clicking outside
                    def on_click_outside(event):
                        # Only destroy if click is outside of both the overlay and the menu_frame
                        if not overlay.winfo_containing(event.x_root, event.y_root) == overlay and \
                        (event.widget not in menu_frame.winfo_children() and event.widget not in scrollable_frame2.winfo_children()):
                            overlay.destroy()
                    

                    if len(options) > 10:
                        canvas2.bind_all("<MouseWheel>", on_scroll2)  # Windows
                        canvas2.bind_all("<Button-4>", on_scroll2)  # Linux Scroll Up
                        canvas2.bind_all("<Button-5>", on_scroll2)
                    # Bind click outside the menu to close the overlay
                    overlay.bind("<Button-1>", on_click_outside)
                
                
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
                        
                            # Get the clicked widget's position on the screen
                            x = event.widget.winfo_rootx()
                            y = event.widget.winfo_rooty() + event.widget.winfo_height()

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
                 
                        
            elif constants.SYNC_STAGE == 1:

                # ================= TOP PANEL =================
                top_panel = tk.Frame(lower_right_panel, bg="white")
                top_panel.pack(fill=tk.X, pady=(10, 10), padx=0)

                # ---- LEFT: TARGET COMPANY ----
                left_top = tk.Frame(top_panel, bg="white")
                left_top.pack(side=tk.LEFT, fill=tk.X, expand=True)

                tk.Label(left_top, text="Target Company", bg="white", fg="#666", font=header_font3)\
                    .pack(anchor="w", padx=(0, 10))

                company_row = tk.Frame(left_top, bg="white")
                company_row.pack(fill=tk.X, pady=(5, 0), padx=(5,0))

                company_options = {x["company_guid"]: x["company_name"] for x in constants.TALLY_ACCOUNTS}
                if constants.MAPPING_HISTORY is not None and len(constants.MAPPING_HISTORY) > 0:
                    if len(constants.MAPPING_HISTORY.get("results", [])) > 0:
                        company_options = {}
                        for x in constants.MAPPING_HISTORY.get("results", []):
                            company_options[x["tally_company_guid"]] = x["tally_company_name"]

                company_var = tk.StringVar(value=list(company_options.values())[0] if company_options else "")
                constants.COMPANY_NAME = company_var.get()
                
                def update_company(*args):
                    print(f"Selected company: {company_var.get()}")
                    constants.COMPANY_NAME = company_var.get()

                dropdown_wrapper = tk.Frame(company_row, bg="#0CA1F6")
                dropdown_wrapper.pack(side=tk.LEFT, padx=(0, 10))

                company_dropdown = tk.OptionMenu(dropdown_wrapper, company_var, *company_options.values())
                company_dropdown.config(
                    bg="#0CA1F6",
                    fg="white",
                    activebackground="#0CA1F6",
                    activeforeground="white",
                    font=("Segoe UI", 10),
                    bd=0,
                    highlightthickness=0,
                    relief="flat",
                    cursor="hand2",
                    indicatoron=False,
                    width=20 
                )
                company_dropdown.pack(side=tk.LEFT, padx=(10, 0), pady=2)

                arrow = tk.Label(
                    dropdown_wrapper,
                    text="▼",
                    bg="#0CA1F6",
                    fg="white",
                    font=("Segoe UI", 8)
                )
                arrow.pack(side=tk.RIGHT, padx=8)
                def on_enter(e):
                    dropdown_wrapper.config(bg="#0CA1F6")
                    company_dropdown.config(bg="#0CA1F6")
                    arrow.config(bg="#0CA1F6")

                def on_leave(e):
                    dropdown_wrapper.config(bg="#0CA1F6")
                    company_dropdown.config(bg="#0CA1F6")
                    arrow.config(bg="#0CA1F6")
                
                dropdown_wrapper.bind("<Enter>", on_enter)
                dropdown_wrapper.bind("<Leave>", on_leave)
                company_dropdown.bind("<Enter>", on_enter)
                company_dropdown.bind("<Leave>", on_leave)
                arrow.bind("<Enter>", on_enter)
                arrow.bind("<Leave>", on_leave)
                company_var.trace_add("write", update_company)
                
                def open_dropdown(event):
                    menu = company_dropdown["menu"]

                    # Get widget position on screen
                    x = company_dropdown.winfo_rootx()
                    y = company_dropdown.winfo_rooty() + company_dropdown.winfo_height()

                    menu.tk_popup(x, y)
                    
                arrow.bind("<Button-1>", open_dropdown)
                dropdown_wrapper.bind("<Button-1>", open_dropdown)
            

                DATE_FORMAT = "%d-%m-%y"  # adjust if your DateEntry format differs

                def validate_dates(*args):
                    try:
                        start_str = constants.SYNC_START_DATE.get()
                        end_str = constants.SYNC_END_DATE.get()

                        if not start_str or not end_str:
                            return
                        
                        
                        if start_str == "dd-mm-yy" or end_str == "dd-mm-yy":
                            messagebox.showerror("Invalid Date", "Please enter valid date.")
                            return

                        start_date = datetime.strptime(start_str, DATE_FORMAT)
                        end_date = datetime.strptime(end_str, DATE_FORMAT)

                        # Rule 1: End date should not be before start date
                        if end_date < start_date:
                            messagebox.showerror("Invalid Date", "End date cannot be before start date.")
                            constants.SYNC_END_DATE.set(start_str)
                            return

                        # Rule 2: Max 30 days range
                        if (end_date - start_date).days > 30:
                            messagebox.showerror("Invalid Range", "You can select a maximum of 30 days only.")
                            
                            # Auto-correct end date to +30 days from start
                            corrected_date = start_date + timedelta(days=30)
                            constants.SYNC_END_DATE.set(corrected_date.strftime(DATE_FORMAT))
                            return
                        
                        if start_date.date() > datetime.now().date() or end_date.date() > datetime.now().date():
                            messagebox.showerror("Invalid Range", "You can't select a future date.")
                            return

                        print(f"Valid Range: {start_date} → {end_date}")

                    except Exception as e:
                        print("Date validation error:", e)
                        
                # tk.Label(company_row, text="Sync Branch", bg="white", fg="#666", font=header_font3).pack(anchor=tk.W)
                branch_image_path = ".\\lib\\images\\sync_btn.png"
                    
                try:
                    branch_image = Image.open(branch_image_path).convert("RGBA")
                    branch_image = branch_image.resize((20, 20), Image.Resampling.LANCZOS)
                    branch_image_tk = ImageTk.PhotoImage(branch_image)
                    print("image loaded")
                except Exception as e:
                    print(f"Error loading image: {e}")
                    branch_image_tk = None

                # Check the correct variable: branch_image_tk, not branch_image
                if branch_image_tk:
                    size = int(max(branch_image.size) * 1.5)

                    # Create canvas
                    canvas2 = tk.Canvas(company_row, width=size, height=size, bg="white", highlightthickness=0)
                    canvas2.pack(anchor=tk.W, padx=(10,0), side=tk.LEFT)

                    # Center coordinates
                    center_x = size // 2
                    center_y = size // 2

                    # Use the already-created PhotoImage and keep a reference
                    image_id = canvas2.create_image(center_x, center_y, image=branch_image_tk)
                    canvas2.image = branch_image_tk  # Keep a reference to prevent garbage collection

                    # Bind click event to the image
                    canvas2.tag_bind(image_id, "<Button-1>", lambda event: show_sync_frame(True))
                else:
                    branch_image_label = tk.Label(
                        company_row,
                        text="[IMG]",
                        bg="white",
                        fg="black",
                        font=label_font,
                        justify=tk.RIGHT
                    )
                    branch_image_label.pack(anchor=tk.E, padx=(10, 0), side=tk.LEFT)

                    
                    #     if "Map Now" not in branch["status"]:
                        
                    #         size = int(max(branch_image.size) * 1.5)  # Add padding for smooth rotation

                    #         # Create canvas
                    #         canvas2 = tk.Canvas(branch_right_frame, width=size, height=size, bg="white", highlightthickness=0)
                    #         canvas2.pack(anchor=tk.E, padx=(10,0), side=tk.LEFT)

                    #         # Center coordinates
                    #         center_x = size // 2
                    #         center_y = size // 2

                    #         # Display the image
                    #         image_tk = ImageTk.PhotoImage(branch_image)
                    #         image_id = canvas2.create_image(center_x, center_y, image=image_tk)

                    #         # Bind click event to the image
                    #         canvas2.tag_bind(image_id, "<Button-1>", lambda event,branch_data=branch, x=canvas2, size=size,image_tk=image_tk, angle=0: toggle_rotation(event,branch_data, x, size, image_tk, angle))

                        
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
                    # else:
                    #     branch_image_label = tk.Label(
                    #         branch_right_frame,
                    #         text="[IMG]",
                    #         bg="white",
                    #         fg="black",
                    #         font=label_font,
                    #         justify=tk.RIGHT
                    #     )
                    #     branch_image_label.pack(anchor=tk.E, padx=(10, 0), side=tk.LEFT)
                        

                # ---- RIGHT: SYNC PERIOD ----
                right_top = tk.Frame(top_panel, bg="white")
                right_top.pack(side=tk.RIGHT, padx=(0, 10))

                tk.Label(right_top, text="Sync Period", bg="white", fg="#666", font=header_font3)\
                    .pack(anchor="w")

                date_row = tk.Frame(right_top, bg="white")
                date_row.pack(pady=(5, 0), padx=(5, 10))

                constants.SYNC_START_DATE = tk.StringVar()
                constants.SYNC_END_DATE = tk.StringVar()
                

                # ================= MODULES SECTION =================
                bottom_panel = tk.Frame(lower_right_panel, bg="white")
                bottom_panel.pack(fill=tk.BOTH, expand=True, padx=0, pady=(20, 20))

                tk.Label(bottom_panel, text="Modules to Sync", bg="white", fg="#444", font=header_font3)\
                    .pack(anchor="w", pady=(0, 10))


                # Split left/right sections
                left_section = tk.Frame(bottom_panel, bg="white")
                left_section.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

                right_section = tk.Frame(bottom_panel, bg="white")
                right_section.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 10))
                
                def update_module_selection():
                    selected_modules = [module for module, var in self.checkbox_vars.items() if var.get()]
                    constants.SELECTED_MODULES = selected_modules
                    print("Selected modules:", selected_modules)
                    # You can add additional logic here to enable/disable the sync button based on selection

                def create_module_section(parent, title, modules):
                    section = tk.Frame(parent, bg="white")
                    section.pack(fill=tk.X, pady=10, padx=(10, 0))

                    # Store checkbox variables
                    vars_list = []

                    # Header row
                    header = tk.Frame(section, bg="white")
                    header.pack(fill=tk.X)

                    tk.Label(header, text=title, bg="white", fg="#1a73e8", font=header_font3)\
                        .pack(side=tk.LEFT)

                    # Select All label (clickable)
                    select_all_lbl = tk.Label(
                        header,
                        text="Select All",
                        bg="white",
                        fg="#1a73e8",
                        cursor="hand2"
                    )
                    select_all_lbl.pack(side=tk.RIGHT)

                    # Grid
                    grid = tk.Frame(section, bg="white")
                    grid.pack(fill=tk.X, pady=(5, 0))

                    for i, module in enumerate(modules):
                        var = tk.BooleanVar()
                        vars_list.append(var)

                        row = i // 2
                        col = i % 2

                        cb = ttk.Checkbutton(
                            grid,
                            text=module,
                            variable=var,
                            style='info.TCheckbutton',
                            command=update_module_selection
                        )
                        
                        cb.grid(row=row, column=col, padx=10, pady=5, sticky="ew")
                        self.checkbox_vars[module] = var
                        

                        grid.grid_columnconfigure(col, weight=1)

                    # ✅ Select All toggle logic
                    def toggle_all(event=None):
                        # Check if all are already selected
                        all_selected = all(v.get() for v in vars_list)

                        # Toggle: if all selected → unselect all, else select all
                        new_val = not all_selected
                        for v in vars_list:
                            v.set(new_val)
                        
                        selected_modules = [module for module, var in self.checkbox_vars.items() if var.get()]
                        constants.SELECTED_MODULES = selected_modules
                        print("Selected modules:", constants.SELECTED_MODULES)
                        

                    select_all_lbl.bind("<Button-1>", toggle_all)

                # ================= DATA MAPPING =================
                modules = list(constants.EXPORT_MODULES.items())

                if len(modules) >= 1:
                    create_module_section(left_section, modules[0][0], modules[0][1])

                if len(modules) >= 2:
                    create_module_section(right_section, modules[1][0], modules[1][1])

                if len(modules) >= 3:
                    create_module_section(left_section, modules[2][0], modules[2][1])

                if len(modules) >= 4:
                    create_module_section(right_section, modules[3][0], modules[3][1])
                


                def open_calendar(entry, var, start_date=None):
                    top = tk.Toplevel(entry)
                    top.overrideredirect(True)

                    # Position BELOW entry (like your dropdown)
                    x = entry.winfo_rootx()
                    y = entry.winfo_rooty() + entry.winfo_height()
                    top.geometry(f"+{x}+{y}")

        
                    cal = Calendar(
                        top, 
                        date_pattern="dd-mm-yy",
                        firstweekday="sunday",
                        
                        # --- Colors matching Tally Sync theme ---
                        background="#004494",              # deep blue matching sidebar
                        headersbackground="#004494",       # match the blue header in calendar
                        headersforeground="white",

                        normalbackground="white",
                        normalforeground="#333333",

                        weekendbackground="white",
                        weekendforeground="#333333",

                        othermonthbackground="white",      
                        othermonthforeground="#BBBBBB",    # lighter gray for other months

                        # --- Selected/Today - Orange highlight (matches the 28 in your image) ---
                        selectbackground="#FF9500",        # orange highlight like in the popup
                        selectforeground="white",

                        todaybackground="#FF9500",         # orange for today
                        todayforeground="white",

                        # --- Border ---
                        bordercolor="#004494",             # match header blue
                        borderwidth=2,

                        # --- Font ---
                        font=("Manrope", 10),
                        headersfont=("Manrope", 10, "bold")
                    )

                    cal.pack(padx=10, pady=10)

                    def select_date(event=None):
                        var.set(cal.get_date())
                        top.destroy()

                        # trigger your validation manually
                        validate_dates()

                    cal.bind("<<CalendarSelected>>", select_date)

                    # Optional: close if click outside
                    def close_on_focus_out(e):
                        top.destroy()

                    top.bind("<FocusOut>", close_on_focus_out)
                    top.focus_set()
                    

                def create_date_input(parent, var, open_calendar):
                    wrapper = tk.Frame(parent, bg="#D9D9D9", bd=0)
                    
                    inner = tk.Frame(wrapper, bg="white", bd=1, relief="solid")
                    inner.pack(fill="both", expand=True)

                    entry = tk.Entry(
                        inner,
                        textvariable=var,
                        width=10,
                        bd=0,
                        font=("Segoe UI", 10),
                        justify="center",
                        state="readonly",
                        readonlybackground="white",
                        fg="#333",
                        cursor="hand2"
                    )
                    entry.pack(side=tk.LEFT, padx=(8, 2), pady=4)

                    icon = tk.Label(
                        inner,
                        text="📅",
                        bg="white",
                        fg="#666",
                        font=("Segoe UI", 10),
                        cursor="hand2"
                    )
                    icon.pack(side=tk.RIGHT, padx=6)

                    wrapper.pack(side=tk.LEFT, padx=5)

                    # --- Click binding ---
                    entry.bind("<ButtonRelease-1>", lambda e: open_calendar(entry, var))
                    icon.bind("<Button-1>", lambda e: open_calendar(entry, var))

                    return entry
                
                current_date = datetime.now().strftime("%d-%m-%y")
                constants.SYNC_START_DATE.set(current_date)
                constants.SYNC_END_DATE.set(current_date)

                start_entry = create_date_input(date_row, constants.SYNC_START_DATE, open_calendar)

                tk.Label(date_row, text="to", bg="white", font=("Segoe UI", 10)).pack(side=tk.LEFT)

                end_entry = create_date_input(date_row, constants.SYNC_END_DATE, open_calendar)

                def on_start_change(*args):
                    try:
                        start_date = datetime.strptime(constants.SYNC_START_DATE.get(), DATE_FORMAT)
                        max_date = start_date + timedelta(days=30)
                        
                        if max_date.date() > datetime.now().date():
                            constants.SYNC_END_DATE.set(datetime.now().date().strftime(DATE_FORMAT))
                        else:
                            constants.SYNC_END_DATE.set(max_date.strftime(DATE_FORMAT))
                    except:
                        pass

                constants.SYNC_START_DATE.trace_add("write", on_start_change)

       
        
        def close_window():
            self.destroy()
            parent.destroy()
            
        def sync_single_branch(data):
            if constants.SELECTED_MODULES == []:
                messagebox.showerror("Sync Issue", "Please select at least one module to sync.")
                return 0
            
            if constants.SYNC_START_DATE.get() == "dd-mm-yy" or constants.SYNC_END_DATE.get() == "dd-mm-yy":
                messagebox.showerror("Invalid Date", "Please enter valid date.")
                return 0
            
            if "Ledgers" in constants.SELECTED_MODULES and len(constants.SELECTED_MODULES) == 1:
                messagebox.showerror("Sync Issue", "Please select at least one more module along with Ledgers for sync.")
                return 0
            # constants.ONE_SYNC = [
            #     {
            #         "chemist_id" : data["chemist_id"],
            #         "tally_company_guid" : data["company_guid"],
            #         "company_name" : str(data["status"]).replace("Mapped as ", ""),
            #         "branch_name" : data["name"]
            #     }
            # ]
            thread1 = threading.Thread(
                target=start_background_thread,
                args=(True,True),
                daemon=True
            )
            thread1.start()
            
            
            
            
        def map_branch_action(branch_name, overlay, branch={}):
            # print(branch_name)
            company_guid = '' 
            if branch == {}:
                branch = constants.CURRENT_BRANCH_SYNC_JSON
            for x in constants.TALLY_ACCOUNTS:
                if x["company_name"] == branch_name:
                    company_guid = x["company_guid"]
            # print('➡ tk_screen.py:599 company_guid:', company_guid)
            constants.COMPANY_MAPPING = [
                        {"chemist_id": branch["chemist_id"], "company_name": branch_name, "company_guid": company_guid, "mapping_type":"single"}
            ]
            # print('➡ tk_screen.py:605 constants.COMPANY_MAPPING:', constants.COMPANY_MAPPING)
            map_rx_companies()
            
            self.update()
            self.update_idletasks()
            print(f"Mapping branch: {branch_name}")
            overlay.destroy()
            create_main_content()
            
        def re_create_main_content():
            constants.STOP_THREAD = True
            create_main_content()
        
        def safe_after_cancel():
            self.after_cancel(animate_gif)
        
        def logout_account(overlay):
            logout()
            overlay.destroy()
            parent.show_frame("LoginScreen")
            [widget.delete(0, tk.END) for widget in parent.winfo_children() if isinstance(widget, tk.Entry)]
                 
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
            try:
                frame = frames[index]
                sync_label.configure(image=frame)
                next_index = (index + 3) % len(frames)
                # Store the after_id so we can cancel it later if needed
                # print(f"Animating frame {index}, next frame {next_index}")
                constants.ANIMATION_AFTER_ID = self.after(100, animate_gif, sync_label, frames, next_index)
            except tk.TclError:
            
                # Widget was destroyed, stop animation
                return

        def check_thread_status():
            while not constants.STOP_THREAD:
                # print("thead alive")
             
                time.sleep(0.5)
            re_create_main_content()

        def check_if_require_reboot():
            while not constants.REQUIRE_REBOOT:
                time.sleep(1)
            create_main_content()
            constants.REQUIRE_REBOOT = False
            check_if_require_reboot()
        
        def show_sync_frame(one_sync = False):
            
            if constants.SYNC_STAGE == 0:
                all_mapped = False
                mapres1 = constants.MAPPING_HISTORY["results"] if isinstance(constants.MAPPING_HISTORY, dict) and "results" in constants.MAPPING_HISTORY.keys() else []
                mapres = [x for x in mapres1 if x["is_mapped"] in ["False", False, 'false', ""]]
                
                available_companies = constants.TALLY_ACCOUNTS.copy()
                for x in constants.TALLY_ACCOUNTS:
                    for j in constants.MAPPING_HISTORY.get("results", []):
                        if x["company_guid"] == j["tally_company_guid"]:
                            available_companies.remove(x)
                all_mapped = len(available_companies) == 0 or len(mapres) == 0
                if all_mapped and len(mapres1) > 0:
                    constants.SYNC_STAGE = 1
                    constants.SYNC_BTN_TEXT = "Sync All"
                    print("stage 1")
                
                
                    for widget in right_panel.winfo_children():
                        if widget.winfo_exists():
                            widget.destroy()

                    print("sync increased")
                    # re_create_main_content()
                    self.after(100, re_create_main_content)
                else:
                    messagebox.showerror("Map Comany", "Please map all your companies first.")
            
            elif constants.SYNC_STAGE == 1:
                if constants.SELECTED_MODULES == []:
                    messagebox.showerror("Sync Issue", "Please select at least one module to sync.")
                    return 0
                
                if constants.SYNC_START_DATE.get() == "dd-mm-yy" or constants.SYNC_END_DATE.get() == "dd-mm-yy":
                    messagebox.showerror("Invalid Date", "Please enter valid date.")
                    return 0
                
                if "Ledgers" in constants.SELECTED_MODULES and len(constants.SELECTED_MODULES) == 1:
                    messagebox.showerror("Sync Issue", "Please select at least one more module along with Ledgers for sync.")
                    return 0
                def stop_thread_process():

                    messagebox.showerror("Tally Sync", "Sync Stopped Abnormally !!")
                    re_create_main_content()

                constants.STOP_THREAD = False
                thread1 = threading.Thread(
                    target=start_background_thread,
                    args=(True,one_sync),
                    daemon=True
                )
                # check_thread_status()
                thread1.start()
                
                for widget in right_panel.winfo_children():
                    if widget.winfo_exists():
                        widget.destroy()
                    
                # print()
                thread1 = threading.Thread(
                    target=check_thread_status,
                    daemon=True
                )
                # check_thread_status()
                thread1.start()


                # right_panel.config(background="#E7F6FF")
                right_panel2 = tk.Frame(right_panel, width=900, bg="#E7F6FF")
                right_panel2.pack(fill=tk.X)
                # title_bar = tk.Frame(right_panel2, width=900, bg="#E7F6FF")
                # title_bar.pack(fill=tk.X)
                # close_button = tk.Button(title_bar, text='x', font=header_font, command=close_window, bg='#E7F6FF', fg='#044C9D', borderwidth=0, relief=tk.SUNKEN)
                # close_button.pack(side=tk.RIGHT, padx=20, pady=(10,5))
                # sync_frame = tk.Frame(right_panel2, bg="white")
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
                
                gif_label = tk.Label(right_panel2, bg="#E7F6FF")
                gif_label.pack(expand=True, anchor=tk.N, pady=(60,20))
                
                
                # gif_label = tk.Label(right_panel2, bg="white")
                # gif_label.pack(expand=True, anchor=tk.N, pady=0)
                
                constants.CURRENT_BRANCH_SYNC = tk.StringVar(value="")
                # print('➡ tk_screen.py:731 constants.CURRENT_BRANCH_SYNC:', constants.CURRENT_BRANCH_SYNC)
                version_label = tk.Label(right_panel2, textvariable=constants.CURRENT_BRANCH_SYNC, bg="#E7F6FF", fg="Black", font=header_font2)
                version_label.pack(pady=(0, 20), padx=40, anchor=tk.N)

                
                sync_all_button = CTkButton(right_panel2, text="Stop", fg_color="#ED5A4A", text_color="white", hover_color='#ED5A4A', font=CTkFont(family='Manrope', size=16, weight='bold'), height=42, width=110, command=stop_thread_process)
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
            # self.after(0, re_create_main_content)
                
        

        # Custom fonts
        header_font = font.Font(family="Manrope", size=14, weight="bold")
        header_font2 = font.Font(family="Manrope", size=12, weight="bold")
        header_font3 = font.Font(family="Manrope", size=10, weight="bold")
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
                if widget.winfo_exists():
                    widget.destroy()
            
            def blur_background():
                x = self.winfo_rootx()
                y = self.winfo_rooty()
                w = self.winfo_width()
                h = self.winfo_height()

                screen = ImageGrab.grab(bbox=(x, y, x + w, y + h))
                return screen.filter(ImageFilter.GaussianBlur(4)), x, y, w, h
            
            def show_logout_popup(event):
                x = self.winfo_rootx()
                y = self.winfo_rooty()
                w = self.winfo_width()
                h = self.winfo_height()
                
                # Capture the screen area
                screen = ImageGrab.grab(bbox=(x, y, x + w, y + h))
                blurred_screen = screen.filter(ImageFilter.GaussianBlur(4))

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
                menu_frame = tk.Frame(overlay, bg="white", bd=2, relief="ridge", padx=10, pady=10)
                menu_frame.place(relx=0.5, rely=0.5, anchor="center")

                tk.Label(menu_frame, text="Are you sure you want to logout?",
                        font=header_font2, bg="white").pack(pady=(15, 10), padx=20)

                button_frame = tk.Frame(menu_frame, bg="white")
                button_frame.pack(pady=10)
                # print("2312")

                # YES button - Blue background with white text
                yes_button = tk.Button(button_frame, text="Yes", width=10, bg="#007BFF", fg="white",
                                    activebackground="#0056b3", activeforeground="white",
                                    relief="flat", font=label_font,
                                    command=lambda x=overlay:logout_account(x))
                yes_button.pack(side="left", padx=10)

                # NO button - White background with blue border and text
                no_button = tk.Button(button_frame, text="No", width=10, bg="white", fg="#007BFF",
                                    activebackground="#e6f2ff", activeforeground="#0056b3",
                                    highlightbackground="#007BFF", highlightthickness=2,
                                    bd=2, font=label_font,
                                    command=lambda x=overlay:x.destroy())
                no_button.pack(side="left", padx=10)

                # Function to close the overlay when clicking outside
                def on_click_outside(event):
                    if not overlay.winfo_containing(event.x_root, event.y_root):
                        overlay.destroy()

                # Bind click outside the menu to close the overlay
                overlay.bind("<Button-1>", on_click_outside)
                
            upper_left_panel = tk.Frame(left_panel, bg="#033D7E", height=150, width=200)
            upper_left_panel.pack(anchor=tk.N, fill=tk.X)

            # Tally Sync Utility header
            header_label = tk.Label(upper_left_panel, text="Tally Sync", bg="#033D7E", fg="white", font=header_font, justify=tk.LEFT)
            header_label.pack(pady=(35, 0), padx=30, anchor=tk.W)
            header_label = tk.Label(upper_left_panel, text="Utility", bg="#033D7E", fg="white", font=header_font, justify=tk.LEFT)
            header_label.pack(pady=(0, 5), padx=30, anchor=tk.W)

            version_label = tk.Label(upper_left_panel, text="Version 3.0", bg="#033D7E", fg="#7E878C", font=small_font)
            version_label.pack(pady=(0, 20), padx=30, anchor=tk.W)
            upper_left_panel.pack_propagate(False)

            lower_left_panel = tk.Frame(left_panel, bg="#004BA8", height=150, width=200)
            lower_left_panel.pack(anchor=tk.W)
            # Auto Sync Section
            # auto_sync_label = tk.Label(lower_left_panel, text="Auto Sync", bg="#004BA8", fg="white", font=label_font, justify=tk.LEFT)
            # auto_sync_label.pack(pady=(20, 5), padx=(10, 20), anchor=tk.W)
                # Auto Sync Section
            
            # auto_sync_frame = tk.Frame(lower_left_panel, bg="#004BA8", height=150, width=270)
            # auto_sync_frame.pack(pady=(10, 20), padx=0, fill=tk.X)

            # auto_sync_label = tk.Label(auto_sync_frame, text="Auto Sync", bg="#004BA8", fg="white", font=header_font2)
            # auto_sync_label.pack(padx=(30, 10), pady=(10, 20),side=tk.LEFT, anchor=tk.W)

            # auto_sync_status = tk.Label(auto_sync_frame, text="Off >", bg="#004BA8", fg="white", font=header_font2)
            # auto_sync_status.pack(padx=(20, 30), pady=(30, 20),side=tk.RIGHT, anchor=tk.E)
            
            # auto_sync_frame2 = tk.Frame(auto_sync_frame, bg="#004BA8", height=150, width=270)
            # auto_sync_frame2.pack(pady=(0, 20), padx=0, fill=tk.X, side=tk.RIGHT)

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
            auto_sync_var.set("Off")

            # Label styled to look like plain text
            # auto_sync_label = tk.Label(
            #     auto_sync_frame2,
            #     textvariable=auto_sync_var,
            #     bg="#004BA8",
            #     fg="#7E878C",
            #     font=label_font2,
            #     justify=tk.LEFT
            # )
            # def show_sync_menu(event):
            #     # Capture the screen
            #     x = self.winfo_rootx()
            #     y = self.winfo_rooty()
            #     w = self.winfo_width()
            #     h = self.winfo_height()
                
            #     # Capture the screen area
            #     screen = ImageGrab.grab(bbox=(x, y, x + w, y + h))
            #     blurred_screen = screen.filter(ImageFilter.GaussianBlur(5))

            #     # Create overlay window
            #     overlay = tk.Toplevel(self)
            #     overlay.geometry(f"{w}x{h}+{x}+{y}")
            #     overlay.overrideredirect(True)

            #     # Display blurred background
            #     bg_image = ImageTk.PhotoImage(blurred_screen)
            #     bg_label = tk.Label(overlay, image=bg_image)
            #     bg_label.image = bg_image
            #     bg_label.pack(fill="both", expand=True)

            #     # Centered menu
            #     menu_frame = tk.Frame(overlay, bg="white", bd=2, relief="ridge")
            #     menu_frame.place(relx=0.5, rely=0.5, anchor="center")

            #     tk.Label(menu_frame, text="Auto Sync", font=header_font2, bg="white").pack(pady=(10, 5), padx=40)

            #     options = ["Off", "30 min", "60 min", "90 min", "120 min", "180 min"]
                
            #     s = ttk.Style()                     # Creating style element
            #     s.configure('Wild.TRadiobutton',    # First argument is the name of style. Needs to end with: .TRadiobutton
            #             background="white",         # Setting background to our specified color above
            #             foreground='black',
            #             font=label_font2) 
                
            #     for option in options:
            #         rb = ttk.Radiobutton(menu_frame, text=option, value=option, variable=auto_sync_var, style = 'Wild.TRadiobutton', command= lambda opt=option, indicatoron=0, overlay=overlay:auto_sync_option_selected(opt, overlay))
            #         rb.pack(anchor="w", padx=(40,20), pady=5, ipadx=20)
                    
            #     # Function to close the overlay when clicking outside
            #     def on_click_outside(event):
            #         # Only destroy if click is outside of both the overlay and the menu_frame
            #         if not overlay.winfo_containing(event.x_root, event.y_root) == overlay and \
            #         event.widget not in menu_frame.winfo_children():
            #             overlay.destroy()

            #     # Bind click outside the menu to close the overlay
            #     overlay.bind("<Button-1>", on_click_outside)

            def show_sync_menu(event):
                # Capture only the app window
                x = self.winfo_rootx()
                y = self.winfo_rooty()
                w = self.winfo_width()
                h = self.winfo_height()

                # Capture the screen area
                screen = ImageGrab.grab(bbox=(x, y, x + w, y + h))
                blurred_screen = screen.filter(ImageFilter.GaussianBlur(4))  # Apply blur effect

                # Create overlay window
                overlay = tk.Toplevel(self)
                overlay.geometry(f"{w}x{h}+{x}+{y}")
                overlay.overrideredirect(True)

                # Display blurred background
                bg_image = ImageTk.PhotoImage(blurred_screen)
                bg_label = tk.Label(overlay, image=bg_image)
                bg_label.image = bg_image
                bg_label.pack(fill="both", expand=True)

                # Centered menu dimensions
                menu_w, menu_h = 250, 330
                menu_x = (w // 2) - (menu_w // 2)  # Center horizontally
                menu_y = (h // 2) - (menu_h // 2)  # Center vertically

                # Create a Canvas for rounded border
                radius = 20
                menu_canvas = tk.Canvas(overlay, width=menu_w, height=menu_h, bg="white", highlightthickness=0)
                menu_canvas.place(x=menu_x, y=menu_y)

                # Draw a smooth rounded rectangle with borders
                draw_rounded_rectangle(menu_canvas, 0, 0, menu_w, menu_h, radius, fill="white", border_color="grey", border_width=2)
                # round_rectangle(menu_canvas, 0, 0, menu_w, menu_h, radius, fill="white", outline="grey", width=2)

                # Frame inside canvas for menu content
                menu_frame = tk.Frame(overlay, bg="white")
                menu_frame.place(x=menu_x + 10, y=menu_y + 10)

                tk.Label(menu_frame, text="Auto Sync", font=("Manrope", 12, "bold"), bg="white").pack(pady=(10, 5), padx=40)

                # Options
                options = ["Off", "30 min", "60 min", "90 min", "120 min", "180 min"]
                s = ttk.Style()
                s.configure('Wild.TRadiobutton', background="white", foreground='black', font=("Manrope", 11))

                for option in options:
                    pady_custom = (5,20) if option == options[-1] else 5
                    pady_custom = 5
                    rb = ttk.Radiobutton(menu_frame, text=option, value=option, variable=auto_sync_var,
                                        style='Wild.TRadiobutton', command=lambda opt=option: auto_sync_option_selected(opt, overlay))
                    rb.pack(anchor="w", padx=(40, 20), pady=pady_custom, ipadx=20)

                # Close overlay when clicking outside
                def on_click_outside(event):
            #         # Only destroy if click is outside of both the overlay and the menu_frame
                    if not overlay.winfo_containing(event.x_root, event.y_root) == overlay and \
                    event.widget not in menu_frame.winfo_children():
                        overlay.destroy()
                
                overlay.bind("<Button-1>", on_click_outside)

            # Corrected Function for Smooth Rounded Border
            def draw_rounded_rectangle(canvas, x1, y1, x2, y2, radius, fill, border_color, border_width):
                """Draws a smooth rounded rectangle without missing corners or random lines."""
                points = [
                    (x1 + radius, y1), (x2 - radius, y1), (x2, y1),
                    (x2, y1 + radius), (x2, y2 - radius), (x2, y2),
                    (x2 - radius, y2), (x1 + radius, y2), (x1, y2),
                    (x1, y2 - radius), (x1, y1 + radius), (x1, y1)
                ]
                # points = [
                #     (x1 + radius, y1), (x2 - radius, y1),
                #     (x2, y1 + radius), (x2, y2 - radius), 
                #     (x2 - radius, y2), (x1 + radius, y2), 
                #     (x1, y2 - radius), (x1, y1 + radius), 
                # ]
                # print('➡ tk_screen.py:1149 points:', points)

                # Create rounded shape
                canvas.create_polygon(points, smooth=True, fill=fill, outline=border_color, width=border_width)

            def round_rectangle(canvas, x1, y1, x2, y2, radius=25, **kwargs):
                    
                points = [x1+radius, y1,
                        x1+radius, y1,
                        x2-radius, y1,
                        x2-radius, y1,
                        x2, y1,
                        x2, y1+radius,
                        x2, y1+radius,
                        x2, y2-radius,
                        x2, y2-radius,
                        x2, y2,
                        x2-radius, y2,
                        x2-radius, y2,
                        x1+radius, y2,
                        x1+radius, y2,
                        x1, y2,
                        x1, y2-radius,
                        x1, y2-radius,
                        x1, y1+radius,
                        x1, y1+radius,
                        x1, y1]
                # print('➡ tk_screen.py:1330 points:', points)

                canvas.create_polygon(points, **kwargs, smooth=True)

            # my_rectangle = round_rectangle(50, 50, 150, 100, radius=20, fill="blue")
            # Attach function to Canvas class
            tk.Canvas.draw_rounded_rectangle = draw_rounded_rectangle
            tk.Canvas.round_rectangle = round_rectangle
            # auto_sync_label.pack(pady=(0, 20), padx=10, anchor=tk.W)
            # auto_sync_label.pack(padx=(20, 0), pady=(30, 20),side=tk.LEFT, anchor=tk.W)

            # Dropdown menu
            # auto_sync_menu = tk.Menu(auto_sync_frame2, tearoff=0, bg="white", fg="black", font=label_font)
            # for option in ["Off",
            #                 # "1 min",
            #                 "30 min", "60 min", "90 min", "120 min", "180 min"]:
            #     auto_sync_menu.add_command(label=option, command=lambda opt=option: auto_sync_option_selected(opt))

            # Bind right-click or left-click to show the menu
            # auto_sync_label.bind("<Button-1>", lambda e: auto_sync_menu.post(e.x_root, e.y_root))
            # auto_sync_label.bind("<Button-1>", show_sync_menu)

            # auto_sync_label = tk.Label(auto_sync_frame2, text=">", bg="#004BA8", fg="#7E878C", font=header_font2)
            # auto_sync_label.pack(padx=(0, 15), pady=(30, 20),side=tk.RIGHT, anchor=tk.E)


            lower_left_panel.pack_propagate(False)

            # User Info Section
            constants.MOBILE_VAR = tk.StringVar(value=constants.MOBILE)
            user_label = tk.Label(left_panel, textvariable=constants.MOBILE_VAR, bg="#004BA8", fg="white", font=header_font2, justify=tk.LEFT)
            user_label.pack(pady=(210, 2), padx=30, anchor=tk.W)

            # logout_label = tk.Button(left_panel, text="Logout >", bg="#004BA8", fg="white",
            #                         highlightbackground='#004BA8', highlightcolor='#004BA8', borderwidth=0,font=label_font2, justify=tk.LEFT, relief=tk.SUNKEN, command=show_logout_popup)
            # logout_label.pack(pady=(0, 20), padx=25, anchor=tk.W)
            logout_label = tk.Label(left_panel, text="Logout >", bg="#004BA8", fg="white",font=label_font2, justify=tk.LEFT)
            logout_label.pack(pady=(0, 15), padx=30, anchor=tk.W)
            logout_label.bind("<Button-1>", show_logout_popup)

            left_panel.pack_propagate(False)
        
        # try:
        #     self.iconbitmap(".\\lib\\images\\app_icon.ico")
        #     print("Window icon loaded")
        # except Exception as e:
        #     print(f"Error loading window icon: {e}")
        

        drag_layer = tk.Frame(
            self,
            # bg="#0CA1F6",
            bg="white",
            height=35
        )
        drag_layer.pack(side=tk.TOP, fill=tk.X)
        
        
        # Load and display icon in title bar
        icon_path = "./lib/images/logo2.ico"  # or use .png
        try:
            icon_image = Image.open(icon_path)
            icon_image = icon_image.resize((20, 20), Image.Resampling.LANCZOS)
            icon_image_tk = ImageTk.PhotoImage(icon_image)
            
            icon_label = tk.Label(
                drag_layer,
                image=icon_image_tk,
                bg="white"
            )
            icon_label.image = icon_image_tk  # Keep reference
            icon_label.pack(side=tk.LEFT, padx=(15, 5), pady=(3, 0))
            print("Title bar icon loaded")
        except Exception as e:
            print(f"Error loading title bar icon: {e}")

        # Title (left side)
        title_label = tk.Label(
            drag_layer,
            text="Tally Sync Utility",
            # bg="#0CA1F6",
            bg="white",
            # fg="white",
            fg="black",
            font=header_font5b
        )
        title_label.pack(side=tk.LEFT, padx=(5, 0), pady=(3,0))

        # Close button (right side)
        close_button = tk.Label(
            drag_layer,
            text="✕",
            # bg="#0CA1F6",
            bg="white",
            # fg="white",
            fg="black",
            font=("Segoe UI", 8, "bold"),
            cursor="hand2"
        )
        close_button.pack(side=tk.RIGHT, padx=15, pady=3)
    
        def on_close_enter(e):
            close_button.config(bg="#E81123")  # Windows red

        def on_close_leave(e):
            # close_button.config(bg="#0CA1F6")
            close_button.config(bg="white")

        close_button.bind("<Enter>", on_close_enter)
        close_button.bind("<Leave>", on_close_leave)

        drag_layer.bind("<Button-1>", self.controller.start_move)
        drag_layer.bind("<B1-Motion>", self.controller.do_move)

        # Also allow dragging from title text
        title_label.bind("<Button-1>", self.controller.start_move)
        title_label.bind("<B1-Motion>", self.controller.do_move)
        
        close_button.bind("<Button-1>", lambda e: close_window())
            
        left_panel = tk.Frame(self, bg="#004BA8", width=220, height=600)
        left_panel.pack(side=tk.LEFT, fill=tk.Y)
        
        
        left_panel.pack_propagate(False)
        right_panel = tk.Frame(self, bg="white", width=600, height=600)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        
        create_left_content()
        create_main_content()
        
        # if constants.MOBILE == "":
        #     thread1 = threading.Thread(
        #         target=check_login_status,
        #         daemon=True
        #     )
        #     # check_thread_status()
        #     thread1.start()


class LogViewerApp:
    def __init__(self, main_app=None):
        self.log_manager = LogManagerObj
        self.root = None
        self.main_app = main_app
        
        # Register the hotkey to show the viewer
        # keyboard.add_hotkey('shift+l', self.show_log_viewer)
        
        # Start a thread to handle the log clearing
        # self.log_manager.clear_thread.start()
    
    def show_log_viewer(self):
        """Show the log viewer window when hotkey is pressed"""
        if self.root is not None and self.root.winfo_exists():
            # If window exists, just focus it
            self.root.lift()
            self.root.focus_force()
            return
        
        # Create a new window
        self.root = tk.Toplevel() if self.main_app else tk.Tk()
        self.root.title("Log Manager")
        self.root.geometry("800x600")
        self.root.iconbitmap("./lib/images/logo2.ico")
        
        # style = ThemedStyle(self.root)
        # print(style.get_themes())
        # style.theme_use("adapta")
        self.root.configure(bg="white")  # Set background to blue
        # self.overrideredirect(True)
        
        
        # Set up the widgets
        self.create_widgets()
        
        # Handle window close event
        # self.root.protocol("WM_DELETE_WINDOW", self.)
    
    def hide_log_viewer(self):
        """Hide the log viewer window"""
        if self.root:
            # self.root.withdraw()
            self.root.destroy()
    
    def create_widgets(self):
        # Create notebook with tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)


        
        # notebook.configure(bg="white")
        
        # Create decrypt logs tab
        # decrypt_frame = ttk.Frame(notebook)
        # notebook.add(decrypt_frame, text="View Decrypted Logs")
        
        # Create management tab
        # manage_frame = ttk.Frame(notebook)
        # notebook.add(manage_frame, text="Log Management")
        
        # Configure decrypt logs tab
        self.setup_decrypt_tab(notebook)
        
        # Configure management tab
        # self.setup_management_tab(manage_frame)
    
    def setup_decrypt_tab(self, parent):
        # Log text area
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        # frame.configure(bg="white")
        
        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        refresh_btn = ttk.Button(btn_frame, text="Refresh Logs", command=self.refresh_logs)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = ttk.Button(btn_frame, text="Clear Logs Now", command=self.clear_logs)
        clear_btn.pack(side=tk.RIGHT)
        
        # Last cleared info
        # self.last_cleared_label = ttk.Label(frame, text="")
        # self.last_cleared_label.pack(pady=10)
        # self.update_last_cleared_info()
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, bg="white")
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Initial load of logs
        self.refresh_logs()
        self.log_text.configure(state=tk.DISABLED)
    
    def setup_management_tab(self, parent):
        # frame = ttk.Frame(parent)
        # frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        # frame.configure(bg="white")
        
        # Clear logs button
        clear_btn = ttk.Button(parent, text="Clear Logs Now", command=self.clear_logs)
        clear_btn.pack(pady=10)
        
        # Last cleared info
        self.last_cleared_label = ttk.Label(parent, text="")
        self.last_cleared_label.pack(pady=10)
        self.update_last_cleared_info()
        
        # Add a log entry frame
        entry_frame = ttk.LabelFrame(parent, text="Add Log Entry")
        entry_frame.pack(fill=tk.X, pady=20, padx=10)
        
        self.log_entry = ttk.Entry(entry_frame, width=50)
        self.log_entry.pack(side=tk.LEFT, padx=5, pady=10, fill=tk.X, expand=True)
        
        add_btn = ttk.Button(entry_frame, text="Add Log", command=self.add_log)
        add_btn.pack(side=tk.RIGHT, padx=5, pady=10)
    
    def refresh_logs(self):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        logs = self.log_manager.read_logs()
        for log in logs:
            self.log_text.insert(tk.END, f"{log}\n")
        self.log_text.configure(state=tk.DISABLED)
    
    def clear_logs(self):
        if messagebox.askyesno("Confirmation", "Are you sure you want to clear all logs?"):
            if self.log_manager.clear_logs():
                messagebox.showinfo("Success", "Logs cleared successfully")
                
                self.log_text.configure(state=tk.NORMAL)
                self.refresh_logs()
                self.update_last_cleared_info()
                self.log_text.configure(state=tk.DISABLED)
            else:
                messagebox.showerror("Error", "Failed to clear logs")
    
    def add_log(self):
        message = self.log_entry.get()
        if not message:
            messagebox.showwarning("Warning", "Please enter a log message")
            return
        
        if self.log_manager.write_log(message):
            self.log_entry.delete(0, tk.END)
            self.refresh_logs()
            messagebox.showinfo("Success", "Log added successfully")
        else:
            messagebox.showerror("Error", "Failed to add log")
    
    def update_last_cleared_info(self):
        last_date = self.log_manager.get_last_clear_date_formatted()
        # self.last_cleared_label.config(text=f"Logs last cleared on: {last_date}")
    
# LogViewerApp()
# Run the application
if __name__ == "__main__":
    app = App()
    app.mainloop()
    freeze_support()
