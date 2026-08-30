"""Windows DPAPI key protection — AES key generation, seal, and unseal.

Uses ctypes to call CryptProtectData/CryptUnprotectData from crypt32.dll.
No external dependencies beyond Windows SDK (available on all Windows systems).
"""

import ctypes
import ctypes.wintypes
from pathlib import Path

from verbamind.config.paths import key_file
from verbamind.security.encryptor import generate_aes_key as _generate_raw_key

_KEY_FILE_NAME = "key.dat"
_KEY_DIR = key_file().parent

_CRYPTPROTECT_UI_FORBIDDEN = 0x1

_crypt32 = ctypes.windll.crypt32
_kernel32 = ctypes.windll.kernel32


class _DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", ctypes.wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_char)),
    ]


def _protect(data: bytes) -> bytes:
    data_in = _DATA_BLOB(len(data), ctypes.cast(ctypes.create_string_buffer(data), ctypes.POINTER(ctypes.c_char)))
    data_out = _DATA_BLOB()
    if not _crypt32.CryptProtectData(
        ctypes.byref(data_in),
        "VerbaMind AES Key",
        None, None, None,
        _CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(data_out),
    ):
        raise OSError("CryptProtectData failed")
    result = ctypes.string_at(data_out.pbData, data_out.cbData)
    _kernel32.LocalFree(data_out.pbData)
    return result


def _unprotect(blob: bytes) -> bytes:
    data_in = _DATA_BLOB(len(blob), ctypes.cast(ctypes.create_string_buffer(blob), ctypes.POINTER(ctypes.c_char)))
    data_out = _DATA_BLOB()
    if not _crypt32.CryptUnprotectData(
        ctypes.byref(data_in),
        None, None, None, None,
        _CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(data_out),
    ):
        raise OSError("CryptUnprotectData failed")
    result = ctypes.string_at(data_out.pbData, data_out.cbData)
    _kernel32.LocalFree(data_out.pbData)
    return result


def generate_aes_key() -> bytes:
    return _generate_raw_key()


_key_dir = _KEY_DIR


def _set_key_dir(path: Path) -> None:
    global _key_dir
    _key_dir = path


def _key_path() -> Path:
    return _key_dir / _KEY_FILE_NAME


def is_key_initialized() -> bool:
    return _key_path().exists()


def initialize_key() -> bool:
    if is_key_initialized():
        return True
    raw_key = generate_aes_key()
    protected = _protect(raw_key)
    _KEY_DIR.mkdir(parents=True, exist_ok=True)
    _key_path().write_bytes(protected)
    return False


def load_key() -> bytes:
    protected = _key_path().read_bytes()
    return _unprotect(protected)
