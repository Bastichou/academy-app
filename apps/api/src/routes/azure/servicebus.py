from typing import AsyncGenerator

from azure.core.exceptions import AzureError
from azure.servicebus import ServiceBusMessage, ServiceBusReceiveMode
from azure.servicebus.aio import ServiceBusClient
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from ...config import get_settings
from ._errors import invalid_connection_string, upstream_failure

router = APIRouter(prefix="/azure/servicebus")

SERVICE = "Service Bus"


async def _get_servicebus_client() -> AsyncGenerator[ServiceBusClient, None]:
    settings = get_settings()
    if not settings.azure_servicebus_connection_string:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Bus is not configured (AZURE_SERVICEBUS_CONNECTION_STRING env var missing)",
        )
    try:
        client = ServiceBusClient.from_connection_string(
            settings.azure_servicebus_connection_string
        )
    except (ValueError, AzureError) as exc:
        raise invalid_connection_string(SERVICE, exc)
    try:
        yield client
    finally:
        await client.close()


class ServiceBusMessageIn(BaseModel):
    body: str


# NOTE: /status must remain declared before any /{param} route — FastAPI matches in order
@router.get("/status")
async def servicebus_status():
    settings = get_settings()
    if not settings.azure_servicebus_connection_string:
        return {"connected": False, "detail": "AZURE_SERVICEBUS_CONNECTION_STRING not set"}
    try:
        client = ServiceBusClient.from_connection_string(
            settings.azure_servicebus_connection_string
        )
    except (ValueError, AzureError) as exc:
        return {"connected": False, "detail": f"invalid connection string: {exc}"}
    try:
        # Opening a sender confirms the namespace/queue are reachable.
        async with client.get_queue_sender(settings.azure_servicebus_queue):
            pass
        return {"connected": True, "queue": settings.azure_servicebus_queue}
    except Exception as exc:
        return {"connected": False, "detail": str(exc)}
    finally:
        await client.close()


@router.post("/messages", status_code=201)
async def send_message(
    body: ServiceBusMessageIn,
    client: ServiceBusClient = Depends(_get_servicebus_client),
):
    queue = get_settings().azure_servicebus_queue
    try:
        async with client.get_queue_sender(queue) as sender:
            await sender.send_messages(ServiceBusMessage(body.body))
    except AzureError as exc:
        raise upstream_failure(SERVICE, exc)
    return {"sent": True, "queue": queue, "body": body.body}


@router.get("/messages")
async def receive_messages(
    max: int = Query(10, ge=1, le=100, description="Maximum number of messages to consume"),
    client: ServiceBusClient = Depends(_get_servicebus_client),
):
    # Receive-and-delete: messages are removed from the queue as soon as they are read.
    queue = get_settings().azure_servicebus_queue
    try:
        async with client.get_queue_receiver(
            queue, receive_mode=ServiceBusReceiveMode.RECEIVE_AND_DELETE
        ) as receiver:
            received = await receiver.receive_messages(
                max_message_count=max, max_wait_time=5
            )
            messages = [{"body": str(msg)} for msg in received]
    except AzureError as exc:
        raise upstream_failure(SERVICE, exc)
    return {"queue": queue, "count": len(messages), "messages": messages}
