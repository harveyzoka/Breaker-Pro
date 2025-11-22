import customtkinter as ctk
from screeninfo import get_monitors

class SingleOverlay(ctk.CTkToplevel):
    def __init__(self, monitor, is_primary=False, message="", duration=30, alpha=0.8, on_unlock=None):
        super().__init__()
        
        self.monitor = monitor
        self.is_primary = is_primary
        self.on_unlock = on_unlock
        
        self.title("Breaker - Overlay")
        
        # Position window on specific monitor
        # Note: On Windows, overrideredirect + geometry is the way to target specific monitors.
        # Do NOT use -fullscreen attribute as it may force to primary.
        self.overrideredirect(True)
        self.geometry(f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}")
        self.attributes("-topmost", True)
        self.configure(fg_color="#000000")
        self.attributes("-alpha", alpha)

        if is_primary:
            self.setup_primary_ui(message, duration)
        else:
            # Blank black screen for secondary monitors
            pass

    def setup_primary_ui(self, message, duration):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        self.msg_label = ctk.CTkLabel(self, text=message, font=("Roboto", 40, "bold"), text_color="white", wraplength=800)
        self.msg_label.grid(row=0, column=0, pady=50)

        self.timer_label = ctk.CTkLabel(self, text=self.format_time(duration), font=("Roboto", 120, "bold"), text_color="#44AA44")
        self.timer_label.grid(row=1, column=0)

        self.unlock_btn = ctk.CTkButton(self, text="Emergency Unlock", command=self.unlock, fg_color="#333333", hover_color="#555555")
        self.unlock_btn.grid(row=2, column=0, pady=50)

    def format_time(self, seconds):
        mins, secs = divmod(seconds, 60)
        return f"{mins:02}:{secs:02}"

    def update_time(self, remaining):
        if self.is_primary:
            self.timer_label.configure(text=self.format_time(remaining))
            if remaining <= 0:
                self.unlock()

    def unlock(self):
        if self.on_unlock:
            self.on_unlock()

class OverlayManager:
    def __init__(self, message, duration, alpha, on_unlock):
        self.windows = []
        self.on_unlock_callback = on_unlock
        
        monitors = get_monitors()
        for i, m in enumerate(monitors):
            # Assume first monitor or monitor at (0,0) is primary? 
            # screeninfo usually puts primary first or has is_primary flag.
            is_primary = m.is_primary if hasattr(m, 'is_primary') else (i==0)
            
            win = SingleOverlay(
                monitor=m, 
                is_primary=is_primary, 
                message=message, 
                duration=duration, 
                alpha=alpha, 
                on_unlock=self.on_unlock
            )
            self.windows.append(win)

    def update_time(self, remaining):
        for win in self.windows:
            win.update_time(remaining)

    def destroy(self):
        for win in self.windows:
            try:
                win.destroy()
            except:
                pass
        self.windows = []

    def winfo_exists(self):
        # Return true if at least one window exists
        return len(self.windows) > 0 and any(w.winfo_exists() for w in self.windows)

    def on_unlock(self):
        if self.on_unlock_callback:
            self.on_unlock_callback()
        self.destroy()
