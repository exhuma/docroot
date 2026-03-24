<template>
  <v-app-bar>
    <v-btn icon="mdi-arrow-left" :to="`/`" />
    <v-toolbar-title> {{ namespace }} — {{ t('projects') }} </v-toolbar-title>
    <v-spacer />
    <AuthBar />
    <v-progress-linear v-if="loading" location="bottom" absolute indeterminate color="primary" />
  </v-app-bar>

  <v-container>
    <v-alert v-if="error" class="mb-4" type="error">
      {{ error }}
    </v-alert>

    <v-list v-if="projects.length > 0">
      <v-list-item
        v-for="proj in projects"
        :key="proj.name"
        link
        :title="proj.name"
        :to="`/${namespace}/${proj.name}`"
      />
    </v-list>

    <v-empty-state v-else-if="!loading" :title="t('noProjects')" />

    <v-btn
      v-if="isAuthenticated()"
      class="mt-4"
      color="primary"
      prepend-icon="mdi-plus"
      @click="createDialog = true"
    >
      {{ t('create') }}
    </v-btn>
  </v-container>

  <v-dialog v-model="createDialog" max-width="400">
    <v-card :title="t('projects')">
      <v-card-text>
        <v-text-field v-model="newName" variant="outlined" autofocus :label="t('name')" />
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn @click="createDialog = false">
          {{ t('back') }}
        </v-btn>
        <v-btn color="primary" :disabled="!newName" @click="onCreate">
          {{ t('create') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { api, type Project } from '@/api'
import { isAuthenticated, token } from '@/auth'
import AuthBar from '@/components/AuthBar.vue'

const { t } = useI18n()
const route = useRoute()
const namespace = route.params.namespace as string

const projects = ref<Project[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const createDialog = ref(false)
const newName = ref('')

async function load() {
  loading.value = true
  error.value = null
  try {
    projects.value = await api.listProjects(namespace, token.value)
  } catch (error_) {
    error.value = (error_ as Error).message
  } finally {
    loading.value = false
  }
}

async function onCreate() {
  if (!newName.value || !token.value) return
  try {
    await api.createProject(namespace, newName.value, token.value)
    createDialog.value = false
    newName.value = ''
    await load()
  } catch (error_) {
    error.value = (error_ as Error).message
  }
}

onMounted(load)
</script>
