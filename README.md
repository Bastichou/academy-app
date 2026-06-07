# Academy App

A full-stack demo application used during workshops on Kubernetes, Cloud Infrastructure, and Terraform. Students deploy and operate this app as a hands-on exercise.

## Architecture

```
Browser
  └── Front (Nginx :80)
        ├── Static HTML/JS
        └── /api/* → API (FastAPI :8080)
                        └── Storage
                              ├── In-Memory (default, local dev)
                              └── Azure Table Storage (prod, via env var)
```

## Services

| Service | Path | Port | Description |
|---------|------|------|-------------|
| `api` | `app/api/` | 8080 | Python FastAPI backend |
| `front` | `app/front/` | 80 | Nginx serving static HTML + reverse proxy |

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check — returns `{"status":"ok"}` |
| `GET` | `/api/messages` | List all messages |
| `POST` | `/api/messages` | Create a message `{"text": "...", "author": "..."}` |

## Quick Start (local dev)

Requires: Docker + Docker Compose

```bash
git clone https://github.com/Bastichou/academy-app.git
cd academy-app
docker compose up --build
```

App is available at <http://localhost:8000>.

## Workshop Usage (pre-built images)

Students pull images published by CI — no build step needed.

```bash
docker compose -f docker-compose.prod.yml up
```

App is available at <http://localhost:8000>.

To pull images individually:

```bash
docker pull ghcr.io/bastichou/academy-app/api:latest
docker pull ghcr.io/bastichou/academy-app/front:latest
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_STORAGE_CONNECTION_STRING` | No | Switches the API from in-memory to Azure Table Storage |

Without this variable the API stores messages in memory (data is lost on restart). Set it to persist data in an Azure Storage Account.

## CI/CD

GitHub Actions builds and publishes Docker images to the GitHub Container Registry (`ghcr.io`) on every push to `main` and on version tags (`v*`).

Images are tagged with:
- `main` (latest build from the main branch)
- `vX.Y.Z` (semantic version, when a tag is pushed)
- Short git SHA (for precise traceability)

See [`.github/workflows/docker-publish.yml`](.github/workflows/docker-publish.yml).

