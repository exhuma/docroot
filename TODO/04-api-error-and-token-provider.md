# refactor(frontend): add ApiError class and TokenProvider seam

**Source kits:** `stack-fastapi-vuetify`, `module-auth-oidc`

## Context

`apps/frontend/src/api.ts` must export a structured `ApiError`
class and a `TokenProvider` seam so that the auth
implementation is swappable without touching individual API
call sites.

## Current state

- `api.ts` throws `new Error(msg)` — callers cannot read the
  HTTP status code programmatically.
- Each API method accepts `token?: string | null` as an
  explicit parameter — no central auth injection point.
- `auth.ts` manages the token reactively via a `ref` but
  there is no `setTokenProvider` seam.

## Required additions

### ApiError class

```ts
export class ApiError extends Error {
  status: number
  data: unknown
}
```

All `handleResponse()` rejections must throw `ApiError`.
Components may then inspect `err.status` to distinguish
401/403/404 etc.

### TokenProvider seam

```ts
export interface TokenProvider {
  getToken(): string | null
}
export function setTokenProvider(p: TokenProvider): void
export function setUnauthorizedHandler(fn: () => void): void
```

- All `api.*` methods read the token via the registered
  `TokenProvider`; the `token` parameter is removed from
  every method signature.
- Bootstrap code in `main.ts` calls `setTokenProvider` with
  the OIDC / manual-token implementation at startup.
- `setUnauthorizedHandler` registers a callback invoked on
  any 401 (typically: redirect to login).

## Impact

⚠️ **Call-site-breaking change across the entire frontend.**
Every component that passes `token` to `api.*` methods and
every try/catch block that inspects the error object must be
updated.

## Acceptance criteria

- [ ] `api.ts` exports `ApiError` with `status` and `data`
- [ ] `api.ts` exports `TokenProvider` interface
- [ ] `api.ts` exports `setTokenProvider()`
- [ ] `api.ts` exports `setUnauthorizedHandler()`
- [ ] All `api.*` methods use `TokenProvider` internally;
      explicit `token` parameter removed from all signatures
- [ ] `auth.ts` or `main.ts` calls `setTokenProvider` at
      bootstrap with the OIDC / manual-token implementation
- [ ] All component call sites updated (token arg removed)
- [ ] Error-handling code updated to use `ApiError`

## Files to change

- `apps/frontend/src/api.ts`
- `apps/frontend/src/auth.ts`
- `apps/frontend/src/main.ts`
- Every `.vue` / `.ts` file that calls `api.*` with a token
  argument or catches `Error` objects
