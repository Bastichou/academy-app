"""Shared error translation for the Azure managed-service routes.

Keeps HTTP semantics consistent across Service Bus and Blob:
- service not configured        → 503 (handled in each dependency)
- connection string is invalid  → 500 (server misconfiguration)
- the Azure call itself fails   → 502 (upstream dependency failed)
"""

from azure.core.exceptions import AzureError
from fastapi import HTTPException, status


def invalid_connection_string(service: str, exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"{service} connection string is invalid: {exc}",
    )


def upstream_failure(service: str, exc: AzureError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"{service} request failed: {exc}",
    )
