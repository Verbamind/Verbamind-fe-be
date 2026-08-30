"""PySide6 GUI entry point — VerbaMind main window.

Spawns the backend automatically if it is not already running, so the
packaged app works with a single click.
"""

import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from PySide6.QtWidgets import QApplication

from verbamind.config.config import get_backend_port
from verbamind.gui.windows.main_window import MainWindow

_CREATE_NO_WINDOW = 0x08000000


def _backend_running(port: int) -> bool:
    try:
        urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/v1/health", timeout=1
        )
        return True
    except urllib.error.HTTPError:
        return True  # 401/403 = backend is up (auth active)
    except Exception:
        return False


def _spawn_backend(port: int) -> None:
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
        exe = base / "backend" / "backend.exe"
        if not exe.exists():
            exe = base / "backend.exe"
        if exe.exists():
            subprocess.Popen(
                [str(exe)],
                cwd=str(base),
                creationflags=_CREATE_NO_WINDOW,
            )
    else:
        root = Path(__file__).resolve().parent.parent
        subprocess.Popen(
            [sys.executable, "-m", "verbamind.backend.main"],
            cwd=str(root),
            creationflags=_CREATE_NO_WINDOW,
        )


def main():
    port = get_backend_port()
    if not _backend_running(port):
        _spawn_backend(port)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
