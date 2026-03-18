/**
 * auth.ts
 *
 * Provides authentication state management for the Docroot UI.
 *
 * Supports two modes:
 *  1. **OIDC** — when the server provides ``oidc_issuer`` and
 *     ``oidc_client_id``, the frontend uses ``oidc-client-ts``
 *     to perform an authorization-code + PKCE flow via a full
 *     browser redirect.
 *  2. **Manual token** — the user pastes a raw JWT directly
 *     (kept for local development and CLI use).
 *
 * The active OIDC ``UserManager`` is lazily initialised after the
 * OIDC configuration is fetched from ``GET /api/oidc-config``.
 */

import { UserManager, type UserManagerSettings } from 'oidc-client-ts'
import { ref } from 'vue'
import { api } from './api'

const STORAGE_KEY = 'docroot_token'

export const token = ref<string | null>(
  localStorage.getItem(STORAGE_KEY),
)

// On module load, sync an existing token to the session cookie so
// that iframe navigations work after a page refresh.
if (token.value) {
  api.createSession(token.value).catch(() => undefined)
}

/**
 * Lazily-created OIDC UserManager.  ``null`` when OIDC is not
 * configured on the server.
 */
let _userManager: UserManager | null = null

/**
 * Return the current OIDC UserManager, or null when not configured.
 *
 * @returns The singleton UserManager instance or null.
 */
export function getUserManager (): UserManager | null {
  return _userManager
}

/**
 * Initialise the OIDC UserManager from server-provided config.
 *
 * Must be called once during application start-up (before the user
 * attempts to log in).  If the server returns null for ``issuer``
 * or ``client_id``, the manager is not created and the UI falls
 * back to manual token entry.
 *
 * @returns Resolved UserManager, or null when OIDC is disabled.
 */
export async function initOidc (): Promise<UserManager | null> {
  try {
    const cfg = await api.getOidcConfig()
    if (!cfg.issuer || !cfg.client_id) {
      return null
    }
    const redirectUri = (
      `${window.location.origin}/oidc-callback`
    )
    const settings: UserManagerSettings = {
      authority: cfg.issuer,
      client_id: cfg.client_id,
      redirect_uri: redirectUri,
      response_type: 'code',
      scope: 'openid profile email',
      post_logout_redirect_uri: window.location.origin,
    }
    _userManager = new UserManager(settings)
    return _userManager
  } catch {
    return null
  }
}

/**
 * Trigger an OIDC authorization-code redirect.
 *
 * Redirects the browser to the configured identity provider.
 * ``initOidc`` must have been called first.
 */
export async function loginWithOidc (): Promise<void> {
  if (_userManager) {
    await _userManager.signinRedirect()
  }
}

/**
 * Complete the OIDC callback flow.
 *
 * Must be called on the redirect callback page.  Exchanges the
 * authorization code for tokens, stores the access token, and
 * creates the session cookie.
 *
 * @returns The subject (``sub``) claim of the received token.
 */
export async function completeOidcCallback (): Promise<string> {
  if (!_userManager) {
    throw new Error('OIDC not initialised')
  }
  const user = await _userManager.signinRedirectCallback()
  const accessToken = user.access_token
  setToken(accessToken)
  return user.profile.sub
}

export function setToken (t: string | null): void {
  token.value = t
  if (t === null) {
    localStorage.removeItem(STORAGE_KEY)
    // Best-effort: clear the HttpOnly session cookie so that
    // subsequent iframe navigations are no longer authenticated.
    api.deleteSession().catch(() => undefined)
  } else {
    localStorage.setItem(STORAGE_KEY, t)
    // Exchange the bearer token for an HttpOnly session cookie.
    // The browser will attach the cookie to all same-origin
    // requests, including iframe navigations that cannot carry
    // custom Authorization headers.
    api.createSession(t).catch(() => undefined)
  }
}

/**
 * Return whether the user is currently authenticated.
 *
 * @returns True when a token is stored in memory.
 */
export function isAuthenticated (): boolean {
  return token.value !== null
}

/**
 * Return the ``sub`` claim of the current JWT, or null.
 *
 * @returns Subject string or null when no token is present.
 */
export function getSubject (): string | null {
  if (!token.value) {
    return null
  }
  try {
    const parts = token.value.split('.')
    if (parts.length !== 3) {
      return null
    }
    // JWTs use base64url; convert to standard base64 before decoding
    const b64 = (parts[1] as string)
      .replace(/-/g, '+')
      .replace(/_/g, '/')
    const payload = JSON.parse(atob(b64))
    return typeof payload.sub === 'string' ? payload.sub : null
  } catch {
    return null
  }
}
