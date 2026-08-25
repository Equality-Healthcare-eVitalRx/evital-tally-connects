import json
import sys
import traceback

from tkcalendar import Calendar
import ctypes
from ctypes import wintypes
from datetime import datetime, timedelta
from multiprocessing.dummy import freeze_support
from pathlib import Path
import threading
import time
import tkinter as tk
from tkinter import font, ttk
from tkinter import messagebox
from tkinter import scrolledtext
from PIL import Image, ImageTk, ImageSequence, ImageGrab, ImageFilter
from customtkinter import CTkButton, CTkFont, CTkFrame, CTkLabel
import pyglet
from functions import (
    login,
    login_with_apikey,
    logout,
    get_all_mapping_details,
    constants,
    get_sync_date_value,
    get_valid_sync_date,
    start_background_thread,
    start_thread,
    map_rx_companies,
    remove_company_mapping,
    encrypt_data,
    decrypt_data,
    LogManagerObj,
)
from lib.import_export_data import (
    get_tally_companies,
    get_entity_sync_history,
    is_tally_reachable,
)

pyglet.options["win32_gdi_font"] = True
fontpath = Path(__file__).parent / "lib/fonts/static/Manrope-Regular.ttf"
themepath = Path(__file__).parent / "lib/fonts/breeze/breeze.tcl"
try:
    if fontpath.is_file():
        pyglet.font.add_file(str(fontpath))
except Exception:
    pass  # Use default font if custom font cannot be loaded
try:  # >= win 8.1
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:  # win 8.0 or less
    ctypes.windll.user32.SetProcessDPIAware()

import ctypes


def _log_exception(exc_type, exc_value, exc_traceback):
    """Write any uncaught exception to the app log so it shows in the log viewer."""
    try:
        text = "".join(
            traceback.format_exception(exc_type, exc_value, exc_traceback)
        )
        LogManagerObj.write_log(f"❌ Unhandled exception:\n{text}")
    except Exception:
        pass
    if exc_type is not SystemExit:
        traceback.print_exception(exc_type, exc_value, exc_traceback)


def _thread_exception_logger(args):
    """Write uncaught exceptions raised inside worker threads to the app log."""
    _log_exception(args.exc_type, args.exc_value, args.exc_traceback)


sys.excepthook = _log_exception
threading.excepthook = _thread_exception_logger


class MARGINS(ctypes.Structure):
    _fields_ = [
        ("cxLeftWidth", wintypes.INT),
        ("cxRightWidth", wintypes.INT),
        ("cyTopHeight", wintypes.INT),
        ("cyBottomHeight", wintypes.INT),
    ]


