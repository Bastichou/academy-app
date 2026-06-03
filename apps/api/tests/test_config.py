# apps/api/tests/test_config.py
from unittest.mock import patch
from fastapi.testclient import TestClient
from src.config import Settings
from src.main import app


def test_config_returns_200(client: TestClient):
    assert client.get("/api/config").status_code == 200


def test_config_memory_backend(client: TestClient):
    body = client.get("/api/config").json()
    assert body["storage_backend"] == "memory"
    assert body["redis_connected"] is False
    assert body["azure_storage_configured"] is False


def test_config_has_app_version(client: TestClient):
    body = client.get("/api/config").json()
    assert "app_version" in body
    assert isinstance(body["app_version"], str)


def test_config_does_not_expose_secrets(client: TestClient):
    body = client.get("/api/config").json()
    assert "azure_storage_connection_string" not in body
    assert "redis_url" not in body


def test_config_redis_flag():
    fake = Settings(redis_url="redis://localhost:6379", azure_storage_connection_string="")
    with patch("src.routes.config.get_settings", return_value=fake):
        with TestClient(app) as c:
            body = c.get("/api/config").json()
            assert body["redis_connected"] is True
            assert body["storage_backend"] == "redis"


def test_config_azure_flag():
    fake = Settings(redis_url="", azure_storage_connection_string="DefaultEndpoints...")
    with patch("src.routes.config.get_settings", return_value=fake):
        with TestClient(app) as c:
            body = c.get("/api/config").json()
            assert body["azure_storage_configured"] is True
            assert body["storage_backend"] == "azure"
