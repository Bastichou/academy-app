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
| `AZURE_STORAGE_CONNECTION_STRING` | No | Switches the API from in-memory to Azure Table Storage; also enables the Blob Storage routes |
| `AZURE_SERVICEBUS_CONNECTION_STRING` | No | Enables the Azure Service Bus routes (`/api/azure/servicebus/*`) |
| `AZURE_SERVICEBUS_QUEUE` | No | Queue name for the Service Bus routes (default `workshop`) |
| `AZURE_BLOB_CONTAINER` | No | Container name for the Blob routes (default `workshop`) |

Without `AZURE_STORAGE_CONNECTION_STRING` the API stores messages in memory (data is lost on restart). Set it to persist data in an Azure Storage Account. The Azure Service Bus and Blob Storage routes are workshop utilities and return `503` until their connection string is configured. See [apps/api/README.md](apps/api/README.md) for the full route list.

## CI/CD

GitHub Actions builds and publishes Docker images to the GitHub Container Registry (`ghcr.io`).

| Workflow | Trigger | Path filter |
|----------|---------|-------------|
| [api.yml](.github/workflows/api.yml) | push / PR to `main`, manual | `apps/api/**` |
| [front.yml](.github/workflows/front.yml) | push / PR to `main`, manual | `apps/front/**` |

Each workflow runs tests and lint, then builds and pushes the image (push to `main` only).

Images are tagged with:
- `main` — latest build from the main branch
- Short git SHA — for precise traceability

### Manual trigger

**GitHub UI:** Actions → select workflow → "Run workflow".

**GitHub CLI:**
```bash
gh workflow run api.yml --ref main
gh workflow run front.yml --ref main
```

> The path filter means a push that only touches workflow files or the README will **not** trigger a run automatically — use the manual trigger in that case.

