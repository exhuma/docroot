import { ref } from 'vue'

export const token = ref<string | null>(null)

export function setToken (t: string | null): void {
  token.value = t
}

export function isAuthenticated (): boolean {
  return token.value !== null
}
