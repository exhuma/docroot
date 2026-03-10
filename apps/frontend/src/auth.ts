import { ref } from 'vue'

const STORAGE_KEY = 'docroot_token'

export const token = ref<string | null>(
  localStorage.getItem(STORAGE_KEY),
)

export function setToken (t: string | null): void {
  token.value = t
  if (t === null) {
    localStorage.removeItem(STORAGE_KEY)
  } else {
    localStorage.setItem(STORAGE_KEY, t)
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
