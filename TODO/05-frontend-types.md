# refactor(frontend): move API boundary types to src/types/

**Source kit:** `stack-fastapi-vuetify`

## Context

The kit requires all TypeScript interfaces that cross the API
boundary to live under `apps/frontend/src/types/`, not inline
in other modules.

## Current state

All eight API interfaces are declared inline at the top of
`apps/frontend/src/api.ts` (lines 3–44):

- `Namespace`, `Project`
- `VersionInfo`, `ResolveResult`
- `OidcConfig`, `Me`
- `AclRole`, `AclData`

The `src/types/` directory does not exist.

## Acceptance criteria

- [ ] `apps/frontend/src/types/` directory created
- [ ] Interfaces extracted from `api.ts` into modules:
      - `src/types/namespaces.ts` → `Namespace`
      - `src/types/projects.ts` → `Project`
      - `src/types/versions.ts` → `VersionInfo`,
        `ResolveResult`
      - `src/types/auth.ts` → `OidcConfig`, `Me`
      - `src/types/acl.ts` → `AclRole`, `AclData`
- [ ] `api.ts` imports types from `src/types/`
- [ ] All `.vue` / `.ts` files that import types from
      `api.ts` are updated to import from `src/types/`
- [ ] `contract.md` records that types are manually
      maintained (not generated from OpenAPI)

## Notes

- Pure mechanical refactor — no runtime behaviour changes.
- Best done in the same PR as issue #4 (ApiError /
  TokenProvider) to avoid two rounds of call-site edits.

## Files to change

- `apps/frontend/src/api.ts`
- `apps/frontend/src/types/*.ts` *(new)*
- All `.vue` and `.ts` files importing types from `api.ts`
