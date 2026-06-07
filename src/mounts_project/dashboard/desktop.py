"""Desktop launcher for the MOUNTS Streamlit dashboard.

Runs Streamlit in-process on a free localhost port and wraps it in a pywebview
window so the bundled PyInstaller binary feels like a native desktop app.
On first run a tkinter folder dialog asks for the OUTPUT_DIR (the folder that
holds ``all-volcanoes.csv`` and the ``images/`` tree); the choice is persisted
to ``%APPDATA%/mounts-project/config.json``.
"""

import os
import sys
import json
import time
import socket
import threading
import urllib.error
import urllib.request
from pathlib import Path


CONFIG_FILENAME = "config.json"
HEALTH_PATH = "/_stcore/health"
READY_TIMEOUT_S = 60
WINDOW_TITLE = "MOUNTS Dashboard"
WINDOW_SIZE = (1400, 900)
WINDOW_MIN_SIZE = (900, 600)


def _config_dir() -> Path:
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    path = Path(base) / "mounts-project"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _load_output_dir() -> str | None:
    config_file = _config_dir() / CONFIG_FILENAME
    if not config_file.exists():
        return None
    try:
        data = json.loads(config_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    value = data.get("output_dir")
    return value if isinstance(value, str) and value else None


def _save_output_dir(path: str) -> None:
    config_file = _config_dir() / CONFIG_FILENAME
    config_file.write_text(
        json.dumps({"output_dir": path}, indent=2), encoding="utf-8"
    )


def _prompt_for_output_dir() -> str:
    """Open a native folder dialog. Returns the picked path or exits on cancel."""
    import tkinter as tk
    from tkinter import filedialog, messagebox

    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(
        WINDOW_TITLE,
        "Select the folder that contains your MOUNTS extraction output "
        "(the folder with all-volcanoes.csv and an images/ subfolder).",
    )
    picked = filedialog.askdirectory(title="Select MOUNTS output folder")
    root.destroy()
    if not picked:
        sys.exit(0)
    return picked


def _resolve_output_dir() -> str:
    existing = _load_output_dir()
    if existing and os.path.isdir(existing):
        return existing
    picked = _prompt_for_output_dir()
    _save_output_dir(picked)
    return picked


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _app_script_path() -> str:
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return str(Path(base) / "mounts_project" / "dashboard" / "app.py")
    return str(Path(__file__).with_name("app.py"))


def _run_streamlit(port: int, script: str) -> None:
    from streamlit.web import bootstrap

    # Streamlit installs a SIGTERM handler at startup, which only works from
    # the main thread. pywebview already owns the main thread, so we host the
    # server in a background thread and neutralise the signal-handler setup.
    def _noop_signal_handler(*_args: object, **_kwargs: object) -> None:
        return None

    setattr(bootstrap, "_set_up_signal_handler", _noop_signal_handler)  # noqa: B010

    bootstrap.load_config_options(
        flag_options={
            "server.port": port,
            "server.address": "127.0.0.1",
            "server.headless": True,
            "browser.gatherUsageStats": False,
            "global.developmentMode": False,
        }
    )
    bootstrap.run(script, is_hello=False, args=[], flag_options={})


def _wait_ready(port: int, timeout: float = READY_TIMEOUT_S) -> bool:
    url = f"http://127.0.0.1:{port}{HEALTH_PATH}"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            time.sleep(0.2)
    return False


def main() -> None:
    output_dir = _resolve_output_dir()
    os.environ["MOUNTS_OUTPUT_DIR"] = output_dir
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

    port = _find_free_port()
    script = _app_script_path()

    server_thread = threading.Thread(
        target=_run_streamlit,
        args=(port, script),
        daemon=True,
    )
    server_thread.start()

    if not _wait_ready(port):
        sys.exit("MOUNTS Dashboard failed to start within the timeout.")

    import webview

    webview.create_window(
        WINDOW_TITLE,
        f"http://127.0.0.1:{port}",
        width=WINDOW_SIZE[0],
        height=WINDOW_SIZE[1],
        min_size=WINDOW_MIN_SIZE,
    )
    webview.start()


if __name__ == "__main__":
    main()
