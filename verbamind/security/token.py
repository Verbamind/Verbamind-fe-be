"""Shared-secret API token — machine-local auth between GUI and backend.

Both the GUI (api_client) and the backend read the same token file, so only
processes on this machine (with filesystem access) can call the localhost API.
This closes the DNS-rebinding / cross-origin / local-process attack surface.
"""

import secrets
from pathlib import Path

_TOKEN_DIR = Path(__file__).resolve().parent.parent.parent / "config"
_TOKEN_FILE = _TOKEN_DIR / "api_token.txt"


def _read_token() -> str | None:
    if _TOKEN_FILE.exists():
        token = _TOKEN_FILE.read_text(encoding="utf-8").strip()
        if token:
            return token
    return None


def get_or_create_token() -> str:
    """Return the shared token, creating it on first use (idempotent)."""
    token = _read_token()
    if token:
        return token
    _TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    token = secrets.token_hex(32)
    _TOKEN_FILE.write_text(token, encoding="utf-8")
    return token


def get_token() -> str:
    return get_or_create_token()
