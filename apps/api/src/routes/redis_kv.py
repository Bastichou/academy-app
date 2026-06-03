import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from ..config import get_settings

router = APIRouter(prefix="/redis")


async def _get_kv_client():
    settings = get_settings()
    if not settings.redis_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis is not configured (REDIS_URL env var missing)",
        )
    client = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


class KeyValuePair(BaseModel):
    key: str
    value: str


@router.get("/status")
async def redis_status():
    settings = get_settings()
    if not settings.redis_url:
        return {"connected": False, "detail": "REDIS_URL not set"}
    client = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        await client.ping()
        return {"connected": True, "url": settings.redis_url.split("@")[-1]}
    except Exception as exc:
        return {"connected": False, "detail": str(exc)}
    finally:
        await client.aclose()


@router.get("/keys")
async def list_keys(client: aioredis.Redis = Depends(_get_kv_client)):
    # KEYS * is O(N) and blocks Redis — fine for workshop, use SCAN in production
    return {"keys": await client.keys("*")}


@router.get("/{key}")
async def get_key(key: str, client: aioredis.Redis = Depends(_get_kv_client)):
    value = await client.get(key)
    if value is None:
        raise HTTPException(status_code=404, detail=f"Key '{key}' not found")
    return {"key": key, "value": value}


@router.post("/keys", status_code=201)
async def set_key(body: KeyValuePair, client: aioredis.Redis = Depends(_get_kv_client)):
    await client.set(body.key, body.value)
    return {"key": body.key, "value": body.value}


@router.delete("/{key}", status_code=204)
async def delete_key(key: str, client: aioredis.Redis = Depends(_get_kv_client)):
    deleted = await client.delete(key)
    if deleted == 0:
        raise HTTPException(status_code=404, detail=f"Key '{key}' not found")
