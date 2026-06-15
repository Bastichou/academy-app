# academy-cloud · frontend

Static HTML/JS application served by Nginx. No build step required.

## Pages

| Page | Route | Description |
|------|-------|-------------|
| `index.html` | `/` | Landing — "Deploy a Cloud-Native Application" overview and covered services |
| `api.html` | `/api.html` | API explorer hub — thin-client explainer, endpoint config, system check, module table of contents |
| `api-testing/messages.html` | `/api-testing/messages.html` | Messages — list/post with storage backend info |
| `api-testing/redis.html` | `/api-testing/redis.html` | KV Store — Redis key-value operations |

The two interactive sub-pages live in `src/api-testing/` — deliberately **not** under
`/api/`, which is reverse-proxied to the backend. This keeps `nginx.conf` trivial (plain
`try_files`, no special rules) and avoids any route collision. All pages link with
**relative paths** (`../style.css`, `messages.html`, `../api.html`, …) so navigation works
both in the container and when served from any sub-path locally — no absolute path can 404.

## Navigation flow

```
index.html
  └── api.html (hub · system check + table of contents)
        ├── api-testing/messages.html  (Messages)
        └── api-testing/redis.html     (KV Store)
```

Every page under the API section shares a **sub-nav** (breadcrumb + segmented tabs) for
moving between siblings. Each sub-page follows the same four-section layout:

1. **What the page does** — feature card + an "expected result" callout
2. **Debug & configure** — live endpoint readout, collapsible debug tips, and an
   "API reference · coming soon" link
3. **Run API commands** — request panels with method badges
4. **Fake shell** — the interactive CLI terminal that prints API responses

## Architecture

```
Browser → Nginx (:80)
              ├── /          → static files  (apps/front/src/)
              └── /api/*     → proxy         → API container (:8080)
```

Nginx proxies all `/api/*` requests to the `api` service — no CORS, no hardcoded URLs.

## Configuring the API endpoint

The frontend stays static (no build step). All API calls go through the `apiUrl()`
helper, which prepends `window.API_BASE` (defined in `config.js`).

- **Default** — `API_BASE` empty → same-origin relative `/api/*`, proxied by Nginx.
  This is the current behavior and needs no configuration.
- **Override** — set the `API_BASE` env var on the container to call a backend
  directly (e.g. `API_BASE=https://api.example.com`). At startup,
  `docker-entrypoint.d/40-api-base.sh` regenerates `config.js` from it. The target
  API must then allow CORS, since requests bypass the Nginx proxy.

```bash
docker run -e API_BASE=https://api.example.com -p 8080:80 \
  ghcr.io/bastichou/academy-app/front:main
```

## API routes covered

### System check (`api.html`)
- `GET /api/health` — liveness check
- `GET /api/config` — active storage backend, version, connection flags

### Messages (`api-testing/messages.html`)
- `GET /api/messages` — list all messages
- `POST /api/messages` — create a message `{ text, author }`

### KV Store (`api-testing/redis.html`) · _requires `REDIS_URL`_
- `GET /api/redis/status` — Redis connectivity (200 even when unconfigured)
- `GET /api/redis/keys` — list all keys
- `GET /api/redis/{key}` — read a single key (404 if missing)
- `POST /api/redis/keys` — set a key `{ key, value }`
- `DELETE /api/redis/{key}` — delete a key (204 on success)

## Shared styles

All pages load `style.css` which provides: nav, layout grid, terminal, log colors,
panels, form elements, buttons, method badges, feature cards, endpoint readouts,
expected-result callouts, debug accordions, the API sub-nav (breadcrumb + tabs), and
module table-of-contents cards.

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
