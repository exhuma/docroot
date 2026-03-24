<template>
  <div />
</template>

<script setup lang="ts">
/**
 * OidcSilent.vue
 *
 * Handles the OIDC silent renew callback inside the hidden
 * iframe that ``oidc-client-ts`` spawns when
 * ``automaticSilentRenew`` is enabled.
 *
 * The page must be reachable at the ``silent_redirect_uri``
 * registered with the identity provider
 * (``/oidc-silent`` by default).  It calls
 * ``signinSilentCallback()`` to complete the token exchange
 * and then the iframe is destroyed by the library.
 */
import { onMounted } from 'vue'
import { getUserManager } from '@/auth'

onMounted(async () => {
  const mgr = getUserManager()
  if (mgr) {
    await mgr.signinSilentCallback()
  }
})
</script>
