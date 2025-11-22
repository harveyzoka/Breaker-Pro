import win32api
import win32con
import winreg
import sys
import os

class IdleMonitor:
    def get_idle_duration(self):
        """Returns the number of seconds the system has been idle."""
        try:
            last_input_info = win32api.GetLastInputInfo()
            millis = win32api.GetTickCount() - last_input_info
            return millis / 1000.0
        except Exception:
            return 0

class AutoStarter:
    APP_NAME = "BreakerApp"
    
    def set_autostart(self, enable=True):
        """Adds or removes the app from Windows Startup registry."""
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            if enable:
                if getattr(sys, 'frozen', False):
                    # Running as compiled exe
                    exe_path = sys.executable
                    cmd = f'"{exe_path}" --minimized'
                else:
                    # Running from source
                    exe_path = sys.executable
                    script_path = os.path.abspath("main.py")
                    cmd = f'"{exe_path}" "{script_path}" --minimized'
                
                winreg.SetValueEx(key, self.APP_NAME, 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, self.APP_NAME)
                except FileNotFoundError:
                    pass # Already deleted
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Error setting autostart: {e}")

    def is_autostart_enabled(self):
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, self.APP_NAME)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False
        except Exception:
            return False
