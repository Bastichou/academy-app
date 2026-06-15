import pytest
from unittest.mock import AsyncMock, patch
from azure.core.exceptions import AzureError
from fastapi.testclient import TestClient

from src.config import Settings
from src.main import app
from src.routes.azure.servicebus import _get_servicebus_client

NO_SB = Settings(azure_servicebus_connection_string="")
WITH_SB = Settings(
    azure_servicebus_connection_string="Endpoint=sb://x/;SharedAccessKeyName=k;SharedAccessKey=v",
    azure_servicebus_queue="workshop",
)


class TestServiceBusStatus:
    """/api/azure/servicebus/status does not use DI — it builds its own client."""

    def test_not_configured(self):
        with patch("src.routes.azure.servicebus.get_settings", return_value=NO_SB):
            with TestClient(app) as c:
                body = c.get("/api/azure/servicebus/status").json()
                assert body["connected"] is False

    def test_configured_but_unreachable(self):
        with patch("src.routes.azure.servicebus.get_settings", return_value=WITH_SB):
            client = AsyncMock()
            client.get_queue_sender = lambda *a, **k: (_ for _ in ()).throw(
                ConnectionError("unreachable")
            )
            with patch(
                "src.routes.azure.servicebus.ServiceBusClient.from_connection_string",
                return_value=client,
            ):
                with TestClient(app) as c:
                    body = c.get("/api/azure/servicebus/status").json()
                    assert body["connected"] is False
                    assert "unreachable" in body["detail"]


@pytest.mark.parametrize(
    "method,path,kwargs",
    [
        ("post", "/api/azure/servicebus/messages", {"json": {"body": "hi"}}),
        ("get", "/api/azure/servicebus/messages", {}),
    ],
)
def test_not_configured_returns_503(method, path, kwargs):
    with patch("src.routes.azure.servicebus.get_settings", return_value=NO_SB):
        with TestClient(app) as c:
            assert getattr(c, method)(path, **kwargs).status_code == 503


class TestServiceBusOps:
    @pytest.fixture(autouse=True)
    def override_client(self, mock_servicebus_client):
        async def fake_client():
            yield mock_servicebus_client

        app.dependency_overrides[_get_servicebus_client] = fake_client
        yield
        app.dependency_overrides.pop(_get_servicebus_client, None)

    def test_send_message_returns_201(self, mock_servicebus_client):
        with patch("src.routes.azure.servicebus.get_settings", return_value=WITH_SB):
            with TestClient(app) as c:
                resp = c.post("/api/azure/servicebus/messages", json={"body": "hello"})
                assert resp.status_code == 201
                assert resp.json() == {
                    "sent": True,
                    "queue": "workshop",
                    "body": "hello",
                }
        mock_servicebus_client.sender.send_messages.assert_awaited_once()

    def test_receive_empty(self, mock_servicebus_client):
        mock_servicebus_client.receiver.receive_messages = AsyncMock(return_value=[])
        with patch("src.routes.azure.servicebus.get_settings", return_value=WITH_SB):
            with TestClient(app) as c:
                body = c.get("/api/azure/servicebus/messages").json()
                assert body == {"queue": "workshop", "count": 0, "messages": []}

    def test_receive_messages(self, mock_servicebus_client):
        mock_servicebus_client.receiver.receive_messages = AsyncMock(
            return_value=["first", "second"]
        )
        with patch("src.routes.azure.servicebus.get_settings", return_value=WITH_SB):
            with TestClient(app) as c:
                body = c.get("/api/azure/servicebus/messages?max=5").json()
                assert body["count"] == 2
                assert body["messages"] == [{"body": "first"}, {"body": "second"}]

    def test_send_upstream_failure_returns_502(self, mock_servicebus_client):
        mock_servicebus_client.sender.send_messages = AsyncMock(
            side_effect=AzureError("queue not found")
        )
        with patch("src.routes.azure.servicebus.get_settings", return_value=WITH_SB):
            with TestClient(app) as c:
                resp = c.post("/api/azure/servicebus/messages", json={"body": "x"})
                assert resp.status_code == 502
                assert "queue not found" in resp.json()["detail"]

    @pytest.mark.parametrize("bad_max", ["0", "-1", "101"])
    def test_receive_rejects_invalid_max(self, bad_max):
        with patch("src.routes.azure.servicebus.get_settings", return_value=WITH_SB):
            with TestClient(app) as c:
                resp = c.get(f"/api/azure/servicebus/messages?max={bad_max}")
                assert resp.status_code == 422
