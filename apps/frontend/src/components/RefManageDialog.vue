<template>
  <v-dialog
    max-width="480"
    :model-value="modelValue"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <v-card :title="t('manageRefsTitle', { version })">
      <v-card-text>
        <!-- Existing refs pointing to this version -->
        <div v-if="currentRefs.length" class="mb-4">
          <div class="text-subtitle-2 mb-2">{{ t('assignedRefs') }}</div>
          <v-chip
            v-for="ref in currentRefs"
            :key="ref"
            class="mr-2 mb-2"
            closable
            :color="ref === 'latest' ? 'green' : 'teal'"
            label
            @click:close="onDeleteRef(ref)"
          >
            {{ ref }}
          </v-chip>
        </div>

        <v-divider v-if="currentRefs.length" class="mb-4" />

        <!-- Assign an existing ref to this version -->
        <div class="text-subtitle-2 mb-2">{{ t('assignRef') }}</div>
        <v-select
          v-model="selectedExisting"
          clearable
          density="compact"
          hide-details
          :items="otherRefNames"
          :label="t('existingRef')"
          :no-data-text="t('noOtherRefs')"
          variant="outlined"
        />
        <div class="text-center my-2 text-caption text-medium-emphasis">
          {{ t('orCreateNew') }}
        </div>
        <v-text-field
          v-model="newRefName"
          density="compact"
          hide-details
          :label="t('newRefName')"
          variant="outlined"
          @keydown.enter="onAssign"
        />
        <v-alert v-if="errorMsg" class="mt-3" density="compact" type="error">
          {{ errorMsg }}
        </v-alert>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn @click="emit('update:modelValue', false)">
          {{ t('cancel') }}
        </v-btn>
        <v-btn color="primary" :disabled="!refToAssign" :loading="loading" @click="onAssign">
          {{ t('assign') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { api, type RefInfo } from '@/api'

const props = defineProps<{
  modelValue?: boolean
  namespace: string
  project: string
  token: string
  version: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'updated'): void
}>()

const { t } = useI18n()

const allRefs = ref<RefInfo[]>([])
const selectedExisting = ref<string | null>(null)
const newRefName = ref('')
const loading = ref(false)
const errorMsg = ref<string | null>(null)

/** Refs that currently point at this version. */
const currentRefs = computed(() =>
  allRefs.value.filter((r) => r.version === props.version).map((r) => r.name),
)

/** Refs that exist but point to a different version. */
const otherRefNames = computed(() =>
  allRefs.value.filter((r) => r.version !== props.version).map((r) => r.name),
)

/** The ref name to assign: new name takes priority over dropdown. */
const refToAssign = computed(() => newRefName.value.trim() || selectedExisting.value || '')

async function loadRefs() {
  try {
    allRefs.value = await api.listRefs(props.namespace, props.project, props.token)
  } catch {
    allRefs.value = []
  }
}

watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      selectedExisting.value = null
      newRefName.value = ''
      errorMsg.value = null
      loadRefs()
    }
  },
  { immediate: true },
)

async function onAssign() {
  const name = refToAssign.value
  if (!name) return
  loading.value = true
  errorMsg.value = null
  try {
    await api.setRef(props.namespace, props.project, name, props.version, props.token)
    emit('updated')
    await loadRefs()
    newRefName.value = ''
    selectedExisting.value = null
  } catch (err) {
    errorMsg.value = (err as Error).message
  } finally {
    loading.value = false
  }
}

async function onDeleteRef(refName: string) {
  loading.value = true
  errorMsg.value = null
  try {
    await api.deleteRef(props.namespace, props.project, refName, props.token)
    emit('updated')
    await loadRefs()
  } catch (err) {
    errorMsg.value = (err as Error).message
  } finally {
    loading.value = false
  }
}
</script>
