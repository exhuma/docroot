<template>
  <v-dialog max-width="500" :model-value="modelValue">
    <v-card :title="t('uploadTitle')">
      <v-card-text>
        <v-file-input
          v-model="file"
          accept=".zip"
          :label="t('upload')"
        />
        <v-text-field
          v-model="versionName"
          class="mt-2"
          :label="t('version')"
        />
        <v-text-field
          v-model="localeName"
          class="mt-2"
          hint="2-letter code, e.g. en"
          :label="t('locale')"
        />
        <v-checkbox
          v-model="isLatest"
          :label="t('setLatest')"
        />
        <v-alert v-if="errorMsg" class="mt-2" type="error">
          {{ errorMsg }}
        </v-alert>
        <v-alert
          v-if="successMsg"
          class="mt-2"
          type="success"
        >
          {{ successMsg }}
        </v-alert>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn @click="emit('update:modelValue', false)">
          {{ t('back') }}
        </v-btn>
        <v-btn
          color="primary"
          :disabled="!file || !versionName || !localeName"
          :loading="loading"
          @click="onSubmit"
        >
          {{ t('upload') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
  import { ref } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { api } from '@/api'

  const props = defineProps<{
    modelValue?: boolean
    namespace: string
    project: string
    token: string
  }>()

  const emit = defineEmits<{
    (e: 'update:modelValue', v: boolean): void
    (e: 'uploaded'): void
  }>()

  const { t } = useI18n()

  const file = ref<File | null>(null)
  const versionName = ref('')
  const localeName = ref('')
  const isLatest = ref(false)
  const loading = ref(false)
  const errorMsg = ref<string | null>(null)
  const successMsg = ref<string | null>(null)

  async function onSubmit () {
    const f = file.value
    if (!f || !versionName.value || !localeName.value) return
    loading.value = true
    errorMsg.value = null
    successMsg.value = null
    try {
      const form = new FormData()
      form.append('file', f)
      form.append('version', versionName.value)
      form.append('locale', localeName.value)
      form.append('latest', String(isLatest.value))
      await api.uploadVersion(
        props.namespace,
        props.project,
        form,
        props.token,
      )
      successMsg.value = t('uploadSuccess')
      emit('uploaded')
    } catch (error) {
      errorMsg.value
        = t('uploadError') + ': ' + (error as Error).message
    } finally {
      loading.value = false
    }
  }
</script>
