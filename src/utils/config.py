import logging
import sys
import os

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Camera Settings
OBS_WIDTH = 1280
OBS_HEIGHT = 720
FPS = 30

# AI Settings
CONFIDENCE_THRESHOLD = 0.5
# YOLO classes to automatically censor (e.g., 67=cell phone)
TARGET_CLASSES = [67] 

# Logging
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
