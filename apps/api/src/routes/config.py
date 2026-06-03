from fastapi import APIRouter
from ..config import get_settings

router = APIRouter()


@router.get("/config")
async def get_config():
    settings = get_settings()
    return {
        "app_version": settings.app_version,
        "storage_backend": settings.storage_backend,
        "redis_connected": bool(settings.redis_url),
        "azure_storage_configured": bool(settings.azure_storage_connection_string),
    }
