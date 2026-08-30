"""Tests for project scaffolding — verifies package imports and entry points."""

from fastapi.testclient import TestClient

from verbamind.backend.main import app
from verbamind.config.config import _load_config, get_config, get_database_url
from verbamind.security.token import get_token

AUTH_HEADERS = {"X-VerbaMind-Token": get_token()}


def test_config_loads_with_defaults():
    config = _load_config()
    assert config["backend"]["host"] == "127.0.0.1"
    assert config["backend"]["port"] == 8000
    assert "sqlite+aiosqlite" in config["database"]["url"]


def test_get_config_caches():
    c1 = get_config()
    c2 = get_config()
    assert c1 is c2


def test_get_database_url():
    url = get_database_url()
    assert url.startswith("sqlite+aiosqlite:///")


def test_backend_health_check():
    client = TestClient(app, headers=AUTH_HEADERS)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
