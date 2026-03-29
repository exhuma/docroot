<template>
  <div class="app-footer">
    <BuildMeta />
  </div>
</template>

<script setup lang="ts">
import BuildMeta from '@/components/BuildMeta.vue'
</script>

<style scoped>
.app-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 4px 16px 8px;
  opacity: 0.4;
  transition: opacity 0.2s ease;
}

.app-footer:hover {
  opacity: 1;
}
</style>
