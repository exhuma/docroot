# Implementation Contract — Versioned Static Documentation Host (v1)

This contract defines scope, structure, invariants, and acceptance criteria for
an autonomous coding agent.

---

# 1. Scope of v1

## Included

* Namespace management (single-level only)
* Project management
* Version + locale upload (ZIP with `index.html` at root)
* Optional `latest`
* Per-version locale variants (`en` base locale in v1)
* Static hosting under `/namespace/project/version/locale/`
* `latest` symlink support
* Filesystem-backed storage only
* OAuth2 JWT validation (resource server behavior)
* TOML-based namespace ACL
* Hardlink-based per-project deduplication
* nginx static serving + rate limiting
* VueJS + Vuetify UI for browsing and upload
* Multi-image deployment stack (one process per container)
* Single mounted volume `/data`

## Explicitly Excluded (must not be implemented)

* Semver parsing or sorting
* Automatic latest detection
* Full-text search
* S3 backend
* CAS storage
* Quota enforcement
* Audit logging
* Cryptographic immutability enforcement

Architecture must not prevent these later.

---

# 2. System Architecture

## Runtime Model

Multiple containers (or equivalent stack deployment), with exactly one long-running
process per container.

Minimum service split:

* FastAPI (uvicorn)
* nginx (reverse proxy + static serving)

Shared directory:

```
/data
```

No database.
No background workers.
No external dependencies except OAuth JWKS endpoint.

---

# 3. Filesystem Specification (Authoritative Data Model)

Root:

```
/data/namespaces/<namespace>/projects/<project>/versions/<version>/<locale>/
```

Each locale directory under a version:

* MUST contain `index.html`
* MAY contain arbitrary files
* MUST contain system-generated `metadata.toml`

Project directory:

```
/data/namespaces/<namespace>/projects/<project>/
  project.toml
  versions/
  latest -> <version> (symlink if exists)
```

`project.toml` fields:

```
display_name = "<human-readable project name>"
```

Version directory:

```
/data/namespaces/<namespace>/projects/<project>/versions/<version>/
  en/
  fr/
  de/
  ...
```

Namespace directory:

```
/data/namespaces/<namespace>/
  namespace.toml
  projects/
```

`namespace.toml` top-level fields include:

```
creator = "<subject>"
creator_display_name = "<display name>"
display_name = "<human-readable namespace name>"
versioning = "<scheme>"
```

---

# 4. Naming Rules

Namespace and project names accept free-form UTF-8 text (the
*display name*).  The server derives a URL-safe *slug* from the
display name by:

1. Applying NFKD Unicode normalisation and stripping combining marks.
2. Lowercasing.
3. Replacing any run of characters outside `[a-z0-9_]` with a
   single hyphen.
4. Stripping leading and trailing hyphens.

The slug is used as the filesystem directory name and URL path
segment.  The display name is stored in the respective TOML file.
A 400 error is returned when no alphanumeric characters remain after
slugification.

Display name constraints:

```
min_length = 1
max_length = 200
```

Version:

```
[a-zA-Z0-9._-]+
```

Locale:

```
[a-z]{2}
```

Locale is mandatory for uploads and resolution. In v1, `en` is the base locale and primary fallback locale.

Reject invalid input with 400.

No nesting in namespaces.

---

# 5. Storage Abstraction Layer (Mandatory)

All filesystem operations MUST go through a storage service interface.

Required interface methods:

* `create_namespace(name)`

* `delete_namespace(name)`

* `list_namespaces()`

* `create_project(namespace, project)`

* `delete_project(namespace, project)`

* `list_projects(namespace)`

* `create_version(namespace, project, version, locale, source_dir, latest, uploader_subject, upload_timestamp)`

* `delete_version(namespace, project, version, locale)`

* `list_versions(namespace, project)`

* `list_locales(namespace, project, version)`

* `set_latest(namespace, project, version)`

