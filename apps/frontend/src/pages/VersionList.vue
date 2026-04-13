<template>
  <v-app-bar>
    <v-img class="ml-2 mr-1" height="36" max-width="110" src="@/assets/logo.svg" />
    <v-btn icon="mdi-arrow-left" :to="`/${namespace}`" />
    <v-toolbar-title> {{ namespace }}/{{ project }} — {{ t('versions') }} </v-toolbar-title>
    <v-spacer />
    <v-btn v-if="isAuthenticated()" prepend-icon="mdi-upload" @click="uploadDialog = true">
      {{ t('upload') }}
    </v-btn>
    <AuthBar />
    <v-progress-linear v-if="loading" absolute color="primary" indeterminate location="bottom" />
  </v-app-bar>

  <v-container>
    <v-alert v-if="error" class="mb-4" type="error">
      {{ error }}
    </v-alert>

    <v-data-table
      :headers="headers"
      hover
      item-value="name"
      :items="versions"
      :items-per-page="-1"
      :no-data-text="t('noVersions')"
    >
      <template #item.name="{ item }">
        {{ item.name }}
        <v-chip
          v-for="ref in item.refs"
          :key="ref"
          class="ml-2"
          :color="ref === 'latest' ? 'green' : 'teal'"
          label
          size="small"
        >
          {{ ref }}
        </v-chip>
      </template>

      <template #item.locales="{ item }">
        <v-chip
          v-for="loc in item.locales"
          :key="loc"
          class="mr-1"
          label
          size="small"
          :to="`/${namespace}/${project}/docs/${item.name}/${loc}`"
        >
          {{ loc }}
        </v-chip>
      </template>

      <template #item.actions="{ item }">
        <div class="d-flex justify-end">
          <v-btn
            v-if="isAuthenticated()"
            density="compact"
            icon="mdi-tag-multiple"
            size="small"
            :title="t('manageRefs')"
            @click="openRefDialog(item.name)"
          />
        </div>
      </template>

      <template #bottom />
    </v-data-table>
  </v-container>

  <UploadDialog
    v-if="uploadDialog && token"
    v-model="uploadDialog"
    :namespace="namespace"
    :project="project"
    :token="token"
    @uploaded="onUploaded"
  />

  <RefManageDialog
    v-if="refDialog && token"
    v-model="refDialog"
    :namespace="namespace"
    :project="project"
    :token="token"
    :version="refDialogVersion"
    @updated="load"
  />
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { api, type VersionInfo } from '@/api'
import { isAuthenticated, token } from '@/auth'
import AuthBar from '@/components/AuthBar.vue'
import RefManageDialog from '@/components/RefManageDialog.vue'
import UploadDialog from '@/components/UploadDialog.vue'

const { t } = useI18n()
const route = useRoute()
const namespace = route.params.namespace as string
const project = route.params.project as string

const versions = ref<VersionInfo[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const uploadDialog = ref(false)
const refDialog = ref(false)
const refDialogVersion = ref('')

const headers = computed(() => [
  { title: t('version'), key: 'name', sortable: false, width: '180px' },
  { title: t('locales'), key: 'locales', sortable: false },
  { title: t('actions'), key: 'actions', sortable: false, width: '48px' },
])

async function load() {
  loading.value = true
  error.value = null
  try {
    versions.value = await api.listVersions(namespace, project, token.value)
  } catch (error_) {
    error.value = (error_ as Error).message
  } finally {
    loading.value = false
  }
}

async function onUploaded() {
  uploadDialog.value = false
  await load()
}

function openRefDialog(version: string) {
  refDialogVersion.value = version
  refDialog.value = true
}

onMounted(load)
</script>
