"""LLM settings — resolve the active Ollama model & base URL at runtime.

Precedence for the model name:
    env var VERBAMIND_LLM_MODEL > %APPDATA%\\VerbaMind\\settings.json > default.

The base URL uses VERBAMIND_OLLAMA_URL > settings.json > default. A helper to
list installed Ollama models is provided for the settings UI so the user can
pick any model they have pulled locally without changing code.
"""

import json
import logging
import os
import urllib.request
from pathlib import Path
from typing import Any

from verbamind.config.paths import app_data_dir

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5:7b-instruct"

_SETTINGS_FILE_NAME = "settings.json"

_settings_cache: dict[str, Any] | None = None


def settings_file() -> Path:
    return app_data_dir() / _SETTINGS_FILE_NAME


def get_settings() -> dict[str, Any]:
    global _settings_cache
    if _settings_cache is None:
        _settings_cache = _read_settings()
    return _settings_cache


def _read_settings() -> dict[str, Any]:
    path = settings_file()
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, OSError):
            logger.warning("Gagal membaca settings, pakai default.", exc_info=True)
    return {}


def save_settings(settings: dict[str, Any]) -> None:
    global _settings_cache
    path = settings_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)
    _settings_cache = settings


def get_llm_base_url() -> str:
    value = (
        os.environ.get("VERBAMIND_OLLAMA_URL")
        or get_settings().get("ollama_base_url")
        or DEFAULT_BASE_URL
    )
    return value.strip() or DEFAULT_BASE_URL


def resolve_llm_model() -> str:
    env = os.environ.get("VERBAMIND_LLM_MODEL")
    if env and env.strip():
        return env.strip()
    model = get_settings().get("llm_model")
    if model and str(model).strip():
        return str(model).strip()
    return DEFAULT_MODEL


def list_ollama_models(base_url: str | None = None) -> list[str]:
    url = (base_url or get_llm_base_url()).rstrip("/") + "/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=2) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return [m.get("name", "") for m in data.get("models", []) if m.get("name")]
    except Exception:
        logger.debug("Tidak bisa membaca daftar model Ollama.", exc_info=True)
        return []
