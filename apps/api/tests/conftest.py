# apps/api/tests/conftest.py
import pytest
from unittest.mock import AsyncMock, MagicMock
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


class _AsyncCtx:
    """Wrap an object so it can be used as an async context manager.

    The Azure SDKs hand back senders/receivers via ``async with``; this lets a
    plain mock stand in for them.
    """

    def __init__(self, obj):
        self._obj = obj

    async def __aenter__(self):
        return self._obj

    async def __aexit__(self, *exc):
        return False


@pytest.fixture
def mock_servicebus_client():
    """AsyncMock ServiceBusClient whose sender/receiver are async context managers."""
    sender = AsyncMock()
    receiver = AsyncMock()
    receiver.receive_messages = AsyncMock(return_value=[])

    client = AsyncMock()
    client.sender = sender
    client.receiver = receiver
    client.get_queue_sender = MagicMock(return_value=_AsyncCtx(sender))
    client.get_queue_receiver = MagicMock(return_value=_AsyncCtx(receiver))
    return client


@pytest.fixture
def mock_blob_container():
    """AsyncMock ContainerClient with a configurable blob client."""
    blob = AsyncMock()
    blob.upload_blob = AsyncMock()
    stream = AsyncMock()
    stream.readall = AsyncMock(return_value=b"")
    blob.download_blob = AsyncMock(return_value=stream)

    container = AsyncMock()
    container.blob = blob
    container.get_blob_client = MagicMock(return_value=blob)

    async def _empty_names():
        for name in []:
            yield name

    container.list_blob_names = MagicMock(return_value=_empty_names())
    return container
