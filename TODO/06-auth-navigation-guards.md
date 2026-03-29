# feat(frontend): add navigation guards for write-protected routes

**Source kit:** `module-auth-oidc`

## Context

`apps/frontend/src/router/index.ts` has no `beforeEach` guard
and no `meta.requiresAuth` annotations. The kit requires
protected routes to carry `meta: { requiresAuth: true }` and
a guard that checks `userManager.getUser()`.

## Important constraint

Docroot allows unauthenticated browsing of public namespaces.
Guards must apply **only** to write-capable actions — not to
read routes. Anonymous access to public namespace pages must
not be broken.

## Affected routes (write operations exposed)

- `NamespaceList` — create/delete namespace buttons
- `ProjectList` — create/delete project buttons
- `VersionList` — upload button, set-latest button

These routes also serve unauthenticated read traffic. The
guard may need to apply at the **action level** (conditional
component rendering) rather than the route level, unless
separate write-only route paths are introduced.

## Acceptance criteria

- [ ] Decision recorded: route-level guard vs. action-level
      guard strategy
- [ ] `router.beforeEach` guard added to
      `apps/frontend/src/router/index.ts`
- [ ] Guard checks `userManager.getUser()` (OIDC mode) and
      falls back to checking token in `localStorage`
      (manual-token mode)
- [ ] Unauthenticated users attempting a write action are
      redirected to OIDC login (OIDC mode) or shown the
      token dialog (manual-token mode)
- [ ] `to.fullPath` passed as OIDC `state` for post-login
      redirect back to the intended page
- [ ] Public read routes remain accessible without
      authentication (no regression)

## Dependency

Simpler to implement after issue #4 (TokenProvider seam),
because the guard can use the central `getToken()`
abstraction rather than reading `localStorage` directly.

## Files to change

- `apps/frontend/src/router/index.ts`
- Possibly: affected page components (action-level guards)
