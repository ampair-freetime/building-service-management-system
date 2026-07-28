<script setup>
defineProps({ mode: { type: String, required: true } })
</script>

<template>
  <main class="auth-shell">
    <section class="auth-identity" aria-label="Building Service Management">
      <RouterLink class="brand" to="/" aria-label="Building Service Management home">
        <span class="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 34 34"><path d="M7 28V13l10-7 10 7v15M12 28V17h10v11M17 6v22" /></svg>
        </span>
        <span>Building Service<br />Management</span>
      </RouterLink>

      <div class="identity-copy">
        <p class="section-label">Operations, in order</p>
        <h1>Keep every building <span class="outline-word">working.</span></h1>
        <p>One dependable workspace for the people, assets, and service requests that keep your properties running.</p>
      </div>

      <div class="building-lines" aria-hidden="true">
        <svg viewBox="0 0 700 360" preserveAspectRatio="xMidYMax meet">
          <g fill="none" stroke="currentColor" stroke-width="1.2">
            <path d="M28 330h644M80 330V128h146v202M226 330V68h196v262M422 330V156h190v174" />
            <path d="M113 128V92h80v36M278 68V30h92v38M470 156v-45h94v45" />
            <path d="M106 172h94M106 216h94M106 260h94M106 304h94M254 110h140M254 158h140M254 206h140M254 254h140M254 302h140M452 198h132M452 244h132M452 290h132" />
            <path d="M139 128v202M167 128v202M303 68v262M338 68v262M373 68v262M496 156v174M540 156v174" />
          </g>
        </svg>
      </div>
    </section>

    <section class="auth-panel">
      <div class="mobile-brand">
        <span class="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 34 34"><path d="M7 28V13l10-7 10 7v15M12 28V17h10v11M17 6v22" /></svg>
        </span>
        <span>BSM</span>
      </div>
      <div class="auth-content">
        <div class="auth-heading">
          <p class="section-label">{{ mode === 'login' ? 'Welcome back' : 'Set up your workspace' }}</p>
          <slot name="heading" />
        </div>
        <slot />
      </div>
      <p class="auth-footer">Secure access for your operations team.</p>
    </section>
  </main>
</template>
