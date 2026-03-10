# nginx Authorization — Problem Analysis and Options

## Context

The stack consists of:

- **FastAPI** — handles all API calls, JWT validation, and
  namespace ACL enforcement.
- **nginx** — reverse-proxies `/api/*` to FastAPI, serves the
  compiled Vue SPA, and serves documentation artefacts directly
  from `/data` under `/{namespace}/{project}/{version}/{locale}/`.
- **namespace.toml** — per-namespace TOML file that declares
  `public_read` and per-role `read`/`write` permissions.

---

## The Problem

nginx serves static documentation files directly from the
filesystem without consulting FastAPI. This means:

1. A namespace configured with `public_read = false` still has
   its content accessible to anyone who can construct the correct
   URL.
2. Role-based read restrictions declared in `namespace.toml` are
   not enforced for static file requests.
3. OIDC tokens are never validated for documentation downloads.

Any solution must satisfy the following non-negotiable
requirements:

- OIDC (JWT + JWKS) must remain the authentication mechanism.
- Namespace ACL from `namespace.toml` must be enforced for reads.
- `public_read = true` namespaces must stay accessible without
  a token.
- FastAPI must not stream large static files directly (contract
  §10).
- The multi-container, one-process-per-container model must be
  preserved (contract §14).

---

## Is nginx the Right Choice?

nginx is a sound choice for high-performance static file serving,
rate limiting, and reverse-proxying. The issue is not nginx
itself but the absence of an authorization step before nginx
serves files. The options below keep nginx in the stack while
adding the missing enforcement, or replace only the static-file
path with a FastAPI route that delegates the actual byte-transfer
back to nginx.

---

## Is namespace.toml a Good ACL Strategy?

`namespace.toml` keeps ACL co-located with the namespace data
under `/data/namespaces/<ns>/namespace.toml`. This has several
advantages:

- Single source of truth for all namespace metadata and access
  policy.
- No external database required (preserves the filesystem-only
  invariant).
- Human-readable and editable without tooling.
- Already cached and invalidated on mtime change in FastAPI.

The limitation is that nginx cannot parse TOML natively. Any
solution must either pass ACL enforcement to FastAPI (one way or
another) or replicate the logic in nginx/Lua — the latter being
undesirable because it duplicates logic and creates a maintenance
burden.

**Recommendation:** keep `namespace.toml` as the single ACL and
metadata file. Enforcement must live in FastAPI.

---

## Option A — nginx `auth_request`

### How it works

nginx's `auth_request` directive sends a sub-request to a
FastAPI endpoint before serving each file. If FastAPI returns
2xx the file is served; 401/403 is forwarded to the client.

```
location ~ ^/([^/]+)/([^/]+)/([^/]+)/([^/]+)(/.*)?$ {
    auth_request /_internal/auth;
    auth_request_set $auth_status $upstream_status;
    alias /data/namespaces/$1/projects/$2/versions/$3/$4$5;
    index index.html;
}

location = /_internal/auth {
    internal;
    proxy_pass http://api:8000;
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
    proxy_set_header X-Original-URI $request_uri;
}
```

FastAPI receives the `X-Original-URI` header, extracts the
namespace from the path, reads its `namespace.toml`, and
evaluates:

- If `public_read = true` → return 200 immediately.
- If a valid JWT is present and the token's roles satisfy the
  ACL → return 200.
- Otherwise → return 401 or 403.

### Pros

- Authorization logic stays entirely in FastAPI (single source
  of truth, no duplication).
- nginx still serves bytes directly from the filesystem
  (performance preserved).
- `namespace.toml` structure is unchanged.
- OIDC flow is unchanged.
- Relatively simple nginx configuration change.

### Cons

- Every file request (including sub-resources such as CSS and
  JS inside an iframe) triggers an HTTP sub-request to FastAPI.
  This adds latency proportional to the number of assets per
  page view.
- The auth endpoint must be fast (no I/O beyond the cached ACL
  and JWT signature check).
- nginx and FastAPI must be on the same Docker network (they
  already are in the compose stack).

### Assessment

This is the lowest-complexity solution that fully enforces ACL
at the nginx layer without duplicating auth logic. The latency
cost is acceptable for a documentation host where page-load
frequency is low compared to, for example, a high-traffic API.
Per-namespace ACL caching in FastAPI mitigates repeated TOML
reads.

---

## Option B — X-Accel-Redirect (FastAPI controls, nginx sends)

### How it works

All requests for documentation artefacts go to FastAPI first.
FastAPI validates the token and ACL, then returns an empty
response with the `X-Accel-Redirect` header pointing to an
internal nginx location mapped to `/data`.

