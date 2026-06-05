# Design: Add Redis to docker-compose

**Date:** 2026-06-05

## Goal

Always provision a Redis service in both `infrastructure/docker-compose.yml` (dev) and `infrastructure/docker-compose.prod.yml` (workshop/prod). The API must automatically use Redis as its storage backend via `REDIS_URL`.

## Scope

- `infrastructure/docker-compose.yml`
- `infrastructure/docker-compose.prod.yml`

No changes to application code or tests.

## Design

### New service: `redis`

Both compose files gain a `redis:7-alpine` service with a healthcheck:

```yaml
redis:
  image: redis:7-alpine
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 5s
    timeout: 3s
    retries: 5
```

No named volume — data is ephemeral and lost on `docker compose down`. This is intentional for the workshop context (clean slate each run).

### API wiring

`REDIS_URL=redis://redis:6379` is set on the `api` service in both files. `AZURE_STORAGE_CONNECTION_STRING` is removed — Redis takes priority in the backend selection logic, so leaving Azure would imply it does something when it doesn't.

The `api` service gains `depends_on: redis: condition: service_healthy` so the API only starts once Redis is accepting connections.

### Startup order

```
redis (healthy) → api (healthy) → front
```

### Build path fix (dev only)

The dev compose currently references `./app/api` and `./app/front` which do not exist. These are corrected to `../apps/api` and `../apps/front` (relative to `infrastructure/`).

## Decision log

- **Ephemeral over persistent**: named volume rejected — would confuse workshop students when stale data appears between sessions.
- **Azure removed**: Azure env var removed from compose files since Redis always takes priority; keeping it would suggest it has an effect.
- **Always-on over profile**: Redis is not behind a Docker Compose profile — every `docker compose up` starts Redis unconditionally.
