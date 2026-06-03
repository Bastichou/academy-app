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
| `AZURE_STORAGE_CONNECTION_STRING` | No | `""` | Azure Table Storage connection string. Enables Azure storage. |

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
  "azure_storage_configured": false
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

## Docker

```bash
docker build -t academy-api .
docker run -p 8080:8080 academy-api

# With Redis
docker run -p 8080:8080 -e REDIS_URL=redis://host.docker.internal:6379 academy-api
```
