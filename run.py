import sys
import logging
import subprocess
import importlib.util

def check_dependencies():
    """Ensure critical dependencies are installed to prevent runtime restarts."""
    required = ['lapx', 'ultralytics', 'pyvirtualcam', 'opencv-python', 'PyQt6']
    missing = []
    
    for package in required:
        # Map package name to import name if different
        import_name = package
        if package == 'lapx': import_name = 'lap'
        if package == 'opencv-python': import_name = 'cv2'
        if package == 'PyQt6': import_name = 'PyQt6'
        
        if importlib.util.find_spec(import_name) is None:
            missing.append(package)
            
    if missing:
        print(f"Missing dependencies detected: {', '.join(missing)}")
        print("Installing missing packages...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
            print("Dependencies installed. Please restart the application.")
            sys.exit(0)
        except subprocess.CalledProcessError as e:
            print(f"Failed to install dependencies: {e}")
            sys.exit(1)

from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.utils.config import LOG_LEVEL, LOG_FORMAT

def main():
    check_dependencies()
    
    # Configure Logging
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    app = QApplication(sys.argv)
    
    # Set Application Metadata
    app.setApplicationName("BlurOBS")
    app.setApplicationVersion("1.0.0")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