def open_log_window(parent, event, LogViewerAppObj):
    # logObj = LogManagerObj()
    if constants.SHOW_LOG_WINDOW:
        LogViewerAppObj.hide_log_viewer()
        # print("hide")
        constants.SHOW_LOG_WINDOW = False
    else:
        # print("show")
        constants.SHOW_LOG_WINDOW = True
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
            ctypes.windll.user32.SendMessageW(
                hwnd, 0x000B, True, 0
            )  # WM_SETREDRAW = 0x000B
            ctypes.windll.user32.RedrawWindow(
                hwnd, None, None, 0x85
            )  # RDW_INVALIDATE | RDW_UPDATENOW | RDW_ALLCHILDREN

        def close_window():
            """Close the application."""
            self.destroy()

        def on_closing():
            if constants.SYNC_RUNNING:
                messagebox.showwarning(
                    "Sync in Progress",
                    "Cannot close the app while data is being imported. Please wait for the sync to finish or stop it first.",
                )
                return
            self.destroy()

        self.frames = {}

        self.geometry("950x650")
        self.configure(bg="#044C9D")  # Set background to blue
        self.overrideredirect(False)

        hwnd = self.winfo_id()

        # Ensure the window has a taskbar presence
        # ctypes.windll.user32.SetWindowLongW(hwnd, -8, 0)  # Set parent to None (GWLP_HWNDPARENT = -8)
        # ctypes.windll.user32.SetWindowLongW(hwnd, -20,
        #                                     ctypes.windll.user32.GetWindowLongW(hwnd, -20) & ~0x00000080)  # Remove WS_EX_TOOLWINDOW
        # ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0020)  # Apply changes (SWP_FRAMECHANGED)

        user32 = ctypes.windll.user32
        x, y = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        x = (x - 900) // 2
        y = (y - 600) // 2

        self.geometry(f"+{str(int(x))}+{str(int(y))}")

        self.resizable(0, 0)

        # The OS/CustomTkinter can silently rescale the window (e.g. when it
        # is dragged onto a monitor with a different DPI). Remember the
        # intended size and snap back to it whenever the real size drifts.
        self._intended_geometry = "950x650"
        self._geometry_check_job = None
        self._follow_overlays = []
        self._last_root_pos = None
        self.bind("<Configure>", self._on_root_configure)

        self.iconbitmap("./lib/images/logo2.ico")
        self.title("eVitalRx Tally Connects")
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

        # # Replace the existing WinAPI block in __init__ with this:
        # hwnd = self.winfo_id()
        # ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
        # ex_style &= ~0x00000080  # Remove WS_EX_TOOLWINDOW
        # ex_style |= 0x00040000   # Add WS_EX_APPWINDOW
        # ctypes.windll.user32.SetWindowLongW(hwnd, -20, ex_style)
        # ctypes.windll.user32.SetWindowLongW(hwnd, -8, 0)
        # ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0,
        #                                 0x0020 | 0x0002 | 0x0001)

        self.update()
        self.update_idletasks()

    def report_callback_exception(self, exc, val, tb):
        """Log exceptions raised inside Tkinter callbacks."""
        if isinstance(exc, tk.TclError) and "invalid command name" in str(val):
            return  # benign: widget was destroyed while a pending event fired
        _log_exception(exc, val, tb)
        super().report_callback_exception(exc, val, tb)

    def apply_intended_geometry(self, geometry):
        """Set the window size and remember it as the size to enforce."""
        self._intended_geometry = geometry
        self.geometry(geometry)

    def register_follow_overlay(self, win):
        """Keep a borderless Toplevel dialog (blurred popup etc.) glued to
        the main window while it is dragged around the screen."""
        if win not in self._follow_overlays:
            self._follow_overlays.append(win)

    def _on_root_configure(self, event):
        # Only react to the root window itself, and debounce so a burst of
        # Configure events (drag/resize/DPI change) triggers one check.
        if event.widget is not self:
            return

        try:
            x, y = self.winfo_x(), self.winfo_y()
        except tk.TclError:
            return
        prev = self._last_root_pos
        self._last_root_pos = (x, y)
        if prev is not None and (x, y) != prev:
            dx, dy = x - prev[0], y - prev[1]
            for overlay in list(self._follow_overlays):
                try:
                    if overlay.winfo_exists():
                        overlay.geometry(
                            f"+{overlay.winfo_x() + dx}+{overlay.winfo_y() + dy}"
                        )
                    else:
                        self._follow_overlays.remove(overlay)
                except tk.TclError:
                    try:
                        self._follow_overlays.remove(overlay)
                    except ValueError:
                        pass

        if self._geometry_check_job is not None:
            return
        try:
            self._geometry_check_job = self.after(250, self._enforce_geometry)
        except tk.TclError:
            # App shutting down - nothing to enforce anymore.
            pass

    def _enforce_geometry(self):
        self._geometry_check_job = None
        try:
            cur_w, cur_h = self.winfo_width(), self.winfo_height()
            intended_w, intended_h = (
                int(part) for part in self._intended_geometry.split("x")
            )
            # Ignore tiny deviations from Tk/CustomTkinter scaling rounding -
            # enforcing those would fight the toolkit in a resize loop.
            if abs(cur_w - intended_w) > 4 or abs(cur_h - intended_h) > 4:
                self.geometry(self._intended_geometry)
        except (tk.TclError, ValueError):
            pass

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
        ctypes.windll.user32.SendMessageW(
            hwnd, 0x000B, True, 0
        )  # WM_SETREDRAW = 0x000B
        ctypes.windll.user32.RedrawWindow(
            hwnd, None, None, 0x85
        )  # RDW_INVALIDATE | RDW_UPDATENOW | RDW_ALLCHILDREN

    def add_shadow(self):
        """Applies a drop shadow effect to the window without making it fully white."""
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        # Do NOT set WS_EX_LAYERED here - layered windows are composited in
        # software on Windows, which makes dragging the window extremely
        # laggy. DWM draws the shadow without needing the layered style.
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 2, ctypes.byref(ctypes.c_int(2)), ctypes.sizeof(ctypes.c_int(2))
        )

    def close_window(self):
        self.destroy()

    def initialize_screens(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.frames["LoadingScreen"] = LoadingScreen(self, self)
        self.frames["LoginScreen"] = LoginScreen(self, self)
        self.frames["Dashboard"] = Dashboard(self, self)

        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

    def show_frame(self, frame_name, **kwargs):
        """Show a frame by name."""
        if frame_name in self.frames:
            self.frames[frame_name].destroy()
            del self.frames[frame_name]

        if frame_name == "LoginScreen":
            self.frames[frame_name] = LoginScreen(self, self)
        elif frame_name == "LoadingScreen":
            self.frames[frame_name] = LoadingScreen(self, self)
        elif frame_name == "Dashboard":
            self.frames[frame_name] = Dashboard(self, self)
        elif frame_name == "SyncHistory":
            self.frames[frame_name] = SyncHistoryScreen(self, self)

        frame = self.frames[frame_name]
        # self.clear_frame_inputs(frame)
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
            # elif isinstance(widget, tk.OptionMenu):
            #     widget.set("")  # Reset dropdown selection if applicable
            elif isinstance(widget, tk.Frame):
                self.clear_frame_inputs(widget)  # Recursively clear nested frames


class LoadingScreen(tk.Frame):
    """Placeholder shown while the cached session is restored and Tally
    connectivity is checked - keeps the window painted and responsive
    instead of freezing on a blank login page. Reuses the login
    screen's layout so it feels native."""

    def __init__(self, parent, controller):
        super().__init__(parent, bg="#044C9D")
        self.controller = controller
        parent.title("eVital<>Tally Connects")

        header_font2b = font.Font(family="Manrope", size=13, weight="bold")
        header_font3 = font.Font(family="Manrope", size=12)

        # Left panel - same artwork as the login screen
        left_panel = tk.Frame(self, bg="#044C9D")
        left_panel.pack(side=tk.LEFT, fill=tk.Y)
        try:
            image = Image.open("./lib/images/login_panel.jpg").resize(
                (500, 600), Image.Resampling.LANCZOS
            )
            image_tk = ImageTk.PhotoImage(image)
            image_label = tk.Label(left_panel, image=image_tk, bg="#004BA8")
            image_label.image = image_tk  # avoid garbage collection
            image_label.pack(pady=(0, 10))
        except Exception:
            pass

        # Right panel - matches the login form styling
        right_panel = tk.Frame(self, bg="white", width=450, height=650)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        right_panel.pack_propagate(False)

        tk.Label(
            right_panel,
            text="Please wait...",
            bg="white",
            font=header_font2b,
            justify=tk.LEFT,
        ).pack(pady=(85, 0), padx=(60, 55), anchor=tk.W)
        tk.Label(
            right_panel,
            text="Checking Tally connection",
            bg="white",
            fg="#6B7280",
            font=header_font3,
            justify=tk.LEFT,
        ).pack(pady=(6, 0), padx=(60, 55), anchor=tk.W)

        progress = ttk.Progressbar(right_panel, mode="indeterminate", length=330)
        progress.pack(pady=(30, 0), padx=(60, 55), anchor=tk.W)
        progress.start(12)

        # Stop the animation before the frame goes away, otherwise the
        # pending after() callback spams "invalid command name" errors.
        def _on_destroy(event):
            if event.widget is self:
                try:
                    progress.stop()
                except tk.TclError:
                    pass

        self.bind("<Destroy>", _on_destroy)


class LoginScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller
        parent.title("eVital<>Tally Connects")
        LogViewerAppObj = LogViewerApp(parent)

        self.bind_all(
            "<Control-d>", lambda e: open_log_window(parent, e, LogViewerAppObj)
        )

        header_font = font.Font(family="Manrope", size=14, weight="bold")
        header_font1 = font.Font(family="Manrope", size=14)
        header_font2 = font.Font(family="Manrope", size=13)
        header_font2b = font.Font(family="Manrope", size=13, weight="bold")
        header_font3 = font.Font(family="Manrope", size=12)
        header_font4 = font.Font(family="Manrope", size=11)
        header_font4b = font.Font(family="Manrope", size=11, weight="bold")
        header_font5 = font.Font(family="Manrope", size=8)
        header_font5b = font.Font(family="Manrope", size=8, weight="bold")

        def close_window():
            self.destroy()
            parent.destroy()

        def check_login():
            if self.login_mode.get() == "apikey":
                check_apikey_login()
            else:
                entity = (
                    "chemist" if str(selected_entity.get()) == "eVitalRx" else "distributor"
                )
                res = login(mobile_entry.get(), password_entry.get(), entity)
                print(res, "login response")
                if res == 1:
                    show_port_popup()
                    print("port popup")

        def check_apikey_login():
            entity = (
                "chemist" if str(selected_entity.get()) == "eVitalRx" else "distributor"
            )
            res = login_with_apikey(apikey_entry.get(), entity)
            print(res, "apikey login response")
            if res == 1:
                show_port_popup()
                print("port popup")

        def toggle_login_mode():
            current = self.login_mode.get()
            if current == "password":
                self.login_mode.set("apikey")
                mobile_label.pack_forget()
                mobile_frame.pack_forget()
                mobile_line.pack_forget()
                password_label.pack_forget()
                password_frame.pack_forget()
                password_line.pack_forget()
                apikey_label.pack(pady=(20, 0), padx=(60, 55), anchor=tk.W)
                apikey_frame.pack(pady=4, padx=65, anchor=tk.W, fill=tk.X)
                apikey_line.pack(pady=(0, 20), padx=65, anchor=tk.W, fill=tk.X)
                login_label.config(text="API Key Login")
                apikey_entry.focus_set()
            else:
                self.login_mode.set("password")
                apikey_label.pack_forget()
                apikey_frame.pack_forget()
                apikey_line.pack_forget()
                mobile_label.pack(pady=(20, 0), padx=(60, 55), anchor=tk.W)
                mobile_frame.pack(pady=4, padx=65, anchor=tk.W, fill=tk.X)
                mobile_line.pack(pady=(0, 10), padx=65, anchor=tk.W, fill=tk.X)
                password_label.pack(pady=(10, 0), padx=(60, 55), anchor=tk.W)
                password_frame.pack(pady=4, padx=65, anchor=tk.W, fill=tk.X)
                password_line.pack(pady=(0, 20), padx=65, anchor=tk.W, fill=tk.X)
                login_label.config(text="Login with")
                mobile_entry.focus_set()

        def update_tally_port(overlay, port, host):
            if not is_tally_reachable(host=host, port=port):
                messagebox.showerror(
                    "Tally Configuration",
                    "Could not connect to Tally at "
                    + str(host)
                    + ":"
                    + str(port)
                    + ".\nMake sure Tally is running and the Host/Port are correct.",
                )
                return

            constants.TALLY_PORT = port
            constants.HOST = host
            constants.TALLY_URL = "http://" + str(host) + ":"
            print(constants.TALLY_URL + str(constants.TALLY_PORT), "changed")

            if constants.LOGIN_MODE == "apikey":
                # Debug session (API key login) is not persisted - keep
                # connection settings in memory only. MOBILE stays as the
                # entity_code captured at login.
                if constants.MOBILE_VAR is not None:
                    constants.MOBILE_VAR.set(constants.MOBILE)
                overlay.destroy()
                [
                    widget.delete(0, tk.END)
                    for widget in parent.winfo_children()
                    if isinstance(widget, tk.Entry)
                ]
                get_all_mapping_details()
                get_tally_companies()
                # parent.update()
                parent.show_frame("Dashboard")
                return

            constants.MOBILE = mobile_entry.get()
            with open("./lib/app_cache.txt") as data_file:
                # data = json.load(data_file)
                data = decrypt_data(data_file.read())
            print(data)
            data["mobile"] = constants.MOBILE
            data["tally_port"] = constants.TALLY_PORT
            data["tally_host"] = constants.HOST
            with open("./lib/app_cache.txt", "w") as json_file:
                # json.dump(data, json_file)
                json_file.write(encrypt_data(data))
            print(data)
            if constants.MOBILE_VAR is not None:
                constants.MOBILE_VAR.set(constants.MOBILE)

            overlay.destroy()
            [
                widget.delete(0, tk.END)
                for widget in parent.winfo_children()
                if isinstance(widget, tk.Entry)
            ]
            get_all_mapping_details()
            get_tally_companies()
            # parent.update()
            parent.show_frame("Dashboard")

        def show_port_popup():
            x = self.winfo_rootx()
            y = self.winfo_rooty()
            w = self.winfo_width()
            h = self.winfo_height()

            def validate(
                action,
                index,
                value_if_allowed,
                prior_value,
                text,
                validation_type,
                trigger_type,
                widget_name,
            ):
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

            vcmd = (
                self.register(validate),
                "%d",
                "%i",
                "%P",
                "%s",
                "%S",
                "%v",
                "%V",
                "%W",
            )

            # Capture the screen area
            screen = ImageGrab.grab(bbox=(x, y, x + w, y + h))
            blurred_screen = screen.filter(ImageFilter.GaussianBlur(4))

            # Create overlay window
            overlay = tk.Toplevel(self)
            overlay.geometry(f"{w}x{h}+{x}+{y}")
            overlay.overrideredirect(True)
            self.winfo_toplevel().register_follow_overlay(overlay)

            # Display blurred background
            bg_image = ImageTk.PhotoImage(blurred_screen)
            bg_label = tk.Label(overlay, image=bg_image)
            bg_label.image = bg_image
            bg_label.pack(fill="both", expand=True)

            # Centered menu
            menu_frame = tk.Frame(
                overlay, bg="white", bd=2, relief="ridge", padx=10, pady=10
            )
            menu_frame.place(relx=0.5, rely=0.5, anchor="center")

            tk.Label(
                menu_frame, text="Tally Configuration", font=header_font2, bg="white"
            ).pack(pady=(20, 20), padx=40)

            # host Entry
            button_frame2 = tk.Frame(menu_frame, bg="white")
            button_frame2.pack(pady=(7, 15))

            host_label = tk.Label(
                button_frame2, text="Tally Host", font=header_font4, bg="white"
            )
            host_label.pack(pady=(0, 10), padx=(10, 20), side=tk.LEFT)

            tally_host_var = tk.StringVar(value=constants.HOST)
            host_entry = tk.Entry(
                button_frame2,
                textvariable=tally_host_var,
                font=header_font3,
                width=13,
                justify="center",
                bd=1,
                relief="solid",
            )
            host_entry.pack(pady=(0, 10), padx=(10, 20), side=tk.RIGHT)
            host_entry.pack_propagate(False)

            # Port Entry
            button_frame = tk.Frame(menu_frame, bg="white")
            button_frame.pack(pady=(7, 15))

            tally_port_var = tk.StringVar(value=constants.TALLY_PORT)
            port_label = tk.Label(
                button_frame, text="Tally Port", font=header_font4, bg="white"
            )
            port_label.pack(pady=(0, 10), padx=(10, 20), side=tk.LEFT)

            port_entry = tk.Entry(
                button_frame,
                textvariable=tally_port_var,
                font=header_font3,
                validate="key",
                validatecommand=vcmd,
                width=13,
                justify="center",
                bd=1,
                relief="solid",
            )
            port_entry.pack(pady=(0, 10), padx=(10, 20), side=tk.RIGHT)
            port_entry.pack_propagate(False)

            # YES button - Blue background with white text
            yes_button2 = CTkButton(
                menu_frame,
                text="Update",
                width=100,
                height=36,
                corner_radius=6,
                bg_color="white",
                fg_color="#007BFF",
                hover_color="#0056b3",
                text_color="white",
                font=CTkFont(family="Manrope", size=14),
                command=lambda: update_tally_port(
                    overlay, tally_port_var.get(), tally_host_var.get()
                ),
            )
            yes_button2.pack(pady=(0, 10), side="left", padx=20, fill=tk.X, expand=True)

            def update_on_enter(event):
                yes_button2.invoke()
                return "break"

            host_entry.bind("<Return>", update_on_enter)
            port_entry.bind("<Return>", update_on_enter)

            # Pull keyboard focus away from the login fields so Enter
            # here updates the configuration instead of re-triggering
            # the login API
            host_entry.focus_set()

            # Function to close the overlay when clicking outside
            def on_click_outside(event):
                if not overlay.winfo_containing(event.x_root, event.y_root):
                    overlay.destroy()

            # Bind click outside the menu to close the overlay
            overlay.bind("<Button-1>", on_click_outside)

        # drag_layer = tk.Frame(
        #     self,
        #     # bg="#0CA1F6",
        #     bg="white",
        #     height=35
        # )
        # drag_layer.pack(side=tk.TOP, fill=tk.X)

        # # Load and display icon in title bar
        # icon_path = "./lib/images/logo2.ico"  # or use .png
        # try:
        #     icon_image = Image.open(icon_path)
        #     icon_image = icon_image.resize((20, 20), Image.Resampling.LANCZOS)
        #     icon_image_tk = ImageTk.PhotoImage(icon_image)

        #     icon_label = tk.Label(
        #         drag_layer,
        #         image=icon_image_tk,
        #         bg="white"
        #     )
        #     icon_label.image = icon_image_tk  # Keep reference
        #     icon_label.pack(side=tk.LEFT, padx=(15, 5), pady=(3, 3))
        #     print("Title bar icon loaded")
        # except Exception as e:
        #     print(f"Error loading title bar icon: {e}")

        # # Title (left side)
        # # title_label = tk.Label(
        # #     drag_layer,
        # #     text="eVital<>Tally Connects",
        # #     # bg="#0CA1F6",
        # #     bg="white",
        # #     # fg="white",
        # #     fg="black",
        # #     font=header_font5b
        # # )
        # # title_label.pack(side=tk.LEFT, padx=(5, 0), pady=(3,0))

        # # Close button (right side)
        # close_button = tk.Label(
        #     drag_layer,
        #     text="✕",
        #     # bg="#0CA1F6",
        #     bg="white",
        #     # fg="white",
        #     fg="black",
        #     font=("Segoe UI", 8, "bold"),
        #     cursor="hand2"
        # )
        # close_button.pack(side=tk.RIGHT, padx=15, pady=3)

        # def on_close_enter(e):
        #     close_button.config(bg="#E81123")  # Windows red

        # def on_close_leave(e):
        #     # close_button.config(bg="#0CA1F6")
        #     close_button.config(bg="white")

        # close_button.bind("<Enter>", on_close_enter)
        # close_button.bind("<Leave>", on_close_leave)

        # drag_layer.bind("<Button-1>", self.controller.start_move)
        # drag_layer.bind("<B1-Motion>", self.controller.do_move)

        # Also allow dragging from title text
        # title_label.bind("<Button-1>", self.controller.start_move)
        # title_label.bind("<B1-Motion>", self.controller.do_move)

        # close_button.bind("<Button-1>", lambda e: close_window())

        # Left panel
        left_panel = tk.Frame(self, bg="#044C9D")
        left_panel.pack(side=tk.LEFT, fill=tk.Y)

        image = Image.open(
            "./lib/images/login_panel.jpg"
        )  # Replace with your image path
        image = image.resize(
            (500, 600), Image.Resampling.LANCZOS
        )  # Resize image to fit the panel
        image_tk = ImageTk.PhotoImage(image)

        image_label = tk.Label(left_panel, image=image_tk, bg="#004BA8")
        image_label.image = image_tk  # Keep a reference to avoid garbage collection
        image_label.pack(pady=(0, 10))

        # title_bar = tk.Frame(self, width=900, bg="white")
        # title_bar.pack(fill=tk.X)

        # close_button = tk.Button(title_bar, text='x', font=header_font, command=close_window, bg='white', fg='#044C9D', borderwidth=0, relief=tk.SUNKEN)
        # close_button.pack(side=tk.RIGHT, padx=20, pady=15)

        right_panel = tk.Frame(self, bg="white", width=450, height=650)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        right_panel.pack_propagate(False)

        login_label = tk.Label(
            right_panel,
            text="Login with",
            bg="white",
            font=header_font2b,
            justify=tk.LEFT,
        )
        login_label.pack(pady=(85, 0), padx=(60, 55), anchor=tk.W)

        entity_selection_frame = tk.Frame(right_panel, bg="white")
        entity_selection_frame.pack(pady=(5, 20), padx=(60, 55), anchor=tk.W)

        entity_button_theme = ttk.Style()
        try:
            if "breeze" not in entity_button_theme.theme_names():
                self.tk.call("source", themepath)
            entity_button_theme.configure(
                "breeze.TRadiobutton",  # First argument is the name of style. Needs to end with: .TRadiobutton
                background="white",
                focuscolor="white",
                highlightthickness=0,
                borderwidth=0,
            )  # You can define colors like this also
            entity_button_theme.theme_use("breeze")
        except Exception:
            entity_button_theme.theme_use("default")

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

        rb1 = ttk.Radiobutton(
            entity_selection_frame,
            style="breeze.TRadiobutton",
            variable=selected_entity,
            value="eVitalRx",
            command=update_color,
        )
        rb1.pack(side="left")

        label1 = tk.Label(
            entity_selection_frame,
            text="eVitalRx",
            font=header_font4b,
            fg=selected_color,
            background="white",
        )
        label1.pack(side="left")

        rb2 = ttk.Radiobutton(
            entity_selection_frame,
            style="breeze.TRadiobutton",
            variable=selected_entity,
            value="eVitalSupply",
            command=update_color,
        )
        rb2.pack(side="left", padx=(30, 0))

        label2 = tk.Label(
            entity_selection_frame,
            text="eVitalSupply",
            font=header_font4b,
            fg=default_color,
            background="white",
        )
        label2.pack(side="left")

        def validate(
            action,
            index,
            value_if_allowed,
            prior_value,
            text,
            validation_type,
            trigger_type,
            widget_name,
        ):
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

        vcmd = (self.register(validate), "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W")

        form_container = tk.Frame(right_panel, bg="white")
        form_container.pack(pady=0, padx=0, fill=tk.X)

        mobile_label = tk.Label(
            form_container,
            text="Mobile Number",
            bg="white",
            fg="#044C9D",
            font=header_font3,
        )
        mobile_label.pack(pady=(20, 0), padx=(60, 55), anchor=tk.W)

        mobile_frame = tk.Frame(form_container, bg="white")
        mobile_frame.pack(pady=4, padx=65, anchor=tk.W, fill=tk.X)

        mobile_entry = tk.Entry(
            mobile_frame,
            bg="white",
            font=header_font2,
            bd=0,
            validate="key",
            validatecommand=vcmd,
        )
        mobile_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        mobile_line = tk.Canvas(
            form_container, height=1, bg="#004BA8", highlightthickness=0
        )
        mobile_line.pack(pady=(0, 10), padx=65, anchor=tk.W, fill=tk.X)

        password_label = tk.Label(
            form_container,
            text="Password",
            bg="white",
            fg="#044C9D",
            font=header_font3,
            width=40,
            justify=tk.LEFT,
            anchor="w",
        )
        password_label.pack(pady=(10, 0), padx=(60, 55), anchor=tk.W)

        password_frame = tk.Frame(form_container, bg="white")
        password_frame.pack(pady=4, padx=65, anchor=tk.W, fill=tk.X)

        eye_label = tk.Label(
            password_frame,
            text="Show",
            bg="white",
            fg="#0CA1F6",
            cursor="hand2",
            font=header_font4,
        )
        eye_label.pack(side=tk.RIGHT)

        password_entry = tk.Entry(
            password_frame, bg="white", font=header_font2, bd=0, show="*"
        )
        password_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        def on_eye_enter(event):
            eye_label.config(fg="#033D7E")

        def on_eye_leave(event):
            eye_label.config(fg="#0CA1F6")

        def toggle_password_visibility():
            if password_entry.cget("show") == "*":
                password_entry.config(show="")
                eye_label.config(text="Hide")
            else:
                password_entry.config(show="*")
                eye_label.config(text="Show")

        eye_label.bind("<Button-1>", lambda e: toggle_password_visibility())
        eye_label.bind("<Enter>", on_eye_enter)
        eye_label.bind("<Leave>", on_eye_leave)

        password_line = tk.Canvas(
            form_container, height=1, bg="#004BA8", highlightthickness=0
        )
        password_line.pack(pady=(0, 20), padx=65, anchor=tk.W, fill=tk.X)

        # API Key login fields (hidden by default)
        self.login_mode = tk.StringVar(value="password")

        apikey_label = tk.Label(
            form_container,
            text="API Key",
            bg="white",
            fg="#044C9D",
            font=header_font3,
            width=40,
            justify=tk.LEFT,
            anchor="w",
        )

        apikey_frame = tk.Frame(form_container, bg="white")

        apikey_eye_label = tk.Label(
            apikey_frame,
            text="Show",
            bg="white",
            fg="#0CA1F6",
            cursor="hand2",
            font=header_font4,
        )
        apikey_eye_label.pack(side=tk.RIGHT)

        apikey_entry = tk.Entry(
            apikey_frame, bg="white", font=header_font2, bd=0, show="*"
        )
        apikey_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        def on_apikey_eye_enter(event):
            apikey_eye_label.config(fg="#033D7E")

        def on_apikey_eye_leave(event):
            apikey_eye_label.config(fg="#0CA1F6")

        def toggle_apikey_visibility():
            if apikey_entry.cget("show") == "*":
                apikey_entry.config(show="")
                apikey_eye_label.config(text="Hide")
            else:
                apikey_entry.config(show="*")
                apikey_eye_label.config(text="Show")

        apikey_eye_label.bind("<Button-1>", lambda e: toggle_apikey_visibility())
        apikey_eye_label.bind("<Enter>", on_apikey_eye_enter)
        apikey_eye_label.bind("<Leave>", on_apikey_eye_leave)

        apikey_line = tk.Canvas(
            form_container, height=1, bg="#004BA8", highlightthickness=0
        )

        # Lock the form height (measured in password mode) so the Login
        # button stays at the same position in both login modes
        self.update_idletasks()
        form_container.pack_propagate(False)
        form_container.configure(height=form_container.winfo_reqheight())

        login_button = CTkButton(
            right_panel,
            text="Login",
            hover_color="#033D7E",
            text_color="white",
            fg_color="#0CA1F6",
            font=CTkFont(family="Manrope", size=16, weight="bold"),
            height=42,
            width=320,
            corner_radius=6,
            command=check_login,
        )
        login_button.pack(pady=20, padx=65)

        apikey_entry.bind("<Return>", lambda e: login_button.invoke())
        password_entry.bind("<Return>", lambda e: login_button.invoke())

        self.bind_all("<Control-k>", lambda e: toggle_login_mode())

        if self.login_mode.get() == "apikey":
            apikey_entry.focus_set()
        else:
            mobile_entry.focus_set()


class Dashboard(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#004BA8")
        for widget in self.winfo_children():
            if widget.winfo_exists():
                widget.destroy()
        self.controller = controller
        self.parent = parent
        parent.title("eVital<>Tally Connects")
        self.checkbox_vars = {}
        header_font5b = font.Font(family="Manrope", size=8, weight="bold")

        # def open_log_window()
        LogViewerAppObj = LogViewerApp(parent)
        self.bind_all(
            "<Control-d>", lambda e: open_log_window(parent, e, LogViewerAppObj)
        )

        def create_main_content():
            nonlocal rebuild_scheduled
            rebuild_scheduled = False
            if not constants.SYNC_RUNNING:
                constants.STOP_THREAD = False
            if getattr(self, "_logout_label", None) is not None:
                self._logout_label.pack(
                    side=tk.BOTTOM, anchor=tk.W, pady=(0, 50), padx=30
                )
                self._user_label.pack(
                    side=tk.BOTTOM, anchor=tk.W, pady=(0, 8), padx=30
                )
            if (
                right_panel.winfo_exists()
            ):  # Ensures widget exists before calling winfo_children()
                for widget in right_panel.winfo_children():
                    if widget.winfo_exists():
                        widget.destroy()

            get_all_mapping_details()
            # all_mapped = False
            # mapres1 = constants.MAPPING_HISTORY["results"] if isinstance(constants.MAPPING_HISTORY, dict) and "results" in constants.MAPPING_HISTORY.keys() else []
            # mapres = [x for x in mapres1 if x["is_mapped"] in ["False", False, 'false', ""]]

            # available_companies = constants.TALLY_ACCOUNTS.copy()
            # for x in constants.TALLY_ACCOUNTS:
            #     for j in constants.MAPPING_HISTORY.get("results", []):
            #         if x["company_guid"] == j["tally_company_guid"] and x in available_companies:
            #             available_companies.remove(x)
            # all_mapped = len(available_companies) == 0 or len(mapres) == 0
            # if all_mapped and len(mapres1) > 0:
            # constants.SYNC_STAGE = 1
            # constants.SYNC_BTN_TEXT = "Sync All"
            # print("stage 1")

            # print(constants.MAPPING_HISTORY, "mapping history in dashboard")
            # # print(constants.COMPANY_MAPPING, "company mapping in dashboard")

            style = ttk.Style()
            style.configure("TLabel", foreground="black")  # Label text color
            style.configure("TButton", foreground="black")  # Button text color
            style.configure(
                "TRadiobutton", foreground="black"
            )  # Radiobutton text color
            style.configure(
                "TCheckbutton", foreground="black"
            )  # Checkbutton text color

            parent.apply_intended_geometry("950x650")

            # Upper right panel (contains last sync and button)
            upper_right_panel = tk.Frame(right_panel, bg="#E7F6FF")
            upper_right_panel.pack(side=tk.TOP, fill=tk.X)

            # Left and right sections inside the upper panel
            top_left_panel = tk.Frame(upper_right_panel, bg="#E7F6FF")
            top_left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(50, 15))

            top_right_panel = tk.Frame(upper_right_panel, bg="#E7F6FF")
            top_right_panel.pack(
                side=tk.RIGHT, fill=tk.BOTH, expand=True, pady=(50, 15), padx=(0, 20)
            )

            # Last Sync header and time
            constants.LAST_SYNC_VAR = tk.StringVar(
                value="" if constants.SYNC_STAGE == 0 else "No Sync"
            )

            constants.LAST_SYNC_HEADER_VAR = tk.StringVar(
                value="Map Your Tally Companies"
                if constants.SYNC_STAGE == 0
                else "Last Sync"
            )
            last_sync_label = tk.Label(
                top_left_panel,
                textvariable=constants.LAST_SYNC_HEADER_VAR,
                bg="#E7F6FF",
                fg="#7E878C",
                font=label_font2,
                justify=tk.LEFT,
            )
            last_sync_label.pack(pady=(10, 0), padx=30, anchor=tk.W)

            if (
                constants.SYNC_STAGE == 1
                and constants.MAPPING_HISTORY is not None
                and len(constants.MAPPING_HISTORY) > 0
                and "login_entity_last_synced" in constants.MAPPING_HISTORY.keys()
                and constants.MAPPING_HISTORY["login_entity_last_synced"] != ""
            ):
                constants.LAST_SYNC_VAR.set(
                    constants.MAPPING_HISTORY["login_entity_last_synced"]
                )

            last_sync_time = tk.Label(
                top_left_panel,
                textvariable=constants.LAST_SYNC_VAR,
                bg="#E7F6FF",
                fg="#004BA8",
                font=label_font2,
                justify=tk.LEFT,
            )
            last_sync_time.pack(pady=(0, 10), padx=30, anchor=tk.W)

            btn_row = tk.Frame(top_right_panel, bg="#E7F6FF")
            btn_row.pack(pady=(10, 10), padx=40, anchor=tk.E)

            history_button = CTkButton(
                btn_row,
                text="🕘 History",
                hover_color="#F3FAFF",
                font=CTkFont(family="Manrope", size=15),
                text_color="#004BA8",
                fg_color="white",
                border_width=2,
                border_color="#B3D9F2",
                height=42,
                width=120,
                corner_radius=6,
                command=lambda: parent.show_frame("SyncHistory"),
            )
            history_button.pack(side=tk.LEFT, padx=(0, 12))

            sync_all_button = CTkButton(
                btn_row,
                text=constants.SYNC_BTN_TEXT,
                hover_color="#033D7E",
                font=CTkFont(family="Manrope", size=16, weight="bold"),
                text_color="white",
                fg_color="#0CA1F6",
                height=42,
                width=120,
                corner_radius=6,
                command=show_sync_frame,
            )
            sync_all_button.pack(side=tk.LEFT)

            # Debug mode banner for internal API-key sessions - sits
            # between the action row and the mapping/sync section so it
            # is clearly visible without displacing the top blocks.
            if constants.LOGIN_MODE == "apikey":
                debug_banner = tk.Label(
                    right_panel,
                    text="⚠ DEBUG MODE — Apikey Session · Server Uploads Disabled",
                    bg="#FFF3CD",
                    fg="#856404",
                    font=("Manrope", 12, "bold"),
                )
                debug_banner.pack(
                    side=tk.TOP, fill=tk.X, padx=14, pady=(18, 4)
                )

            # Lower right panel (contains branch data)
            lower_right_panel = tk.Frame(right_panel, bg="white")
            if constants.LOGIN_MODE == "apikey":
                # The DEBUG banner above consumes vertical space - reclaim
                # part of the large bottom margin so the module checkboxes
                # are not clipped (window size stays fixed).
                lower_right_panel.pack(
                    side=tk.TOP, fill=tk.X, expand=True, padx=30, pady=(0, 30)
                )
            else:
                lower_right_panel.pack(
                    side=tk.TOP, fill=tk.X, expand=True, padx=30, pady=(0, 80)
                )

            if constants.SYNC_STAGE == 0:
                mapping_results = (
                    constants.MAPPING_HISTORY.get("results", [])
                    if isinstance(constants.MAPPING_HISTORY, dict)
                    else []
                )
                branches = (
                    []
                    if constants.EVITAL_RX_API_KEY == ""
                    else [
                        {
                            "name": x["branch_name"],
                            "status": "Map Now"
                            if x["tally_company_name"] == ""
                            else str("Mapped as ") + str(x["tally_company_name"]),
                            "time": "No Sync"
                            if x["last_synced"] == ""
                            else x["last_synced"],
                            "chemist_id": x["entity_id"],
                            "company_guid": x["tally_company_guid"],
                        }
                        for x in mapping_results
                    ]
                )
                remaining_branch = [x["company_name"] for x in constants.TALLY_ACCOUNTS]
                custom_padding = 100
                if len(branches) > 0:
                    max_branch = max([len(str(x["name"])) for x in branches])
                    max_branch_time = max([len(str(x["time"])) for x in branches])

                    custom_padding = (
                        280 - (max_branch + max_branch_time)
                        if max_branch + max_branch_time < 34
                        else (
                            (280 - ((max_branch + max_branch_time) * 3.5))
                            if max_branch + max_branch_time < 45
                            else (280 - ((max_branch + max_branch_time) * 4.5))
                        )
                    )
                custom_padding = custom_padding if custom_padding > 0 else 0
                branches_label = tk.Label(
                    lower_right_panel,
                    text=str(len(branches)) + " Branches",
                    bg="white",
                    fg="#A9A9A9",
                    font=label_font,
                    justify=tk.LEFT,
                )
                branches_label.pack(pady=(30, 5), padx=5, anchor=tk.W)

                canvas = tk.Canvas(
                    lower_right_panel,
                    bg="white",
                    bd=0,
                    highlightthickness=0,
                    relief="ridge",
                    height=350,
                )
                scrollbar = ttk.Scrollbar(
                    lower_right_panel, orient="vertical", command=canvas.yview
                )
                scrollable_frame = tk.Frame(canvas, bg="white")

                # Configure the canvas
                scrollable_frame.bind(
                    "<Configure>",
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
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

                # def rotate_image(canvas2, size, image_tk, angle):
                #     while not constants.STOP_THREAD:
                #         # Rotate image smoothly
                #         rotated_image = branch_image.rotate(angle, resample=Image.BICUBIC, expand=True)

                #         # Create a transparent background to prevent jiggling
                #         background = Image.new("RGBA", (size, size), (255, 255, 255, 0))
                #         offset = (
                #             int((size - rotated_image.width) / 2),
                #             int((size - rotated_image.height) / 2)
                #         )
                #         background.paste(rotated_image, offset, rotated_image)

                #         # Update the image on canvas
                #         image_tk = ImageTk.PhotoImage(background)
                #         canvas2.itemconfig(image_id, image=image_tk)

                #         # Increment angle for rotation
                #         angle = (angle - 15) % 360
                #         time.sleep(0.05)
                #     re_create_main_content()

                # def toggle_rotation(event, branch_data, canvas2, size, image_tk, angle=0):
                #     # print('➡ tk_screen.py:528 toggle_rotation:')
                #     # print(event)
                #     # print(branch_data)
                #     sync_single_branch(branch_data)
                #     if not constants.STOP_THREAD:
                #         threading.Thread(target=rotate_image, args=(canvas2, size, image_tk, angle), daemon=True).start()

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
                    self.winfo_toplevel().register_follow_overlay(overlay)

                    # Display blurred background
                    bg_image = ImageTk.PhotoImage(blurred_screen)
                    bg_label = tk.Label(overlay, image=bg_image)
                    bg_label.image = bg_image
                    bg_label.pack(fill="both", expand=True)

                    options = remaining_branch

                    ACCENT = "#0CA1F6"
                    HEADER_BG = "#004BA8"
                    HEADER_HOVER = "#003A80"
                    HOVER_BG = "#E7F6FF"
                    TEXT = "#1F2430"
                    MUTED = "#7E878C"
                    BORDER = "#E3E8EF"
                    CHEVRON = "#C9D2DC"
                    LIST_BG = "#F3F6F9"

                    MENU_WIDTH = 460
                    ROW_HEIGHT = 46
                    ROW_PAD_Y = 6
                    MAX_LIST_HEIGHT = 368
                    MAX_VISIBLE_ROWS = MAX_LIST_HEIGHT // (ROW_HEIGHT + ROW_PAD_Y)

                    # Centered menu with a subtle border
                    menu_frame = tk.Frame(
                        overlay,
                        bg="white",
                        highlightbackground=BORDER,
                        highlightthickness=1,
                    )
                    menu_frame.place(relx=0.5, rely=0.5, anchor="center")

                    # ================= HEADER =================
                    header = tk.Frame(menu_frame, bg=HEADER_BG)
                    header.pack(fill=tk.X)

                    header_text = tk.Frame(header, bg=HEADER_BG)
                    header_text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(20, 8), pady=14)

                    tk.Label(
                        header_text,
                        text="MAP BRANCH",
                        bg=HEADER_BG,
                        fg="#9DD3FF",
                        font=small_font,
                        anchor=tk.W,
                    ).pack(anchor=tk.W, pady=(0, 3))

                    branch_name = branch_data["name"]
                    if len(branch_name) > 55:
                        branch_name = branch_name[:54] + "…"
                    tk.Label(
                        header_text,
                        text=branch_name,
                        bg=HEADER_BG,
                        fg="white",
                        font=header_font,
                        anchor=tk.W,
                        justify=tk.LEFT,
                        wraplength=330,
                    ).pack(anchor=tk.W, pady=(0, 3))
                    tk.Label(
                        header_text,
                        text="Select a Tally company to map this branch",
                        bg=HEADER_BG,
                        fg="#EAF6FF",
                        font=small_font,
                        anchor=tk.W,
                    ).pack(anchor=tk.W)

                    close_btn = tk.Label(
                        header,
                        text="✕",
                        bg=HEADER_BG,
                        fg="white",
                        font=header_font2,
                        cursor="hand2",
                        padx=14,
                        pady=8,
                    )
                    close_btn.pack(side=tk.RIGHT, padx=(4, 10))
                    close_btn.bind("<Button-1>", lambda e: overlay.destroy())
                    close_btn.bind("<Enter>", lambda e: close_btn.configure(bg=HEADER_HOVER))
                    close_btn.bind("<Leave>", lambda e: close_btn.configure(bg=HEADER_BG))

                    # ================= BODY =================
                    noun = "company" if len(options) == 1 else "companies"
                    tk.Label(
                        menu_frame,
                        text=f"{len(options)} Tally {noun} available",
                        bg="white",
                        fg=MUTED,
                        font=label_font,
                        anchor=tk.W,
                    ).pack(fill=tk.X, padx=20, pady=(14, 4))

                    list_wrapper = tk.Frame(
                        menu_frame,
                        bg=LIST_BG,
                        highlightbackground=BORDER,
                        highlightthickness=1,
                    )
                    list_wrapper.pack(fill=tk.X, padx=20, pady=(0, 16))

                    canvas2 = tk.Canvas(
                        list_wrapper, bg=LIST_BG, bd=0, highlightthickness=0, relief="flat"
                    )
                    scrollbar2 = ttk.Scrollbar(
                        list_wrapper, orient="vertical", command=canvas2.yview
                    )
                    scrollable_frame2 = tk.Frame(canvas2, bg=LIST_BG)

                    scrollable_frame2.bind(
                        "<Configure>",
                        lambda e: canvas2.configure(scrollregion=canvas2.bbox("all")),
                    )

                    has_scrollbar = len(options) > MAX_VISIBLE_ROWS
                    list_height = min(
                        MAX_LIST_HEIGHT, len(options) * (ROW_HEIGHT + ROW_PAD_Y)
                    )
                    list_width = MENU_WIDTH - 40 if not has_scrollbar else MENU_WIDTH - 58
                    canvas2.configure(width=MENU_WIDTH - 40, height=list_height)
                    canvas2.create_window(
                        (0, 0), window=scrollable_frame2, anchor="nw", width=list_width
                    )
                    canvas2.configure(yscrollcommand=scrollbar2.set)

                    canvas2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                    scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)
                    if not has_scrollbar:
                        scrollbar2.pack_forget()

                    tip_states = []

                    row_inner_width = list_width - 12
                    bullet_total = label_font.measure("●") + 26
                    chevron_total = label_font.measure("→") + 14
                    name_avail = row_inner_width - bullet_total - chevron_total

                    def on_scroll2(event):
                        for st in tip_states:
                            if st["after"] is not None:
                                try:
                                    st["widget"].after_cancel(st["after"])
                                except tk.TclError:
                                    pass
                                st["after"] = None
                            if st["win"] is not None:
                                try:
                                    st["win"].destroy()
                                except tk.TclError:
                                    pass
                                st["win"] = None
                        if event.delta:  # Windows scrolling
                            canvas2.yview_scroll(-1 * (event.delta // 120), "units")
                        elif event.num == 4:  # Linux scroll up
                            canvas2.yview_scroll(-1, "units")
                        elif event.num == 5:  # Linux scroll down
                            canvas2.yview_scroll(1, "units")

                    for option in options:
                        row = tk.Frame(
                            scrollable_frame2,
                            bg="white",
                            cursor="hand2",
                            highlightbackground=BORDER,
                            highlightthickness=1,
                        )
                        row.configure(height=ROW_HEIGHT)
                        row.pack(fill=tk.X, padx=6, pady=3)
                        row.pack_propagate(False)

                        needs_tip = label_font.measure(option) > name_avail
                        if needs_tip:
                            shown_name = option
                            while (
                                len(shown_name) > 1
                                and label_font.measure(shown_name + "…") > name_avail
                            ):
                                shown_name = shown_name[:-1]
                            shown_name += "…"
                        else:
                            shown_name = option
                        bullet = tk.Label(
                            row, text="●", bg="white", fg=ACCENT, font=label_font
                        )
                        bullet.pack(side=tk.LEFT, padx=(14, 12))
                        name = tk.Label(
                            row,
                            text=shown_name,
                            bg="white",
                            fg=TEXT,
                            font=label_font,
                            anchor=tk.W,
                        )
                        name.pack(side=tk.LEFT, fill=tk.X, expand=True)
                        chevron = tk.Label(
                            row, text="→", bg="white", fg=CHEVRON, font=label_font
                        )
                        chevron.pack(side=tk.RIGHT, padx=14)

                        tip_state = {"after": None, "win": None, "widget": None}
                        tip_states.append(tip_state)

                        def show_tip(e, option=option, row=row, tip_state=tip_state):
                            try:
                                if tip_state["win"] is not None:
                                    return
                                x = row.winfo_rootx()
                                y = row.winfo_rooty() + row.winfo_height() + 4
                                screen_h = overlay.winfo_screenheight()
                                if y + 100 > screen_h:
                                    y = row.winfo_rooty() - 8
                                tip = tk.Toplevel(overlay)
                                tip.wm_overrideredirect(True)
                                tip.wm_geometry(f"+{x}+{y}")
                                tip.configure(bg=TEXT)
                                tk.Label(
                                    tip,
                                    text=option,
                                    bg=TEXT,
                                    fg="white",
                                    font=small_font,
                                    justify=tk.LEFT,
                                    wraplength=380,
                                    padx=10,
                                    pady=6,
                                ).pack()
                                tip_state["win"] = tip
                            except tk.TclError:
                                return

                        def on_row_enter(
                            e,
                            row=row,
                            bullet=bullet,
                            name=name,
                            chevron=chevron,
                            option=option,
                            needs_tip=needs_tip,
                            tip_state=tip_state,
                        ):
                            row.configure(bg=HOVER_BG, highlightbackground=ACCENT)
                            bullet.configure(bg=HOVER_BG)
                            name.configure(bg=HOVER_BG)
                            chevron.configure(bg=HOVER_BG, fg=ACCENT)
                            if needs_tip:
                                if tip_state["after"] is not None:
                                    try:
                                        tip_state["widget"].after_cancel(tip_state["after"])
                                    except tk.TclError:
                                        pass
                                tip_state["widget"] = e.widget
                                tip_state["after"] = e.widget.after(
                                    500,
                                    lambda: show_tip(
                                        None, option=option, row=row, tip_state=tip_state
                                    ),
                                )

                        def on_row_leave(
                            e,
                            row=row,
                            bullet=bullet,
                            name=name,
                            chevron=chevron,
                            tip_state=tip_state,
                        ):
                            row.configure(bg="white", highlightbackground=BORDER)
                            bullet.configure(bg="white")
                            name.configure(bg="white")
                            chevron.configure(bg="white", fg=CHEVRON)
                            if tip_state["after"] is not None:
                                try:
                                    tip_state["widget"].after_cancel(tip_state["after"])
                                except tk.TclError:
                                    pass
                                tip_state["after"] = None
                            if tip_state["win"] is not None:
                                try:
                                    tip_state["win"].destroy()
                                except tk.TclError:
                                    pass
                                tip_state["win"] = None

                        for widget in (row, bullet, name, chevron):
                            widget.bind("<Enter>", on_row_enter)
                            widget.bind("<Leave>", on_row_leave)
                            widget.bind(
                                "<Button-1>",
                                lambda e, opt=option: map_branch_action(opt, overlay),
                            )
                            if has_scrollbar:
                                widget.bind("<MouseWheel>", on_scroll2)
                                widget.bind("<Button-4>", on_scroll2)
                                widget.bind("<Button-5>", on_scroll2)

                    # Function to close the overlay when clicking outside
                    def on_click_outside(event):
                        try:
                            mx = menu_frame.winfo_rootx()
                            my = menu_frame.winfo_rooty()
                            mw = menu_frame.winfo_width()
                            mh = menu_frame.winfo_height()
                        except tk.TclError:
                            return
                        if not (
                            mx <= event.x_root <= mx + mw
                            and my <= event.y_root <= my + mh
                        ):
                            overlay.destroy()

                    # Bind click outside the menu and Escape to close the overlay
                    overlay.bind("<Button-1>", on_click_outside)
                    overlay.bind("<Escape>", lambda e: overlay.destroy())
                    overlay.focus_set()

                canvas.bind_all("<MouseWheel>", on_scroll)  # Windows
                canvas.bind_all("<Button-4>", on_scroll)  # Linux Scroll Up
                canvas.bind_all("<Button-5>", on_scroll)  # Linux Scroll Down
                # branches = [
                #     {"name":"Branch 1sjnsdgjsldngslgnsglsjgslkgjsglksjglskgjsglksjglksgjslkgsjgklsgjslkgsjlgksdjglksdgj", "status":"Map Now", "time" : "No Sync", "chemist_id" : 1, "company_guid" : 1}
                #     for x in range(10)
                # ]
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
                        justify=tk.LEFT,
                    )
                    chemist_name.pack(anchor=tk.W, padx=5)

                    branch_left_frame2 = tk.Frame(branch_frame, bg="white")
                    branch_left_frame2.pack(side=tk.LEFT, fill=tk.X, expand=True)

                    if "Map Now" in branch["status"]:

                        def test_menu(branch_data, event):
                            constants.CURRENT_BRANCH_SYNC_JSON = branch_data

                            # Get the clicked widget's position on the screen
                            x = event.widget.winfo_rootx()
                            y = event.widget.winfo_rooty() + event.widget.winfo_height()

                            # Ensure menu does not go outside the application window
                            if x < 0:
                                x = 0
                            if y < 0:
                                y = 0

                            # Show menu at the correct location
                            map_menu.post(x, y)

                        if len(remaining_branch) > 0:
                            test_button = tk.Label(
                                branch_left_frame,
                                text="Map Now >",
                                fg="red",
                                bg="white",
                                font=label_font,
                            )
                            test_button.pack(
                                anchor=tk.E, padx=(10, 5), fill=tk.X, side=tk.LEFT
                            )
                            test_button.bind(
                                "<Button-1>",
                                lambda event, branch_data=branch: show_map_menu(
                                    event, branch_data
                                ),
                            )

                            # test_button.pack_info()
                        else:
                            test_button = tk.Label(
                                branch_left_frame,
                                text="Tally company not available",
                                fg="red",
                                bg="white",
                                font=label_font,
                            )
                            test_button.pack(
                                anchor=tk.E, padx=(10, 5), fill=tk.X, side=tk.LEFT
                            )

                        map_menu = tk.Menu(
                            branch_left_frame2,
                            tearoff=0,
                            bg="white",
                            fg="black",
                            font=label_font,
                        )
                        for option in remaining_branch:
                            # map_menu.add_command(label=option, command=lambda opt=option: map_branch_action(opt))
                            map_menu.add_radiobutton(
                                label=option,
                                command=lambda opt=option: map_branch_action(
                                    opt,
                                ),
                            )
                            # map_menu.add_separator()

                    else:
                        mapped_status = tk.Label(
                            branch_left_frame,
                            text="Mapped as:",
                            bg="white",
                            fg="#7E878C",
                            font=label_font,
                            justify=tk.LEFT,
                        )
                        mapped_status.pack(anchor=tk.W, padx=(10, 0), side=tk.LEFT)
                        mapped_status = tk.Label(
                            branch_left_frame,
                            text=branch["status"].replace("Mapped as", ""),
                            bg="white",
                            fg="black",
                            font=label_font,
                            justify=tk.LEFT,
                        )
                        mapped_status.pack(anchor=tk.W, padx=(5, 10), side=tk.LEFT)

                        remove_label = tk.Label(
                            branch_left_frame,
                            text="Remove",
                            fg="red",
                            bg="white",
                            cursor="hand2",
                            font=label_font,
                        )
                        remove_label.pack(
                            anchor=tk.E, padx=(10, 5), fill=tk.X, side=tk.LEFT
                        )
                        remove_label.bind(
                            "<Button-1>",
                            lambda event, branch_data=branch: remove_branch_mapping(
                                branch_data
                            ),
                        )

                    branch_right_frame = tk.Frame(branch_frame, bg="white")
                    branch_right_frame.pack(
                        side=tk.RIGHT, fill=tk.X, padx=(custom_padding, 0)
                    )

                    if branch["time"] != "No Sync":
                        branch_time = tk.Label(
                            branch_right_frame,
                            text=branch["time"],
                            bg="white",
                            fg="#004BA8",
                            font=label_font,
                            justify=tk.RIGHT,
                        )
                        branch_time.pack(anchor=tk.E, padx=(10, 0), side=tk.LEFT)

            elif constants.SYNC_STAGE == 1:
                # ================= TOP PANEL =================
                top_panel = tk.Frame(lower_right_panel, bg="white")
                top_panel.pack(fill=tk.X, pady=(24, 12), padx=0)

                # ---- LEFT: TARGET COMPANY ----
                left_top = tk.Frame(top_panel, bg="white")
                left_top.pack(side=tk.LEFT, fill=tk.X, expand=True)

                tk.Label(
                    left_top,
                    text="Target Tally Company",
                    bg="white",
                    fg="#444",
                    font=header_font3,
                ).pack(anchor="w", padx=(0, 10))

                company_row = tk.Frame(left_top, bg="white")
                company_row.pack(fill=tk.X, pady=(5, 0), padx=(5, 0))

                company_options = {
                    x["company_guid"]: x["company_name"]
                    for x in constants.TALLY_ACCOUNTS
                }
                tally_guids = list(company_options.keys())
                if (
                    constants.MAPPING_HISTORY is not None
                    and len(constants.MAPPING_HISTORY) > 0
                ):
                    if len(constants.MAPPING_HISTORY.get("results", [])) > 0:
                        company_options = {}
                        try:
                            with open("./lib/tally_data.txt", "a") as f:
                                f.write("-"*50 + "\n")
                                f.write("Company Data  " + "\n")
                                f.write("-"*50 + "\n")
                                
                                f.write(json.dumps(constants.MAPPING_HISTORY) + "\n")
                                f.write(json.dumps(constants.TALLY_ACCOUNTS) + "\n")
                        except:
                            pass
                        for x in constants.MAPPING_HISTORY.get("results", []):
                            if x["is_mapped"] in ["False", False, "false", ""]:
                                continue
                            if x["tally_company_guid"] in tally_guids:
                                company_options[x["tally_company_guid"]] = x[
                                    "tally_company_name"
                                ]
                            # if x["tally_company_guid"] not in tally_guids:
                            # messagebox.showerror("Tally Comapny", "Mapped tally company not found. Please contact support.")
                            # logout()
                            # close_window()
                            # parent.quit()
                            # import sys
                            # sys.exit(1)

                            # # re_create_main_content()

                        if len(company_options) <= 0:
                            if constants.LOGIN_MODE == "apikey":
                                # Debug session: the client's mapped company does
                                # not exist on this machine - fall back to all
                                # local Tally companies as stand-in targets.
                                LogManagerObj.write_log(
                                    "⚠ Debug mode: mapped company not found locally,"
                                    " using local Tally companies as stand-ins."
                                )
                                company_options = {
                                    x["company_guid"]: x["company_name"]
                                    for x in constants.TALLY_ACCOUNTS
                                }
                            else:
                                messagebox.showerror(
                                    "Tally Comapny",
                                    "eVital Mapped Tally company is not loaded.\nPlease open the mapped company in Tally and try again.",
                                )
                                # logout()
                                parent.quit()
                                import sys

                                sys.exit(1)

                company_var = tk.StringVar(
                    company_row,
                    value=list(company_options.values())[0] if company_options else "",
                )
                constants.COMPANY_NAME = company_var.get()

                def update_company(*args):
                    print(f"Selected company: {company_var.get()}")
                    constants.COMPANY_NAME = company_var.get()

                dropdown_wrapper = tk.Frame(
                    company_row,
                    bg="white",
                    highlightbackground="#C4C7CC",
                    highlightcolor="#C4C7CC",
                    highlightthickness=1,
                    bd=0,
                )
                dropdown_wrapper.pack(side=tk.LEFT, padx=(0, 5))

                company_dropdown = tk.OptionMenu(
                    dropdown_wrapper, company_var, *company_options.values()
                )
                company_dropdown.config(
                    bg="white",
                    fg="#333",
                    activebackground="white",
                    activeforeground="#333",
                    font=("Segoe UI", 10),
                    bd=0,
                    highlightthickness=0,
                    relief="flat",
                    cursor="hand2",
                    indicatoron=False,
                    width=20,
                    padx=4,
                    pady=2,
                    anchor=tk.W,
                )
                company_dropdown.pack(
                    side=tk.LEFT, padx=(10, 0), pady=3
                )

                arrow = tk.Label(
                    dropdown_wrapper,
                    text="▾",
                    bg="white",
                    fg="#0CA1F6",
                    cursor="hand2",
                    font=("Segoe UI", 10, "bold"),
                )
                arrow.pack(side=tk.RIGHT, padx=(4, 10))

                # Sync button in its own box right after the dropdown (single-company sync)
                sync_box = tk.Frame(
                    company_row,
                    bg="white",
                    cursor="hand2",
                    highlightbackground="#C4C7CC",
                    highlightcolor="#C4C7CC",
                    highlightthickness=1,
                    bd=0,
                )
                sync_box.pack(side=tk.LEFT, padx=(0, 10), pady=3)

                branch_image_path = ".\\lib\\images\\sync_btn.png"
                try:
                    branch_image = Image.open(branch_image_path).convert("RGBA")
                    branch_image = branch_image.resize(
                        (24, 24), Image.Resampling.LANCZOS
                    )
                    branch_image_tk = ImageTk.PhotoImage(branch_image)
                except Exception as e:
                    print(f"Error loading image: {e}")
                    branch_image_tk = None

                if branch_image_tk:
                    sync_icon = tk.Canvas(
                        sync_box,
                        width=29,
                        height=29,
                        bg="white",
                        cursor="hand2",
                        highlightthickness=0,
                    )
                    sync_icon.pack(padx=5, pady=2)
                    image_id = sync_icon.create_image(
                        int(sync_icon["width"]) / 2,
                        int(sync_icon["height"]) / 2,
                        image=branch_image_tk,
                    )
                    sync_icon.image = branch_image_tk
                    sync_icon.tag_bind(
                        image_id, "<Button-1>", lambda event: show_sync_frame(True)
                    )

                    def sync_box_enter(e):
                        sync_box.config(
                            highlightbackground="#0CA1F6", highlightcolor="#0CA1F6"
                        )
                        schedule_tooltip(
                            "Sync data to the selected tally company",
                            e.widget.winfo_rootx() + 10,
                            e.widget.winfo_rooty() + 24,
                        )

                    def sync_box_leave(e):
                        sync_box.config(
                            highlightbackground="#C4C7CC", highlightcolor="#C4C7CC"
                        )
                        hide_tooltip()

                    for widget in (sync_box, sync_icon):
                        widget.bind("<Enter>", sync_box_enter)
                        widget.bind("<Leave>", sync_box_leave)
                        widget.bind(
                            "<Button-1>", lambda event: show_sync_frame(True)
                        )
                else:
                    branch_image_label = tk.Label(
                        sync_box,
                        text="[IMG]",
                        bg="white",
                        fg="black",
                        font=label_font,
                    )
                    branch_image_label.pack(padx=6, pady=4)

                dd_menu = company_dropdown["menu"]
                dd_menu.config(
                    tearoff=0,
                    bg="white",
                    fg="#333",
                    activebackground="#E7F6FF",
                    activeforeground="#0CA1F6",
                    font=("Segoe UI", 10),
                    bd=0,
                    relief=tk.FLAT,
                )

                # Replace radio entries (they add a checkmark column that shifts the
                # list to the right) with plain command entries so the list aligns
                # straight under the button
                dd_menu.delete(0, "end")
                for _name in company_options.values():
                    dd_menu.add_command(
                        label=_name,
                        command=lambda v=_name: company_var.set(v),
                    )

                def fit_menu_width():
                    f = tk.font.Font(font=("Segoe UI", 10))
                    btn_w = company_dropdown.winfo_width()
                    try:
                        max_w = (
                            max(f.measure(v) for v in company_options.values()) + 40
                        )
                    except ValueError:
                        max_w = 0
                    target = max(btn_w, max_w)
                    last = dd_menu.index("end")
                    if last is None:
                        return
                    for i in range(last + 1):
                        txt = dd_menu.entrycget(i, "label")
                        if f.measure(txt) < target:
                            pad = " " * max(
                                1, int((target - f.measure(txt)) / f.measure(" "))
                            )
                            dd_menu.entryconfigure(i, label=txt + pad)

                dd_menu.configure(postcommand=fit_menu_width)

                tooltip = None
                tip_job = None

                def show_tooltip(text, x, y):
                    nonlocal tooltip, tip_job
                    if tooltip is not None and getattr(tooltip, "_tip_text", None) == text:
                        tooltip.wm_geometry(f"+{x}+{y}")
                        return
                    hide_tooltip()
                    if not text:
                        return
                    screen_w = company_row.winfo_screenwidth()
                    screen_h = company_row.winfo_screenheight()
                    if x + 20 > screen_w:
                        x = screen_w - 20
                    if y + 20 > screen_h:
                        y = screen_h - 20
                    tip = tk.Toplevel(company_row)
                    tip.wm_overrideredirect(True)
                    tip.wm_attributes("-topmost", True)
                    tip.configure(bg="#333")
                    tk.Label(
                        tip,
                        text=text,
                        bg="#333",
                        fg="white",
                        font=("Segoe UI", 10),
                        padx=10,
                        pady=5,
                        justify=tk.LEFT,
                    ).pack()
                    tip._tip_text = text
                    tip.wm_geometry(f"+{x}+{y}")
                    tip_job = None
                    tooltip = tip

                def hide_tooltip(event=None):
                    nonlocal tooltip, tip_job
                    if tip_job is not None:
                        try:
                            company_dropdown.after_cancel(tip_job)
                        except Exception:
                            pass
                        tip_job = None
                    if tooltip is not None:
                        tooltip.destroy()
                        tooltip = None

                def schedule_tooltip(text, x, y, delay=500):
                    nonlocal tip_job
                    hide_tooltip()
                    if not text:
                        return
                    tip_job = company_dropdown.after(
                        delay, lambda: show_tooltip(text, x, y)
                    )

                def show_button_tooltip(event):
                    full = company_var.get()
                    if full and len(full) > 22:
                        schedule_tooltip(
                            full, event.x_root + 10, event.y_root + 22
                        )
                    else:
                        hide_tooltip()

                def show_menu_tooltip(event):
                    try:
                        idx = int(dd_menu.index(f"@{event.x},{event.y}"))
                    except (tk.TclError, ValueError):
                        hide_tooltip()
                        return
                    if idx < 0 or idx >= len(company_options):
                        hide_tooltip()
                        return
                    name = list(company_options.values())[idx]
                    schedule_tooltip(name, event.x_root + 20, event.y_root + 15)

                dd_menu.bind("<Motion>", show_menu_tooltip)
                dd_menu.bind("<Leave>", hide_tooltip)
                dd_menu.bind("<Map>", hide_tooltip)
                dd_menu.bind("<Unmap>", hide_tooltip)

                def on_enter(e):
                    dropdown_wrapper.config(
                        highlightbackground="#0CA1F6", highlightcolor="#0CA1F6"
                    )
                    company_dropdown.config(bg="white")
                    arrow.config(bg="white")

                def on_leave(e):
                    dropdown_wrapper.config(
                        highlightbackground="#C4C7CC", highlightcolor="#C4C7CC"
                    )
                    company_dropdown.config(bg="white")
                    arrow.config(bg="white")

                dropdown_wrapper.bind("<Enter>", on_enter)
                dropdown_wrapper.bind("<Leave>", on_leave)
                company_dropdown.bind("<Enter>", on_enter)
                company_dropdown.bind("<Leave>", on_leave)
                company_dropdown.bind("<Motion>", show_button_tooltip)
                company_dropdown.bind("<Leave>", hide_tooltip)
                arrow.bind("<Enter>", on_enter)
                arrow.bind("<Leave>", on_leave)
                company_var.trace_add("write", update_company)

                def open_dropdown(event):
                    hide_tooltip()
                    menu = company_dropdown["menu"]

                    # Get widget position on screen
                    x = company_dropdown.winfo_rootx()
                    y = company_dropdown.winfo_rooty() + company_dropdown.winfo_height() + 1

                    # Keep the menu aligned and inside the screen
                    fit_menu_width()
                    menu.update_idletasks()
                    mw = menu.winfo_reqwidth()
                    mh = menu.winfo_reqheight()
                    screen_w = self.winfo_screenwidth()
                    screen_h = self.winfo_screenheight()
                    if x + mw > screen_w:
                        x = screen_w - mw
                    if y + mh > screen_h:
                        y = company_dropdown.winfo_rooty() - mh - 1

                    try:
                        menu.tk_popup(x, y)
                    finally:
                        menu.grab_release()

                arrow.bind("<Button-1>", open_dropdown)
                dropdown_wrapper.bind("<Button-1>", open_dropdown)
                company_dropdown.bind("<Button-1>", hide_tooltip)

                DATE_FORMAT = "%d-%m-%y"  # adjust if your DateEntry format differs

                def validate_dates(*args):
                    try:
                        start_str = get_sync_date_value(constants.SYNC_START_DATE)
                        end_str = get_sync_date_value(constants.SYNC_END_DATE)

                        if not start_str or not end_str:
                            return

                        if start_str == "dd-mm-yy" or end_str == "dd-mm-yy":
                            messagebox.showerror(
                                "Invalid Date", "Please enter valid date."
                            )
                            return

                        start_date = datetime.strptime(start_str, DATE_FORMAT)
                        end_date = datetime.strptime(end_str, DATE_FORMAT)

                        # Rule 1: End date should not be before start date
                        if end_date < start_date:
                            messagebox.showerror(
                                "Invalid Date", "End date cannot be before start date."
                            )
                            constants.SYNC_END_DATE.set(start_str)
                            return

                        # Rule 2: Max 30 days range
                        if (end_date - start_date).days > 180:
                            messagebox.showerror(
                                "Invalid Range",
                                "You can select a maximum of 30 days only.",
                            )

                            # Auto-correct end date to +30 days from start
                            corrected_date = start_date + timedelta(days=180)
                            constants.SYNC_END_DATE.set(
                                corrected_date.strftime(DATE_FORMAT)
                            )
                            return

                        if (
                            start_date.date() > datetime.now().date()
                            or end_date.date() > datetime.now().date()
                        ):
                            messagebox.showerror(
                                "Invalid Range", "You can't select a future date."
                            )
                            return

                        print(f"Valid Range: {start_date} → {end_date}")

                    except Exception as e:
                        print("Date validation error:", e)

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

                tk.Label(
                    right_top,
                    text="Sync Period",
                    bg="white",
                    fg="#444",
                    font=header_font3,
                ).pack(anchor="w", padx=(5, 0))

                date_row = tk.Frame(right_top, bg="white")
                date_row.pack(pady=(5, 0), padx=(5, 10))

                constants.SYNC_START_DATE = tk.StringVar()
                constants.SYNC_END_DATE = tk.StringVar()

                # ================= MODULES SECTION =================
                bottom_panel = tk.Frame(lower_right_panel, bg="white")
                bottom_panel.pack(fill=tk.BOTH, expand=True, padx=0, pady=(20, 20))

                tk.Label(
                    bottom_panel,
                    text="Modules to Sync",
                    bg="white",
                    fg="#444",
                    font=header_font3,
                ).pack(anchor="w", pady=(0, 10))

                # Split left/right sections
                left_section = tk.Frame(bottom_panel, bg="white")
                left_section.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

                right_section = tk.Frame(bottom_panel, bg="white")
                right_section.pack(
                    side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 10)
                )

                def update_module_selection():
                    selected_modules = [
                        module
                        for module, var in self.checkbox_vars.items()
                        if var.get()
                    ]
                    constants.SELECTED_MODULES = selected_modules
                    print("Selected modules:", selected_modules)
                    # You can add additional logic here to enable/disable the sync button based on selection

                def create_module_section(parent, title, modules):
                    section = tk.Frame(parent, bg="white")
                    section.pack(fill=tk.X, pady=10, padx=(10, 0))
                    # print("Section created:", title)
                    # print("Modules:", modules)

                    # Store checkbox variables
                    vars_list = []

                    # Header row
                    header = tk.Frame(section, bg="white")
                    header.pack(fill=tk.X)

                    tk.Label(
                        header, text=title, bg="white", fg="#1a73e8", font=header_font3
                    ).pack(side=tk.LEFT)

                    # Select All label (only for multi-module groups)
                    select_all_lbl = None
                    if len(modules) > 1:
                        select_all_lbl = tk.Label(
                            header,
                            text="Select All",
                            bg="white",
                            fg="#1a73e8",
                            cursor="hand2",
                        )
                        select_all_lbl.pack(side=tk.RIGHT)

                    # Grid
                    grid = tk.Frame(section, bg="white")
                    grid.pack(fill=tk.X, pady=(5, 0))

                    # print("m,ap|",constants.MAPPING_HISTORY)
                    # constants.MAPPING_HISTORY["login_entity_stock_transfer_import_enabled"] = True
                    for i, module in enumerate(modules):
                        if constants.MAPPING_HISTORY.get("login_entity_stock_transfer_import_enabled", False):
                            if module == "Purchase":
                                module = "Purchase/Stock In"
                            elif module == "Wholesale":
                                module = "Wholesale/Stock Out"
                        var = tk.BooleanVar()
                        vars_list.append(var)

                        row = i // 2
                        col = i % 2

                        cb = ttk.Checkbutton(
                            grid,
                            text=module,
                            variable=var,
                            style="info.TCheckbutton",
                            cursor="hand2",
                            command=update_module_selection,
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

                        selected_modules = [
                            module
                            for module, var in self.checkbox_vars.items()
                            if var.get()
                        ]
                        constants.SELECTED_MODULES = selected_modules
                        print("Selected modules:", constants.SELECTED_MODULES)

                    if select_all_lbl is not None:
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
                        # --- Colors matching eVital<>Tally Connects theme ---
                        background="#004494",  # deep blue matching sidebar
                        headersbackground="#004494",  # match the blue header in calendar
                        headersforeground="white",
                        normalbackground="white",
                        normalforeground="#333333",
                        weekendbackground="white",
                        weekendforeground="#333333",
                        othermonthbackground="white",
                        othermonthforeground="#BBBBBB",  # lighter gray for other months
                        # --- Selected/Today - Orange highlight (matches the 28 in your image) ---
                        selectbackground="#FF9500",  # orange highlight like in the popup
                        selectforeground="white",
                        todaybackground="#FF9500",  # orange for today
                        todayforeground="white",
                        # --- Border ---
                        bordercolor="#004494",  # match header blue
                        borderwidth=2,
                        # --- Font ---
                        font=("Manrope", 10),
                        headersfont=("Manrope", 10, "bold"),
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
                        
                    def close_on_focus_out_cal(e):
                        top.destroy()
                        cal.destroy()

                    cal.bind("<FocusOut>", close_on_focus_out_cal)
                    # cal.bind("<FocusOut>", close_on_focus_out)
                    # top.bind("<FocusOut>", close_on_focus_out)
                    top.focus_set()

                def create_date_input(parent, var, open_calendar):
                    wrapper = tk.Frame(parent, bg="#D9D9D9", bd=0)

                    inner = tk.Frame(
                        wrapper,
                        bg="white",
                        bd=0,
                        highlightbackground="#C4C7CC",
                        highlightcolor="#C4C7CC",
                        highlightthickness=1,
                    )
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
                        cursor="hand2",
                    )
                    entry.pack(side=tk.LEFT, padx=(8, 2), pady=4)

                    icon = tk.Label(
                        inner,
                        text="📅",
                        bg="white",
                        fg="#666",
                        font=("Segoe UI", 10),
                        cursor="hand2",
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

                start_entry = create_date_input(
                    date_row, constants.SYNC_START_DATE, open_calendar
                )

                tk.Label(date_row, text="to", bg="white", font=("Segoe UI", 10)).pack(
                    side=tk.LEFT
                )

                end_entry = create_date_input(
                    date_row, constants.SYNC_END_DATE, open_calendar
                )

                def on_start_change(*args):
                    try:
                        start_date = datetime.strptime(
                            constants.SYNC_START_DATE.get(), DATE_FORMAT
                        )
                        max_date = start_date + timedelta(days=180)

                        if max_date.date() > datetime.now().date():
                            constants.SYNC_END_DATE.set(
                                datetime.now().date().strftime(DATE_FORMAT)
                            )
                        else:
                            constants.SYNC_END_DATE.set(max_date.strftime(DATE_FORMAT))
                    except:
                        pass

                constants.SYNC_START_DATE.trace_add("write", on_start_change)

        def close_window():
            self.destroy()
            parent.destroy()

        def sync_single_branch(data):
            # if constants.SELECTED_MODULES == []:
            #     messagebox.showerror(
            #         "Sync Issue", "Please select at least one module to sync."
            #     )
            #     return 0

            if (
                get_valid_sync_date(constants.SYNC_START_DATE) is None
                or get_valid_sync_date(constants.SYNC_END_DATE) is None
            ):
                messagebox.showerror("Invalid Date", "Please enter valid date.")
                return 0

            if (
                "Ledgers" in constants.SELECTED_MODULES
                and len(constants.SELECTED_MODULES) == 1
            ):
                messagebox.showerror(
                    "Sync Issue",
                    "Please select at least one more module along with Ledgers for sync.",
                )
                return 0
            # constants.ONE_SYNC = [
            #     {
            #         "chemist_id" : data["chemist_id"],
            #         "tally_company_guid" : data["company_guid"],
            #         "company_name" : str(data["status"]).replace("Mapped as ", ""),
            #         "branch_name" : data["name"]
            #     }
            # ]
            if constants.SYNC_RUNNING:
                messagebox.showerror(
                    "Sync Issue", "A sync is already running. Please wait."
                )
                return 0

            thread1 = threading.Thread(
                target=start_background_thread, args=(True, True), daemon=True
            )
            thread1.start()

        def map_branch_action(branch_name, overlay, branch={}):
            if constants.LOGIN_MODE == "apikey":
                messagebox.showwarning(
                    "Debug Mode",
                    "Saving mappings is disabled in debug mode.\n"
                    "This protects the client's production Tally mapping.",
                )
                return
            # print(branch_name)
            company_guid = ""
            if branch == {}:
                branch = constants.CURRENT_BRANCH_SYNC_JSON
            for x in constants.TALLY_ACCOUNTS:
                if x["company_name"] == branch_name:
                    company_guid = x["company_guid"]
            # print('➡ tk_screen.py:599 company_guid:', company_guid)
            constants.COMPANY_MAPPING = [
                {
                    "chemist_id": branch["chemist_id"],
                    "company_name": branch_name,
                    "company_guid": company_guid,
                    "mapping_type": "single",
                }
            ]
            # print('➡ tk_screen.py:605 constants.COMPANY_MAPPING:', constants.COMPANY_MAPPING)
            map_rx_companies()

            # self.update()
            # self.update_idletasks()
            print(f"Mapping branch: {branch_name}")
            overlay.destroy()
            create_main_content()

        def get_branch_apikey(chemist_id):
            # get_mapping_details is the source of truth - prefer its
            # apikey over the (possibly stale) cached login_response
            if isinstance(constants.MAPPING_HISTORY, dict):
                for r in constants.MAPPING_HISTORY.get("results", []):
                    if (
                        isinstance(r, dict)
                        and str(r.get("entity_id")) == str(chemist_id)
                        and str(r.get("apikey", "") or "") != ""
                    ):
                        return r["apikey"]
            businesses = constants.LOGIN_RESPONSE["data"]["business_details"]
            logged_in = businesses["logged_in_business"]
            if logged_in["id"] == chemist_id and logged_in.get("apikey", "") != "":
                return logged_in["apikey"]
            for x in businesses.get("child_businesses", []):
                if x["id"] == chemist_id and x.get("apikey", "") != "":
                    return x["apikey"]
            return ""

        def remove_branch_mapping(branch_data):
            if constants.LOGIN_MODE == "apikey":
                messagebox.showwarning(
                    "Debug Mode",
                    "Removing mappings is disabled in debug mode.\n"
                    "This protects the client's production Tally mapping.",
                )
                return
            if not messagebox.askyesno(
                "Remove Mapping",
                f"Are you sure you want to remove the tally mapping for '{branch_data['name']}'?",
            ):
                return

            branch_apikey = get_branch_apikey(branch_data["chemist_id"])
            if branch_apikey == "":
                messagebox.showerror(
                    "Remove Mapping", "No API key found for this branch."
                )
                return

            res = remove_company_mapping(branch_apikey)
            success = isinstance(res, dict) and res.get("status_code") in [
                1,
                "1",
                "1.0",
            ]
            if success:
                messagebox.showinfo(
                    "Remove Mapping", "Tally company mapping removed successfully."
                )
            else:
                error_detail = (
                    res.get("status_message")
                    if isinstance(res, dict)
                    else None
                )
                messagebox.showerror(
                    "Remove Mapping",
                    "Error while removing mapping details"
                    + (": " + str(error_detail) if error_detail else "."),
                )
            re_create_main_content()

        def re_create_main_content():
            constants.STOP_THREAD = True
            create_main_content()

        # def safe_after_cancel():
        #     self.after_cancel(animate_gif)

        def logout_account(overlay):
            logout()
            overlay.destroy()
            parent.show_frame("LoginScreen")
            [
                widget.delete(0, tk.END)
                for widget in parent.winfo_children()
                if isinstance(widget, tk.Entry)
            ]

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
                constants.ANIMATION_AFTER_ID = self.after(
                    100, animate_gif, sync_label, frames, next_index
                )
            except tk.TclError:
                # Widget was destroyed, stop animation
                return

        rebuild_scheduled = False

        def check_thread_status():
            nonlocal rebuild_scheduled
            while not constants.STOP_THREAD:
                # print("thead alive")

                time.sleep(0.5)
            if not rebuild_scheduled:
                rebuild_scheduled = True
                self.after(0, re_create_main_content)

        def check_if_require_reboot():
            while not constants.REQUIRE_REBOOT:
                time.sleep(1)
            self.after(0, create_main_content)
            constants.REQUIRE_REBOOT = False
            check_if_require_reboot()

        def show_sync_frame(one_sync=False):

            if constants.SYNC_STAGE == 0:

                if constants.LOGIN_MODE == "apikey":
                    # Debug session: mappings are server-side and read-only
                    # here - allow proceeding; sync uses a local stand-in.
                    constants.SYNC_STAGE = 1
                    constants.SYNC_BTN_TEXT = "Sync All"
                    print("sync increased")
                    self.after(100, re_create_main_content)
                    return

                mapping_results = (
                    constants.MAPPING_HISTORY.get("results", [])
                    if isinstance(constants.MAPPING_HISTORY, dict)
                    else []
                )
                mapped_current = [
                    x
                    for x in mapping_results
                    if x["is_mapped"] in ["True", True, "True"]
                ]
                if len(mapped_current) <= 0:
                    messagebox.showerror(
                        "Map Comany", "Please map any of your current company(s)"
                    )
                else:
                    constants.SYNC_STAGE = 1
                    constants.SYNC_BTN_TEXT = "Sync All"

                    # for widget in right_panel.winfo_children():
                    #     if widget.winfo_exists():
                    #         widget.destroy()

                    print("sync increased")
                    # re_create_main_content()
                    self.after(100, re_create_main_content)
    
            elif constants.SYNC_STAGE == 1:
                if constants.SELECTED_MODULES == []:
                    messagebox.showerror(
                        "Sync Issue", "Please select at least one module to sync."
                    )
                    return 0

                if (
                    get_valid_sync_date(constants.SYNC_START_DATE) is None
                    or get_valid_sync_date(constants.SYNC_END_DATE) is None
                ):
                    messagebox.showerror("Invalid Date", "Please enter valid date.")
                    return 0

                # if (
                #     "Ledgers" in constants.SELECTED_MODULES
                #     and len(constants.SELECTED_MODULES) == 1
                # ):
                #     messagebox.showerror(
                #         "Sync Issue",
                #         "Please select at least one more module along with Ledgers for sync.",
                #     )
                #     return 0

                def stop_thread_process():
                    nonlocal rebuild_scheduled
                    constants.STOP_THREAD = True
                    messagebox.showerror("eVital<>Tally Connects", "Sync Stopped Abnormally !!")
                    if not rebuild_scheduled:
                        rebuild_scheduled = True
                        re_create_main_content()

                if constants.SYNC_RUNNING:
                    messagebox.showerror(
                        "Sync Issue", "A sync is already running. Please wait."
                    )
                    return 0

                constants.STOP_THREAD = False
                thread1 = threading.Thread(
                    target=start_background_thread, args=(True, one_sync), daemon=True
                )
                # check_thread_status()
                thread1.start()

                for widget in right_panel.winfo_children():
                    if widget.winfo_exists():
                        widget.destroy()

                # print()
                thread1 = threading.Thread(target=check_thread_status, daemon=True)
                # check_thread_status()
                thread1.start()

                if getattr(self, "_logout_label", None) is not None:
                    self._logout_label.pack_forget()
                    self._user_label.pack_forget()

                # right_panel.config(background="#E7F6FF")
                right_panel2 = tk.Frame(right_panel, width=900, bg="#E7F6FF")
                right_panel2.pack(fill=tk.BOTH, expand=True)
                # title_bar = tk.Frame(right_panel2, width=900, bg="#E7F6FF")
                # title_bar.pack(fill=tk.X)
                # close_button = tk.Button(title_bar, text='x', font=header_font, command=close_window, bg='#E7F6FF', fg='#044C9D', borderwidth=0, relief=tk.SUNKEN)
                # close_button.pack(side=tk.RIGHT, padx=20, pady=(10,5))
                # sync_frame = tk.Frame(right_panel2, bg="white")
                # sync_frame.pack(fill=tk.BOTH, expand=True, pady=0)

                # Load GIF and create frames
                gif_path = r"lib\images\GIF.gif"  # Update with your gif path
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

                constants.CURRENT_BRANCH_SYNC = tk.StringVar(value="")
                # print('➡ tk_screen.py:731 constants.CURRENT_BRANCH_SYNC:', constants.CURRENT_BRANCH_SYNC)
                version_label = tk.Label(
                    right_panel2,
                    textvariable=constants.CURRENT_BRANCH_SYNC,
                    bg="#E7F6FF",
                    fg="Black",
                    font=header_font2,
                )

                sync_all_button = CTkButton(
                    right_panel2,
                    text="Stop",
                    fg_color="#ED5A4A",
                    text_color="white",
                    hover_color="#C93A2B",
                    font=CTkFont(family="Manrope", size=16, weight="bold"),
                    height=35,
                    width=85,
                    command=stop_thread_process,
                )

                gif_label = tk.Label(right_panel2, bg="#E7F6FF")
                gif_label.pack(anchor=tk.N, pady=(60, 20))

                version_label.pack(pady=(0, 20), padx=40, anchor=tk.N)

                sync_all_button.pack(padx=40)
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
                self.winfo_toplevel().register_follow_overlay(overlay)

                # Display blurred background
                bg_image = ImageTk.PhotoImage(blurred_screen)
                bg_label = tk.Label(overlay, image=bg_image)
                bg_label.image = bg_image
                bg_label.pack(fill="both", expand=True)

                # Centered menu
                menu_frame = tk.Frame(
                    overlay, bg="white", bd=2, relief="ridge", padx=10, pady=10
                )
                menu_frame.place(relx=0.5, rely=0.5, anchor="center")

                tk.Label(
                    menu_frame,
                    text="Are you sure you want to logout?",
                    font=header_font2,
                    bg="white",
                ).pack(pady=(15, 10), padx=20)

                button_frame = tk.Frame(menu_frame, bg="white")
                button_frame.pack(pady=10)
                # print("2312")

                # YES button - Blue background with white text
                yes_button = CTkButton(
                    button_frame,
                    text="Yes",
                    width=100,
                    height=34,
                    corner_radius=6,
                    bg_color="white",
                    fg_color="#007BFF",
                    hover_color="#0056b3",
                    text_color="white",
                    font=CTkFont(family="Manrope", size=13),
                    command=lambda x=overlay: logout_account(x),
                )
                yes_button.pack(side="left", padx=10)

                # NO button - White background with blue border and text
                no_button = CTkButton(
                    button_frame,
                    text="No",
                    width=100,
                    height=34,
                    corner_radius=6,
                    bg_color="white",
                    fg_color="white",
                    hover_color="#e6f2ff",
                    text_color="#007BFF",
                    border_width=2,
                    border_color="#007BFF",
                    font=CTkFont(family="Manrope", size=13),
                    command=lambda x=overlay: x.destroy(),
                )
                no_button.pack(side="left", padx=10)

                # Function to close the overlay when clicking outside
                def on_click_outside(event):
                    if not overlay.winfo_containing(event.x_root, event.y_root):
                        overlay.destroy()

                # Bind click outside the menu to close the overlay
                overlay.bind("<Button-1>", on_click_outside)

            upper_left_panel = tk.Frame(left_panel, bg="#033D7E", height=150, width=200)
            upper_left_panel.pack(anchor=tk.N, fill=tk.X)

            # "eVital<>Tally Connects" header
            header_label = tk.Label(
                upper_left_panel,
                text="eVital<>Tally",
                bg="#033D7E",
                fg="white",
                font=header_font,
                justify=tk.LEFT,
            )
            connects_label = tk.Label(
                upper_left_panel,
                text="Connects",
                bg="#033D7E",
                fg="white",
                font=header_font,
                justify=tk.LEFT,
            )

            version_label = tk.Label(
                upper_left_panel,
                text="Version 3.10.8",
                bg="#033D7E",
                fg="#7E878C",
                font=small_font,
            )

            upper_left_panel.grid_propagate(False)
            upper_left_panel.grid_rowconfigure(0, weight=2)
            upper_left_panel.grid_rowconfigure(4, weight=1)
            upper_left_panel.grid_columnconfigure(0, weight=1)
            header_label.grid(row=1, column=0, sticky="w", padx=30)
            connects_label.grid(row=2, column=0, sticky="w", padx=30, pady=(0, 5))
            version_label.grid(row=3, column=0, sticky="w", padx=30)
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
            def auto_sync_option_selected(option, overlay):
                auto_sync_var.set(option)  # Update the label text
                constants.SYNC_TIMER = (
                    0
                    if str(option) == "Off"
                    else int(str(option).replace(" minutes", "").replace(" min", ""))
                )
                if constants.SYNC_TIMER == 0:
                    constants.STOP_THREAD = True
                start_thread(False, False)
                thread1 = threading.Thread(
                    target=check_if_require_reboot,
                    # args=(False, False),
                    daemon=True,
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
                blurred_screen = screen.filter(
                    ImageFilter.GaussianBlur(4)
                )  # Apply blur effect

                # Create overlay window
                overlay = tk.Toplevel(self)
                overlay.geometry(f"{w}x{h}+{x}+{y}")
                overlay.overrideredirect(True)
                self.winfo_toplevel().register_follow_overlay(overlay)

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
                menu_canvas = tk.Canvas(
                    overlay,
                    width=menu_w,
                    height=menu_h,
                    bg="white",
                    highlightthickness=0,
                )
                menu_canvas.place(x=menu_x, y=menu_y)

                # Draw a smooth rounded rectangle with borders
                draw_rounded_rectangle(
                    menu_canvas,
                    0,
                    0,
                    menu_w,
                    menu_h,
                    radius,
                    fill="white",
                    border_color="grey",
                    border_width=2,
                )
                # round_rectangle(menu_canvas, 0, 0, menu_w, menu_h, radius, fill="white", outline="grey", width=2)

                # Frame inside canvas for menu content
                menu_frame = tk.Frame(overlay, bg="white")
                menu_frame.place(x=menu_x + 10, y=menu_y + 10)

                tk.Label(
                    menu_frame,
                    text="Auto Sync",
                    font=("Manrope", 12, "bold"),
                    bg="white",
                ).pack(pady=(10, 5), padx=40)

                # Options
                options = ["Off", "30 min", "60 min", "90 min", "120 min", "180 min"]
                s = ttk.Style()
                s.configure(
                    "Wild.TRadiobutton",
                    background="white",
                    foreground="black",
                    font=("Manrope", 11),
                )

                for option in options:
                    pady_custom = (5, 20) if option == options[-1] else 5
                    pady_custom = 5
                    rb = ttk.Radiobutton(
                        menu_frame,
                        text=option,
                        value=option,
                        variable=auto_sync_var,
                        style="Wild.TRadiobutton",
                        command=lambda opt=option: auto_sync_option_selected(
                            opt, overlay
                        ),
                    )
                    rb.pack(anchor="w", padx=(40, 20), pady=pady_custom, ipadx=20)

                # Close overlay when clicking outside
                def on_click_outside(event):
                    #         # Only destroy if click is outside of both the overlay and the menu_frame
                    if (
                        not overlay.winfo_containing(event.x_root, event.y_root)
                        == overlay
                        and event.widget not in menu_frame.winfo_children()
                    ):
                        overlay.destroy()

                overlay.bind("<Button-1>", on_click_outside)

            # Corrected Function for Smooth Rounded Border
            def draw_rounded_rectangle(
                canvas, x1, y1, x2, y2, radius, fill, border_color, border_width
            ):
                """Draws a smooth rounded rectangle without missing corners or random lines."""
                points = [
                    (x1 + radius, y1),
                    (x2 - radius, y1),
                    (x2, y1),
                    (x2, y1 + radius),
                    (x2, y2 - radius),
                    (x2, y2),
                    (x2 - radius, y2),
                    (x1 + radius, y2),
                    (x1, y2),
                    (x1, y2 - radius),
                    (x1, y1 + radius),
                    (x1, y1),
                ]
                # points = [
                #     (x1 + radius, y1), (x2 - radius, y1),
                #     (x2, y1 + radius), (x2, y2 - radius),
                #     (x2 - radius, y2), (x1 + radius, y2),
                #     (x1, y2 - radius), (x1, y1 + radius),
                # ]
                # print('➡ tk_screen.py:1149 points:', points)

                # Create rounded shape
                canvas.create_polygon(
                    points,
                    smooth=True,
                    fill=fill,
                    outline=border_color,
                    width=border_width,
                )

            def round_rectangle(canvas, x1, y1, x2, y2, radius=25, **kwargs):

                points = [
                    x1 + radius,
                    y1,
                    x1 + radius,
                    y1,
                    x2 - radius,
                    y1,
                    x2 - radius,
                    y1,
                    x2,
                    y1,
                    x2,
                    y1 + radius,
                    x2,
                    y1 + radius,
                    x2,
                    y2 - radius,
                    x2,
                    y2 - radius,
                    x2,
                    y2,
                    x2 - radius,
                    y2,
                    x2 - radius,
                    y2,
                    x1 + radius,
                    y2,
                    x1 + radius,
                    y2,
                    x1,
                    y2,
                    x1,
                    y2 - radius,
                    x1,
                    y2 - radius,
                    x1,
                    y1 + radius,
                    x1,
                    y1 + radius,
                    x1,
                    y1,
                ]
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
            # Caches saved by older versions may not contain a "mobile"
            # key - fall back to the logged-in business details so the
            # side panel never renders an empty identity.
            if str(constants.MOBILE).strip() == "":
                try:
                    logged_in = constants.LOGIN_RESPONSE["data"][
                        "business_details"
                    ]["logged_in_business"]
                    constants.MOBILE = (
                        logged_in.get("mobile", "")
                        or logged_in.get("entity_code", "")
                    )
                except (KeyError, TypeError, AttributeError):
                    pass
            constants.MOBILE_VAR = tk.StringVar(value=constants.MOBILE)
            user_label = tk.Label(
                left_panel,
                textvariable=constants.MOBILE_VAR,
                bg="#004BA8",
                fg="white",
                font=header_font2,
                anchor=tk.W,
                justify=tk.LEFT,
                wraplength=160,
            )

            # logout_label = tk.Button(left_panel, text="Logout >", bg="#004BA8", fg="white",
            #                         highlightbackground='#004BA8', highlightcolor='#004BA8', borderwidth=0,font=label_font2, justify=tk.LEFT, relief=tk.SUNKEN, command=show_logout_popup)
            # logout_label.pack(pady=(0, 20), padx=25, anchor=tk.W)
            logout_label = tk.Label(
                left_panel,
                text="Logout >",
                bg="#004BA8",
                fg="white",
                cursor="hand2",
                font=label_font2,
                anchor=tk.W,
                justify=tk.LEFT,
                wraplength=160,
            )
            logout_label.pack(
                side=tk.BOTTOM, anchor=tk.W, pady=(0, 50), padx=30
            )
            logout_label.bind("<Button-1>", show_logout_popup)

            user_label.pack(
                side=tk.BOTTOM, anchor=tk.W, pady=(0, 8), padx=30
            )

            self._logout_label = logout_label
            self._user_label = user_label

            left_panel.pack_propagate(False)

        # try:
        #     self.iconbitmap(".\\lib\\images\\app_icon.ico")
        #     print("Window icon loaded")
        # except Exception as e:
        #     print(f"Error loading window icon: {e}")

        # drag_layer = tk.Frame(
        #     self,
        #     # bg="#0CA1F6",
        #     bg="white",
        #     height=35
        # )
        # drag_layer.pack(side=tk.TOP, fill=tk.X)

        # Load and display icon in title bar
        # icon_path = "./lib/images/logo2.ico"  # or use .png
        # try:
        #     icon_image = Image.open(icon_path)
        #     icon_image = icon_image.resize((20, 20), Image.Resampling.LANCZOS)
        #     icon_image_tk = ImageTk.PhotoImage(icon_image)

        #     icon_label = tk.Label(
        #         drag_layer,
        #         image=icon_image_tk,
        #         bg="white"
        #     )
        #     icon_label.image = icon_image_tk  # Keep reference
        #     icon_label.pack(side=tk.LEFT, padx=(15, 5), pady=(3, 0))
        #     print("Title bar icon loaded")
        # except Exception as e:
        #     print(f"Error loading title bar icon: {e}")

        # Title (left side)
        # title_label = tk.Label(
        #     drag_layer,
        #     text="eVital<>Tally Connects",
        #     # bg="#0CA1F6",
        #     bg="white",
        #     # fg="white",
        #     fg="black",
        #     font=header_font5b
        # )
        # title_label.pack(side=tk.LEFT, padx=(5, 0), pady=(3,0))

        # Close button (right side)
        # close_button = tk.Label(
        #     drag_layer,
        #     text="✕",
        #     # bg="#0CA1F6",
        #     bg="white",
        #     # fg="white",
        #     fg="black",
        #     font=("Segoe UI", 8, "bold"),
        #     cursor="hand2"
        # )
        # close_button.pack(side=tk.RIGHT, padx=15, pady=3)

        # def on_close_enter(e):
        #     close_button.config(bg="#E81123")  # Windows red

        # def on_close_leave(e):
        #     # close_button.config(bg="#0CA1F6")
        #     close_button.config(bg="white")

        # close_button.bind("<Enter>", on_close_enter)
        # close_button.bind("<Leave>", on_close_leave)

        # drag_layer.bind("<Button-1>", self.controller.start_move)
        # drag_layer.bind("<B1-Motion>", self.controller.do_move)

        # Also allow dragging from title text
        # title_label.bind("<Button-1>", self.controller.start_move)
        # title_label.bind("<B1-Motion>", self.controller.do_move)

        # close_button.bind("<Button-1>", lambda e: close_window())

        left_panel = tk.Frame(self, bg="#004BA8", width=220, height=600)
        left_panel.pack(side=tk.LEFT, fill=tk.Y)

        left_panel.pack_propagate(False)
        right_panel = tk.Frame(self, bg="white", width=600, height=150)
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


class SyncHistoryScreen(tk.Frame):
    RANGE_CHIPS = [
        ("last_7_days", "Last 7 days"),
        ("last_15_days", "Last 15 days"),
        ("last_30_days", "Last 30 days"),
        # ("last_60_days", "Last 60 days"),
        # ("last_90_days", "Last 90 days"),
    ]
    MODULE_LABELS = {"accounts": "Ledgers"}

    HEAD_H = 44
    ROW_H = 58
    PAD_L = 20
    PAD_R = 22

    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller
        self.parent = parent
        parent.title("eVital<>Tally Connects")

        ACCENT = "#0CA1F6"
        HEADER_BG = "#004BA8"
        HEADER_HOVER = "#003A80"
        HOVER_BG = "#E7F6FF"
        TEXT = "#1F2430"
        MUTED = "#7E878C"
        BORDER = "#E3E8EF"
        ZEBRA_BG = "#F0F4F8"
        HEAD_BG = "#EEF4FA"

        f_title = font.Font(family="Manrope", size=15, weight="bold")
        f_eyebrow = font.Font(family="Manrope", size=9, weight="bold")
        f_h3 = font.Font(family="Manrope", size=11, weight="bold")
        f_body = font.Font(family="Manrope", size=10)
        f_body_b = font.Font(family="Manrope", size=10, weight="bold")
        f_small = font.Font(family="Manrope", size=9)
        f_small_b = font.Font(family="Manrope", size=9, weight="bold")
        f_empty = font.Font(family="Segoe UI Emoji", size=26)

        state = {
            "page": 1,
            "rpp": 20,
            "total": 0,
            "loading": False,
            "range": "last_7_days",
            "records": [],
            "err": None,
        }
        dots_job = {"id": None}
        resize_job = {"id": None}
        btn_state = {"prev": False, "next": False}
        retry_holder = {"btn": None}
        tip_holder = {"win": None, "after": None}

        def go_back(e=None):
            controller.show_frame("Dashboard")

        def range_label(value):
            for v, lbl in self.RANGE_CHIPS:
                if v == value:
                    return lbl
            return str(value)

        def module_label(v):
            s = str(v or "").strip()
            if not s:
                return "-"
            low = s.lower()
            if low in self.MODULE_LABELS:
                return self.MODULE_LABELS[low]
            return s.title() if s.islower() else s

        def fmt_date_str(value):
            raw = str(value or "")
            for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
                try:
                    return datetime.strptime(raw, fmt).strftime("%d %b %Y")
                except ValueError:
                    continue
            return raw if raw else "-"

        def split_sync_dt(value):
            parts = str(value or "").split(" ")
            if len(parts) >= 2:
                return fmt_date_str(parts[0]), " ".join(parts[1:])
            raw = str(value or "")
            return (raw, "") if raw else ("-", "")

        def fmt_count(value):
            try:
                return f"{int(value):,}"
            except (TypeError, ValueError):
                return str(value) if value not in (None, "") else "-"

        def status_style(v):
            s = str(v or "").strip().lower()
            if s in ("success", "successful", "completed", "done", "ok"):
                return "#E6F6EC", "#1E9E5A"
            if s in ("failed", "failure", "error", "aborted", "stopped"):
                return "#FDECEA", "#D93025"
            if s in ("pending", "partial", "in_progress", "processing", "running"):
                return "#FFF4E0", "#B7791F"
            return "#EEF1F4", "#5A6572"

        def status_icon(v):
            s = str(v or "").strip().lower()
            if s in ("success", "successful", "completed", "done", "ok"):
                return "✓"
            if s in ("failed", "failure", "error", "aborted", "stopped"):
                return "✕"
            if s in ("pending", "partial", "in_progress", "processing", "running"):
                return "◐"
            return "•"

        def ellipsize(txt, fnt, maxw):
            if fnt.measure(txt) <= maxw:
                return txt
            while len(txt) > 1 and fnt.measure(txt + "…") > maxw:
                txt = txt[:-1]
            return txt + "…"

        header_wrap = tk.Frame(self, bg="white")
        header_wrap.pack(fill=tk.X, padx=14, pady=(14, 0))

        header = CTkFrame(header_wrap, fg_color=HEADER_BG, corner_radius=14)
        header.pack(fill=tk.X)

        back_btn = CTkButton(
            header,
            text="←  Back",
            fg_color="#033D7E",
            hover_color="#022D5E",
            text_color="white",
            font=("Manrope", 12, "bold"),
            width=90,
            height=32,
            corner_radius=8,
            command=go_back,
        )
        back_btn.pack(side=tk.LEFT, padx=(16, 12), pady=14)

        title_block = tk.Frame(header, bg=HEADER_BG)
        title_block.pack(side=tk.LEFT, fill=tk.Y, pady=14)
        tk.Label(
            title_block,
            text="SYNC HISTORY",
            bg=HEADER_BG,
            fg="#7EC8F8",
            font=("Manrope", 9, "bold"),
            anchor=tk.W,
        ).pack(anchor=tk.W)
        tk.Label(
            title_block,
            text="Module-wise Sync Activity",
            bg=HEADER_BG,
            fg="white",
            font=("Manrope", 15, "bold"),
            anchor=tk.W,
        ).pack(anchor=tk.W, pady=(2, 0))

        badge_wrap = tk.Frame(header, bg=HEADER_BG)
        badge_wrap.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 20))
        total_badge = CTkLabel(
            badge_wrap,
            text="",
            corner_radius=8,
            bg_color=HEADER_BG,
            fg_color="#022D5E",
            text_color="white",
            font=("Manrope", 12, "bold"),
            padx=14,
            pady=8,
        )
        total_badge.pack(expand=True)

        toolbar = tk.Frame(self, bg="white")
        toolbar.pack(fill=tk.X, padx=26, pady=(12, 8))

        tk.Label(
            toolbar, text="Period: ", bg="white", fg=MUTED, font=f_body
        ).pack(side=tk.LEFT)

        chips_frame = tk.Frame(toolbar, bg="white")
        chips_frame.pack(side=tk.LEFT, padx=(14, 0))
        chips = {}
        chip_font = CTkFont(family="Manrope", size=12, weight="bold")

        for value, label in self.RANGE_CHIPS:
            chip = CTkButton(
                chips_frame,
                text=label,
                height=34,
                width=max(104, chip_font.measure(label) + 34),
                corner_radius=16,
                border_width=1,
                border_color=BORDER,
                fg_color="white",
                text_color=TEXT,
                hover_color="#F3FAFF",
                font=chip_font,
                command=lambda v=value: select_range(v),
            )
            chip.pack(side=tk.LEFT, padx=(0, 8))

            def paint_chip(c=chip, v=value):
                sel = state["range"] == v
                c.configure(
                    fg_color=ACCENT if sel else "white",
                    text_color="white" if sel else TEXT,
                    border_color=ACCENT if sel else BORDER,
                    hover_color="#0A90DC" if sel else "#F3FAFF",
                )

            chips[value] = paint_chip

        def paint_all_chips():
            for paint in chips.values():
                paint()

        footer = tk.Frame(self, bg="white")
        footer.pack(side=tk.BOTTOM, fill=tk.X, padx=26, pady=(8, 12))

        card = tk.Frame(
            self, bg="white", highlightbackground=BORDER, highlightthickness=1
        )
        card.pack(fill=tk.BOTH, expand=True, padx=26)

        inner = tk.Frame(card, bg="white")
        inner.pack(fill=tk.BOTH, expand=True)
        inner.grid_rowconfigure(1, weight=1)
        inner.grid_columnconfigure(0, weight=1)

        head_cv = tk.Canvas(
            inner, bg=HEAD_BG, height=self.HEAD_H, bd=0, highlightthickness=0
        )
        body = tk.Canvas(inner, bg="white", bd=0, highlightthickness=0)
        sb = ttk.Scrollbar(inner, orient="vertical", command=body.yview)
        body.configure(yscrollcommand=sb.set)
        head_cv.grid(row=0, column=0, sticky="ew")
        body.grid(row=1, column=0, sticky="nsew")
        sb.grid(row=0, column=1, rowspan=2, sticky="ns")

        COL_FR = [0.22, 0.17, 0.12, 0.17, 0.32]

        def compute_cols(w):
            usable = w - self.PAD_L - self.PAD_R
            xs = []
            cur = self.PAD_L
            for frac in COL_FR:
                xs.append(cur)
                cur += usable * frac
            mids = [xs[i] + usable * COL_FR[i] / 2 for i in range(5)]
            widths = [usable * frac - 18 for frac in COL_FR]
            return xs, mids, widths, w

        range_lbl = tk.Label(footer, text="", bg="white", fg=MUTED, font=f_small)
        range_lbl.pack(side=tk.LEFT)

        def nav_button(key, text, cmd):
            lbl = tk.Label(
                footer,
                text=text,
                bg="white",
                fg=MUTED,
                font=f_small_b,
                cursor="arrow",
                padx=14,
                pady=6,
                highlightbackground=BORDER,
                highlightthickness=1,
            )

            def click(e):
                if btn_state[key]:
                    cmd(e)

            lbl.bind("<Button-1>", click)
            lbl.bind(
                "<Enter>",
                lambda e: lbl.configure(bg=HOVER_BG) if btn_state[key] else None,
            )
            lbl.bind("<Leave>", lambda e: lbl.configure(bg="white"))
            return lbl

        def go_prev(e=None):
            if state["loading"] or state["page"] <= 1:
                return
            state["page"] -= 1
            load_data()

        def go_next(e=None):
            if state["loading"] or state["page"] >= total_pages():
                return
            state["page"] += 1
            load_data()

        next_btn = nav_button("next", "Next ›", go_next)
        next_btn.pack(side=tk.RIGHT)

        page_info = tk.Label(footer, text="", bg="white", fg=TEXT, font=f_small_b)
        page_info.pack(side=tk.RIGHT, padx=16)

        prev_btn = nav_button("prev", "‹ Prev", go_prev)
        prev_btn.pack(side=tk.RIGHT)

        rpp_btn = tk.Menubutton(
            footer,
            text=f"{state['rpp']} / page ▾",
            bg="white",
            fg=TEXT,
            font=f_small,
            cursor="hand2",
            relief=tk.FLAT,
            bd=0,
            padx=8,
        )
        rpp_menu = tk.Menu(
            rpp_btn,
            tearoff=0,
            bg="white",
            fg="#333",
            font=f_small,
            bd=0,
            activebackground=HOVER_BG,
            activeforeground=ACCENT,
        )
        for v in (20, 50, 100):
            rpp_menu.add_command(label=str(v), command=lambda vv=v: set_rpp(vv))
        rpp_btn["menu"] = rpp_menu
        rpp_btn.pack(side=tk.RIGHT, padx=(0, 14))

        def set_rpp(v):
            if state["loading"] or v == state["rpp"]:
                return
            state["rpp"] = v
            state["page"] = 1
            rpp_btn.configure(text=f"{v} / page ▾")
            load_data()

        def total_pages():
            rpp = state["rpp"] if state["rpp"] else 20
            return max(1, (state["total"] + rpp - 1) // rpp)

        def update_pagination():
            pages = total_pages()
            page_info.configure(text=f"Page {state['page']} of {pages}")
            can_prev = state["page"] > 1 and not state["loading"]
            can_next = state["page"] < pages and not state["loading"]
            btn_state["prev"] = can_prev
            btn_state["next"] = can_next
            prev_btn.configure(
                fg=TEXT if can_prev else MUTED,
                cursor="hand2" if can_prev else "arrow",
            )
            next_btn.configure(
                fg=TEXT if can_next else MUTED,
                cursor="hand2" if can_next else "arrow",
            )
            if state["total"] > 0:
                start_i = (state["page"] - 1) * state["rpp"] + 1
                end_i = min(state["page"] * state["rpp"], state["total"])
                range_lbl.configure(
                    text=f"Showing {start_i}–{end_i} of {state['total']:,}"
                )
            else:
                range_lbl.configure(text="No records")

        def cancel_anim():
            if dots_job["id"] is not None:
                try:
                    self.after_cancel(dots_job["id"])
                except Exception:
                    pass
                dots_job["id"] = None

        def hide_tip():
            if tip_holder["after"] is not None:
                try:
                    self.after_cancel(tip_holder["after"])
                except Exception:
                    pass
                tip_holder["after"] = None
            if tip_holder["win"] is not None:
                try:
                    tip_holder["win"].destroy()
                except Exception:
                    pass
                tip_holder["win"] = None

        def schedule_tip(e, msg):
            hide_tip()

            def show():
                tip_holder["after"] = None
                if not self.winfo_exists():
                    return
                win = tk.Toplevel(self)
                win.wm_overrideredirect(True)
                win.attributes("-topmost", True)
                tk.Label(
                    win,
                    text=msg,
                    bg="#2B3440",
                    fg="white",
                    font=f_small,
                    justify=tk.LEFT,
                    wraplength=420,
                    padx=10,
                    pady=6,
                ).pack()
                x = e.x_root + 14
                y = e.y_root + 18
                win.update_idletasks()
                if x + win.winfo_reqwidth() > self.winfo_screenwidth() - 8:
                    x = e.x_root - win.winfo_reqwidth() - 10
                win.wm_geometry(f"+{x}+{y}")
                tip_holder["win"] = win

            tip_holder["after"] = self.after(450, show)

        def on_destroy(e):
            if e.widget is self:
                hide_tip()

        self.bind("<Destroy>", on_destroy)

        def clear_canvas():
            cancel_anim()
            hide_tip()
            if retry_holder["btn"] is not None:
                try:
                    retry_holder["btn"].destroy()
                except Exception:
                    pass
                retry_holder["btn"] = None
            head_cv.delete("all")
            body.delete("all")

        def draw_loading(W, H):
            cy0 = max(H / 2 - 16, 100)
            item = body.create_text(
                W / 2,
                cy0,
                text="Loading sync history",
                font=f_body,
                fill=MUTED,
            )

            def anim(n=0):
                try:
                    if not body.winfo_exists():
                        return
                    body.itemconfig(item, text="Loading sync history" + "." * (n % 4))
                    dots_job["id"] = self.after(350, lambda: anim(n + 1))
                except tk.TclError:
                    return

            def show_hint():
                try:
                    if not body.winfo_exists() or not state["loading"]:
                        return
                    body.create_text(
                        W / 2,
                        cy0 + 26,
                        text="Fetching records from server — this may take a moment",
                        font=f_small,
                        fill="#A6ADB3",
                    )
                except tk.TclError:
                    pass

            anim()
            self.after(4000, show_hint)

        def draw_error(W, H):
            cy0 = max(H / 2 - 46, 90)
            body.create_text(
                W / 2, cy0, text="⚠", font=("Segoe UI Emoji", 24), fill="#D93025"
            )
            body.create_text(
                W / 2,
                cy0 + 40,
                text=state["err"],
                font=f_body,
                fill="#D93025",
                width=min(W - 120, 620),
                justify=tk.CENTER,
            )
            btn = CTkButton(
                self,
                text="Retry",
                hover_color="#033D7E",
                text_color="white",
                fg_color=ACCENT,
                font=CTkFont(family="Manrope", size=12, weight="bold"),
                height=32,
                width=96,
                corner_radius=6,
                command=lambda: on_refresh(),
            )
            retry_holder["btn"] = btn
            body.create_window(W / 2, cy0 + 94, window=btn)

        def draw_empty(W, H):
            cy0 = max(H / 2 - 40, 100)
            body.create_text(W / 2, cy0, text="🕘", font=f_empty, fill="#B9C4CE")
            body.create_text(
                W / 2, cy0 + 46, text="No sync history found", font=f_h3, fill=TEXT
            )
            body.create_text(
                W / 2,
                cy0 + 72,
                text="Try a different period using the filters above.",
                font=f_small,
                fill=MUTED,
            )

        def draw_rows(records, W):
            xs, mids, widths, _ = compute_cols(W)
            cy_step = self.ROW_H
            y = 0
            for i, rec in enumerate(records):
                bgc = "white" if i % 2 == 0 else ZEBRA_BG
                tag = f"r{i}"
                bgtag = f"r{i}_bg"
                cy = y + cy_step / 2
                body.create_rectangle(
                    0, y, W, y + cy_step, fill=bgc, outline="", tags=(tag, bgtag)
                )

                name = module_label(rec.get("module_name"))
                mod_item = body.create_text(
                    mids[0],
                    cy,
                    text=ellipsize(name, f_body_b, widths[0]),
                    font=f_body_b,
                    fill=TEXT,
                    tags=tag,
                )

                d_str, t_str = split_sync_dt(rec.get("sync_datetime"))
                if t_str:
                    body.create_text(
                        mids[1], cy - 8, text=d_str, font=f_body, fill=TEXT, tags=tag
                    )
                    body.create_text(
                        mids[1],
                        cy + 10,
                        text=t_str,
                        font=f_small,
                        fill=MUTED,
                        tags=tag,
                    )
                else:
                    body.create_text(
                        mids[1], cy, text=d_str, font=f_body, fill=TEXT, tags=tag
                    )

                pbg, pfg = status_style(rec.get("status"))
                err_msg = str(rec.get("error_message") or "").strip()
                icon = status_icon(rec.get("status"))
                stag = f"{tag}_st"
                bd = 26
                bcx, bcy = mids[2], cy
                body.create_oval(
                    bcx - bd / 2,
                    bcy - bd / 2,
                    bcx + bd / 2,
                    bcy + bd / 2,
                    fill=pbg,
                    outline="",
                    tags=(tag, stag),
                )
                body.create_text(
                    bcx,
                    bcy - 1,
                    text=icon,
                    font=("Segoe UI Symbol", 11, "bold"),
                    fill=pfg,
                    tags=(tag, stag),
                )

                body.create_text(
                    mids[3],
                    cy,
                    text=fmt_count(rec.get("records_count")),
                    font=f_body,
                    fill=TEXT,
                    tags=tag,
                )

                s_d, e_d = rec.get("start_date"), rec.get("end_date")
                if not s_d and not e_d:
                    period_txt = "—"
                    period_fill = MUTED
                else:
                    period_txt = (
                        f"{fmt_date_str(s_d)}  →  {fmt_date_str(e_d)}"
                    )
                    period_fill = "#444444"
                body.create_text(
                    mids[4],
                    cy,
                    text=ellipsize(period_txt, f_body, widths[4]),
                    font=f_body,
                    fill=period_fill,
                    tags=tag,
                )

                def on_enter(e, t=bgtag, m=mod_item):
                    body.itemconfig(t, fill=HOVER_BG)
                    try:
                        body.itemconfig(m, fill=ACCENT)
                    except tk.TclError:
                        pass

                def on_leave(e, t=bgtag, b=bgc, m=mod_item):
                    hide_tip()
                    body.itemconfig(t, fill=b)
                    try:
                        body.itemconfig(m, fill=TEXT)
                    except tk.TclError:
                        pass

                body.tag_bind(tag, "<Enter>", on_enter)
                body.tag_bind(tag, "<Leave>", on_leave)
                if err_msg:
                    body.tag_bind(
                        stag, "<Enter>", lambda e: body.configure(cursor="hand2")
                    )
                    body.tag_bind(
                        stag,
                        "<Motion>",
                        lambda e, m=err_msg: schedule_tip(e, m),
                    )
                    body.tag_bind(
                        stag,
                        "<Leave>",
                        lambda e: (body.configure(cursor=""), hide_tip()),
                    )
                y += cy_step

            line_h = max(y, body.winfo_height())
            for bx in (xs[1], xs[2], xs[3], xs[4]):
                body.create_line(bx, 6, bx, line_h - 6, fill="#D8E1EA")
            body.configure(scrollregion=(0, 0, W, max(y, 1)))

        def draw_all():
            W = body.winfo_width()
            H = body.winfo_height()
            if W < 60:
                return
            clear_canvas()
            xs, mids, widths, _ = compute_cols(W)
            head_cv.create_rectangle(0, 0, W, self.HEAD_H, fill=HEAD_BG, outline="")
            head_cv.create_line(
                0, self.HEAD_H - 1, W, self.HEAD_H - 1, fill="#D7E2EE"
            )
            texts = ["MODULE", "SYNCED AT", "STATUS", "RECORDS", "PERIOD"]
            for i, txt in enumerate(texts):
                head_cv.create_text(
                    mids[i],
                    self.HEAD_H / 2,
                    text=txt,
                    font=f_small_b,
                    fill="#5A6572",
                )
            if state["loading"]:
                draw_loading(W, H)
            elif state["err"]:
                draw_error(W, H)
            elif state["records"]:
                for bx in (xs[1], xs[2], xs[3], xs[4]):
                    head_cv.create_line(bx, 8, bx, self.HEAD_H - 8, fill="#D0DCE9")
                draw_rows(state["records"], W)
            else:
                draw_empty(W, H)
            body.yview_moveto(0)

        def on_resize(e):
            if resize_job["id"] is not None:
                try:
                    self.after_cancel(resize_job["id"])
                except Exception:
                    pass

            def do_resize():
                resize_job["id"] = None
                draw_all()

            resize_job["id"] = self.after(80, do_resize)

        body.bind("<Configure>", on_resize)
        head_cv.bind("<Configure>", on_resize)

        def on_wheel(e):
            if state["loading"]:
                return
            if getattr(e, "delta", 0):
                body.yview_scroll(-1 * (e.delta // 120), "units")
            elif getattr(e, "num", None) == 4:
                body.yview_scroll(-1, "units")
            elif getattr(e, "num", None) == 5:
                body.yview_scroll(1, "units")

        body.bind("<MouseWheel>", on_wheel)
        body.bind("<Button-4>", on_wheel)
        body.bind("<Button-5>", on_wheel)

        def select_range(v):
            if state["loading"] or state["range"] == v:
                return
            state["range"] = v
            state["page"] = 1
            paint_all_chips()
            load_data()

        def render_response(res):
            state["loading"] = False
            if not isinstance(res, dict) or str(res.get("status_code")) not in (
                "1",
                "1.0",
            ):
                state["err"] = (
                    str(
                        res.get("error_message")
                        or res.get("status_message")
                        or "Failed to fetch sync history."
                    )
                    if isinstance(res, dict)
                    else "Failed to fetch sync history."
                )
                state["records"] = []
                state["total"] = 0
            else:
                state["err"] = None
                data = res.get("data") or {}
                state["records"] = data.get("results") or []
                try:
                    state["total"] = int(data.get("total_records") or 0)
                except (TypeError, ValueError):
                    state["total"] = 0
                try:
                    state["rpp"] = int(data.get("rpp") or state["rpp"])
                except (TypeError, ValueError):
                    pass
                try:
                    state["page"] = int(data.get("page") or state["page"])
                except (TypeError, ValueError):
                    pass
            total_badge.configure(
                text=f"  {state['total']:,}  \n  RECORDS  " if state["total"] else "",
                fg_color="#022D5E" if state["total"] else "transparent",
            )
            update_pagination()
            draw_all()

        def load_data():
            if state["loading"]:
                return
            state["loading"] = True
            state["records"] = []
            state["err"] = None
            update_pagination()
            draw_all()

            date_range = state["range"]
            page = state["page"]
            rpp = state["rpp"]

            def worker():
                res = get_entity_sync_history(date_range, page=page, rpp=rpp)

                def done():
                    try:
                        if not self.winfo_exists():
                            return
                    except tk.TclError:
                        return
                    render_response(res)

                try:
                    self.after(0, done)
                except RuntimeError:
                    pass

            threading.Thread(target=worker, daemon=True).start()

        def on_refresh():
            if state["loading"]:
                return
            state["page"] = 1
            load_data()

        self.bind("<Escape>", go_back)
        paint_all_chips()
        update_pagination()
        load_data()


class LogViewerApp:
    def __init__(self, main_app=None):
        self.log_manager = LogManagerObj
        self.root = None
        self.main_app = main_app
        self._refresh_job = None

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
        self.root.title("Logs | eVital<>Tally Connects")
        self.root.geometry("800x600")
        self.root.minsize(640, 420)
        self.root.configure(bg="#E7F6FF")
        try:
            self.root.iconbitmap("./lib/images/logo2.ico")
        except tk.TclError:
            pass

        self.root.protocol("WM_DELETE_WINDOW", self.hide_log_viewer)

        # Set up the widgets
        self.create_widgets()
        self._schedule_auto_refresh()

    def _font(self, size=10, bold=False):
        return font.Font(
            family="Manrope", size=size, weight="bold" if bold else "normal"
        )

    def hide_log_viewer(self):
        """Hide the log viewer window"""
        self._cancel_refresh_job()
        if self.root is not None:
            try:
                self.root.destroy()
            except tk.TclError:
                pass
            self.root = None

    def create_widgets(self):
        # ================= HEADER =================
        HEADER_BG = "#004BA8"

        header_wrap = tk.Frame(self.root, bg="white")
        header_wrap.pack(fill=tk.X, padx=14, pady=(14, 0))

        header = CTkFrame(header_wrap, fg_color=HEADER_BG, corner_radius=14)
        header.pack(fill=tk.X)

        title_block = tk.Frame(header, bg=HEADER_BG)
        title_block.pack(side=tk.LEFT, fill=tk.Y, pady=14, padx=(20, 0))
        tk.Label(
            title_block,
            text="LOG MANAGER",
            bg=HEADER_BG,
            fg="#7EC8F8",
            font=("Manrope", 9, "bold"),
            anchor=tk.W,
        ).pack(anchor=tk.W)
        tk.Label(
            title_block,
            text="Application Logs & Activity",
            bg=HEADER_BG,
            fg="white",
            font=("Manrope", 15, "bold"),
            anchor=tk.W,
        ).pack(anchor=tk.W, pady=(2, 0))

        # ================= TOOLBAR =================
        toolbar = tk.Frame(self.root, bg="white")
        toolbar.pack(fill=tk.X, padx=14, pady=(14, 4))

        ttk.Style().configure(
            "Logs.TCheckbutton",
            background="white",
            foreground="black",
            focuscolor="white",
            lightcolor="white",
            darkcolor="white",
        )

        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            toolbar,
            text="Auto-scroll",
            variable=self.auto_scroll_var,
            style="Logs.TCheckbutton",
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=(20, 10))

        self.auto_refresh_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            toolbar,
            text="Auto-refresh",
            variable=self.auto_refresh_var,
            style="Logs.TCheckbutton",
            cursor="hand2",
            command=self._on_auto_refresh_toggle,
        ).pack(side=tk.LEFT, padx=(0, 10))

        refresh_btn = CTkButton(
            toolbar,
            text="Refresh",
            fg_color="#0CA1F6",
            hover_color="#033D7E",
            text_color="white",
            font=CTkFont(family="Manrope", size=12, weight="bold"),
            height=30,
            width=90,
            corner_radius=6,
            command=self.refresh_logs,
        )
        refresh_btn.pack(side=tk.RIGHT, padx=(0, 8), pady=6)

        clear_btn = CTkButton(
            toolbar,
            text="Clear",
            fg_color="#ED5A4A",
            hover_color="#C93A2B",
            text_color="white",
            font=CTkFont(family="Manrope", size=12, weight="bold"),
            height=30,
            width=90,
            corner_radius=6,
            command=self.clear_logs,
        )
        clear_btn.pack(side=tk.RIGHT, padx=(0, 14), pady=6)

        # ================= LOG TEXT =================
        text_frame = tk.Frame(self.root, bg="white", bd=1, relief="solid")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=(8, 6))

        self.log_text = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            bg="white",
            fg="#333",
            insertbackground="#0CA1F6",
            selectbackground="#0CA1F6",
            selectforeground="white",
            font=self._font(size=10),
            padx=8,
            pady=6,
            highlightthickness=0,
            bd=0,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # ================= STATUS BAR =================
        status = tk.Frame(self.root, bg="#E7F6FF")
        status.pack(fill=tk.X, side=tk.BOTTOM)

        self.count_label = tk.Label(
            status,
            text="",
            bg="#E7F6FF",
            fg="#7E878C",
            font=self._font(size=9),
        )
        self.count_label.pack(side=tk.LEFT, padx=14, pady=6)

        self.last_cleared_label = tk.Label(
            status,
            text="",
            bg="#E7F6FF",
            fg="#7E878C",
            font=self._font(size=9),
        )
        self.last_cleared_label.pack(side=tk.RIGHT, padx=14, pady=6)

        self.update_last_cleared_info()

    def _on_auto_refresh_toggle(self):
        if self.auto_refresh_var.get():
            self._schedule_auto_refresh()
        else:
            self._cancel_refresh_job()

    def _cancel_refresh_job(self):
        if self._refresh_job is not None:
            try:
                if self.root is not None and self.root.winfo_exists():
                    self.root.after_cancel(self._refresh_job)
            except (tk.TclError, AttributeError):
                pass
            self._refresh_job = None

    def _schedule_auto_refresh(self):
        self._cancel_refresh_job()
        if (
            self.root is not None
            and self.root.winfo_exists()
            and self.auto_refresh_var.get()
        ):
            self.refresh_logs()
            self._refresh_job = self.root.after(3000, self._schedule_auto_refresh)

    def refresh_logs(self):
        if not hasattr(self, "log_text") or not self.log_text.winfo_exists():
            return
        self.all_logs = self.log_manager.read_logs()
        self._render_logs()

    def _render_logs(self):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        for log in self.all_logs:
            self.log_text.insert(tk.END, log + "\n")
        self.log_text.configure(state=tk.DISABLED)

        if self.auto_scroll_var.get():
            self.log_text.see(tk.END)

        if self.count_label.winfo_exists():
            self.count_label.config(
                text=f"{len(self.all_logs)} entries"
            )

    def clear_logs(self):
        if messagebox.askyesno("Clear Logs", "Are you sure you want to clear all logs?"):
            if self.log_manager.clear_logs():
                self.refresh_logs()
                self.update_last_cleared_info()
                messagebox.showinfo("Success", "Logs cleared successfully")
            else:
                messagebox.showerror("Error", "Failed to clear logs")

    def update_last_cleared_info(self):
        if (
            hasattr(self, "last_cleared_label")
            and self.last_cleared_label.winfo_exists()
        ):
            last_date = self.log_manager.get_last_clear_date_formatted()
            self.last_cleared_label.config(text=f"Last cleared: {last_date}")


# LogViewerApp()
# Run the application
if __name__ == "__main__":
    app = App()
    app.mainloop()
    freeze_support()
