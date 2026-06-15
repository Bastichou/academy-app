from fastapi import APIRouter

from ..config import get_settings

router = APIRouter()


@router.get("/status")
async def feature_status():
    """Big-picture view of which features are enabled by the current configuration.

    Lets the frontend render available features without probing every service.
    Reports configuration only — it does not open connections.
    """
    settings = get_settings()
    return {
        "app_version": settings.app_version,
        "storage_backend": settings.storage_backend,
        "features": [
            {
                "id": "messages",
                "name": "Messages",
                "enabled": True,
                "path": "/api/messages",
                "backend": settings.storage_backend,
            },
            {
                "id": "redis",
                "name": "Redis Key/Value",
                "enabled": bool(settings.redis_url),
                "path": "/api/redis",
                "env": "REDIS_URL",
            },
            {
                "id": "azure_servicebus",
                "name": "Azure Service Bus",
                "enabled": bool(settings.azure_servicebus_connection_string),
                "path": "/api/azure/servicebus",
                "env": "AZURE_SERVICEBUS_CONNECTION_STRING",
            },
            {
                "id": "azure_blob",
                "name": "Azure Blob Storage",
                "enabled": bool(settings.azure_storage_connection_string),
                "path": "/api/azure/blob",
                "env": "AZURE_STORAGE_CONNECTION_STRING",
            },
        ],
    }
