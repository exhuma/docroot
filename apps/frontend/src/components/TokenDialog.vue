<template>
  <v-btn
    prepend-icon="mdi-key"
    @click="dialog = true"
  >
    {{ isAuthenticated() ? t('logout') : t('login') }}
  </v-btn>

  <v-dialog v-model="dialog" max-width="420">
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
  import { ref } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { isAuthenticated, setToken } from '@/auth'

  const { t } = useI18n()

  const dialog = ref(false)
  const inputToken = ref('')

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
