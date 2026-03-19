<template>
  <!-- ── Logged-in state ──────────────────────────────────── -->
  <template v-if="isAuthenticated()">
    <v-avatar
      class="mr-1"
      :image="avatarSrc ?? undefined"
      size="32"
    >
      <v-icon v-if="!avatarSrc">
        mdi-account
      </v-icon>
    </v-avatar>
    <span class="text-body-2 mr-2">{{ displayName }}</span>
    <v-btn
      density="compact"
      prepend-icon="mdi-logout"
      variant="tonal"
      @click="onLogout"
    >
      {{ t('logout') }}
    </v-btn>
  </template>

  <!-- ── Logged-out state ─────────────────────────────────── -->
  <template v-else>
    <!-- OIDC login button — always shown when OIDC is available -->
    <v-btn
      v-if="oidcEnabled"
      color="primary"
      prepend-icon="mdi-openid"
      @click="onOidcLogin"
    >
      {{ t('login') }}
    </v-btn>

    <!--
      Manual token button — shown always when OIDC is disabled;
      in dev mode it is also shown (smaller) when OIDC is enabled.
      In production builds it is hidden when OIDC is available to
      avoid exposing a token-paste backdoor.
    -->
    <v-btn
      v-if="showSetToken"
      class="ml-1"
      :density="oidcEnabled ? 'compact' : 'default'"
      prepend-icon="mdi-key"
      :variant="oidcEnabled ? 'tonal' : 'elevated'"
      @click="tokenDialog = true"
    >
      {{ t('setToken') }}
    </v-btn>
  </template>

  <!-- ── Manual token dialog ──────────────────────────────── -->
  <v-dialog v-model="tokenDialog" max-width="420">
    <v-card :title="t('authToken')">
      <v-card-text>
        <v-text-field
          v-model="inputToken"
          autofocus
          :label="t('authToken')"
          type="password"
        />
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn @click="tokenDialog = false">
          {{ t('back') }}
        </v-btn>
        <v-btn
          color="primary"
          :disabled="!inputToken"
          @click="onSetToken"
        >
          {{ t('setToken') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
  import { computed, ref } from 'vue'
  import { useI18n } from 'vue-i18n'
  import {
    getAvatarUrl,
    getDisplayName,
    isAuthenticated,
    loginWithOidc,
    logout,
    oidcEnabled,
    setToken,
  } from '@/auth'

  const { t } = useI18n()

  const tokenDialog = ref(false)
  const inputToken = ref('')

  /**
   * Display name for the logged-in user.  Reads reactive state
   * from ``currentUser`` / ``token`` via ``getDisplayName()``.
   */
  const displayName = computed(() => getDisplayName() ?? '—')

  /**
   * Avatar URL from the ``picture`` OIDC claim, or null.
   */
  const avatarSrc = computed(() => getAvatarUrl())

  /**
   * Show the manual token button only when:
   *  - OIDC is disabled (no production IDP configured), OR
   *  - We are in a Vite development build (``import.meta.env.DEV``).
   */
  const showSetToken = computed(
    () => !oidcEnabled.value || import.meta.env.DEV,
  )

  async function onOidcLogin () {
    await loginWithOidc()
  }

  function onSetToken () {
    if (!inputToken.value) return
    setToken(inputToken.value)
    inputToken.value = ''
    tokenDialog.value = false
  }

  async function onLogout () {
    await logout()
  }
</script>
