"""
Comprehensive Logging System for SecureStudio

Provides:
- File-based logging (persists across sessions)
- Console logging (for debugging)
- Event logging (user actions, model events)
- Error logging (exceptions, failures)
- Log rotation (prevents huge log files)
- Crash logging (captures unexpected shutdowns)
"""

import logging
import os
import sys
import traceback
import atexit
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Log directory
LOG_DIR = os.path.join(os.path.expanduser("~"), ".securestudio", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Log file paths
ERROR_LOG = os.path.join(LOG_DIR, "error.log")
EVENT_LOG = os.path.join(LOG_DIR, "events.log")
DEBUG_LOG = os.path.join(LOG_DIR, "debug.log")
CRASH_LOG = os.path.join(LOG_DIR, "crash.log")

# Track app state for crash detection
_app_state = {
    "started": False,
    "clean_exit": False,
    "start_time": None,
    "video_thread_alive": False,
    "last_phase": "init"
}

# Formatters
DETAILED_FORMAT = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
SIMPLE_FORMAT = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
EVENT_FORMAT = logging.Formatter(
    '%(asctime)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def _global_exception_hook(exc_type, exc_value, exc_traceback):
    """
    Global exception handler - catches all uncaught exceptions.
    """
    if issubclass(exc_type, KeyboardInterrupt):
        # Don't log keyboard interrupt as crash
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # Log the crash
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logging.critical(f"UNCAUGHT EXCEPTION:\n{error_msg}")
    
    # Write to crash log
    _write_crash_log(
        crash_type="UNCAUGHT_EXCEPTION",
        error=f"{exc_type.__name__}: {exc_value}",
        traceback_str=error_msg
    )
    
    # Call default handler
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


def _on_exit():
    """
    Called when the application exits - detects unexpected shutdowns.
    """
    if _app_state["started"] and not _app_state["clean_exit"]:
        runtime = "unknown"
        if _app_state["start_time"]:
            runtime = str(datetime.now() - _app_state["start_time"])
        
        logging.warning(f"Application exited without clean shutdown. Runtime: {runtime}")
        _write_crash_log(
            crash_type="UNEXPECTED_EXIT",
            error="Application terminated without calling mark_clean_exit()",
            runtime=runtime,
            extra_info=f"Video thread alive: {_app_state['video_thread_alive']}, Last phase: {_app_state['last_phase']}"
        )


def _write_crash_log(crash_type: str, error: str, traceback_str: str = "", runtime: str = "", extra_info: str = ""):
    """Write detailed crash information to crash.log"""
    try:
        with open(CRASH_LOG, "a", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write(f"CRASH REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n")
            f.write(f"Type: {crash_type}\n")
            if runtime:
                f.write(f"Runtime: {runtime}\n")
            f.write(f"Error: {error}\n")
            if extra_info:
                f.write(f"Info: {extra_info}\n")
            if traceback_str:
                f.write(f"\nTraceback:\n{traceback_str}\n")
            f.write("\n")
    except Exception:
        pass  # Don't fail if we can't write crash log


def setup_logging(debug_mode=False):
    """
    Initialize the logging system.
    
    Args:
        debug_mode: If True, enables verbose debug logging to console
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # 1. Console Handler (INFO level, or DEBUG if debug_mode)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)
    console_handler.setFormatter(SIMPLE_FORMAT)
    root_logger.addHandler(console_handler)
    
    # 2. Debug Log File (captures everything)
    debug_handler = RotatingFileHandler(
        DEBUG_LOG, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
    )
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(DETAILED_FORMAT)
    root_logger.addHandler(debug_handler)
    
    # 3. Error Log File (only warnings and above)
    error_handler = RotatingFileHandler(
        ERROR_LOG, maxBytes=2*1024*1024, backupCount=5, encoding='utf-8'
    )
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(DETAILED_FORMAT)
    root_logger.addHandler(error_handler)
    
    # Install global exception hook
    sys.excepthook = _global_exception_hook
    
    # Register exit handler
    atexit.register(_on_exit)
    
    # Mark app as started
    _app_state["started"] = True
    _app_state["start_time"] = datetime.now()
    
    logging.info(f"Logging initialized. Logs stored in: {LOG_DIR}")
    return root_logger


def mark_clean_exit():
    """
    Mark that the application is exiting cleanly.
    Call this before normal application exit.
    """
    _app_state["clean_exit"] = True
    if _app_state["start_time"]:
        runtime = datetime.now() - _app_state["start_time"]
        logging.info(f"Clean shutdown. Total runtime: {runtime}")


def set_video_thread_status(alive: bool):
    """Track video thread status for crash diagnostics."""
    _app_state["video_thread_alive"] = alive


def set_app_phase(phase: str):
    """
    Track current application phase for crash diagnostics.
    Phases: init, model_loading, camera_connect, virtualcam_init, running, shutting_down
    """
    _app_state["last_phase"] = phase
    logging.debug(f"App phase: {phase}")


# Event Logger (separate logger for user/app events)
event_logger = logging.getLogger("events")
event_logger.setLevel(logging.INFO)
event_logger.propagate = False  # Don't send to root logger

# Event log file handler
_event_handler = RotatingFileHandler(
    EVENT_LOG, maxBytes=2*1024*1024, backupCount=3, encoding='utf-8'
)
_event_handler.setFormatter(EVENT_FORMAT)
event_logger.addHandler(_event_handler)


def log_event(event_type: str, message: str, **kwargs):
    """
    Log a user or application event.
    
    Args:
        event_type: Category of event (e.g., "APP", "MODEL", "SETTINGS", "DETECTION")
        message: Description of the event
        **kwargs: Additional key-value pairs to log
    """
    extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
    full_message = f"[{event_type}] {message}"
    if extra_info:
        full_message += f" | {extra_info}"
    event_logger.info(full_message)


def log_error(error: Exception, context: str = "", fatal: bool = False):
    """
    Log an error with full traceback.
    
    Args:
        error: The exception that occurred
        context: Additional context about what was happening
        fatal: If True, also write to crash log
    """
    error_msg = f"{context}: {type(error).__name__}: {str(error)}" if context else f"{type(error).__name__}: {str(error)}"
    tb_str = traceback.format_exc()
    
    if fatal:
        logging.critical(error_msg)
        _write_crash_log(
            crash_type="FATAL_ERROR",
            error=error_msg,
            traceback_str=tb_str
        )
    else:
        logging.error(error_msg)
    
    logging.debug(f"Traceback:\n{tb_str}")


def get_log_paths():
    """Return dictionary of log file paths."""
    return {
        "debug": DEBUG_LOG,
        "error": ERROR_LOG,
        "events": EVENT_LOG,
        "crash": CRASH_LOG,
        "directory": LOG_DIR
    }


def get_recent_crashes(count: int = 5) -> str:
    """
    Get recent crash reports.
    
    Args:
        count: Number of crash reports to retrieve
    
    Returns:
        String containing recent crash reports
    """
    if not os.path.exists(CRASH_LOG):
        return "No crash reports found."
    
    try:
        with open(CRASH_LOG, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Split by crash separator and get last N
        reports = content.split("=" * 80 + "\n")
        reports = [r for r in reports if r.strip()]
        
        if not reports:
            return "No crash reports found."
        
        recent = reports[-count:] if len(reports) > count else reports
        return ("=" * 80 + "\n").join(recent)
    except Exception as e:
        return f"Error reading crash log: {e}"


def get_recent_errors(count=10):
    """
    Get the most recent error log entries.
    
    Args:
        count: Number of recent errors to retrieve
    
    Returns:
        List of error log lines
    """
    if not os.path.exists(ERROR_LOG):
        return []
    
    try:
        with open(ERROR_LOG, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return lines[-count:] if len(lines) > count else lines
    except Exception:
        return []
