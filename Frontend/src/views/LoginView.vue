<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import AuthShell from '../components/AuthShell.vue'
import PasswordField from '../components/PasswordField.vue'

const router = useRouter()
const form = reactive({ email: '', password: '', remember: false })
const errors = reactive({ email: '', password: '' })
const submitted = ref(false)

function logIn() {
  errors.email = /\S+@\S+\.\S+/.test(form.email) ? '' : 'Enter a valid work email.'
  errors.password = form.password ? '' : 'Enter your password.'
  if (errors.email || errors.password) return
  submitted.value = true
  window.setTimeout(() => router.push('/'), 500)
}
</script>

<template>
  <AuthShell mode="login">
    <template #heading>
      <h2>Log in to your account</h2>
      <p>Enter your details to continue to the operations workspace.</p>
    </template>
    <form class="auth-form" novalidate @submit.prevent="logIn">
      <div class="field-group">
        <label for="login-email">Work email</label>
        <input id="login-email" v-model.trim="form.email" type="email" autocomplete="email" placeholder="name@company.com"
          :aria-invalid="Boolean(errors.email)" :aria-describedby="errors.email ? 'login-email-error' : undefined" />
        <p v-if="errors.email" id="login-email-error" class="field-error">{{ errors.email }}</p>
      </div>
      <PasswordField id="login-password" v-model="form.password" label="Password" :error="errors.password" />
      <div class="form-options">
        <label class="check-control"><input v-model="form.remember" type="checkbox" /><span aria-hidden="true"></span>Remember me</label>
        <a href="mailto:support@example.com?subject=Password reset">Forgot password?</a>
      </div>
      <button class="primary-button" type="submit" :disabled="submitted">
        <span>{{ submitted ? 'Opening workspace…' : 'Log in' }}</span>
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M14 7l5 5-5 5" /></svg>
      </button>
    </form>
    <p class="auth-switch">New to Building Service Management? <RouterLink to="/signup">Create an account</RouterLink></p>
  </AuthShell>
</template>
