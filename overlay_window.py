import customtkinter as ctk

class OverlayWindow(ctk.CTkToplevel):
    def __init__(self, message="Time to Change!", duration=30, alpha=0.8, on_unlock=None):
        super().__init__()
        
        self.title("Breaker - Transition")
        
        self.attributes("-fullscreen", True)
        self.attributes("-topmost", True)
        self.overrideredirect(True)
        self.configure(fg_color="#000000")
        self.attributes("-alpha", alpha)

        self.on_unlock = on_unlock
        self.remaining_time = duration

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
        self.remaining_time = remaining
        self.timer_label.configure(text=self.format_time(remaining))
        if remaining <= 0:
            self.unlock()

    def unlock(self):
        if self.on_unlock:
            self.on_unlock()
        self.destroy()
