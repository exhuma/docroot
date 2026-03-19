<template>
  <v-btn
    prepend-icon="mdi-login"
    @click="onButtonClick"
  >
    {{ isAuthenticated() ? t('logout') : t('login') }}
  </v-btn>

  <v-dialog v-model="dialog" max-width="420">
    <v-card :title="t('authToken')">
      <v-card-text>
        <v-btn
          v-if="oidcAvailable"
          block
          class="mb-4"
          color="primary"
          prepend-icon="mdi-openid"
          @click="onOidcLogin"
        >
          {{ t('loginWithOidc') }}
        </v-btn>
        <v-divider
          v-if="oidcAvailable"
          class="mb-4"
        />
        <v-text-field
          v-model="inputToken"
          autofocus
          :label="t('authToken')"
          type="password"
        />
      </v-card-text>
      <v-card-actions>
        <v-btn
          v-if="isAuthenticated()"
          color="error"
          @click="onClear"
        >
          {{ t('logout') }}
        </v-btn>
        <v-spacer />
        <v-btn @click="dialog = false">
          {{ t('back') }}
        </v-btn>
        <v-btn
          color="primary"
          :disabled="!inputToken"
          @click="onSet"
        >
          {{ t('login') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
  import { onMounted, ref } from 'vue'
  import { useI18n } from 'vue-i18n'
  import {
    getUserManager,
    isAuthenticated,
    loginWithOidc,
    setToken,
  } from '@/auth'

  const { t } = useI18n()

  const dialog = ref(false)
  const inputToken = ref('')
  const oidcAvailable = ref(false)

  onMounted(() => {
    oidcAvailable.value = getUserManager() !== null
  })

  function onButtonClick () {
    if (isAuthenticated()) {
      onClear()
    } else {
      dialog.value = true
    }
  }

  async function onOidcLogin () {
    dialog.value = false
    await loginWithOidc()
  }

  function onSet () {
    if (!inputToken.value) return
    setToken(inputToken.value)
    dialog.value = false
  }

  function onClear () {
    setToken(null)
    inputToken.value = ''
    dialog.value = false
  }
</script>
