import tkinter as tk
from tkinter import ttk, messagebox

class PortUpdateWindow(tk.Tk):
    def __init__(self, current_port=5000):
        super().__init__()
        self.title("Change Port")
        self.geometry("400x180")
        self.configure(bg="white")
        self.resizable(False, False)

        self.current_port = current_port
        self.new_port = tk.StringVar()

        # Center the window
        self.eval('tk::PlaceWindow . center')

        # Header Label
        label = tk.Label(self, text="Enter new port for the application:", font=("Arial", 12), bg="white")
        label.pack(pady=(20, 10))

        # Port Entry
        entry_frame = tk.Frame(self, bg="white")
        entry_frame.pack()
        self.port_entry = tk.Entry(entry_frame, textvariable=self.new_port, font=("Arial", 12), width=10, justify="center", bd=2, relief="solid")
        self.port_entry.pack(pady=5)

        # Buttons
        button_frame = tk.Frame(self, bg="white")
        button_frame.pack(pady=15)

        update_btn = tk.Button(button_frame, text="Update", command=self.update_port, font=("Arial", 12, "bold"), 
                               bg="#007BFF", fg="white", width=10, height=2, borderwidth=0, activebackground="#0056b3")
        update_btn.pack(side="left", padx=10)

        cancel_btn = tk.Button(button_frame, text="Cancel", command=self.destroy, font=("Arial", 12, "bold"), 
                               bg="white", fg="black", width=10, height=2, borderwidth=2, relief="solid", activebackground="#E5E5E5")
        cancel_btn.pack(side="left", padx=10)

    def update_port(self):
        """Validates and updates the port"""
        port = self.new_port.get().strip()

        if not port.isdigit():
            messagebox.showerror("Invalid Input", "Port must be a number!")
            return
        
        port = int(port)
        if port < 1024 or port > 65535:
            messagebox.showerror("Invalid Port", "Port must be between 1024 and 65535!")
            return

        messagebox.showinfo("Success", f"Port updated to {port}!")
        self.destroy()

# Run the UI
if __name__ == "__main__":
    app = PortUpdateWindow(current_port=5000)
    app.mainloop()
