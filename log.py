import threading, os
from datetime import date, datetime, timedelta
from lib import constants
import re
import time
from cryptography.fernet import Fernet

class LogManager:
    def __init__(self, log_file="./lib/app_logs.txt"):
        self.log_file = log_file
        self.last_clear_date = self._get_last_clear_date()
        
        # Start the log clearing thread
        self.clear_thread = threading.Thread(target=self._monitor_for_clearing, daemon=True)
        self.clear_thread.start()

    def _get_last_clear_date(self):
        """Extract the date when the log was created from the first line of the log file"""
        if not os.path.exists(self.log_file):
            return date.today() - timedelta(days=1)  # Default to yesterday
        
        try:
            with open(self.log_file, "rb") as f:
                first_line = f.readline().strip()
                if first_line.startswith(b'# Log file created on'):
                    # Try to decrypt if it's encrypted
                    try:
                        key = constants.ENCRYPTION_KEY
                        fernet = Fernet(key)
                        line = fernet.decrypt(first_line).decode('utf-8')
                    except:
                        # Not encrypted, just decode
                        line = first_line.decode('utf-8')
                    
                    # Extract date using regex
                    match = re.search(r'created on (\d{4}-\d{2}-\d{2})', line)
                    if match:
                        date_str = match.group(1)
                        return datetime.strptime(date_str, "%Y-%m-%d").date()
                
                # If we get here, check the timestamps in the logs
                self._rewind_file(f)
                latest_date = None
                
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        # Try to decrypt the line
                        key = self._get_key()
                        fernet = Fernet(key)
                        decrypted = fernet.decrypt(line).decode('utf-8')
                        
                        # Extract timestamp
                        match = re.search(r'\[(\d{4}-\d{2}-\d{2})', decrypted)
                        if match:
                            date_str = match.group(1)
                            log_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                            if latest_date is None or log_date > latest_date:
                                latest_date = log_date
                    except:
                        pass
                
                if latest_date:
                    return latest_date
                
            # Default to yesterday if we couldn't find a date
            return date.today() - timedelta(days=1)
        except Exception as e:
            print(f"Error determining last clear date: {e}")
            return date.today() - timedelta(days=1)
    
    def _update_last_clear_date(self):
        """Update the date of the last log clearing"""
        metadata_file = "log_metadata.txt"
        with open(metadata_file, "w") as f:
            f.write(date.today().strftime("%Y-%m-%d"))
        self.last_clear_date = date.today()
    
    def _monitor_for_clearing(self):
        """Thread function to check for daily log clearing"""
        while True:
            today = date.today()
            last_clear_date = self._get_last_clear_date()
            
            if today > last_clear_date:
                self.clear_logs()
            
            # Check every hour
            time.sleep(3600)
    
    def clear_logs(self):
        """Clear the log file and update the clear date"""
        try:
            creation_date = datetime.now()
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
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {message}"
            
            # Encrypt the log entry
            # key = self._get_key()
            key = constants.ENCRYPTION_KEY
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
            # key = self._get_key()
            key = constants.ENCRYPTION_KEY
            fernet = Fernet(key)
            
            logs = []
            with open(self.log_file, "rb") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            decrypted_line = fernet.decrypt(line).decode('utf-8')
                            logs.append(decrypted_line)
                        except:
                            # Skip lines that can't be decrypted (could be plain text headers)
                            if line.startswith(b'#'):
                                logs.append(line.decode('utf-8'))
            
            return logs
        except Exception as e:
            print(f"Error reading logs: {e}")
            return [f"Error: {e}"]
        
    def get_last_clear_date_formatted(self):
        """Get the formatted last clear date for display"""
        return self._get_last_clear_date().strftime("%Y-%m-%d")

LogManagerObj = LogManager()