```python
# FastAPI handler (sketch — no code change made here)
headers = {"X-Accel-Redirect": f"/internal-data/{path}"}
return Response(status_code=200, headers=headers)
```

```
location /internal-data/ {
    internal;
    alias /data/;
}
```

### Pros

- FastAPI fully controls auth before any byte is sent.
- nginx handles efficient file I/O.
- No sub-request overhead; request flow is: client → FastAPI
  → nginx internal redirect.

### Cons

- Every documentation request first traverses FastAPI.
  With many concurrent users this increases load on FastAPI.
- Requires adding a download endpoint to FastAPI for each
  documentation path, or a catch-all route.
- The internal nginx alias exposes the entire `/data` tree to
  FastAPI redirection; careful path validation is required to
  avoid traversal.
- More code to add and maintain compared to Option A.

### Assessment

Suitable when fine-grained per-file access control is needed
in the future (e.g., file-level ACL, audit logging). For v1
it is heavier than necessary. The traversal risk on the
internal alias requires careful validation.

---

## Option C — OpenResty / Lua JWT Validation in nginx

### How it works

Replace the standard nginx image with
[OpenResty](https://openresty.org/) and add a Lua script that:

1. Reads the `Authorization` header.
2. Validates the JWT signature using a cached JWKS.
3. Reads `namespace.toml` from disk.
4. Enforces the ACL rule before serving the file.

### Pros

- No additional HTTP round-trip per request.
- FastAPI is not involved in reads at all.

### Cons

- Lua code must replicate JWT validation and TOML parsing;
  this duplicates complex security-critical logic.
- OpenResty is a different image from standard nginx; the
  Dockerfile and image supply chain change.
- Testing Lua ACL logic requires a separate test harness.
- Maintenance burden is high: two codebases must stay in sync
  whenever ACL semantics change.
- TOML libraries for Lua are not part of the standard OpenResty
  distribution.

### Assessment

Disproportionate complexity for the security gain. Not
recommended.

---

## Option D — Move Static Serving to FastAPI

### How it works

Remove the nginx static-file location block. All documentation
requests are handled by FastAPI using `FileResponse` or
`StreamingResponse`.

### Pros

- Auth is native and straightforward.
- No nginx configuration changes needed.

### Cons

- Directly violates contract §10: "FastAPI must not serve large
  static files directly."
- Loses nginx-level rate limiting, caching headers, and
  zero-copy sendfile optimisation.
- Not viable without a contract amendment.

### Assessment

Ruled out by the contract.

---

## Option E — Signed URL Tokens (Pre-authorisation)

### How it works

When the frontend loads the documentation iframe, it first calls
a FastAPI endpoint to exchange the OIDC token for a short-lived
signed URL or cookie. nginx validates the signature (e.g., via
the `ngx_http_secure_link_module`) before serving the file.

### Pros

- After the initial exchange, nginx serves files with no
  FastAPI sub-request.
- Suitable for high-throughput download scenarios.

### Cons

- Complex implementation: token generation, signature scheme,
  expiry handling.
- Signed URLs are valid for a window of time; a leaked URL
  grants temporary access.
- Does not map naturally to browser-based iframe navigation
  where sub-resources (CSS, JS, images) need the same token.
- `ngx_http_secure_link_module` signs URLs, not JWT; a
  separate signing key must be managed.

### Assessment

Over-engineered for a documentation host. Better suited to
media-streaming or download services.

---

## Recommendation

**Implement Option A (`auth_request`).**

It is the most pragmatic solution: authorization logic stays
entirely in FastAPI (no duplication), nginx continues to serve
files efficiently, `namespace.toml` is unchanged, and the OIDC
flow is unmodified. The implementation requires:

1. A new lightweight FastAPI endpoint (e.g.
   `GET /_internal/auth`) that:
   - Accepts `X-Original-URI` from nginx.
   - Parses the namespace from the path.
   - Reads and caches the namespace ACL.
   - Returns 200, 401, or 403.

2. Two changes to `apps/nginx/conf.d/default.conf`:
   - Add `auth_request /_internal/auth;` to the static
     location block.
   - Add the `/_internal/auth` internal proxy location.

3. The existing JWT validation and ACL caching logic in
   FastAPI can be reused with minimal additions.

### namespace.toml — Retain As-Is

The `namespace.toml` format is already well-suited for
combined metadata and ACL. Splitting the file would increase
complexity without clear benefit. Retain the single-file
approach. If additional metadata fields are needed in the
future they can be added to the same file under new TOML
table headings.

---

## Impact on Development Workflow

`auth_request` only applies to the nginx layer, which is
optional during development (see
[Running Locally](running-locally.md)). Developers working
only with the FastAPI backend and Vite frontend are unaffected.
The auth endpoint must be covered by unit tests as part of the
backend test suite.
