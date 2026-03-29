<template>
  <v-app-bar>
    <v-img src="@/assets/logo.svg" height="36" max-width="110" class="ml-2 mr-1" />
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

    <v-row v-if="versions.length > 0">
      <v-col v-for="ver in versions" :key="ver.name" cols="12" md="6">
        <v-card>
          <v-card-title>
            {{ ver.name }}
            <v-chip v-if="ver.is_latest" class="ml-2" color="green" label size="small">
              {{ t('latest') }}
            </v-chip>
          </v-card-title>
          <v-card-text>
            <v-chip v-for="loc in ver.locales" :key="loc" class="mr-1" label size="small">
              {{ loc }}
            </v-chip>
          </v-card-text>
          <v-card-actions>
            <v-select
              v-model="selectedLocale[ver.name]"
              density="compact"
              hide-details
              :items="ver.locales"
              :label="t('selectLocale')"
              style="max-width: 120px"
              variant="solo"
            />
            <v-btn
              color="primary"
              :disabled="!selectedLocale[ver.name]"
              @click="viewDocs(ver.name)"
            >
              {{ t('viewDocs') }}
            </v-btn>
            <v-btn v-if="isAuthenticated() && !ver.is_latest" @click="onSetLatest(ver.name)">
              {{ t('setLatest') }}
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <v-empty-state v-else-if="!loading" :title="t('noVersions')" />
  </v-container>

  <UploadDialog
    v-if="uploadDialog && token"
    v-model="uploadDialog"
    :namespace="namespace"
    :project="project"
    :token="token"
    @uploaded="onUploaded"
  />
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { api, type VersionInfo } from '@/api'
import { isAuthenticated, token } from '@/auth'
import AuthBar from '@/components/AuthBar.vue'
import UploadDialog from '@/components/UploadDialog.vue'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const namespace = route.params.namespace as string
const project = route.params.project as string

const versions = ref<VersionInfo[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const uploadDialog = ref(false)
const selectedLocale = reactive<Record<string, string>>({})

async function load() {
  loading.value = true
  error.value = null
  try {
    versions.value = await api.listVersions(namespace, project, token.value)
    for (const v of versions.value) {
      if (v.locales.length > 0 && !selectedLocale[v.name]) {
        selectedLocale[v.name] = v.locales[0] ?? ''
      }
    }
  } catch (error_) {
    error.value = (error_ as Error).message
  } finally {
    loading.value = false
  }
}

function viewDocs(version: string) {
  const loc = selectedLocale[version]
  if (!loc) return
  router.push(`/${namespace}/${project}/docs/${version}/${loc}`)
}

async function onSetLatest(version: string) {
  if (!token.value) return
  try {
    await api.setLatest(namespace, project, version, token.value)
    await load()
  } catch (error_) {
    error.value = (error_ as Error).message
  }
}

async function onUploaded() {
  uploadDialog.value = false
  await load()
}

onMounted(load)
</script>
