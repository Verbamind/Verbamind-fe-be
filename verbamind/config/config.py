"""Configuration management — reads config.json with graceful fallback to defaults."""

import json
from pathlib import Path
from typing import Any

_CONFIG_DIR = Path(__file__).resolve().parent
_DEFAULT_CONFIG: dict[str, Any] = {
    "backend": {
        "host": "127.0.0.1",
        "port": 8000,
    },
    "database": {
        "url": "sqlite+aiosqlite:///./verbamind.db",
    },
    "models": {
        "whisper": "models/whisper/",
        "SpeechToNonverbalInformation": "models/SpeechToNonverbalInformation/",
        "llm": "models/llm/",
    },
    "recording": {
        "sample_rate": 16000,
        "channels": 2,
        "chunk_size": 1024,
    },
    "audio": {
        "input_dir": "recordings/",
        "output_format": ".vera",
    },
}

_config: dict[str, Any] | None = None


def _load_config() -> dict[str, Any]:
    config_path = _CONFIG_DIR / "config.json"
    loaded = _DEFAULT_CONFIG.copy()
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                user_config = json.load(f)
            _deep_merge(loaded, user_config)
        except (json.JSONDecodeError, OSError):
            pass
    return loaded


def _deep_merge(base: dict, override: dict) -> None:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def get_config() -> dict[str, Any]:
    global _config
    if _config is None:
        _config = _load_config()
    return _config


def get_backend_port() -> int:
    return int(get_config()["backend"]["port"])


def get_database_url() -> str:
    return str(get_config()["database"]["url"])


def get_models_dir() -> dict[str, str]:
    return {k: str(v) for k, v in get_config()["models"].items()}
