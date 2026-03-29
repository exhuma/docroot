# Docroot

**Docroot** is a lightweight, self-hosted documentation host.
Upload versioned ZIP archives containing an `index.html` and
browse them through a web UI or REST API.

> **MVP Release** — the API, file layout, and configuration
> keys may change between releases without a compatibility
> guarantee.

## Quick install

```yaml
# docker-compose.yml
services:
  api:
    image: ghcr.io/exhuma/docroot/backend:latest
    environment:
      DOCROOT_API_DATA_ROOT: /data
      DOCROOT_API_OAUTH_JWKS_URL: "https://your-idp/jwks.json"
      DOCROOT_API_OAUTH_AUDIENCE: "docroot-api"
    volumes:
      - docroot_data:/data
  web:
    image: ghcr.io/exhuma/docroot/nginx:latest
    ports:
      - "80:80"
    environment:
      DOCROOT_WEB_OIDC_ISSUER: "https://your-idp"
      DOCROOT_WEB_OIDC_CLIENT_ID: "docroot-web"
    volumes:
      - docroot_data:/data
volumes:
  docroot_data:
```

```bash
docker compose up -d
```

Full documentation: <https://docroot.readthedocs.io/>

## Repository layout

| Path | Contents |
|---|---|
| `apps/frontend` | Vue + Vuetify single-page application |
| `apps/backend` | FastAPI backend |
| `apps/nginx` | nginx reverse-proxy / static-file server |
| `deploy/compose` | Docker Compose stacks |
| `docs/` | Sphinx documentation source |
| `contract.md` | Product and behaviour contract |
