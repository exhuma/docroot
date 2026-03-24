<template>
  <div v-if="hasContent" class="build-meta">
    <a
      v-if="githubUrl"
      class="build-meta__github"
      :href="githubUrl"
      rel="noopener noreferrer"
      target="_blank"
      :title="t('githubRepo')"
    >
      <v-icon size="18">mdi-github</v-icon>
    </a>

    <template v-if="commit">
      <!--
        DiceBear identicon seeded from the short commit hash.
        A visually distinct icon immediately signals a build change.
        Disabled when `isolated` is true (air-gapped / privacy mode).
      -->
      <img
        v-if="!isolated"
        :alt="t('buildCommit')"
        class="build-meta__icon"
        height="18"
        :src="`https://api.dicebear.com/9.x/identicon/svg?seed=${commit}`"
        :title="chipTitle"
        width="18"
      />
      <v-chip density="compact" label size="x-small" :title="chipTitle" variant="tonal">
        {{ commit }}
      </v-chip>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

interface Props {
  /**
   * When true, the DiceBear identicon image is not rendered.
   * Use in air-gapped environments or when external requests
   * are not permitted. Defaults to false.
   */
  isolated?: boolean
}

const { isolated = false } = defineProps<Props>()

const { t } = useI18n()

const githubUrl = import.meta.env.VITE_GITHUB_REPO_URL ?? ''
const commit = (import.meta.env.VITE_APP_COMMIT ?? '').slice(0, 7)
const buildTime = import.meta.env.VITE_APP_BUILD_TIME ?? ''

/** True when there is at least one piece of metadata to display. */
const hasContent = computed(() => Boolean(githubUrl || commit))

/** Tooltip: "Build — <timestamp>" when available, else the label. */
const chipTitle = computed(() =>
  buildTime ? `${t('buildCommit')} — ${buildTime}` : t('buildCommit'),
)
</script>

<style scoped>
.build-meta {
  display: flex;
  align-items: center;
  gap: 6px;
}

.build-meta__github {
  color: inherit;
  display: flex;
  align-items: center;
  text-decoration: none;
}

.build-meta__icon {
  border-radius: 3px;
  flex-shrink: 0;
  vertical-align: middle;
}
</style>
