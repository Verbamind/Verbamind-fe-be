"""Runtime paths — single user-writable app-data directory for persistent files.

Both the GUI and the backend resolve runtime files (token, key, database,
recordings) to the same location so they work consistently in dev and when
packaged as a standalone installer.
"""

import os
import sys
from pathlib import Path

APP_DIR_NAME = "VerbaMind"


def is_frozen() -> bool:
    """True when packaged (PyInstaller sets sys.frozen; Nuitka sets __compiled__)."""
    return getattr(sys, "frozen", False) or hasattr(
        sys.modules.get("__main__"), "__compiled__"
    )


def app_data_dir() -> Path:
    """User-writable directory (Windows: %APPDATA%\\VerbaMind).

    Not in Program Files, so it is writable without admin rights.
    """
    base = os.environ.get("APPDATA") or str(Path.home())
    d = Path(base) / APP_DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def app_install_dir() -> Path:
    """Read-only install directory holding bundled resources.

    Frozen (backend): {app} (parent of the backend/ dir). Dev: repo root.
    Used to locate bundled models and the FAISS index.
    """
    if is_frozen():
        return Path(sys.executable).resolve().parent.parent
    return Path(__file__).resolve().parents[2]


def token_file() -> Path:
    return app_data_dir() / "api_token.txt"


def key_file() -> Path:
    return app_data_dir() / "key.dat"


def database_path() -> Path:
    return app_data_dir() / "verbamind.db"


def recordings_dir() -> Path:
    d = app_data_dir() / "recordings"
    d.mkdir(parents=True, exist_ok=True)
    return d
