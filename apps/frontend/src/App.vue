<template>
  <v-app>
    <v-main>
      <router-view />
    </v-main>
    <!--
      Footer is suppressed on DocsPage where the panel already
      carries the GitHub icon and build info.
    -->
    <AppFooter v-if="!isDocsPage" />
  </v-app>
</template>

<script lang="ts" setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppFooter from '@/components/AppFooter.vue'

const route = useRoute()

/**
 * True when the current route is the docs viewer.
 * Checked against the route pattern (not the actual path) so
 * a namespace literally named "docs" does not trigger this.
 */
const isDocsPage = computed(() => route.matched.some((r) => r.path.includes('/docs/')))
</script>
