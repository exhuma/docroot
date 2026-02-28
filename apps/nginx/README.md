# nginx Service

nginx serves as reverse proxy and static file server.

Responsibilities:

- Static documentation served from `/data` under
  `/{namespace}/{project}/{version}/{locale}/`
- Upload endpoint rate limiting (5 requests/minute per IP)
- Max body size enforcement (512 MB)
- Reverse proxy to FastAPI API at `http://api:8000`
- Frontend SPA served with HTML5 history fallback

## Build

The Dockerfile uses a multi-stage build. Stage 1 builds the Vue
frontend. Stage 2 produces the final nginx image with the compiled
frontend and runtime configuration.

Build context is the `apps/` directory:

```
docker build -f nginx/Dockerfile -t docroot-nginx .
```
