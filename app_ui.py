import customtkinter as ctk
from timer_logic import Timer
from overlay_window import OverlayManager
from system_utils import AutoStarter
from settings_manager import SettingsManager
import threading
import winsound
import playsound
from tkinter import filedialog
import pystray
from PIL import Image, ImageDraw
import os
import sys

class BreakerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Breaker - Pro")
        self.geometry("500x750")
        ctk.set_appearance_mode("Dark")
        
        if os.path.exists("app.ico"):
            self.iconbitmap("app.ico")
        
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.load_settings()
        
        # State
        self.strict_mode = ctk.BooleanVar(value=self.settings["strict_mode"])
        self.sit_msg = ctk.StringVar(value=self.settings["sit_msg"])
        self.stand_msg = ctk.StringVar(value=self.settings["stand_msg"])
        self.auto_start = ctk.BooleanVar(value=self.settings["auto_start"])
        self.overlay_alpha = ctk.DoubleVar(value=self.settings["overlay_alpha"])
        self.sound_path = ctk.StringVar(value=self.settings["sound_path"])
        
        self.auto_starter = AutoStarter()
        # Sync auto-start state with registry
        is_auto = self.auto_starter.is_autostart_enabled()
        if self.auto_start.get() != is_auto:
            # If settings say one thing but registry says another, trust registry? 
            # Or enforce settings? Let's trust registry for the UI toggle state.
            self.auto_start.set(is_auto)

        self.timer = Timer(
            sitting_duration=self.settings["sitting_duration"],
            standing_duration=self.settings["standing_duration"],
            transition_duration=self.settings["transition_duration"],
            work_schedules=self.settings["work_schedules"],
            idle_threshold_mins=self.settings["idle_threshold"],
            on_tick=self.update_timer_display, 
            on_finish=self.on_timer_finish,
            on_idle_reset=self.on_idle_reset
        )

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_timer = self.tabview.add("Timer")
        self.tab_settings = self.tabview.add("Settings")

        self.overlay = None
        self.tray_icon = None
        
        self.setup_timer_tab()
        self.setup_settings_tab()
        
        # System Tray Setup
        self.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
        
        # Auto-start timer on launch
        self.toggle_timer()

    def setup_timer_tab(self):
        frame = self.tab_timer
        frame.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(frame, text="SITTING TIME", font=("Roboto Medium", 20), text_color="#A0A0A0")
        self.status_label.grid(row=0, column=0, pady=(40, 0))

        self.timer_label = ctk.CTkLabel(frame, text="00:00", font=("Roboto", 90, "bold"))
        self.timer_label.grid(row=1, column=0, pady=(10, 30))

        self.progress_bar = ctk.CTkProgressBar(frame, width=350)
        self.progress_bar.grid(row=2, column=0, pady=(0, 30))
        self.progress_bar.set(1.0)
        
        self.update_timer_display(self.timer.current_duration)

        controls = ctk.CTkFrame(frame, fg_color="transparent")
        controls.grid(row=3, column=0)

        self.start_button = ctk.CTkButton(controls, text="START", command=self.toggle_timer, width=120, height=50, font=("Roboto", 16, "bold"))
        self.start_button.grid(row=0, column=0, padx=10)

        self.skip_button = ctk.CTkButton(controls, text="SKIP", command=self.skip_timer, width=80, height=50, fg_color="#555555", hover_color="#444444")
        self.skip_button.grid(row=0, column=1, padx=10)
        
        self.reset_button = ctk.CTkButton(controls, text="RESET", command=self.reset_timer, width=80, height=50, fg_color="#AA3333", hover_color="#882222")
        self.reset_button.grid(row=0, column=2, padx=10)
        
        self.info_label = ctk.CTkLabel(frame, text="Timer pauses outside work hours or if idle.", font=("Roboto", 10), text_color="gray")
        self.info_label.grid(row=4, column=0, pady=20)

    def setup_settings_tab(self):
        frame = self.tab_settings
        frame.grid_columnconfigure(1, weight=1)
        
        # Durations
        ctk.CTkLabel(frame, text="Durations", font=("Roboto", 14, "bold")).grid(row=0, column=0, sticky="w", pady=(5, 2))
        
        ctk.CTkLabel(frame, text="Sit (min):").grid(row=1, column=0, sticky="w")
        self.sit_entry = ctk.CTkEntry(frame, width=50)
        self.sit_entry.insert(0, str(self.settings["sitting_duration"]))
        self.sit_entry.grid(row=1, column=1, sticky="w", padx=10)
        
        ctk.CTkLabel(frame, text="Stand (min):").grid(row=2, column=0, sticky="w")
        self.stand_entry = ctk.CTkEntry(frame, width=50)
        self.stand_entry.insert(0, str(self.settings["standing_duration"]))
        self.stand_entry.grid(row=2, column=1, sticky="w", padx=10)

        ctk.CTkLabel(frame, text="Transition (sec):").grid(row=3, column=0, sticky="w")
        self.trans_entry = ctk.CTkEntry(frame, width=50)
        self.trans_entry.insert(0, str(self.settings["transition_duration"]))
        self.trans_entry.grid(row=3, column=1, sticky="w", padx=10)

        # Work Hours
        ctk.CTkLabel(frame, text="Work Schedule (HH:MM-HH:MM)", font=("Roboto", 14, "bold")).grid(row=4, column=0, sticky="w", pady=(10, 2))
        self.schedule_text = ctk.CTkTextbox(frame, width=200, height=60)
        self.schedule_text.insert("0.0", "\n".join(self.settings["work_schedules"]))
        self.schedule_text.grid(row=5, column=0, columnspan=2, sticky="ew", pady=2)

        # Idle
        ctk.CTkLabel(frame, text="Idle Reset (min):").grid(row=6, column=0, sticky="w", pady=(5,0))
        self.idle_entry = ctk.CTkEntry(frame, width=50)
        self.idle_entry.insert(0, str(self.settings["idle_threshold"]))
        self.idle_entry.grid(row=6, column=1, sticky="w", padx=10, pady=(5,0))

        # Sound
        ctk.CTkLabel(frame, text="Sound", font=("Roboto", 14, "bold")).grid(row=7, column=0, sticky="w", pady=(10, 2))
        self.sound_entry = ctk.CTkEntry(frame, textvariable=self.sound_path, width=150)
        self.sound_entry.grid(row=8, column=0, sticky="ew")
        self.browse_btn = ctk.CTkButton(frame, text="Browse", width=50, command=self.browse_sound)
        self.browse_btn.grid(row=8, column=1, padx=5)

        # Overlay Settings
        ctk.CTkLabel(frame, text="Overlay", font=("Roboto", 14, "bold")).grid(row=9, column=0, sticky="w", pady=(10, 2))
        
        ctk.CTkLabel(frame, text="Transparency:").grid(row=10, column=0, sticky="w")
        self.alpha_slider = ctk.CTkSlider(frame, from_=0.3, to=0.9, variable=self.overlay_alpha)
        self.alpha_slider.grid(row=10, column=1, sticky="ew", padx=10)

        self.strict_switch = ctk.CTkSwitch(frame, text="Strict Mode (Block during Transition)", variable=self.strict_mode)
        self.strict_switch.grid(row=11, column=0, columnspan=2, sticky="w", pady=5)

        # Messages
        ctk.CTkLabel(frame, text="Messages", font=("Roboto", 14, "bold")).grid(row=12, column=0, sticky="w", pady=(10, 2))
        self.sit_msg_entry = ctk.CTkEntry(frame, placeholder_text="Msg: Prepare to Sit", textvariable=self.sit_msg, width=200)
        self.sit_msg_entry.grid(row=13, column=0, columnspan=2, sticky="ew", pady=2)
        self.stand_msg_entry = ctk.CTkEntry(frame, placeholder_text="Msg: Prepare to Stand", textvariable=self.stand_msg, width=200)
        self.stand_msg_entry.grid(row=14, column=0, columnspan=2, sticky="ew", pady=2)
        
        self.autostart_switch = ctk.CTkSwitch(frame, text="Run on Startup", variable=self.auto_start, command=self.toggle_autostart)
        self.autostart_switch.grid(row=15, column=0, columnspan=2, sticky="w", pady=10)

        self.apply_btn = ctk.CTkButton(frame, text="Save & Apply Settings", command=self.apply_settings, fg_color="#228822")
        self.apply_btn.grid(row=16, column=0, columnspan=2, pady=10)

    def browse_sound(self):
        filename = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav")])
        if filename:
            self.sound_path.set(filename)

    def toggle_timer(self):
        if self.timer.is_running:
            self.timer.pause()
            self.start_button.configure(text="START", fg_color="#1f6aa5")
        else:
            self.timer.start()
            self.start_button.configure(text="PAUSE", fg_color="#E59400")

    def skip_timer(self):
        was_running = self.timer.is_running
        self.timer.skip()
        self.update_ui_mode()
        
        if was_running:
            self.timer.start()
            self.start_button.configure(text="PAUSE", fg_color="#E59400")
        else:
            self.start_button.configure(text="START", fg_color="#1f6aa5")

    def reset_timer(self):
        self.timer.reset()
        self.start_button.configure(text="START", fg_color="#1f6aa5")
        self.progress_bar.set(1.0)

    def browse_sound(self):
        filename = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav")])
        if filename:
            self.sound_path.set(filename)

    def apply_settings(self):
        try:
            sit = int(self.sit_entry.get())
            stand = int(self.stand_entry.get())
            trans = int(self.trans_entry.get())
            idle = int(self.idle_entry.get())
            schedules = [s.strip() for s in self.schedule_text.get("0.0", "end").strip().split('\n') if s.strip()]
            
            # Update Timer
            self.timer.update_settings(sit, stand, trans, schedules, idle)
            
            # Save to JSON
            settings = {
                "sitting_duration": sit,
                "standing_duration": stand,
                "transition_duration": trans,
                "work_schedules": schedules,
                "idle_threshold": idle,
                "overlay_alpha": self.overlay_alpha.get(),
                "strict_mode": self.strict_mode.get(),
                "auto_start": self.auto_start.get(),
                "sit_msg": self.sit_msg.get(),
                "stand_msg": self.stand_msg.get(),
                "sound_path": self.sound_path.get()
            }
            self.settings_manager.save_settings(settings)
            
            print("Settings Saved & Applied")
        except ValueError:
            print("Invalid Input")

    def toggle_autostart(self):
        self.auto_starter.set_autostart(self.auto_start.get())

    def update_timer_display(self, remaining_seconds):
        # Ensure this runs on main thread
        self.after(0, lambda: self._update_timer_display_safe(remaining_seconds))

    def _update_timer_display_safe(self, remaining_seconds):
        mins, secs = divmod(remaining_seconds, 60)
        time_str = f"{mins:02}:{secs:02}"
        self.timer_label.configure(text=time_str)
        
        total = self.timer.current_duration
        if total > 0:
            self.progress_bar.set(remaining_seconds / total)
            
        # Update Tray Icon Title
        if self.tray_icon:
            try:
                # Get idle time
                idle_sec = self.timer.idle_monitor.get_idle_duration()
                idle_min = int(idle_sec // 60)
                
                mode_str = self.timer.mode
                if mode_str == "Transition":
                    mode_str = "Prep"
                
                title = f"{mode_str}: {time_str} | Idle: {idle_min}m"
                self.tray_icon.title = title
                self.update_tray_menu(title)
            except Exception:
                pass

        if self.overlay and self.overlay.winfo_exists():
            self.overlay.update_time(remaining_seconds)

    def on_idle_reset(self):
        print("Timer reset due to idle.")

    def on_timer_finish(self, new_mode):
        # Ensure this runs on main thread
        self.after(0, lambda: self._on_timer_finish_safe(new_mode))

    def _on_timer_finish_safe(self, new_mode):
        threading.Thread(target=self.play_notification_sound).start()
        
        self.update_ui_mode()
        
        if new_mode == "Transition":
            msg = self.sit_msg.get() if self.timer.next_mode == "Sitting" else self.stand_msg.get()
            if self.strict_mode.get():
                self.show_overlay(msg, self.timer.current_duration)
        else:
            if self.overlay and self.overlay.winfo_exists():
                self.overlay.destroy()

    def show_overlay(self, message, duration):
        if self.overlay and self.overlay.winfo_exists():
            self.overlay.destroy()
            
        alpha = self.overlay_alpha.get()
        self.overlay = OverlayManager(message=message, duration=duration, alpha=alpha, on_unlock=self.on_overlay_unlock)

    def on_overlay_unlock(self):
        pass

    def update_tray_menu(self, status_text):
        if self.tray_icon:
            # Recreate menu with new status
            self.tray_icon.menu = pystray.Menu(
                pystray.MenuItem(status_text, lambda i, it: None, enabled=False),
                pystray.MenuItem("Show", self.show_window),
                pystray.MenuItem("Quit", self.quit_app)
            )

    def update_ui_mode(self):
        mode = self.timer.mode
        if mode == "Sitting":
            self.status_label.configure(text="SITTING TIME", text_color="#A0A0A0")
            self.progress_bar.configure(progress_color="#1f6aa5")
        elif mode == "Standing":
            self.status_label.configure(text="STANDING TIME", text_color="#44AA44")
            self.progress_bar.configure(progress_color="#44AA44")
        else:
            self.status_label.configure(text="PREPARE TO CHANGE", text_color="#E59400")
            self.progress_bar.configure(progress_color="#E59400")
            
        self.update_timer_display(self.timer.current_duration)

    def play_notification_sound(self):
        sound_file = self.sound_path.get()
        if sound_file and os.path.exists(sound_file):
            try:
                playsound.playsound(sound_file)
            except Exception as e:
                print(f"Error playing sound: {e}")
                self.play_beep()
        else:
            self.play_beep()

    def play_beep(self):
        try:
            winsound.Beep(1000, 500)
            winsound.Beep(1500, 500)
        except:
            pass

    # --- System Tray Logic ---
    def minimize_to_tray(self):
        self.withdraw()
        
        if not self.tray_icon:
            image = self.create_tray_image()
            menu = pystray.Menu(
                pystray.MenuItem("Status: Checking...", lambda i, it: None, enabled=False),
                pystray.MenuItem("Show", self.show_window),
                pystray.MenuItem("Quit", self.quit_app)
            )
            self.tray_icon = pystray.Icon("Breaker", image, "Breaker Pro", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_window(self, icon=None, item=None):
        self.deiconify()
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None

    def quit_app(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
        self.quit()
        sys.exit()

    def create_tray_image(self):
        if os.path.exists("app.ico"):
            return Image.open("app.ico")
        else:
            # Fallback
            width = 64
            height = 64
            image = Image.new('RGB', (width, height), color=(30, 30, 30))
            dc = ImageDraw.Draw(image)
            dc.ellipse((10, 10, 54, 54), fill=(31, 106, 165))
            dc.text((20, 20), "B", fill="white")
            return image
