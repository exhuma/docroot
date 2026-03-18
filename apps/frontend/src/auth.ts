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

export function isAuthenticated (): boolean {
  return token.value !== null
}

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
