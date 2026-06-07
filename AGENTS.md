# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

Teaching demo app used in Kubernetes/Cloud Infrastructure/Terraform workshops. Students deploy and operate it as a hands-on exercise.

**Monorepo layout:**
```
apps/api/        # Python FastAPI backend
apps/front/      # Static HTML/JS + Nginx
infrastructure/  # docker-compose files
.agents/skills/  # Project-specific Claude skills (symlinked into .claude/skills/)
```

## API — `apps/api/`

**Note:** `CLAUDE.md` is a symlink to `AGENTS.md` — edit `AGENTS.md` directly.

**Package manager:** `uv` (not pip). All commands run via `uv run`.

```bash
# Install dependencies
cd apps/api && uv sync

# Install with test/lint tools (dev extras are NOT included by plain uv sync)
cd apps/api && uv sync --extra dev

# Run dev server (port 8080)
uv run fastapi dev src/main.py --host 0.0.0.0 --port 8080

# Run tests
uv run pytest

# Lint
uv run ruff check .

# Run a single test
uv run pytest tests/test_messages.py::test_create_message -v
```

**Architecture — storage backends:**

`deps.py` selects the storage backend at first call (singleton). Priority: Redis > Azure > Memory.
- Default: `InMemoryStorage` (ephemeral, no setup needed)
- With `REDIS_URL` env var: `RedisStorage` (async, via `redis[asyncio]`)
- With `AZURE_STORAGE_CONNECTION_STRING` env var: `AzureTableStorage`

All implement the abstract `MessageStorage` interface in `storage/base.py`. Configuration centralised in `src/config.py` (pydantic-settings).

**Routes:** All prefixed `/api/`
- `GET /api/health` → `{"status": "ok", "service": "academy-api"}`
- `GET /api/messages` → list
- `POST /api/messages` → `{"text": str, "author": str}` (author defaults to `"Anonyme"`)
- `GET /api/config` → safe config values (storage backend, version, connection flags — no secrets)
- `GET /api/redis/status|keys|{key}`, `POST /api/redis/keys`, `DELETE /api/redis/{key}` → Redis KV workshop utility (503 when `REDIS_URL` unset)

**Testing:**
- `asyncio_mode = "auto"` in pyproject.toml — no `@pytest.mark.asyncio` needed
- Patch FastAPI async generator deps via `app.dependency_overrides[fn] = fake_gen`, not `mock.patch`
- `httpx2` deprecation warning in test output is from FastAPI's testclient — not project code

## Frontend — `apps/front/`

Pure HTML/JS, no build step. Nginx serves static files and reverse-proxies `/api/*` to `api:8080`.

## Local Development

```bash
# Build and run both services
cd infrastructure
docker compose up --build

# App is at http://localhost:8000
```

## Workshop / Students

```bash
cd infrastructure
docker compose -f docker-compose.prod.yml up
```

Pulls pre-built images from `ghcr.io/bastichou/academy-app/{api,front}:main`.

## CI/CD

Two dedicated workflows push Docker images to `ghcr.io`. Both use `GITHUB_TOKEN` — no extra secrets needed.
- `.github/workflows/api.yml` — triggers on `apps/api/**`; runs test → lint (ruff) → build/push
- `.github/workflows/front.yml` — triggers on `apps/front/**`; runs build/push

Images are built on every event (including PRs) but only pushed on merge to `main`.
