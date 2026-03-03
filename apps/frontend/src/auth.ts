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
