<script setup>
import { ref } from 'vue'

defineProps({
  id: { type: String, required: true },
  label: { type: String, required: true },
  autocomplete: { type: String, default: 'current-password' },
  placeholder: { type: String, default: 'Enter your password' },
  error: { type: String, default: '' },
})
const model = defineModel({ type: String, default: '' })
const isVisible = ref(false)
</script>

<template>
  <div class="field-group">
    <label :for="id">{{ label }}</label>
    <div class="input-wrap">
      <input :id="id" v-model="model" :type="isVisible ? 'text' : 'password'" :autocomplete="autocomplete"
        :placeholder="placeholder" :aria-invalid="Boolean(error)" :aria-describedby="error ? `${id}-error` : undefined" />
      <button class="visibility-button" type="button" :aria-label="isVisible ? 'Hide password' : 'Show password'"
        @click="isVisible = !isVisible">
        <svg v-if="!isVisible" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z" /><circle cx="12" cy="12" r="2.5" />
        </svg>
        <svg v-else viewBox="0 0 24 24" aria-hidden="true">
          <path d="m3 3 18 18M10.6 6.1A10.8 10.8 0 0 1 12 6c6 0 9.5 6 9.5 6a16 16 0 0 1-2.1 2.8M6.2 6.2C3.8 8 2.5 12 2.5 12s3.5 6 9.5 6c1.2 0 2.3-.2 3.3-.6M9.9 9.9a3 3 0 0 0 4.2 4.2" />
        </svg>
      </button>
    </div>
    <p v-if="error" :id="`${id}-error`" class="field-error">{{ error }}</p>
  </div>
</template>
