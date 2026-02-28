# AI Assistant Rules

Before generating or modifying files:
- Read `docs/developer/code-style.md`.
- Read `docs/developer/invariants.md`.
- Ensure generated content respects line-length limits.

This file defines enforceable rules for coding agents in this repository.
Correctness and security take priority over convenience.

## Start Here

- `docs/developer/invariants.md` — mandatory rules.
- `docs/developer/architecture.md` — boundaries and ownership.
- `docs/developer/security.md` — authn/authz/upload/storage safeguards.
- `docs/developer/code-style.md` — style and formatting requirements.
- `contract.md` — product and behavior contract.

## Non-Negotiable

- Do not edit `contract.md` unless explicitly asked.
- Keep implementation aligned with `contract.md`.
- Respect service split: FastAPI API service and nginx static/reverse-proxy
  service in separate containers.
- Keep filesystem as source of truth under `/data`.
- Do not add databases, ORMs, or background workers.
- Do not implement features excluded by the contract.

## Layering Rules

- API handlers own HTTP concerns only.
- Business logic and filesystem mutations belong to the backend service layer.
- API handlers must not perform direct filesystem operations.
- All filesystem operations must go through the storage abstraction.
- Version resolution must always go through the resolver.

## Security Rules

- Never bypass authentication or authorization checks.
- Write operations require valid JWT plus namespace ACL write permission.
- Preserve stateless auth; no session state.
- Validate upload ZIPs defensively:
  - no traversal entries,
  - no symlink entries,
  - enforce size and file-count limits,
  - require top-level `index.html`.
- Ensure writes are atomic and immutable once created.

## Agent Behavior

- Prefer minimal, focused changes.
- Update documentation when behavior or architecture changes.
- Add tests for security-sensitive logic when implementation exists.
- Do not introduce project-specific assumptions not present in `contract.md`.
