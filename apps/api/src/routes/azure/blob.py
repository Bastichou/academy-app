from typing import AsyncGenerator

from azure.core.exceptions import (
    AzureError,
    ResourceExistsError,
    ResourceNotFoundError,
)
from azure.storage.blob.aio import BlobServiceClient, ContainerClient
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ...config import get_settings
from ._errors import invalid_connection_string, upstream_failure

router = APIRouter(prefix="/azure/blob")

SERVICE = "Blob Storage"


async def _get_container_client() -> AsyncGenerator[ContainerClient, None]:
    settings = get_settings()
    if not settings.azure_storage_connection_string:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Blob Storage is not configured (AZURE_STORAGE_CONNECTION_STRING env var missing)",
        )
    try:
        service = BlobServiceClient.from_connection_string(
            settings.azure_storage_connection_string
        )
    except (ValueError, AzureError) as exc:
        raise invalid_connection_string(SERVICE, exc)
    try:
        container = service.get_container_client(settings.azure_blob_container)
        try:
            await container.create_container()
        except ResourceExistsError:
            pass
        except AzureError as exc:
            raise upstream_failure(SERVICE, exc)
        yield container
    finally:
        await service.close()


class BlobContentIn(BaseModel):
    content: str


# NOTE: /status and / (list) must remain declared before /{name} — FastAPI matches in order
@router.get("/status")
async def blob_status():
    settings = get_settings()
    if not settings.azure_storage_connection_string:
        return {"connected": False, "detail": "AZURE_STORAGE_CONNECTION_STRING not set"}
    try:
        service = BlobServiceClient.from_connection_string(
            settings.azure_storage_connection_string
        )
    except (ValueError, AzureError) as exc:
        return {"connected": False, "detail": f"invalid connection string: {exc}"}
    try:
        await service.get_account_information()
        return {"connected": True, "container": settings.azure_blob_container}
    except Exception as exc:
        return {"connected": False, "detail": str(exc)}
    finally:
        await service.close()


@router.get("/")
async def list_blobs(container: ContainerClient = Depends(_get_container_client)):
    try:
        names = [name async for name in container.list_blob_names()]
    except AzureError as exc:
        raise upstream_failure(SERVICE, exc)
    return {"container": get_settings().azure_blob_container, "blobs": names}


@router.put("/{name}")
async def write_blob(
    name: str,
    body: BlobContentIn,
    container: ContainerClient = Depends(_get_container_client),
):
    try:
        await container.get_blob_client(name).upload_blob(
            body.content.encode(), overwrite=True
        )
    except AzureError as exc:
        raise upstream_failure(SERVICE, exc)
    return {"name": name, "size": len(body.content)}


@router.get("/{name}")
async def read_blob(
    name: str,
    container: ContainerClient = Depends(_get_container_client),
):
    try:
        stream = await container.get_blob_client(name).download_blob()
        data = await stream.readall()
    except ResourceNotFoundError:
        raise HTTPException(status_code=404, detail=f"Blob '{name}' not found")
    except AzureError as exc:
        raise upstream_failure(SERVICE, exc)
    return {"name": name, "content": data.decode()}
