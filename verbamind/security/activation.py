"""License activation — HWID generation, license key validation, activation state."""

import hashlib
import hmac
import os
import platform
import uuid
from pathlib import Path

_ACTIVATION_FILE = Path(__file__).resolve().parent.parent.parent / "config" / ".activated"
_LICENSE_FILE = Path(__file__).resolve().parent.parent.parent / "config" / ".license"


def get_hardware_id() -> str:
    components = [
        platform.node(),
        platform.processor(),
        str(uuid.getnode()),
    ]
    raw = "|".join(components)
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def generate_license_key(hwid: str, master_key: str) -> str:
    msg = hwid.encode()
    key = master_key.encode()
    signature = hmac.new(key, msg, hashlib.sha256).hexdigest()[:16]
    return f"{hwid[:8]}-{signature}"


def validate_license_key(license_key: str, hwid: str, master_key: str) -> bool:
    try:
        expected = generate_license_key(hwid, master_key)
        return hmac.compare_digest(license_key, expected)
    except Exception:
        return False


def is_activated() -> bool:
    return _ACTIVATION_FILE.exists()


def activate(license_key: str) -> None:
    _LICENSE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _LICENSE_FILE.write_text(license_key)
    _ACTIVATION_FILE.parent.mkdir(parents=True, exist_ok=True)
    _ACTIVATION_FILE.touch()


def deactivate() -> None:
    if _LICENSE_FILE.exists():
        _LICENSE_FILE.unlink()
    if _ACTIVATION_FILE.exists():
        _ACTIVATION_FILE.unlink()
