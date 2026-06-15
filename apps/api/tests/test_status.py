from unittest.mock import patch
from fastapi.testclient import TestClient

from src.config import Settings
from src.main import app


def test_status_returns_200(client: TestClient):
    assert client.get("/api/status").status_code == 200


def test_status_all_disabled_by_default(client: TestClient):
    body = client.get("/api/status").json()
    assert body["storage_backend"] == "memory"
    by_id = {f["id"]: f for f in body["features"]}
    # Messages is always available; cloud features off until configured.
    assert by_id["messages"]["enabled"] is True
    assert by_id["redis"]["enabled"] is False
    assert by_id["azure_servicebus"]["enabled"] is False
    assert by_id["azure_blob"]["enabled"] is False


def test_status_does_not_expose_secrets(client: TestClient):
    body = client.get("/api/status").json()
    blob = next(f for f in body["features"] if f["id"] == "azure_blob")
    # Only the env-var name is exposed, never its value.
    assert blob["env"] == "AZURE_STORAGE_CONNECTION_STRING"
    assert "AZURE_STORAGE_CONNECTION_STRING" not in str(body).replace(
        "AZURE_STORAGE_CONNECTION_STRING", ""
    )


def test_status_reflects_enabled_features():
    fake = Settings(
        redis_url="redis://localhost:6379",
        azure_servicebus_connection_string="Endpoint=sb://x/;SharedAccessKeyName=k;SharedAccessKey=v",
        azure_storage_connection_string="DefaultEndpointsProtocol=https;AccountName=a;AccountKey=k==;EndpointSuffix=core.windows.net",
    )
    with patch("src.routes.status.get_settings", return_value=fake):
        with TestClient(app) as c:
            body = c.get("/api/status").json()
            by_id = {f["id"]: f for f in body["features"]}
            assert body["storage_backend"] == "redis"
            assert by_id["redis"]["enabled"] is True
            assert by_id["azure_servicebus"]["enabled"] is True
            assert by_id["azure_blob"]["enabled"] is True
