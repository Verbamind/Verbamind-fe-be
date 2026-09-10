"""Tests for LLM settings resolution (env > settings.json > default)."""

import json

import pytest

from verbamind.config import llm_settings


@pytest.fixture
def clean_settings(monkeypatch, tmp_path):
    monkeypatch.setattr(llm_settings, "_settings_cache", None)
    monkeypatch.setattr(llm_settings, "settings_file", lambda: tmp_path / "settings.json")
    monkeypatch.delenv("VERBAMIND_LLM_MODEL", raising=False)
    monkeypatch.delenv("VERBAMIND_OLLAMA_URL", raising=False)
    yield tmp_path
    monkeypatch.setattr(llm_settings, "_settings_cache", None)


def test_resolve_defaults_to_builtin(clean_settings):
    assert llm_settings.resolve_llm_model() == "qwen2.5:7b-instruct"
    assert llm_settings.get_llm_base_url() == "http://localhost:11434"


def test_resolve_env_overrides_everything(clean_settings, monkeypatch):
    monkeypatch.setenv("VERBAMIND_LLM_MODEL", "qwen2.5:3b-instruct")
    assert llm_settings.resolve_llm_model() == "qwen2.5:3b-instruct"


def test_resolve_settings_file(clean_settings):
    llm_settings.save_settings({"llm_model": "llama3.1"})
    assert llm_settings.resolve_llm_model() == "llama3.1"


def test_resolve_env_beats_settings(clean_settings, monkeypatch):
    llm_settings.save_settings({"llm_model": "llama3.1"})
    monkeypatch.setenv("VERBAMIND_LLM_MODEL", "mistral")
    assert llm_settings.resolve_llm_model() == "mistral"


def test_base_url_from_settings(clean_settings):
    llm_settings.save_settings({"ollama_base_url": "http://127.0.0.1:9999"})
    assert llm_settings.get_llm_base_url() == "http://127.0.0.1:9999"


def test_save_settings_roundtrip(clean_settings):
    llm_settings.save_settings({"llm_model": "qwen2.5:3b-instruct"})
    assert llm_settings.get_settings()["llm_model"] == "qwen2.5:3b-instruct"
    path = llm_settings.settings_file()
    assert json.loads(path.read_text(encoding="utf-8"))["llm_model"] == "qwen2.5:3b-instruct"


def test_resolve_strips_whitespace(clean_settings):
    llm_settings.save_settings({"llm_model": "  qwen2.5:3b-instruct  "})
    assert llm_settings.resolve_llm_model() == "qwen2.5:3b-instruct"


def test_list_ollama_models_parses_response(clean_settings, monkeypatch):
    def fake_urlopen(url, timeout):
        class Resp:
            def read(self):
                return json.dumps(
                    {"models": [{"name": "qwen2.5:3b-instruct"}, {"name": "nomic-embed-text"}]}
                ).encode()

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        return Resp()

    monkeypatch.setattr(llm_settings.urllib.request, "urlopen", fake_urlopen)
    assert llm_settings.list_ollama_models() == ["qwen2.5:3b-instruct", "nomic-embed-text"]


def test_list_ollama_models_returns_empty_on_error(clean_settings, monkeypatch):
    def boom(url, timeout):
        raise OSError("down")

    monkeypatch.setattr(llm_settings.urllib.request, "urlopen", boom)
    assert llm_settings.list_ollama_models() == []
