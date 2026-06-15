# Academy API

Python FastAPI backend for the Kubernetes/Cloud workshop demo app.

## Quick Start

```bash
# Install dependencies
uv sync

# Run dev server (reloads on change)
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8080

# Run tests
uv run pytest

# Run a single test
uv run pytest tests/test_messages.py::test_create_message_returns_201 -v
```

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `REDIS_URL` | No | `""` | Redis connection URL, e.g. `redis://localhost:6379`. Enables Redis storage. |
| `AZURE_STORAGE_CONNECTION_STRING` | No | `""` | Storage Account connection string. Enables Azure Table storage **and** the Blob Storage routes. |
| `AZURE_SERVICEBUS_CONNECTION_STRING` | No | `""` | Service Bus namespace connection string. Enables the Service Bus routes. |
| `AZURE_SERVICEBUS_QUEUE` | No | `workshop` | Queue used by the Service Bus send/consume routes. |
| `AZURE_BLOB_CONTAINER` | No | `workshop` | Blob container used by the Blob Storage routes (created if missing). |

### Storage Backend Priority

1. **Redis** — if `REDIS_URL` is set
2. **Azure Table Storage** — if `AZURE_STORAGE_CONNECTION_STRING` is set
3. **In-Memory** — default, no configuration needed (data lost on restart)

## API Routes

All routes are prefixed with `/api`.

### Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Returns `{"status": "ok", "service": "academy-api"}` |

### Messages

| Method | Path | Body | Description |
|---|---|---|---|
| `GET` | `/api/messages` | — | List all messages |
| `POST` | `/api/messages` | `{"text": str, "author": str}` | Create a message (`author` defaults to `"Anonyme"`) |

### Status (feature discovery)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/status` | Lists every feature and whether it is enabled by the current configuration. Reports config only (no live probing), so the frontend can show a big picture of what's available. Exposes only env-var **names**, never their values. |

Example response:
```json
{
  "app_version": "0.1.0",
  "storage_backend": "memory",
  "features": [
    {"id": "messages", "name": "Messages", "enabled": true, "path": "/api/messages", "backend": "memory"},
    {"id": "redis", "name": "Redis Key/Value", "enabled": false, "path": "/api/redis", "env": "REDIS_URL"},
    {"id": "azure_servicebus", "name": "Azure Service Bus", "enabled": false, "path": "/api/azure/servicebus", "env": "AZURE_SERVICEBUS_CONNECTION_STRING"},
    {"id": "azure_blob", "name": "Azure Blob Storage", "enabled": false, "path": "/api/azure/blob", "env": "AZURE_STORAGE_CONNECTION_STRING"}
  ]
}
```

### Config

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/config` | Returns active storage backend, app version, and connection flags. Never exposes secrets. |

Example response:
```json
{
  "app_version": "0.1.0",
  "storage_backend": "memory",
  "redis_connected": false,
  "azure_storage_configured": false,
  "azure_servicebus_configured": false,
  "azure_blob_configured": false
}
```

### Redis Key/Value (Workshop Utility)

These routes expose raw Redis operations for workshop exercises. They return `503` when `REDIS_URL` is not set.

| Method | Path | Body | Description |
|---|---|---|---|
| `GET` | `/api/redis/status` | — | Ping Redis and report connection status |
| `GET` | `/api/redis/keys` | — | List all keys |
| `GET` | `/api/redis/{key}` | — | Get value for a key (404 if missing) |
| `POST` | `/api/redis/keys` | `{"key": str, "value": str}` | Set a key/value pair |
| `DELETE` | `/api/redis/{key}` | — | Delete a key (404 if missing) |

### Azure Service Bus (Workshop Utility)

Vendor-specific managed services live under the cloud-named prefix `/api/azure/`. These
routes exercise an Azure Service Bus queue and return `503` when
`AZURE_SERVICEBUS_CONNECTION_STRING` is not set.

| Method | Path | Body | Description |
|---|---|---|---|
| `GET` | `/api/azure/servicebus/status` | — | Report connection status to the configured queue |
| `POST` | `/api/azure/servicebus/messages` | `{"body": str}` | Send a message to the queue (201) |
| `GET` | `/api/azure/servicebus/messages?max=10` | — | Consume up to `max` messages (receive-and-delete) — for testing |

### Azure Blob Storage (Workshop Utility)

These routes read/write blobs in a container of the Storage Account. They reuse
`AZURE_STORAGE_CONNECTION_STRING` and return `503` when it is not set. The container
(`AZURE_BLOB_CONTAINER`, default `workshop`) is created on first use.

| Method | Path | Body | Description |
|---|---|---|---|
| `GET` | `/api/azure/blob/status` | — | Report connection status to the Storage Account |
| `GET` | `/api/azure/blob/` | — | List blob names in the container |
| `PUT` | `/api/azure/blob/{name}` | `{"content": str}` | Write (overwrite) a blob |
| `GET` | `/api/azure/blob/{name}` | — | Read a blob's content (404 if missing) |

#### Error semantics (Azure routes)

| Status | When |
|---|---|
| `503` | Service not configured (its connection-string env var is unset) |
| `500` | Connection string is set but malformed |
| `502` | The Azure call itself failed (bad credentials, missing queue/container, network) — the upstream error message is returned in `detail` |
| `422` | Invalid request input (e.g. `max` outside `1..100` on the consume route) |
| `404` | Blob not found |

## Docker

```bash
docker build -t academy-api .
docker run -p 8080:8080 academy-api

# With Redis
docker run -p 8080:8080 -e REDIS_URL=redis://host.docker.internal:6379 academy-api
```
