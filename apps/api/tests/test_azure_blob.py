import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from azure.core.exceptions import AzureError, ResourceNotFoundError
from fastapi.testclient import TestClient

from src.config import Settings
from src.main import app
from src.routes.azure.blob import _get_container_client

NO_BLOB = Settings(azure_storage_connection_string="")
WITH_BLOB = Settings(
    azure_storage_connection_string="DefaultEndpointsProtocol=https;AccountName=a;AccountKey=k==;EndpointSuffix=core.windows.net",
    azure_blob_container="workshop",
)


class TestBlobStatus:
    """/api/azure/blob/status does not use DI — it builds its own client."""

    def test_not_configured(self):
        with patch("src.routes.azure.blob.get_settings", return_value=NO_BLOB):
            with TestClient(app) as c:
                body = c.get("/api/azure/blob/status").json()
                assert body["connected"] is False

    def test_configured_but_unreachable(self):
        with patch("src.routes.azure.blob.get_settings", return_value=WITH_BLOB):
            service = AsyncMock()
            service.get_account_information = AsyncMock(
                side_effect=ConnectionError("unreachable")
            )
            with patch(
                "src.routes.azure.blob.BlobServiceClient.from_connection_string",
                return_value=service,
            ):
                with TestClient(app) as c:
                    body = c.get("/api/azure/blob/status").json()
                    assert body["connected"] is False
                    assert "unreachable" in body["detail"]


@pytest.mark.parametrize(
    "method,path,kwargs",
    [
        ("get", "/api/azure/blob/", {}),
        ("put", "/api/azure/blob/foo", {"json": {"content": "x"}}),
        ("get", "/api/azure/blob/foo", {}),
    ],
)
def test_not_configured_returns_503(method, path, kwargs):
    with patch("src.routes.azure.blob.get_settings", return_value=NO_BLOB):
        with TestClient(app) as c:
            assert getattr(c, method)(path, **kwargs).status_code == 503


class TestBlobOps:
    @pytest.fixture(autouse=True)
    def override_container(self, mock_blob_container):
        async def fake_container():
            yield mock_blob_container

        app.dependency_overrides[_get_container_client] = fake_container
        yield
        app.dependency_overrides.pop(_get_container_client, None)

    def test_write_blob(self, mock_blob_container):
        with patch("src.routes.azure.blob.get_settings", return_value=WITH_BLOB):
            with TestClient(app) as c:
                resp = c.put("/api/azure/blob/hello", json={"content": "world"})
                assert resp.status_code == 200
                assert resp.json() == {"name": "hello", "size": 5}
        mock_blob_container.blob.upload_blob.assert_awaited_once()

    def test_read_existing_blob(self, mock_blob_container):
        stream = AsyncMock()
        stream.readall = AsyncMock(return_value=b"world")
        mock_blob_container.blob.download_blob = AsyncMock(return_value=stream)
        with patch("src.routes.azure.blob.get_settings", return_value=WITH_BLOB):
            with TestClient(app) as c:
                body = c.get("/api/azure/blob/hello").json()
                assert body == {"name": "hello", "content": "world"}

    def test_read_missing_blob_404(self, mock_blob_container):
        mock_blob_container.blob.download_blob = AsyncMock(
            side_effect=ResourceNotFoundError("nope")
        )
        with patch("src.routes.azure.blob.get_settings", return_value=WITH_BLOB):
            with TestClient(app) as c:
                assert c.get("/api/azure/blob/missing").status_code == 404

    def test_list_blobs(self, mock_blob_container):
        async def _names():
            for n in ["a.txt", "b.txt"]:
                yield n

        mock_blob_container.list_blob_names = MagicMock(return_value=_names())
        with patch("src.routes.azure.blob.get_settings", return_value=WITH_BLOB):
            with TestClient(app) as c:
                body = c.get("/api/azure/blob/").json()
                assert body == {"container": "workshop", "blobs": ["a.txt", "b.txt"]}

    def test_write_upstream_failure_returns_502(self, mock_blob_container):
        mock_blob_container.blob.upload_blob = AsyncMock(
            side_effect=AzureError("auth failed")
        )
        with patch("src.routes.azure.blob.get_settings", return_value=WITH_BLOB):
            with TestClient(app) as c:
                resp = c.put("/api/azure/blob/x", json={"content": "y"})
                assert resp.status_code == 502
                assert "auth failed" in resp.json()["detail"]

    def test_read_upstream_failure_returns_502(self, mock_blob_container):
        mock_blob_container.blob.download_blob = AsyncMock(
            side_effect=AzureError("server busy")
        )
        with patch("src.routes.azure.blob.get_settings", return_value=WITH_BLOB):
            with TestClient(app) as c:
                resp = c.get("/api/azure/blob/x")
                assert resp.status_code == 502
                assert "server busy" in resp.json()["detail"]
