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
from src.ui.setup_wizard import needs_setup, run_setup_wizard
from src.utils.logger import setup_logging, log_event, log_error, mark_clean_exit

def main():
    check_dependencies()
    
    # Initialize comprehensive logging system
    debug_mode = "--debug" in sys.argv
    setup_logging(debug_mode=debug_mode)
    
    log_event("APP", "Application starting", version="2.0.0", debug=debug_mode)
    
    try:
        app = QApplication(sys.argv)
        
        # Set Application Metadata
        app.setApplicationName("SecureStudio")
        app.setApplicationVersion("2.0.0")
        
        # Check if first-run setup is needed
        if needs_setup():
            log_event("APP", "First run - launching setup wizard")
            if not run_setup_wizard(app):
                log_event("APP", "Setup wizard cancelled by user")
                sys.exit(0)
            log_event("APP", "Setup wizard completed")
        
        window = MainWindow()
        window.show()
        
        log_event("APP", "Main window displayed")
        
        exit_code = app.exec()
        
        # Mark clean exit before exiting
        mark_clean_exit()
        log_event("APP", "Application exiting", exit_code=exit_code)
        sys.exit(exit_code)
        
    except Exception as e:
        log_error(e, "Fatal error during application startup", fatal=True)
        raise

if __name__ == "__main__":
    main()
