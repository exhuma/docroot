/**
 * auth.ts
 *
 * Provides authentication state management for the Docroot UI.
 *
 * Supports two modes:
 *  1. **OIDC** — when the server provides ``oidc_issuer`` and
 *     ``oidc_client_id``, the frontend uses ``oidc-client-ts``
 *     to perform an authorization-code + PKCE flow via a full
 *     browser redirect.  Silent renewal runs automatically in the
 *     background via a dedicated ``/oidc-silent`` page.
 *  2. **Manual token** — the user pastes a raw JWT directly
 *     (kept for local development and CLI use).
 *
 * The active OIDC ``UserManager`` is lazily initialised after the
 * OIDC configuration is fetched from ``GET /api/oidc-config``.
 */

import {
  type User,
  UserManager,
  type UserManagerSettings,
} from 'oidc-client-ts'
import { ref } from 'vue'
import { api } from './api'

const STORAGE_KEY = 'docroot_token'

export const token = ref<string | null>(
  localStorage.getItem(STORAGE_KEY),
)

/**
 * ``true`` when the server has OIDC configured.  Reactive so that
 * components can conditionally render OIDC controls.
 */
export const oidcEnabled = ref(false)

/**
 * The resolved OIDC ``User`` object from oidc-client-ts, or
 * ``null`` when not logged in via OIDC.  Reactive.
 */
export const currentUser = ref<User | null>(null)

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
 * Parse a JWT and return its decoded payload, or null on error.
 */
function parseJwtPayload (
  jwt: string,
): Record<string, unknown> | null {
  try {
    const parts = jwt.split('.')
    if (parts.length !== 3) {
      return null
    }
    // JWTs use base64url; convert to standard base64 before decoding
    const b64 = (parts[1] as string)
      .replace(/-/g, '+')
      .replace(/_/g, '/')
    return JSON.parse(atob(b64)) as Record<string, unknown>
  } catch {
    return null
  }
}

/**
 * Apply a new token value to reactive state and the session cookie.
 * Passing ``null`` clears the token and invalidates the session.
 */
function applyToken (t: string | null): void {
  token.value = t
  if (t === null) {
    localStorage.removeItem(STORAGE_KEY)
    api.deleteSession().catch(() => undefined)
  } else {
    localStorage.setItem(STORAGE_KEY, t)
    // Exchange the bearer token for an HttpOnly session cookie so
    // that iframe navigations can also be authenticated.
    api.createSession(t).catch(() => undefined)
  }
}

/**
 * Initialise the OIDC UserManager from server-provided config.
 *
 * Called once during application start-up (and again inside the
 * silent-renew iframe).  Sets up the UserManager and event handlers
 * but does **not** attempt a silent login — call
 * ``trySigninSilent()`` separately from the main page context.
 *
 * @returns Resolved UserManager, or null when OIDC is disabled.
 */
export async function initOidc (): Promise<UserManager | null> {
  try {
    const cfg = await api.getOidcConfig()
    if (!cfg.issuer || !cfg.client_id) {
      return null
    }
    oidcEnabled.value = true
    const origin = window.location.origin
    const settings: UserManagerSettings = {
      authority: cfg.issuer,
      client_id: cfg.client_id,
      redirect_uri: `${origin}/oidc-callback`,
      silent_redirect_uri: `${origin}/oidc-silent`,
      response_type: 'code',
      scope: 'openid profile email',
      post_logout_redirect_uri: origin,
      automaticSilentRenew: true,
    }
    _userManager = new UserManager(settings)

    // Keep reactive state in sync with UserManager lifecycle events.
    _userManager.events.addUserLoaded(user => {
      applyToken(user.access_token)
      currentUser.value = user
    })
    _userManager.events.addUserUnloaded(() => {
      applyToken(null)
      currentUser.value = null
    })
    _userManager.events.addUserSignedOut(() => {
      applyToken(null)
      currentUser.value = null
    })
    _userManager.events.addSilentRenewError(() => {
      // Token could not be renewed silently; reset to unauthenticated.
      applyToken(null)
      currentUser.value = null
    })

    return _userManager
  } catch {
    return null
  }
}

/**
 * Attempt a transparent silent login using an existing SSO session.
 *
 * Must be called **only from the main page context** — never from
 * inside the silent-renew iframe (``/oidc-silent``).  Calling it
 * inside the iframe would spawn a new iframe, creating an infinite
 * loop.  ``initOidc()`` must have been called first.
 *
 * State is updated via the ``addUserLoaded`` event handler when
 * the silent login succeeds.
 */
export async function trySigninSilent (): Promise<void> {
  if (!_userManager) {
    return
  }
  try {
    await _userManager.signinSilent()
  } catch {
    // No existing SSO session — user must log in explicitly.
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
 * authorization code for tokens, updates reactive state, and
 * creates the session cookie.
 *
 * @returns The subject (``sub``) claim of the received token.
 */
export async function completeOidcCallback (): Promise<string> {
  if (!_userManager) {
    throw new Error('OIDC not initialised')
  }
  const user = await _userManager.signinRedirectCallback()
  // State (token + currentUser) is updated via the addUserLoaded event.
  return user.profile.sub
}

/**
 * Log the user out.
 *
 * For OIDC sessions, removes the local user and clears the token.
 * For manual tokens, simply clears the stored value.
 */
export async function logout (): Promise<void> {
  if (_userManager) {
    await _userManager.removeUser()
  }
  applyToken(null)
  currentUser.value = null
}

export function setToken (t: string | null): void {
  applyToken(t)
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
  const payload = parseJwtPayload(token.value)
  if (!payload) {
    return null
  }
  return typeof payload.sub === 'string' ? payload.sub : null
}

/**
 * Return the display name for the currently authenticated user.
 *
 * For OIDC sessions the OIDC id-token profile is used.
 * For manually-set tokens the JWT payload is decoded.
 * Claim priority: ``name`` → ``preferred_username`` → ``email``
 * → ``sub``.  Returns ``null`` when not authenticated.
 */
export function getDisplayName (): string | null {
  const PROFILE_CLAIMS = [
    'name',
    'preferred_username',
    'email',
    'sub',
  ] as const
  if (currentUser.value) {
    const p = currentUser.value.profile
    for (const claim of PROFILE_CLAIMS) {
      const v = p[claim]
      if (typeof v === 'string' && v) {
        return v
      }
    }
    return null
  }
  if (!token.value) {
    return null
  }
  const payload = parseJwtPayload(token.value)
  if (!payload) {
    return null
  }
  for (const claim of PROFILE_CLAIMS) {
    if (typeof payload[claim] === 'string' && payload[claim]) {
      return payload[claim] as string
    }
  }
  return null
}

/**
 * Return the avatar URL for the currently authenticated user, or
 * null when no ``picture`` claim is present.
 */
export function getAvatarUrl (): string | null {
  if (currentUser.value) {
    const pic = currentUser.value.profile.picture
    return typeof pic === 'string' ? pic : null
  }
  if (!token.value) {
    return null
  }
  const payload = parseJwtPayload(token.value)
  if (!payload) {
    return null
  }
  return typeof payload.picture === 'string'
    ? payload.picture
    : null
}
