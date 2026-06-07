import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from src.config import Settings
from src.main import app
from src.routes.redis_kv import _get_kv_client

NO_REDIS = Settings(redis_url="", azure_storage_connection_string="")
WITH_REDIS = Settings(redis_url="redis://localhost:6379", azure_storage_connection_string="")


def _make_redis_mock(**ping_kwargs) -> AsyncMock:
    m = AsyncMock()
    m.ping = AsyncMock(**ping_kwargs)
    m.aclose = AsyncMock()
    return m


class TestRedisStatus:
    def test_no_redis_configured(self):
        with patch("src.routes.redis_kv.get_settings", return_value=NO_REDIS):
            with TestClient(app) as c:
                body = c.get("/api/redis/status").json()
                assert body["connected"] is False

    def test_redis_connected(self):
        with patch("src.routes.redis_kv.get_settings", return_value=WITH_REDIS):
            with patch("src.routes.redis_kv.aioredis.from_url", return_value=_make_redis_mock(return_value=True)):
                with TestClient(app) as c:
                    assert c.get("/api/redis/status").json()["connected"] is True

    def test_redis_unreachable(self):
        with patch("src.routes.redis_kv.get_settings", return_value=WITH_REDIS):
            with patch("src.routes.redis_kv.aioredis.from_url", return_value=_make_redis_mock(side_effect=ConnectionError("refused"))):
                with TestClient(app) as c:
                    body = c.get("/api/redis/status").json()
                    assert body["connected"] is False
                    assert "refused" in body["detail"]


@pytest.mark.parametrize("method,path,kwargs", [
    ("get",    "/api/redis/keys",  {}),
    ("get",    "/api/redis/mykey", {}),
    ("post",   "/api/redis/keys",  {"json": {"key": "k", "value": "v"}}),
    ("delete", "/api/redis/mykey", {}),
])
def test_no_redis_returns_503(method, path, kwargs):
    with patch("src.routes.redis_kv.get_settings", return_value=NO_REDIS):
        with TestClient(app) as c:
            assert getattr(c, method)(path, **kwargs).status_code == 503


class TestRedisOps:
    @pytest.fixture(autouse=True)
    def setup_redis_override(self, mock_redis):
        async def fake_client():
            yield mock_redis

        app.dependency_overrides[_get_kv_client] = fake_client
        yield
        app.dependency_overrides.pop(_get_kv_client, None)

    def test_list_keys_empty(self, mock_redis):
        mock_redis.keys = AsyncMock(return_value=[])
        with TestClient(app) as c:
            assert c.get("/api/redis/keys").json() == {"keys": []}

    def test_list_keys_with_items(self, mock_redis):
        mock_redis.keys = AsyncMock(return_value=["foo", "bar"])
        with TestClient(app) as c:
            assert c.get("/api/redis/keys").json() == {"keys": ["foo", "bar"]}

    def test_get_existing_key(self, mock_redis):
        mock_redis.get = AsyncMock(return_value="world")
        with TestClient(app) as c:
            assert c.get("/api/redis/hello").json() == {"key": "hello", "value": "world"}

    def test_get_missing_key_404(self, mock_redis):
        mock_redis.get = AsyncMock(return_value=None)
        with TestClient(app) as c:
            assert c.get("/api/redis/missing").status_code == 404

    def test_set_key_returns_201(self, mock_redis):
        mock_redis.set = AsyncMock(return_value=True)
        with TestClient(app) as c:
            response = c.post("/api/redis/keys", json={"key": "x", "value": "42"})
            assert response.status_code == 201
            assert response.json() == {"key": "x", "value": "42"}

    def test_delete_existing_key_204(self, mock_redis):
        mock_redis.delete = AsyncMock(return_value=1)
        with TestClient(app) as c:
            assert c.delete("/api/redis/x").status_code == 204

    def test_delete_missing_key_404(self, mock_redis):
        mock_redis.delete = AsyncMock(return_value=0)
        with TestClient(app) as c:
            assert c.delete("/api/redis/missing").status_code == 404
