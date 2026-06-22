<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuth } from '@/composables/useAuth'

const { initAuth } = useAuth()

onMounted(() => {
  initAuth()
})
</script>

<template>
  <router-view />
</template>