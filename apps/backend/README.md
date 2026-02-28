# Backend (FastAPI)

FastAPI service exposing the REST API for the documentation host.

## Structure

```
app/
  main.py            — FastAPI app, CORS middleware, router registration
  models.py          — Pydantic response models
  storage.py         — Filesystem storage abstraction (all FS ops)
  resolver.py        — Version/locale resolver
  acl.py             — TOML-based ACL with mtime-invalidated cache
  auth.py            — Stateless OAuth2 JWT validation via JWKS
  keycloak_extractor.py — Keycloak role extraction from realm_access
  validators.py      — Name format validators (400 on invalid input)
  zipvalidator.py    — ZIP upload security validation
  routes/
    namespaces.py    — Namespace CRUD endpoints
    projects.py      — Project CRUD endpoints
    versions.py      — Version upload, listing, resolve, set-latest
```

## Environment Variables

| Variable | Description |
|---|---|
| `DATA_ROOT` | Filesystem root (default `/data`) |
| `OAUTH_JWKS_URL` | JWKS endpoint for JWT validation |
| `OAUTH_AUDIENCE` | Expected token audience |
| `OAUTH_ROLE_EXTRACTOR` | Role extractor: `keycloak` (default) |
| `CORS_ORIGINS` | Comma-separated allowed origins (default `*`) |

## Running Tests

```bash
pip install -e ".[dev]"
pytest
```
