<script setup>
import { onMounted, ref } from 'vue'

import { getHealth } from '../services/api'

const apiStatus = ref('Checking API…')

onMounted(async () => {
  try {
    const health = await getHealth()
    apiStatus.value = health.status === 'ok' ? 'API connected' : 'API unavailable'
  } catch {
    apiStatus.value = 'API unavailable'
  }
})
</script>

<template>
  <main class="shell">
    <section class="hero">
      <p class="eyebrow">Operations workspace</p>
      <h1>Building Service Management</h1>
      <p class="summary">
        Manage facilities, service requests, assets, and maintenance from one place.
      </p>
      <div class="status" role="status">
        <span class="status-dot" aria-hidden="true"></span>
        {{ apiStatus }}
      </div>
    </section>
  </main>
</template>

