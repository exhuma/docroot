<template>
  <v-app-bar>
    <v-btn
      icon="mdi-arrow-left"
      :to="`/${namespace}/${project}`"
    />
    <v-toolbar-title>
      {{ namespace }}/{{ project }}
    </v-toolbar-title>
    <v-spacer />
    <v-select
      v-model="selectedVersion"
      class="mr-2"
      density="compact"
      hide-details
      :items="versionNames"
      :label="t('selectVersion')"
      style="max-width: 160px"
      @update:model-value="onVersionChange"
    />
    <v-select
      v-model="selectedLocale"
      class="mr-2"
      density="compact"
      hide-details
      :items="availableLocales"
      :label="t('selectLocale')"
      style="max-width: 120px"
      @update:model-value="onLocaleChange"
    />
  </v-app-bar>

  <v-container>
    <v-alert
      v-if="fallbackUsed && resolved"
      class="mb-4"
      type="info"
    >
      {{ t('fallbackNotice', { locale: resolved.locale }) }}
    </v-alert>

    <v-alert v-if="error" class="mb-4" type="error">
      {{ error }}
    </v-alert>

    <iframe
      v-if="iframeSrc"
      :src="iframeSrc"
      style="
        width: 100%;
        height: calc(100vh - 120px);
        border: none;
      "
    />
  </v-container>
</template>

<script setup lang="ts">
  import { computed, onMounted, ref } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { useRoute, useRouter } from 'vue-router'
  import { api, type ResolveResult, type VersionInfo }
    from '@/api'
  import { token } from '@/auth'

  const { t } = useI18n()
  const route = useRoute()
  const router = useRouter()

  const namespace = route.params.namespace as string
  const project = route.params.project as string
  const initVersion = route.params.version as string
  const initLocale = route.params.locale as string

  const versions = ref<VersionInfo[]>([])
  const resolved = ref<ResolveResult | null>(null)
  const error = ref<string | null>(null)
  const selectedVersion = ref(initVersion)
  const selectedLocale = ref(initLocale)
  const fallbackUsed = ref(false)

  const versionNames = computed(() =>
    versions.value.map(v => v.name),
  )

  const availableLocales = computed(() => {
    const ver = versions.value.find(
      v => v.name === selectedVersion.value,
    )
    return ver ? ver.locales : []
  })

  const iframeSrc = computed(() => {
    if (!resolved.value) return ''
    const { version, locale } = resolved.value
    return (
      `/${namespace}/${project}/`
      + `${version}/${locale}/`
    )
  })

  async function resolve () {
    error.value = null
    try {
      resolved.value = await api.resolveVersion(
        namespace,
        project,
        selectedVersion.value,
        selectedLocale.value,
        token.value,
      )
      fallbackUsed.value = resolved.value.fallback_used
    } catch (error_) {
      error.value = (error_ as Error).message
    }
  }

  function onVersionChange (v: string) {
    const path = `/${namespace}/${project}/docs/`
      + `${v}/${selectedLocale.value}`
    router.push(path)
  }

  function onLocaleChange (loc: string) {
    const path = `/${namespace}/${project}/docs/`
      + `${selectedVersion.value}/${loc}`
    router.push(path)
  }

  onMounted(async () => {
    try {
      versions.value = await api.listVersions(
        namespace,
        project,
        token.value,
      )
    } catch (error_) {
      error.value = (error_ as Error).message
    }
    await resolve()
  })
</script>
