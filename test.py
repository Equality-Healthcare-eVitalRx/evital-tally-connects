import ctypes
import tkinter as tk
from tkinter import ttk
from PIL import ImageGrab, ImageFilter, ImageTk

try: # >= win 8.1
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except: # win 8.0 or less
    ctypes.windll.user32.SetProcessDPIAware()

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("400x400")
        self.title("Tkinter Menu Example")

        self.button = tk.Button(self, text="Show Menu", command=self.show_menu)
        self.button.pack(pady=50)

    def show_menu(self):
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

        tk.Label(menu_frame, text="Auto Sync", font=("Arial", 14, "bold"), bg="white").pack(pady=(10, 5))

        options = ["Off", "30 minutes", "60 minutes", "90 minutes", "120 minutes", "180 minutes"]
        selected = tk.StringVar(value="90 minutes")
        
        # def done(x):
        #     rb.sel

        for option in options:
            rb = ttk.Radiobutton(menu_frame, text=option, value=option, variable=selected, command= lambda x=option: print("selected",x))
            rb.pack(anchor="w", padx=20, pady=5)

        # Remove the close button from menu
        # close_btn = tk.Button(menu_frame, text="Close", command=overlay.destroy)
        # close_btn.pack(pady=10)

        # Function to close the overlay when clicking outside
        def on_click_outside(event):
            # Only destroy if click is outside of both the overlay and the menu_frame
            if not overlay.winfo_containing(event.x_root, event.y_root) == overlay and \
               event.widget not in menu_frame.winfo_children():
                print('➡ test.py:64 event.x_root:', event.x_root)
                print('➡ test.py:65 event.y_root:', event.y_root)
                print("ds")
                overlay.destroy()

        # Bind click outside the menu to close the overlay
        overlay.bind("<Button-1>", on_click_outside)

if __name__ == "__main__":
    app = Application()
    app.mainloop()
