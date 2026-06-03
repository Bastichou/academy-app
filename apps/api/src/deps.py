import redis.asyncio as aioredis
from .config import get_settings
from .storage.base import MessageStorage
from .storage.memory import InMemoryStorage
from .storage.azure import AzureTableStorage
from .storage.redis_store import RedisStorage

_storage: MessageStorage | None = None
_redis_client: aioredis.Redis | None = None


def get_redis_client() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        if not settings.redis_url:
            raise RuntimeError("REDIS_URL is not configured")
        _redis_client = aioredis.from_url(settings.redis_url, decode_responses=False)
    return _redis_client


def get_storage() -> MessageStorage:
    global _storage
    if _storage is None:
        settings = get_settings()
        backend = settings.storage_backend
        if backend == "redis":
            _storage = RedisStorage(get_redis_client())
        elif backend == "azure":
            _storage = AzureTableStorage()
        else:
            _storage = InMemoryStorage()
    return _storage
