import ctypes
import tkinter as tk
from tkinter import ttk
from PIL import ImageGrab, ImageFilter, ImageTk

try: # >= win 8.1
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except: # win 8.0 or less
    ctypes.windll.user32.SetProcessDPIAware()
import tkinter as tk
from tkinter import ttk
from PIL import ImageGrab, ImageFilter, ImageTk

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("400x400")
        self.title("Tkinter Logout Confirmation Example")

        self.menu_button = tk.Button(self, text="Show Menu", command=self.show_menu)
        self.menu_button.pack(pady=20)

        self.logout_button = tk.Button(self, text="Logout", command=self.show_logout_popup)
        self.logout_button.pack(pady=20)

    def blur_background(self):
        x = self.winfo_rootx()
        y = self.winfo_rooty()
        w = self.winfo_width()
        h = self.winfo_height()

        screen = ImageGrab.grab(bbox=(x, y, x + w, y + h))
        return screen.filter(ImageFilter.GaussianBlur(5)), x, y, w, h

    def show_menu(self):
        blurred_screen, x, y, w, h = self.blur_background()

        overlay = tk.Toplevel(self)
        overlay.geometry(f"{w}x{h}+{x}+{y}")
        overlay.overrideredirect(True)

        bg_image = ImageTk.PhotoImage(blurred_screen)
        bg_label = tk.Label(overlay, image=bg_image)
        bg_label.image = bg_image
        bg_label.pack(fill="both", expand=True)

        menu_frame = tk.Frame(overlay, bg="white", bd=2, relief="ridge")
        menu_frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(menu_frame, text="Auto Sync", font=("Arial", 14, "bold"), bg="white").pack(pady=(10, 5))

        options = ["Off", "30 minutes", "60 minutes", "90 minutes", "120 minutes", "180 minutes"]
        selected = tk.StringVar(value="Off")

        style = ttk.Style()
        style.configure("Custom.TRadiobutton", padding=(15, 5))

        for option in options:
            rb = ttk.Radiobutton(menu_frame, text=option, value=option, variable=selected, style="Custom.TRadiobutton")
            rb.pack(anchor="w", pady=5)

        def on_click_outside(event):
            if not overlay.winfo_containing(event.x_root, event.y_root):
                overlay.destroy()

        overlay.bind("<Button-1>", on_click_outside)

    def show_logout_popup(self):
        blurred_screen, x, y, w, h = self.blur_background()

        overlay = tk.Toplevel(self)
        overlay.geometry(f"{w}x{h}+{x}+{y}")
        overlay.overrideredirect(True)

        bg_image = ImageTk.PhotoImage(blurred_screen)
        bg_label = tk.Label(overlay, image=bg_image)
        bg_label.image = bg_image
        bg_label.pack(fill="both", expand=True)

        popup_frame = tk.Frame(overlay, bg="white", bd=2, relief="ridge")
        popup_frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(popup_frame, text="Are you sure you want to logout?",
                 font=("Arial", 14, "bold"), bg="white").pack(pady=(15, 10), padx=20)

        button_frame = tk.Frame(popup_frame, bg="white")
        button_frame.pack(pady=10)

        # YES button - Blue background with white text
        yes_button = tk.Button(button_frame, text="Yes", width=10, bg="#007BFF", fg="white",
                               activebackground="#0056b3", activeforeground="white",
                               relief="flat", font=("Arial", 12, "bold"),
                               command=self.quit)
        yes_button.pack(side="left", padx=10)

        # NO button - White background with blue border and text
        no_button = tk.Button(button_frame, text="No", width=10, bg="white", fg="#007BFF",
                              activebackground="#e6f2ff", activeforeground="#0056b3",
                              highlightbackground="#007BFF", highlightthickness=2,
                              bd=2, font=("Arial", 12, "bold"),
                              command=overlay.destroy)
        no_button.pack(side="left", padx=10)

        def on_click_outside(event):
            if not popup_frame.winfo_containing(event.x_root, event.y_root):
                overlay.destroy()

        overlay.bind("<Button-1>", on_click_outside)

if __name__ == "__main__":
    app = Application()
    app.mainloop()
