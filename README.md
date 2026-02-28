# Versioned Static Documentation Host

This project provides a filesystem-backed host for versioned documentation with namespace and project scoping, optional `latest` resolution, locale-aware documentation paths, ACL-based access control, and a Vue + Vuetify UI for browsing and uploads.

## What this repository contains

- Product and architecture contract: [contract.md](contract.md)
- Frontend application (Vue + Vuetify): [apps/frontend](apps/frontend)
- Backend scaffold (FastAPI placeholder): [apps/backend](apps/backend)
- nginx scaffold (static/reverse-proxy placeholder): [apps/nginx](apps/nginx)
- Deployment scaffold: [deploy/compose](deploy/compose)
- Developer-centric scaffolding and setup notes: [docs/README.md](docs/README.md)

## Quick start

- Install frontend dependencies: `npm run frontend:install`
- Run frontend dev server: `npm run dev`
- Run scaffold CI checks locally: `npm run ci`

## Status

The implementation scope and invariants are defined in [contract.md](contract.md). Use that file as the authoritative source for v1 behavior.
