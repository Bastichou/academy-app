# academy-cloud · frontend

Static HTML/JS application served by Nginx. No build step required.

## Pages

| Page | Route | Description |
|------|-------|-------------|
| `index.html` | `/` | Workshop home — architecture overview and covered services |
| `api.html` | `/api.html` | Pre-flight system check — health + config, links to modules |
| `messages.html` | `/messages.html` | Module 01 — Messages CRUD with storage backend info |
| `redis.html` | `/redis.html` | Module 02 — Redis key-value store operations |

## Navigation flow

```
index.html
  └── api.html (system check)
        ├── messages.html  (Module 01 — Messages)
        └── redis.html     (Module 02 — KV Store)
```

Each module page has a **chapter bar** with back/forward navigation, a **feature introduction**, a **requirements box** (env var `.env`-style snippets), collapsible **debug tips**, and the interactive CLI terminal.

## Architecture

```
Browser → Nginx (:80)
              ├── /          → static files  (apps/front/src/)
              └── /api/*     → proxy         → API container (:8080)
```

Nginx proxies all `/api/*` requests to the `api` service — no CORS, no hardcoded URLs.

## API routes covered

### System check (`api.html`)
- `GET /api/health` — liveness check
- `GET /api/config` — active storage backend, version, connection flags

### Module 01 — Messages (`messages.html`)
- `GET /api/messages` — list all messages
- `POST /api/messages` — create a message `{ text, author }`

### Module 02 — KV Store (`redis.html`) · _requires `REDIS_URL`_
- `GET /api/redis/status` — Redis connectivity (200 even when unconfigured)
- `GET /api/redis/keys` — list all keys
- `GET /api/redis/{key}` — read a single key (404 if missing)
- `POST /api/redis/keys` — set a key `{ key, value }`
- `DELETE /api/redis/{key}` — delete a key (204 on success)

## Shared styles

All pages load `style.css` which provides: nav, layout grid, terminal, log colors,
panels, form elements, buttons, method badges, feature cards, requirements boxes,
debug accordions, chapter bars, and module navigation cards.

Page-specific overrides live in each file's `<style>` block.
Module accent color is set per page via `--module-accent` CSS custom property.

## Local development

```bash
# Run the full stack (API + front)
cd infrastructure
docker compose up --build

# App is available at http://localhost:8000
```

## Docker image

Built and pushed to `ghcr.io/bastichou/academy-app/front:main` on every merge to `main`
via `.github/workflows/front.yml`.
