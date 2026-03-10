# ADR-001 — nginx Static File Authorization

**Status:** Accepted  
**Date:** 2026-03-10

---

## Problem

nginx served documentation files from `/data` directly, without
consulting FastAPI.  Any user who could construct the correct URL
could read files from a private namespace, bypassing both JWT
validation and the `namespace.toml` ACL.

---

## Constraints

- OIDC (JWT + JWKS) must remain the authentication mechanism.
- Namespace ACL in `namespace.toml` must be enforced for reads.
- `public_read = true` namespaces must be accessible without a
  token.
- FastAPI must not stream large static files directly (contract
  §10).
- Multi-container, one-process-per-container model preserved
  (contract §14).

---

## Options Considered

- **A — nginx `auth_request`** ✅ *Chosen* — nginx sub-requests
  FastAPI before serving; FastAPI checks JWT + ACL.
- **B — X-Accel-Redirect** — all doc requests traverse FastAPI
  first; FastAPI delegates byte transfer to nginx internally.
  Viable but heavier than necessary for v1.
- **C — OpenResty / Lua** ❌ — JWT validation and TOML parsing
  replicated in Lua; duplicates security-critical logic.
- **D — FastAPI streaming** ❌ — FastAPI serves files directly;
  violates contract §10.
- **E — Signed URLs** — short-lived tokens exchanged and
  validated by nginx; over-engineered for a documentation host.

---

## Decision

**Option A — nginx `auth_request`.**

nginx sends a sub-request to `GET /_internal/auth` (FastAPI)
before serving any static file.  FastAPI reads the namespace
from `X-Original-URI`, checks the ACL, and returns 200, 401, or
403.  nginx forwards non-200 responses to the original client.

The `/_internal/auth` location is marked `internal` in nginx, so
external clients cannot call it directly.

---

## Implementation

### FastAPI — `apps/backend/src/app/routes/internal.py`

New route: `GET /_internal/auth`

- Reads `X-Original-URI` from the request headers.
- Parses the namespace from the first path segment.
- Reads the namespace ACL via the cached `AclCache`.
- Returns 200 (allowed), 401 (unauthenticated), 403
  (authenticated but forbidden), or 404 (no such namespace).

### nginx — `apps/nginx/conf.d/default.conf`

Added to the static documentation location:

```nginx
auth_request /_internal/auth;
auth_request_set $auth_status $upstream_status;
```

New internal proxy location:

```nginx
location = /_internal/auth {
    internal;
    proxy_pass http://api:8000;
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
    proxy_set_header X-Original-URI $request_uri;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

---

## namespace.toml — Retained As-Is

`namespace.toml` remains the single file for ACL and namespace
metadata.  Splitting into a separate ACL file would increase
complexity without benefit.  ACL enforcement lives exclusively
in FastAPI; nginx has no access to the TOML file.

---

## Consequences

- Every file request (including sub-resources) triggers a
  FastAPI sub-request.  Latency impact is mitigated by the
  in-memory ACL cache in FastAPI.
- The `/_internal/auth` endpoint has dedicated unit tests.
- nginx is still the right choice: the auth gap was the missing
  sub-request delegation, not a fundamental architectural
  problem.
- During development, nginx is optional; the new endpoint is
  exercised purely through the FastAPI test suite.
