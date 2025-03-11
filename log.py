import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
import datetime
from cryptography.fernet import Fernet
import threading
import time
import re
import keyboard  # You'll need to install this: pip install keyboard

class LogManager:
    def __init__(self, log_file="./lib/app_logs.txt"):
        self.log_file = log_file
        self.key = "kphEig0_Dtx3iq2-Ok19KP0MTtVnXxO0gMlJ4ggAzPE="

        
        # Start the log clearing thread
        self.clear_thread = threading.Thread(target=self._monitor_for_clearing, daemon=True)
        self.clear_thread.start()
    
    
    def _get_last_clear_date(self):
        """Extract the date when the log was created from the first line of the log file"""
        if not os.path.exists(self.log_file):
            return datetime.date.today() - datetime.timedelta(days=1)  # Default to yesterday
        
        try:
            with open(self.log_file, "rb") as f:
                first_line = f.readline().strip()
                if first_line.startswith(b'# Log file created on'):
                    # Try to decrypt if it's encrypted
                    try:
                        key = self.key
                        fernet = Fernet(key)
                        line = fernet.decrypt(first_line).decode('utf-8')
                    except:
                        # Not encrypted, just decode
                        line = first_line.decode('utf-8')
                    
                    # Extract date using regex
                    match = re.search(r'created on (\d{4}-\d{2}-\d{2})', line)
                    if match:
                        date_str = match.group(1)
                        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                
                # If we get here, check the timestamps in the logs
                self._rewind_file(f)
                latest_date = None
                
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        # Try to decrypt the line
                        key = self.key
                        fernet = Fernet(key)
                        decrypted = fernet.decrypt(line).decode('utf-8')
                        
                        # Extract timestamp
                        match = re.search(r'\[(\d{4}-\d{2}-\d{2})', decrypted)
                        if match:
                            date_str = match.group(1)
                            log_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                            if latest_date is None or log_date > latest_date:
                                latest_date = log_date
                    except:
                        pass
                
                if latest_date:
                    return latest_date
                
            # Default to yesterday if we couldn't find a date
            return datetime.date.today() - datetime.timedelta(days=1)
        except Exception as e:
            print(f"Error determining last clear date: {e}")
            return datetime.date.today() - datetime.timedelta(days=1)
    
    def _rewind_file(self, file_obj):
        """Rewind file to beginning"""
        file_obj.seek(0)
    
    def _monitor_for_clearing(self):
        """Thread function to check for daily log clearing"""
        while True:
            today = datetime.date.today()
            last_clear_date = self._get_last_clear_date()
            
            if today > last_clear_date:
                self.clear_logs()
            
            # Check every hour
            time.sleep(3600)
    
    def clear_logs(self):
        """Clear the log file and update the clear date"""
        try:
            creation_date = datetime.datetime.now()
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
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {message}"
            
            # Encrypt the log entry
            key = self.key
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
            key = self.key
            fernet = Fernet(key)
            
            logs = []
            with open(self.log_file, "rb") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            # Try to decrypt the line
                            decrypted_line = fernet.decrypt(line).decode('utf-8')
                            logs.append(decrypted_line)
                        except:
                            # If decryption fails, it might be a plaintext header
                            if line.startswith(b'#'):
                                logs.append(line.decode('utf-8'))
            
            return logs
        except Exception as e:
            print(f"Error reading logs: {e}")
            return [f"Error: {e}"]
    
    def get_last_clear_date_formatted(self):
        """Get the formatted last clear date for display"""
        return self._get_last_clear_date().strftime("%Y-%m-%d")


class LogViewerApp:
    def __init__(self, main_app=None):
        self.log_manager = LogManager()
        self.root = None
        self.main_app = main_app
        
        # self.root = tk.Toplevel() if self.main_app else tk.Tk()
        self.root = self.main_app
        self.root.title("Log Manager")
        self.root.geometry("800x600")
        
        # Set up the widgets
        self.create_widgets()
        
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
        
        # Set up the widgets
        self.create_widgets()
        
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.hide_log_viewer)
    
    def hide_log_viewer(self):
        """Hide the log viewer window"""
        if self.root:
            self.root.withdraw()
    
    def create_widgets(self):
        # Create notebook with tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create decrypt logs tab
        decrypt_frame = ttk.Frame(notebook)
        notebook.add(decrypt_frame, text="View Decrypted Logs")
        
        # Create management tab
        manage_frame = ttk.Frame(notebook)
        notebook.add(manage_frame, text="Log Management")
        
        # Configure decrypt logs tab
        self.setup_decrypt_tab(decrypt_frame)
        
        # Configure management tab
        self.setup_management_tab(manage_frame)
    
    def setup_decrypt_tab(self, parent):
        # Log text area
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        refresh_btn = ttk.Button(btn_frame, text="Refresh Logs", command=self.refresh_logs)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Initial load of logs
        self.refresh_logs()
    
    def setup_management_tab(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Clear logs button
        clear_btn = ttk.Button(frame, text="Clear Logs Now", command=self.clear_logs)
        clear_btn.pack(pady=10)
        
        # Last cleared info
        self.last_cleared_label = ttk.Label(frame, text="")
        self.last_cleared_label.pack(pady=10)
        self.update_last_cleared_info()
        
        # Add a log entry frame
        entry_frame = ttk.LabelFrame(frame, text="Add Log Entry")
        entry_frame.pack(fill=tk.X, pady=20, padx=10)
        
        self.log_entry = ttk.Entry(entry_frame, width=50)
        self.log_entry.pack(side=tk.LEFT, padx=5, pady=10, fill=tk.X, expand=True)
        
        add_btn = ttk.Button(entry_frame, text="Add Log", command=self.add_log)
        add_btn.pack(side=tk.RIGHT, padx=5, pady=10)
    
    def refresh_logs(self):
        self.log_text.delete(1.0, tk.END)
        logs = self.log_manager.read_logs()
        for log in logs:
            self.log_text.insert(tk.END, f"{log}\n")
    
    def clear_logs(self):
        if messagebox.askyesno("Confirmation", "Are you sure you want to clear all logs?"):
            if self.log_manager.clear_logs():
                messagebox.showinfo("Success", "Logs cleared successfully")
                self.refresh_logs()
                self.update_last_cleared_info()
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
        self.last_cleared_label.config(text=f"Logs last cleared on: {last_date}")


# Example of how to integrate with your main applicatio

# This is how you would use the log viewer in standalone mode
if __name__ == "__main__":
    # Example 1: Using with your main application
    root = tk.Tk()
    app = LogViewerApp(root)
    root.mainloop()
    
    # Example 2: Using just the log viewer (uncomment to use)
    # log_viewer = LogViewerApp()
    # 
    # # Block main thread with a simple loop
    # # (The log viewer will appear when Shift+L is pressed)
    # try:
    #     while True:
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     pass