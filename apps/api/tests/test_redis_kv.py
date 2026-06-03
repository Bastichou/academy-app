# apps/api/tests/test_redis_kv.py
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from src.config import Settings
from src.main import app

NO_REDIS = Settings(redis_url="", azure_storage_connection_string="")
WITH_REDIS = Settings(redis_url="redis://localhost:6379", azure_storage_connection_string="")


class TestRedisStatus:
    def test_no_redis_configured(self):
        with patch("src.routes.redis_kv.get_settings", return_value=NO_REDIS):
            with TestClient(app) as c:
                body = c.get("/api/redis/status").json()
                assert body["connected"] is False

    def test_redis_connected(self):
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_client.aclose = AsyncMock()
        with patch("src.routes.redis_kv.get_settings", return_value=WITH_REDIS):
            with patch("src.routes.redis_kv.aioredis.from_url", return_value=mock_client):
                with TestClient(app) as c:
                    assert c.get("/api/redis/status").json()["connected"] is True

    def test_redis_unreachable(self):
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(side_effect=ConnectionError("refused"))
        mock_client.aclose = AsyncMock()
        with patch("src.routes.redis_kv.get_settings", return_value=WITH_REDIS):
            with patch("src.routes.redis_kv.aioredis.from_url", return_value=mock_client):
                with TestClient(app) as c:
                    body = c.get("/api/redis/status").json()
                    assert body["connected"] is False
                    assert "refused" in body["detail"]


class TestNoRedisUrl:
    def test_list_keys_503(self):
        with patch("src.routes.redis_kv.get_settings", return_value=NO_REDIS):
            with TestClient(app) as c:
                assert c.get("/api/redis/keys").status_code == 503

    def test_get_key_503(self):
        with patch("src.routes.redis_kv.get_settings", return_value=NO_REDIS):
            with TestClient(app) as c:
                assert c.get("/api/redis/mykey").status_code == 503

    def test_set_key_503(self):
        with patch("src.routes.redis_kv.get_settings", return_value=NO_REDIS):
            with TestClient(app) as c:
                assert c.post("/api/redis/keys", json={"key": "k", "value": "v"}).status_code == 503

    def test_delete_key_503(self):
        with patch("src.routes.redis_kv.get_settings", return_value=NO_REDIS):
            with TestClient(app) as c:
                assert c.delete("/api/redis/mykey").status_code == 503


class TestRedisOps:
    def _setup_override(self, mock):
        from src.routes.redis_kv import _get_kv_client

        async def fake_client():
            yield mock

        app.dependency_overrides[_get_kv_client] = fake_client

    def _teardown_override(self):
        from src.routes.redis_kv import _get_kv_client

        app.dependency_overrides.pop(_get_kv_client, None)

    def test_list_keys_empty(self, mock_redis):
        mock_redis.keys = AsyncMock(return_value=[])
        self._setup_override(mock_redis)
        try:
            with TestClient(app) as c:
                assert c.get("/api/redis/keys").json() == {"keys": []}
        finally:
            self._teardown_override()

    def test_list_keys_with_items(self, mock_redis):
        mock_redis.keys = AsyncMock(return_value=["foo", "bar"])
        self._setup_override(mock_redis)
        try:
            with TestClient(app) as c:
                assert c.get("/api/redis/keys").json() == {"keys": ["foo", "bar"]}
        finally:
            self._teardown_override()

    def test_get_existing_key(self, mock_redis):
        mock_redis.get = AsyncMock(return_value="world")
        self._setup_override(mock_redis)
        try:
            with TestClient(app) as c:
                body = c.get("/api/redis/hello").json()
                assert body == {"key": "hello", "value": "world"}
        finally:
            self._teardown_override()

    def test_get_missing_key_404(self, mock_redis):
        mock_redis.get = AsyncMock(return_value=None)
        self._setup_override(mock_redis)
        try:
            with TestClient(app) as c:
                assert c.get("/api/redis/missing").status_code == 404
        finally:
            self._teardown_override()

    def test_set_key_returns_201(self, mock_redis):
        mock_redis.set = AsyncMock(return_value=True)
        self._setup_override(mock_redis)
        try:
            with TestClient(app) as c:
                response = c.post("/api/redis/keys", json={"key": "x", "value": "42"})
                assert response.status_code == 201
                assert response.json() == {"key": "x", "value": "42"}
        finally:
            self._teardown_override()

    def test_delete_existing_key_204(self, mock_redis):
        mock_redis.delete = AsyncMock(return_value=1)
        self._setup_override(mock_redis)
        try:
            with TestClient(app) as c:
                assert c.delete("/api/redis/x").status_code == 204
        finally:
            self._teardown_override()

    def test_delete_missing_key_404(self, mock_redis):
        mock_redis.delete = AsyncMock(return_value=0)
        self._setup_override(mock_redis)
        try:
            with TestClient(app) as c:
                assert c.delete("/api/redis/missing").status_code == 404
        finally:
            self._teardown_override()
