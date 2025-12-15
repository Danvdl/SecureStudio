import json
import os
import logging

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    # Setup wizard settings
    "setup_complete": False,
    "terms_accepted": False,
    "share_diagnostic_logs": False,
    
    # Video settings
    "obs_width": 1920,
    "obs_height": 1080,
    "fps": 30,
    "target_classes": [67],  # Default: Cell Phone
    "auto_blur": True,
    "show_preview": False,
    "use_custom_model": False, # False = Standard COCO, True = YOLO-World
    "custom_classes": [], # User-typed custom prompts
    "security_classes_enabled": ["credit card", "id card", "passport"], # Selected checkboxes
    "confidence_threshold": 0.3, # Balanced threshold
    "model_size": "s", # s=Small (Fast), m=Medium (Balanced), l=Large (Accurate)
    "blur_style": "pixelate", # "gaussian" or "pixelate"
    "smooth_factor": 0.5 # 0.0 (No smoothing) to 0.9 (Heavy smoothing)
}

# Common COCO Classes for the UI
AVAILABLE_CLASSES = {
    0: "Person",
    67: "Cell Phone",
    63: "Laptop",
    64: "Mouse",
    66: "Keyboard",
    39: "Bottle",
    41: "Cup",
    73: "Book",
    24: "Backpack",
    26: "Handbag",
    77: "Teddy Bear"
}

# Common Security Prompts for YOLO-World
SECURITY_CLASSES = [
    "credit card",
    "debit card",
    "id card",
    "passport",
    "driver license",
    "face",
    "license plate",
    "document with text",
    "signature",
    "qr code",
    "naked person",
    "exposed chest",
    "buttocks",
    "underwear"
]

class SettingsManager:
    def __init__(self):
        self.settings = DEFAULT_SETTINGS.copy()
        self.load()

    def load(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    loaded = json.load(f)
                    self.settings.update(loaded)
            except Exception as e:
                logging.error(f"Failed to load settings: {e}")
        else:
            self.save()

    def save(self):
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            logging.error(f"Failed to save settings: {e}")

    def get(self, key, default=None):
        """Get a setting value, with optional default if key doesn't exist."""
        if default is not None:
            return self.settings.get(key, default)
        return self.settings.get(key, DEFAULT_SETTINGS.get(key))

    def set(self, key, value):
        self.settings[key] = value
        self.save()

# Global instance
settings_manager = SettingsManager()
