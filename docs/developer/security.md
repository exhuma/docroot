# Security Guide

This project is a stateless OAuth2 resource server with ACL-controlled writes.

## Authentication

- Validate JWT signature against `OAUTH_JWKS_URL`.
- Validate token expiration and audience (`OAUTH_AUDIENCE`).
- Keep token validation centralized and identity-provider agnostic.
- Attach authenticated principal to request context after validation.
- Do not introduce session-based auth or server-side session state.

## Role Extraction and Authorization

- Use pluggable role extraction (`OAUTH_ROLE_EXTRACTOR`).
- Role extractor receives raw token value only after successful validation.
- Role extractor context must include issuer and audience.
- Namespace ACL in `namespace.toml` controls read/write authorization.
- `public_read=true` allows unauthenticated reads only.
- All writes require valid JWT and ACL write permission.

## Upload Security

- Accept ZIP uploads only when namespace/project authorization is valid.
- Reject traversal paths and symlink entries in ZIP archives.
- Require top-level `index.html` in archive content.
- Enforce extraction size and file-count limits.
- Ignore uploaded `metadata.toml`; generate metadata server-side.
- Keep extraction and final write on same filesystem for atomic rename.

## Filesystem and Immutability

- `/data` is the authoritative data store.
- Never allow overwriting existing version+locale artifacts.
- Perform all writes through storage abstraction.
- Ensure atomic creation and `latest` symlink updates.

## Resolution and Fallback Safety

- Use resolver for every version lookup, including `latest`.
- Locale fallback order is fixed and deterministic:
  requested locale, then `en`, then any existing locale, then `404`.
- If fallback occurs, UI should show a gentle notice.

## nginx and Exposure Controls

- nginx serves static documentation from `/data`.
- nginx enforces upload request limits and max body size.
- FastAPI should not stream large static files directly.

## Security Review Checklist

- Auth check runs before every write operation.
- ACL write check is present for all mutating endpoints.
- ZIP validation includes traversal and symlink rejection.
- Filesystem writes are atomic and immutable.
- Resolver is used for `latest` and locale handling everywhere.
