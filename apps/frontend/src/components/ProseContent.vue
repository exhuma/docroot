<template>
  <!--
    v-html is intentional here.  The markdown sources are statically
    bundled at build time from files under source control — no
    user-supplied input ever reaches marked.parse().
  -->
  <div
    class="prose-content"
    v-html="html"
  />
</template>

<script setup lang="ts">
  import { marked } from 'marked'
  import { computed } from 'vue'
  import { useI18n } from 'vue-i18n'
  import deMd from '@/assets/content/intro.de.md?raw'
  import enMd from '@/assets/content/intro.en.md?raw'
  import frMd from '@/assets/content/intro.fr.md?raw'

  const { locale } = useI18n()

  const sources: Record<string, string> = {
    en: enMd,
    fr: frMd,
    de: deMd,
  }

  const html = computed(() => {
    const src = sources[locale.value] ?? enMd
    return marked.parse(src, { async: false }) as string
  })
</script>

<style scoped>
.prose-content :deep(h1) {
  font-size: 1.5rem;
  font-weight: 500;
  margin-bottom: 0.75rem;
}

.prose-content :deep(h2) {
  font-size: 1.15rem;
  font-weight: 500;
  margin-top: 1.25rem;
  margin-bottom: 0.5rem;
}

.prose-content :deep(p) {
  margin-bottom: 0.75rem;
}

.prose-content :deep(ol),
.prose-content :deep(ul) {
  padding-left: 1.5rem;
  margin-bottom: 0.75rem;
}

.prose-content :deep(li) {
  margin-bottom: 0.25rem;
}

.prose-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin-bottom: 0.75rem;
}

.prose-content :deep(th),
.prose-content :deep(td) {
  border: 1px solid rgba(0, 0, 0, 0.12);
  padding: 0.4rem 0.75rem;
  text-align: left;
}

.prose-content :deep(th) {
  background-color: rgba(0, 0, 0, 0.04);
  font-weight: 500;
}

.prose-content :deep(code) {
  background-color: rgba(0, 0, 0, 0.06);
  border-radius: 3px;
  padding: 0 4px;
  font-family: monospace;
}

.prose-content :deep(a) {
  color: rgb(var(--v-theme-primary));
}
</style>
