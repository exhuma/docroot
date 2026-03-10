# Running the Stack Locally

This guide explains how to run the project for development. The
stack has three components: a FastAPI backend, a VueJS frontend,
and an nginx reverse-proxy / static-file server.

During everyday development only the backend and frontend need to
be running. nginx is required only for end-to-end integration
testing of static file serving and the full production routing.

---

## Prerequisites

- **Python 3.12+** with [uv](https://docs.astral.sh/uv/) installed.
- **Node.js 22+** with npm.
- **Docker + Docker Compose** — only needed for the full nginx
  stack.
- **Task** ([taskfile.dev](https://taskfile.dev)) — task runner
  used throughout this repo.

---

## Quick-start (backend + frontend only)

This is the recommended loop for day-to-day feature work.

### 1. Create the dev environment file

```
task setup:dev
```

This copies `deploy/dev/.env.example` to `deploy/dev/.env`.
Edit the file if you need to adjust any values. The defaults
work out of the box for local dev.

### 2. Install dependencies

```
task install
```

### 3. Start the servers in parallel

```
task dev
```

This runs `dev:api` and `dev:frontend` concurrently:

| Service  | URL                       |
|----------|---------------------------|
| Backend  | http://localhost:8000     |
| Frontend | http://localhost:3000     |

The frontend Vite dev-server proxies `/api/*` to
`http://localhost:8000`, so you do not need nginx for API
requests during development.

### 4. Obtain a development JWT

```
task gen-token
```

Custom subject and roles:

```
task gen-token -- --sub alice --roles editor,viewer
```

Pass the token as a `Bearer` value in the `Authorization` header
for any write operations.

---

## Running servers individually

```
task dev:api       # FastAPI + uvicorn (hot-reload)
task dev:frontend  # Vite dev server (HMR)
```

---

## Full stack with nginx (integration testing)

Use this only when you need to verify static file routing, rate
limiting, or the nginx reverse-proxy behaviour.

```
cd deploy/compose
cp .env.example .env   # adjust OAUTH_* variables
docker compose up --build
```

The stack exposes:

| Service  | URL                   |
|----------|-----------------------|
| nginx    | http://localhost:80   |

nginx serves the compiled frontend SPA, proxies `/api/*` to the
FastAPI container, and serves documentation artefacts from
`/data` under `/{namespace}/{project}/{version}/{locale}/`.

> **Note:** `deploy/compose/.env` requires real (or test) OIDC
> credentials. The `file://` JWKS shortcut used in `deploy/dev`
> is not available inside Docker containers by default unless you
> volume-mount the JWKS file.

---

## Environment variables reference

All variables use the `DOCROOT_` prefix. See
`apps/backend/src/app/settings.py` for the authoritative list.

| Variable                     | Dev default             |
|------------------------------|-------------------------|
| `DOCROOT_DATA_ROOT`          | `./deploy/dev/data`     |
| `DOCROOT_OAUTH_JWKS_URL`     | `file://./deploy/dev/jwks.json` |
| `DOCROOT_OAUTH_AUDIENCE`     | `docroot-dev`           |
| `DOCROOT_OAUTH_ROLE_EXTRACTOR` | `keycloak`            |
| `DOCROOT_CORS_ORIGINS`       | `http://localhost:3000` |

---

## Running the tests

```
task test:backend   # pytest
task lint           # ESLint
task type-check     # TypeScript tsc
task ci             # full pipeline
```
