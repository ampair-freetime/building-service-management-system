<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import AuthShell from '../components/AuthShell.vue'
import PasswordField from '../components/PasswordField.vue'

const router = useRouter()
const form = reactive({ name: '', email: '', password: '', terms: false })
const errors = reactive({ name: '', email: '', password: '', terms: '' })
const submitted = ref(false)

function createAccount() {
  errors.name = form.name.trim().length >= 2 ? '' : 'Enter your full name.'
  errors.email = /\S+@\S+\.\S+/.test(form.email) ? '' : 'Enter a valid work email.'
  errors.password = form.password.length >= 8 ? '' : 'Use at least 8 characters.'
  errors.terms = form.terms ? '' : 'Accept the terms to continue.'
  if (Object.values(errors).some(Boolean)) return
  submitted.value = true
  window.setTimeout(() => router.push('/login'), 500)
}
</script>

<template>
  <AuthShell mode="signup">
    <template #heading>
      <h2>Create your account</h2>
      <p>Start organizing service work across your properties.</p>
    </template>
    <form class="auth-form" novalidate @submit.prevent="createAccount">
      <div class="field-group">
        <label for="signup-name">Full name</label>
        <input id="signup-name" v-model.trim="form.name" type="text" autocomplete="name" placeholder="Your full name"
          :aria-invalid="Boolean(errors.name)" :aria-describedby="errors.name ? 'signup-name-error' : undefined" />
        <p v-if="errors.name" id="signup-name-error" class="field-error">{{ errors.name }}</p>
      </div>
      <div class="field-group">
        <label for="signup-email">Work email</label>
        <input id="signup-email" v-model.trim="form.email" type="email" autocomplete="email" placeholder="name@company.com"
          :aria-invalid="Boolean(errors.email)" :aria-describedby="errors.email ? 'signup-email-error' : undefined" />
        <p v-if="errors.email" id="signup-email-error" class="field-error">{{ errors.email }}</p>
      </div>
      <PasswordField id="signup-password" v-model="form.password" label="Password" autocomplete="new-password"
        placeholder="At least 8 characters" :error="errors.password" />
      <div class="terms-block">
        <label class="check-control"><input v-model="form.terms" type="checkbox" /><span aria-hidden="true"></span>
          <span>I agree to the <a href="#">Terms of service</a> and <a href="#">Privacy policy</a>.</span>
        </label>
        <p v-if="errors.terms" class="field-error">{{ errors.terms }}</p>
      </div>
      <button class="primary-button" type="submit" :disabled="submitted">
        <span>{{ submitted ? 'Creating account…' : 'Create account' }}</span>
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M14 7l5 5-5 5" /></svg>
      </button>
    </form>
    <p class="auth-switch">Already have an account? <RouterLink to="/login">Log in</RouterLink></p>
  </AuthShell>
</template>