* `resolve_version(namespace, project, version_or_alias, locale)`

API handlers MUST NOT perform direct filesystem operations.

---

# 6. Upload Contract

Endpoint:

```
POST /api/{namespace}/{project}/upload
```

Multipart form:

* `file`: zip archive
* `version`: string
* `locale`: 2-letter lowercase string (required)
* `latest`: boolean (optional, default false)
* `uploader_subject`: string (optional)
* `upload_timestamp`: string (optional; RFC3339 recommended)

Validation:

* Namespace exists
* Project exists
* Locale is valid per naming rules
* Version+locale does not already exist
* Write permission granted
* ZIP contains top-level `index.html`
* No path traversal entries
* Max extracted size enforcement
* Max file count enforcement

Upload archive requirements:

* Archive must be system-agnostic documentation content.
* `metadata.toml` in the archive, if present, MUST NOT be trusted as API metadata input.
* Metadata values are supplied via POST form fields (or derived by server defaults), then written by the server.

Extraction process:

1. Extract to temp dir inside same filesystem.
2. If previous version exists for the same locale:

   * Hardlink clone previous version into temp target.
   * Rsync extracted content over it.
3. Else:

   * Copy extracted files directly.
4. Generate internal `metadata.toml` from POST metadata fields and server defaults.
5. Atomic rename into final locale directory for the target version.
6. If `latest=true`, atomically update symlink.

At no point may partial versions become visible.

---

# 7. Version Resolution Rules

`resolve_version(namespace, project, version_or_alias, locale)`:

* If `version_or_alias == "latest"`:

  * Resolve symlink target.
  * 404 if missing.
* Else:

  * Must match existing directory.

Locale resolution for the resolved version:

1. Try requested locale.
2. If missing, try `en`.
3. If missing, pick any existing locale for that version (deterministic order).
4. If none exists, return 404.

This function MUST be used everywhere.

---

# 8. ACL Specification

Each namespace MUST contain:

```
namespace.toml
```

Structure:

```
[access]
public_read = true|false

[[access.roles]]
role = "<role>"
read = true|false
write = true|false
```

Rules:

* If `public_read=true`, no token required for read.
* Write always requires valid JWT.
* If role matches and write=true → upload allowed.
* Role matching is exact string match.

ACL must be:

* Parsed on demand
* Cached in memory
* Invalidated on file mtime change

No in-memory mutation allowed.

---

# 9. OAuth Resource Server Behavior

Environment variables:

```
OAUTH_JWKS_URL
OAUTH_AUDIENCE
OAUTH_ROLE_EXTRACTOR
```

Requirements:

* Validate JWT signature via JWKS
* Validate expiration
* Validate audience
* Keep token validation centralized and IDP-agnostic
* Extract roles via pluggable role-extractor
* Role extractor configuration is extractor-specific; claim paths are owned by the extractor
* Call role extractor with the raw token value after validation
* Call role extractor with authentication context sufficient for opaque-token introspection
* Authentication context MUST include issuer and audience, and MAY include introspection endpoint and client credentials depending on extractor needs
* v1 MUST include keycloak-compatible role extraction
* Architecture MUST allow additional extractors for github, gitlab, and azure IDPs later
* Attach authenticated principal to request context

No session storage.
Stateless only.

A stateless browser cookie carrying a JWT for nginx auth bridging is
permitted. This does not constitute server-side session storage.

---

# 10. Static Hosting Rules

Public route:

```
/{namespace}/{project}/{version}/{locale}/
```

nginx responsibilities:

* Serve static files from `/data` after authorization is
  confirmed via `auth_request`.
* Delegate every static-file request to `GET /api/auth`
  (FastAPI) before serving.  Access is denied if FastAPI
  returns 401 or 403.
* Rate limit upload endpoints.
* Enforce max body size.
* Optional sub_filter rewriting (feature toggle via config).

FastAPI responsibilities:

