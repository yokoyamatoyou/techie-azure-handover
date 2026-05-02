import os

import socket
import subprocess
import sys
import tempfile
import webbrowser
import ctypes
import traceback
import logging
import logging.handlers
import json
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


class _JSONFormatter(logging.Formatter):
    """ログをJSON形式にフォーマットする"""
    def format(self, record):
        data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "service": os.environ.get("SERVICE_NAME", "unknown"),
            "module": record.module,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            data["traceback"] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False)


def setup_app_logging() -> None:
    """アプリ起動時に呼び出して、ログを設定する"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    root = logging.getLogger()
    for handler in root.handlers:
        if isinstance(handler, logging.handlers.RotatingFileHandler) and getattr(handler, "_techie_log", False):
            return

    handler = logging.handlers.RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=10 * 1024 * 1024,   # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    handler.setFormatter(_JSONFormatter(datefmt="%Y-%m-%dT%H:%M:%S"))
    handler._techie_log = True

    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    root.setLevel(level)
    root.addHandler(handler)

    # 起動時のログ
    logging.info("アプリ起動 (LOG_LEVEL=%s)", level_name)

# Mutex constants
ERROR_ALREADY_EXISTS = 183
MUTEX_NAME = "Global\\SeoAioAppMutex_v2"
PORT_FILE_NAME = "seo_aio_app_v2.port"

def get_bundle_path() -> Path:
    """Returns the path to the bundled resources (temp dir in OneyFile mode)."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent

def get_exe_path() -> Path:
    """Returns the path to the executable (or script if not frozen)."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

def setup_logging(exe_dir: Path):
    """Sets up a simple file logger in the exe directory for debugging startup issues."""
    log_file = exe_dir / "app_startup.log"
    if getattr(sys, 'frozen', False):
        try:
            # Line-buffered so startup logs appear immediately.
            sys.stdout = open(log_file, "a", encoding="utf-8", buffering=1)
            sys.stderr = sys.stdout
            print(f"--- Startup: {datetime.now()} ---", flush=True)
        except Exception:
            pass # Cannot write log, ignored

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Return True if the TCP port is already bound."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0

def find_free_port(start_port: int, max_port: int = 8600) -> int:
    """Finds the first free port in range."""
    for port in range(start_port, max_port):
        if not is_port_in_use(port):
            return port
    return start_port # Fallback

def acquire_mutex(mutex_name: str):
    """
    Acquire a named mutex to prevent multiple instances.
    Returns handle if successful, None if already exists.
    """
    kernel32 = ctypes.windll.kernel32
    mutex_name_bytes = mutex_name.encode('utf-8')
    mutex = kernel32.CreateMutexA(None, False, mutex_name_bytes)
    last_error = kernel32.GetLastError()
    
    if last_error == ERROR_ALREADY_EXISTS:
        return None
    return mutex

def get_active_port() -> int:
    """Reads the active port from the temp file."""
    try:
        port_file = Path(tempfile.gettempdir()) / PORT_FILE_NAME
        if port_file.exists():
            return int(port_file.read_text().strip())
    except Exception:
        pass
    return 8501 # Fallback, though likely wrong if mutex held

def set_active_port(port: int):
    """Writes the active port to the temp file."""
    try:
        port_file = Path(tempfile.gettempdir()) / PORT_FILE_NAME
        port_file.write_text(str(port))
    except Exception:
        print("Failed to write port file")

def main() -> int:
    bundle_path = get_bundle_path()
    exe_path = get_exe_path()
    
    setup_logging(exe_path)
    
    print(f"Bundle Path: {bundle_path}")
    print(f"Exe Path: {exe_path}")

    # Single-instance guard using Named Mutex
    mutex = acquire_mutex(MUTEX_NAME)
    if not mutex:
        print("Application is already running.")
        current_port = get_active_port()
        print(f"Connecting to existing instance on port {current_port}...")
        
        if is_port_in_use(current_port):
             if os.environ.get("HEADLESS", "").lower() not in ("1", "true", "yes"):
                webbrowser.open(f"http://127.0.0.1:{current_port}")
        else:
            print(f"Port {current_port} does not seem active. Ghost instance?")
        return 0

    try:
        # Load .env from the EXECUTABLE directory (user config)
        if load_dotenv:
            env_path = exe_path / ".env"
            if env_path.exists():
                print(f"Loading .env from {env_path}")
                load_dotenv(env_path)
            else:
                print(f".env not found in {env_path}, relying on system env vars")

        setup_app_logging()

        # Determine port - Dynamic allocation
        preferred_port = int(
            os.environ.get("PORT")
            or "8081"
        )
        
        target_port = find_free_port(preferred_port)
        print(f"Selected Port: {target_port}")
        
        # Write the selected port for other instances to find
        set_active_port(target_port)

        # Ensure correct working directory/pythonpath
        # NOTE: In onefile mode, bundle_path points to a temp extraction directory.
        # We want user-generated outputs (PDF, logs, etc.) to persist next to the exe.
        os.chdir(exe_path)
        sys.path.insert(0, str(bundle_path))
        # Also add nested core path (for PyArmor layout fallback)
        nested_core = bundle_path / "core"
        if nested_core.exists():
            sys.path.insert(0, str(nested_core))

        # In onefile builds, modules may not exist as physical .py files under bundle_path.
        # So we validate by importing instead of checking file existence.
        try:
            import nicegui_app  # noqa: F401
        except Exception as exc:
            print(f"Error: Failed to import application entrypoint 'nicegui_app': {exc}")
            return 1

        headless = os.environ.get("HEADLESS", "").lower() in ("1", "true", "yes")
        
        # --- Manual Browser Open Trigger Removed (Handled in nicegui_app.py) ---
        # if not headless:
        #     import threading
        #     import time
        #     def open_browser_delayed(url):
        #         # Wait a bit for the server to start
        #         time.sleep(2.5) 
        #         print(f"Opening browser to {url}...")
        #         webbrowser.open(url)
        #     
        #     app_url = f"http://127.0.0.1:{target_port}"
        #     threading.Thread(target=open_browser_delayed, args=(app_url,), daemon=True).start()

        print(f"Starting NiceGUI on port {target_port}")
        from nicegui_app import run_app as nicegui_run_app
        nicegui_run_app(host="127.0.0.1", port=target_port)
        return 0

    except Exception:
        logging.getLogger(__name__).error("起動処理に失敗しました", exc_info=True)
        traceback.print_exc()
        return 1
    
if __name__ == "__main__":
    main()
