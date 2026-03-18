<template>
  <!-- Full-screen documentation iframe (compose/prod only) -->
  <iframe
    v-if="iframeSrc && !isDev"
    class="docs-frame"
    :src="iframeSrc"
  />

  <!--
    Dev-server notice: static docs are served by nginx in the
    compose stack. The vite dev server has no route for those
    paths, so we show a direct link instead of a broken iframe.
  -->
  <div v-if="iframeSrc && isDev" class="docs-dev-notice">
    <v-alert
      class="docs-dev-notice__alert"
      type="info"
      variant="tonal"
    >
      {{ t('devModeNotice') }}
    </v-alert>
  </div>

  <!-- Error shown floating when iframe cannot load -->
  <div v-if="error" class="docs-error-overlay">
    <v-alert type="error">
      {{ error }}
    </v-alert>
  </div>

  <!--
    Floating version-switcher card.
    - Anchored to bottom-right by default.
    - Drag the toolbar to reposition it.
    - Click the chevron to collapse/expand.
  -->
  <v-card
    ref="panelEl"
    elevation="8"
    min-width="240"
    rounded="sm"
    :style="panelStyle"
  >
    <!-- Toolbar acts as drag handle -->
    <v-toolbar
      :aria-label="t('dragPanel')"
      color="primary"
      density="compact"
      role="button"
      style="cursor: grab; user-select: none;"
      tabindex="0"
      :title="`${namespace}/${project}`"
      @keydown="onPanelKeydown"
      @mousedown="startDrag"
    >
      <template #append>
        <v-btn
          color="white"
          density="compact"
          :icon="
            expanded
              ? 'mdi-chevron-down'
              : 'mdi-chevron-up'
          "
          variant="text"
          @click.stop="expanded = !expanded"
        />
      </template>
    </v-toolbar>

    <!-- Expandable body with version/locale selectors -->
    <v-card-text v-if="expanded">
      <v-alert
        v-if="fallbackUsed && resolved"
        class="mb-3"
        density="compact"
        type="info"
      >
        {{
          t('fallbackNotice', { locale: resolved.locale })
        }}
      </v-alert>

      <v-select
        v-model="selectedVersion"
        class="mb-3"
        density="compact"
        hide-details
        :items="versionNames"
        :label="t('selectVersion')"
        variant="solo"
        @update:model-value="onVersionChange"
      />

      <v-select
        v-model="selectedLocale"
        density="compact"
        hide-details
        :items="availableLocales"
        :label="t('selectLocale')"
        variant="solo"
        @update:model-value="onLocaleChange"
      />
      <v-btn
        class="mt-4"
        color="primary"
        density="compact"
        :to="`/${namespace}/${project}`"
      >
        <v-icon left>mdi-arrow-left</v-icon>
        {{ $t('back') }}
      </v-btn>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
  import {
    computed,
    onMounted,
    onUnmounted,
    ref,
  } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { useRoute, useRouter } from 'vue-router'
  import {
    api,
    type ResolveResult,
    type VersionInfo,
  } from '@/api'
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
  const expanded = ref(true)
  const isDev = import.meta.env.DEV
  // v-card is a component; access the root DOM element via .$el.
  const panelEl = ref<{ $el: HTMLElement } | null>(null)

  /** Pixel coordinates used while dragging. */
  type PanelPos = {
    top: string | null
    left: string | null
    bottom: string | null
    right: string | null
  }

  /**
   * Panel position.  Before any drag the panel is anchored to
   * the bottom-right via CSS bottom/right.  After the first
   * drag it switches to top/left absolute coordinates so the
   * element follows the cursor exactly.
   */
  const panelPos = ref<PanelPos>({
    top: null,
    left: null,
    bottom: '16px',
    right: '16px',
  })

  const panelStyle = computed(() => {
    const s: Record<string, string> = {
      position: 'fixed',
      // Keep the card above the iframe (z-index 0) but below
      // Vuetify's teleported overlay layer (~2000) so that
      // v-select dropdown menus render on top of the card.
      zIndex: '10',
    }
    if (panelPos.value.top === null) {
      s.bottom = panelPos.value.bottom ?? '16px'
      s.right = panelPos.value.right ?? '16px'
    } else {
      s.top = panelPos.value.top
      s.left = panelPos.value.left ?? '16px'
    }
    return s
  })

  let dragOffsetX = 0
  let dragOffsetY = 0

  function onDrag (event: MouseEvent) {
    panelPos.value = {
      top: `${event.clientY - dragOffsetY}px`,
      left: `${event.clientX - dragOffsetX}px`,
      bottom: null,
      right: null,
    }
  }

  function stopDrag () {
    window.removeEventListener('mousemove', onDrag)
    window.removeEventListener('mouseup', stopDrag)
  }

  function startDrag (event: MouseEvent) {
    if (!panelEl.value) return
    const rect = panelEl.value.$el.getBoundingClientRect()
    dragOffsetX = event.clientX - rect.left
    dragOffsetY = event.clientY - rect.top
    // Snapshot current position as top/left so the panel
    // moves smoothly relative to the pointer.
    panelPos.value = {
      top: `${rect.top}px`,
      left: `${rect.left}px`,
      bottom: null,
      right: null,
    }
    window.addEventListener('mousemove', onDrag)
    window.addEventListener('mouseup', stopDrag)
  }

  /** Move the panel 16 px per arrow-key press. */
  function onPanelKeydown (event: KeyboardEvent) {
    const STEP = 16
    const rect = panelEl.value?.$el?.getBoundingClientRect()
    if (!rect) return
    const top = rect.top
    const left = rect.left
    const moves: Record<string, [number, number]> = {
      ArrowUp: [0, -STEP],
      ArrowDown: [0, STEP],
      ArrowLeft: [-STEP, 0],
      ArrowRight: [STEP, 0],
    }
    const delta = moves[event.key]
    if (!delta) return
    event.preventDefault()
    panelPos.value = {
      top: `${top + delta[1]}px`,
      left: `${left + delta[0]}px`,
      bottom: null,
      right: null,
    }
  }

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

  onUnmounted(() => {
    stopDrag()
  })
</script>

<style scoped>
  /** Full-screen documentation frame. */
  .docs-frame {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    border: none;
    z-index: 0;
  }

  /**
   * Error alert centred at the top of the viewport,
   * layered above the iframe.
   */
  .docs-error-overlay {
    position: fixed;
    top: 16px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 10000;
    max-width: 600px;
    width: 90%;
  }

  /**
   * Dev-server notice centred in the viewport, visible only
   * when running under the vite dev server.
   */
  .docs-dev-notice {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100vh;
    padding: 24px;
  }

  .docs-dev-notice__alert {
    max-width: 600px;
    width: 100%;
  }

  /** Toolbar cursor switches to grabbing while dragging. */
  .v-toolbar:active {
    cursor: grabbing !important;
  }
</style>