* Expose `GET /api/auth` as the nginx `auth_request` gate.
* Extract the namespace from the ``X-Original-URI`` header
  and evaluate the namespace ACL.
* Return 200 (allow), 401 (unauthenticated), or 403
  (forbidden).

FastAPI must not serve large static files directly.

---

# 11. UI Requirements (Vue + Vuetify)

Views:

1. Namespace list
2. Project list
3. Version list
4. Upload dialog
5. Documentation iframe view

Behavior:

* Version selector dropdown
* Locale selector in the documentation overlay, scoped to selected version
* Latest clearly labeled
* Upload button visible only if write permission
* Upload requires explicit locale (2-letter standard)
* Docs rendered in iframe pointing to locale-aware static path
* If selected locale is missing, UI must gently inform the user and apply fallback order: requested locale -> `en` -> any available locale -> 404
* If fallback occurs, UI must indicate which locale is currently shown

UI internationalization:

* UI chrome can be translated into English, French, and German
* Documentation locale selection is independent from UI language

UI must rely entirely on REST API.
No filesystem assumptions.

### OIDC UI Mode

When OIDC login is enabled:

* The browser UI acts as a separate OIDC public client.
* The UI uses Authorization Code + PKCE.
* The API remains a stateless JWT resource server.
* Any cookie used for docs access is a stateless browser-to-nginx
  bridge and not server-side session storage.

---

# 12. Security Requirements

Mandatory protections:

* Path normalization for all inputs
* Reject traversal attempts
* Reject overwriting existing version+locale artifacts
* Reject invalid ZIP structure
* Reject symlink entries in ZIP
* Extraction must not follow symlinks
* No executable code execution
* Atomic directory renames only

---

# 13. Concurrency Guarantees

Must handle:

* Concurrent uploads to different projects
* Concurrent uploads to same project (different versions and/or locales)

Must prevent:

* Two uploads creating same version+locale artifact

Implementation may use:

* File locks
* Atomic directory creation semantics

No global locks allowed.

---

# 14. Docker Requirements

Multiple Docker images and containers (stack deployment) are required when more
than one process is needed.

Must:

* Provide at least one image per long-running service process
* Keep FastAPI and nginx in separate containers
* Expose nginx on port 80
* Share one external volume: `/data`

All containers must support starting with empty `/data`.

---

# 15. Metadata Stub (Extension Compatibility)

Each version+locale artifact MUST include:

```
metadata.toml
```

Fields:

```
upload_timestamp
uploader_subject
latest
locale
```

Nothing else required in v1.

Future features must rely on this file.

---

# 16. Acceptance Criteria

System is complete when:

* Namespaces can be created and deleted.
* Projects can be created and deleted.
* ZIP upload works.
* Version+locale artifacts are immutable.
* Latest symlink works.
* Static hosting works under prefixed locale-aware route.
* ACL enforcement works for both API and static file routes.
* Static documentation requests are gated by nginx
  ``auth_request`` delegating to ``GET /api/auth``.
* Public namespaces work without JWT.
* Locale-aware resolution and fallback work
  (requested -> `en` -> any -> 404).
* Missing locale is shown gently in UI when fallback is used.
* Invalid uploads are rejected safely.
* System runs as a multi-container stack with one process per
  container.
* Restart does not lose data.
* Multiple versions share files via hardlinks (verified by
  inode).

---

# 17. Non-Functional Requirements

* No blocking CPU-heavy work on main event loop.
* Extraction may use threadpool.
* Codebase must have clear service boundaries.
* No direct filesystem calls outside storage layer.
* No ORM.
* No database driver installed.

---

# 18. Architectural Invariants (Must Never Be Violated)

* Filesystem is the source of truth.
* API layer does not depend on directory layout.
* Version resolution always passes through resolver.
* All writes are atomic.
* Version+locale artifacts are immutable.
* Storage backend replaceable in future.
* Role extraction is pluggable and independent from token validation.

