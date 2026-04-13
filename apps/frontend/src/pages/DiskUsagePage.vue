<template>
  <v-app-bar>
    <v-btn icon="mdi-arrow-left" :to="'/'" />
    <v-toolbar-title>{{ t('diskUsageTitle') }}</v-toolbar-title>
    <v-spacer />
    <AuthBar />
    <v-progress-linear
      v-if="loading"
      absolute
      color="primary"
      indeterminate
      location="bottom"
    />
  </v-app-bar>

  <v-container>
    <v-alert v-if="error" class="mb-4" type="error">
      {{ error }}
    </v-alert>

    <v-alert
      v-if="!isAuthenticated()"
      class="mb-4"
      density="compact"
      type="info"
      variant="tonal"
    >
      {{ t('diskUsageLoginRequired') }}
    </v-alert>

    <template v-if="groups.length === 0 && !loading && !error">
      <v-alert density="compact" type="info" variant="tonal">
        {{ t('diskUsageNoData') }}
      </v-alert>
    </template>

    <v-card
      v-for="(group, index) in groups"
      :key="group.mount_group"
      class="mb-4"
    >
      <v-card-title class="d-flex align-center">
        {{ t('diskUsageMountGroup', { index: index + 1 }) }}
        <v-chip
          v-if="group.low_space"
          class="ml-2"
          color="error"
          density="compact"
          prepend-icon="mdi-alert"
          size="small"
        >
          {{ t('diskUsageLowSpace') }}
        </v-chip>
      </v-card-title>

      <v-card-text>
        <v-row class="mb-2" dense>
          <v-col cols="12" sm="4">
            <div class="text-caption text-medium-emphasis">
              {{ t('diskUsageTotal') }}
            </div>
            <div class="text-body-2">
              {{ formatBytes(group.total_bytes) }}
            </div>
          </v-col>
          <v-col cols="12" sm="4">
            <div class="text-caption text-medium-emphasis">
              {{ t('diskUsageUsed') }}
            </div>
            <div class="text-body-2">
              {{ formatBytes(group.used_bytes) }}
            </div>
          </v-col>
          <v-col cols="12" sm="4">
            <div class="text-caption text-medium-emphasis">
              {{ t('diskUsageFree') }}
            </div>
            <div
              class="text-body-2"
              :class="group.low_space ? 'text-error' : ''"
            >
              {{ formatBytes(group.free_bytes) }}
            </div>
          </v-col>
        </v-row>

        <v-progress-linear
          class="mb-3"
          :color="group.low_space ? 'error' : 'primary'"
          :model-value="usedPercent(group)"
          rounded
        />

        <v-table density="compact">
          <thead>
            <tr>
              <th>{{ t('diskUsageNamespace') }}</th>
              <th class="text-right">{{ t('diskUsageSize') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="ns in group.namespaces" :key="ns.name">
              <td>
                <router-link :to="`/${ns.name}`">
                  {{ ns.display_name || ns.name }}
                </router-link>
              </td>
              <td class="text-right">
                {{ formatBytes(ns.size_bytes) }}
              </td>
            </tr>
          </tbody>
        </v-table>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { api, type DiskUsageGroup } from '@/api'
import { isAuthenticated, token } from '@/auth'
import AuthBar from '@/components/AuthBar.vue'

const { t } = useI18n()

const groups = ref<DiskUsageGroup[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

/**
 * Format a byte count as a human-readable string.
 *
 * Uses GiB/MiB/KiB/B units rounded to one decimal place.
 */
function formatBytes(bytes: number): string {
  if (bytes >= 1024 ** 3) {
    return `${(bytes / 1024 ** 3).toFixed(1)} GiB`
  }
  if (bytes >= 1024 ** 2) {
    return `${(bytes / 1024 ** 2).toFixed(1)} MiB`
  }
  if (bytes >= 1024) {
    return `${(bytes / 1024).toFixed(1)} KiB`
  }
  return `${bytes} B`
}

/**
 * Compute the percentage of used space for a mount group.
 *
 * Returns 0 when total_bytes is zero to avoid division by zero.
 */
function usedPercent(group: DiskUsageGroup): number {
  if (group.total_bytes === 0) return 0
  return Math.round((group.used_bytes / group.total_bytes) * 100)
}

async function load() {
  if (!token.value) return
  loading.value = true
  error.value = null
  try {
    groups.value = await api.getDiskUsage(token.value)
  } catch (err) {
    error.value = (err as Error).message
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
