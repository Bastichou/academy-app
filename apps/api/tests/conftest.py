# apps/api/tests/conftest.py
import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from src.main import app
from src.config import get_settings
from src import deps


@pytest.fixture(autouse=True)
def reset_singletons():
    deps._storage = None
    deps._redis_client = None
    get_settings.cache_clear()
    yield
    deps._storage = None
    deps._redis_client = None
    get_settings.cache_clear()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_redis():
    mock = AsyncMock()
    mock.ping = AsyncMock(return_value=True)
    mock.keys = AsyncMock(return_value=[])
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=1)
    mock.aclose = AsyncMock()
    return mock
