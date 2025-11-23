import json
import os

    def __init__(self):
        self.FILE_PATH = self._get_settings_path()

    def _get_settings_path(self):
        if getattr(sys, 'frozen', False):
            # Running as compiled exe
            base_path = os.path.dirname(sys.executable)
        else:
            # Running from source
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, "settings.json")
    
    DEFAULT_SETTINGS = {
        "sitting_duration": 25,
        "standing_duration": 5,
        "transition_duration": 30,
        "work_schedules": ["08:00-12:00", "13:00-17:00"],
        "idle_threshold": 5,
        "overlay_alpha": 0.8,
        "strict_mode": True,
        "auto_start": False,
        "sit_msg": "Prepare to Sit Down",
        "stand_msg": "Prepare to Stand Up",
        "sound_path": ""
    }

    def load_settings(self):
        if not os.path.exists(self.FILE_PATH):
            return self.DEFAULT_SETTINGS.copy()
        
        try:
            with open(self.FILE_PATH, "r") as f:
                data = json.load(f)
                # Merge with defaults to ensure all keys exist
                settings = self.DEFAULT_SETTINGS.copy()
                settings.update(data)
                return settings
        except Exception:
            return self.DEFAULT_SETTINGS.copy()

    def save_settings(self, settings):
        try:
            with open(self.FILE_PATH, "w") as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")
