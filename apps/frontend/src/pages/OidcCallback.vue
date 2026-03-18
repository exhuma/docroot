<template>
  <v-container class="d-flex align-center justify-center">
    <v-progress-circular
      v-if="loading"
      indeterminate
      size="64"
    />
    <v-alert
      v-else-if="error"
      type="error"
    >
      {{ error }}
    </v-alert>
  </v-container>
</template>

<script setup lang="ts">
  /**
   * OidcCallback.vue
   *
   * Handles the OIDC authorization-code redirect callback.
   *
   * The identity provider redirects the browser to
   * ``/oidc-callback`` after the user authenticates.  This page
   * completes the code-exchange, stores the access token, and
   * redirects the user to the home page.
   */
  import { onMounted, ref } from 'vue'
  import { useRouter } from 'vue-router'
  import { completeOidcCallback, initOidc } from '@/auth'

  const router = useRouter()
  const loading = ref(true)
  const error = ref<string | null>(null)

  onMounted(async () => {
    try {
      await initOidc()
      await completeOidcCallback()
      router.replace('/')
    } catch (error_) {
      error.value = (error_ as Error).message
    } finally {
      loading.value = false
    }
  })
</script>
