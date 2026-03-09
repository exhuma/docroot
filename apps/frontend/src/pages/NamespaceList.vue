<template>
  <v-app-bar>
    <v-toolbar-title>{{ t('namespaces') }}</v-toolbar-title>
    <v-spacer />
    <v-select
      v-model="uiLocale"
      class="mr-2"
      density="compact"
      hide-details
      :items="uiLocales"
      :label="t('language')"
      style="max-width: 120px"
    />
    <TokenDialog />
  </v-app-bar>

  <v-container>
    <v-alert
      v-if="error"
      class="mb-4"
      type="error"
    >
      {{ error }}
    </v-alert>

    <v-list v-if="namespaces.length > 0">
      <v-list-item
        v-for="ns in namespaces"
        :key="ns.name"
        link
        :subtitle="ns.creator ? t('createdBy', { creator: ns.creator }) : undefined"
        :title="ns.name"
        :to="`/${ns.name}`"
      >
        <template #append>
          <v-chip
            v-if="ns.public_read"
            class="mr-2"
            color="success"
            density="compact"
            size="small"
          >
            {{ t('publicRead') }}
          </v-chip>
          <v-btn
            v-if="isAuthenticated() && ns.creator !== currentSubject()"
            density="compact"
            size="small"
            variant="text"
            @click.prevent="onTakeOwnership(ns.name)"
          >
            {{ t('takeOwnership') }}
          </v-btn>
        </template>
      </v-list-item>
    </v-list>

    <v-empty-state
      v-else-if="!loading"
      :title="t('noNamespaces')"
    />

    <v-progress-circular
      v-if="loading"
      indeterminate
    />

    <v-btn
      class="mt-4"
      color="primary"
      prepend-icon="mdi-plus"
      @click="createDialog = true"
    >
      {{ t('create') }}
    </v-btn>
  </v-container>

  <v-dialog v-model="createDialog" max-width="400">
    <v-card :title="t('namespaces')">
      <v-card-text>
        <v-text-field
          v-model="newName"
          autofocus
          :label="t('name')"
        />
        <v-checkbox
          v-model="newPublicRead"
          :label="t('publicRead')"
        />
        <v-alert
          v-if="!isAuthenticated()"
          density="compact"
          type="warning"
        >
          {{ t('loginRequired') }}
        </v-alert>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn @click="createDialog = false">
          {{ t('back') }}
        </v-btn>
        <v-btn
          color="primary"
          :disabled="!newName || !isAuthenticated()"
          @click="onCreate"
        >
          {{ t('create') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
  import { onMounted, ref, watch } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { api, type Namespace } from '@/api'
  import { getSubject, isAuthenticated, token } from '@/auth'
  import TokenDialog from '@/components/TokenDialog.vue'

  const { t, locale } = useI18n()

  const uiLocales = ['en', 'fr', 'de']
  const uiLocale = ref(locale.value)

  watch(uiLocale, v => {
    locale.value = v
  })

  const namespaces = ref<Namespace[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const createDialog = ref(false)
  const newName = ref('')
  const newPublicRead = ref(false)

  function currentSubject (): string {
    return getSubject() ?? ''
  }

  async function load () {
    loading.value = true
    error.value = null
    try {
      namespaces.value = await api.listNamespaces()
    } catch (error_) {
      error.value = (error_ as Error).message
    } finally {
      loading.value = false
    }
  }

  async function onCreate () {
    if (!newName.value || !token.value) return
    try {
      await api.createNamespace(
        newName.value,
        token.value,
        newPublicRead.value,
      )
      createDialog.value = false
      newName.value = ''
      newPublicRead.value = false
      await load()
    } catch (error_) {
      error.value = (error_ as Error).message
    }
  }

  async function onTakeOwnership (name: string) {
    if (!token.value) return
    try {
      await api.transferOwnership(name, token.value)
      await load()
    } catch (error_) {
      error.value = (error_ as Error).message
    }
  }

  onMounted(load)
</script>
