<script setup>
import { useStaffLogin } from "../view-logic/staff-login/useStaffLogin.js";

const {
  identifier,
  password,
  rememberMe,
  showPassword,
  loading,
  forgotModalOpen,
  resetEmail,
  toastMessage,
  toastVisible,
  togglePassword,
  openForgotModal,
  closeForgotModal,
  handleForgotPassword,
  handleLogin,
  loginWithGoogle,
} = useStaffLogin();
</script>

<template>
  <div class="staff-login-page">
    <svg
      aria-hidden="true"
      width="0"
      height="0"
      style="position: absolute; overflow: hidden"
    >
      <symbol id="i-eye" viewBox="0 0 24 24">
        <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z" />
        <circle cx="12" cy="12" r="2.5" />
      </symbol>
      <symbol id="i-eye-off" viewBox="0 0 24 24">
        <path
          d="m3 3 18 18M10.6 6.2A11 11 0 0 1 12 6c6.5 0 10 6 10 6a16 16 0 0 1-2.2 3M6.7 6.7C3.7 8.4 2 12 2 12s3.5 6 10 6c1 0 1.9-.1 2.8-.4M9.9 9.9a3 3 0 0 0 4.2 4.2"
        />
      </symbol>
      <symbol id="i-check" viewBox="0 0 24 24">
        <path d="m5 12 4 4L19 6" />
      </symbol>
      <symbol id="i-tools" viewBox="0 0 24 24">
        <path
          d="m14.7 6.3 3-3a5 5 0 0 1-6.4 6.4l-6.7 6.7a2 2 0 0 0 3 3l6.7-6.7a5 5 0 0 0 6.4-6.4l-3 3-3-3Z"
        />
        <path d="m5 4 4 4" />
      </symbol>
      <symbol id="i-broom" viewBox="0 0 24 24">
        <path d="m14 11 6-8M12 10l4 3-5 8H4l5-11zM7 16h6M6 19h5" />
      </symbol>
      <symbol id="i-box" viewBox="0 0 24 24">
        <path d="m3 7 9-4 9 4-9 4-9-4ZM3 7l9 4 9-4v10l-9 4-9-4V7Zm9 4v10" />
      </symbol>
      <symbol id="i-shield" viewBox="0 0 24 24">
        <path d="M12 3 4 6v5c0 5.2 3.3 8.5 8 10 4.7-1.5 8-4.8 8-10V6l-8-3Z" />
        <path d="m9 12 2 2 4-4" />
      </symbol>
      <symbol id="i-close" viewBox="0 0 24 24">
        <path d="m6 6 12 12M18 6 6 18" />
      </symbol>
    </svg>
    <div class="visual-brand" aria-label="CS Building Care">
      <span class="brand-mark">CS</span><span>CS Building Care</span>
    </div>
    <div class="page-visual" aria-hidden="true">
      <div class="building-art">
        <svg viewBox="0 0 440 240">
          <path
            fill="none"
            stroke="currentColor"
            stroke-width="7"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      </div>
    </div>
    <main class="login-shell">
      <section class="login-panel" aria-label="CS Building Care Staff Portal">
        <div class="login-card">
          <div class="login-content">
            <header class="login-head">
              <div class="eyebrow">สำหรับเจ้าหน้าที่</div>
              <h2>เข้าสู่ระบบเจ้าหน้าที่</h2>
            </header>
            <form id="login-form" class="login-form" @submit.prevent="handleLogin">
            <div class="field">
              <label for="staff-id">อีเมลหรือรหัสเจ้าหน้าที่</label
              ><input
                id="staff-id"
                v-model="identifier"
                autocomplete="username"
                placeholder="name@cmu.ac.th"
                required
                aria-describedby="staffIdError"
              /><small
                class="field-error"
                id="staffIdError"
                aria-live="polite"
              ></small>
            </div>
            <div class="field">
              <label for="password">รหัสผ่าน</label>
              <div class="password-wrap">
                <input
                  id="password"
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  autocomplete="current-password"
                  placeholder="กรอกรหัสผ่าน"
                  required
                  aria-describedby="passwordError"
                /><button
                  type="button"
                  class="password-toggle"
                  id="passwordToggle"
                  :aria-label="showPassword ? 'ซ่อนรหัสผ่าน' : 'แสดงรหัสผ่าน'"
                  @click="togglePassword"
                >
                  <svg class="icon">
                    <use :href="showPassword ? '#i-eye-off' : '#i-eye'" />
                  </svg>
                </button>
              </div>
              <small
                class="field-error"
                id="passwordError"
                aria-live="polite"
              ></small>
            </div>
            <div class="form-options">
              <label class="remember"
                ><input v-model="rememberMe" type="checkbox" id="rememberMe" /> จดจำฉัน</label
              ><button
                type="button"
                class="link-button"
                id="forgotPassword"
                @click="openForgotModal"
              >
                ลืมรหัสผ่าน?
              </button>
            </div>
            <button
              class="login-button"
              id="loginButton"
              type="submit"
              :disabled="loading"
            >
              {{ loading ? "กำลังเข้าสู่ระบบ…" : "เข้าสู่ระบบ" }}
            </button>
            <!-- <div class="divider">หรือ</div>
            <button
              class="google-button"
              id="googleLogin"
              type="button"
              @click="loginWithGoogle"
            >
              <span class="google-logo">G</span> เข้าสู่ระบบด้วย Google
            </button> -->
            </form>
          </div>
        </div>
      </section>
    </main>

    <div
      class="modal"
      :class="{ open: forgotModalOpen }"
      id="forgotModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="forgotModalTitle"
      :aria-hidden="String(!forgotModalOpen)"
    >
      <section class="modal-card">
        <header class="modal-head">
          <h3 id="forgotModalTitle">ลืมรหัสผ่าน</h3>
          <button
            type="button"
            class="modal-close"
            data-close="forgotModal"
            aria-label="ปิด"
            @click="closeForgotModal"
          >
            <svg class="icon"><use href="#i-close" /></svg>
          </button>
        </header>
        <p class="modal-copy">
          กรอกอีเมลเจ้าหน้าที่เพื่อรับลิงก์ตั้งรหัสผ่านใหม่
        </p>
        <form id="forgotForm" @submit.prevent="handleForgotPassword">
          <div class="field">
            <label for="resetEmail">อีเมลเจ้าหน้าที่</label
            ><input
              id="resetEmail"
              v-model="resetEmail"
              type="email"
              required
              placeholder="name@cmu.ac.th"
            />
          </div>
          <div class="modal-actions">
            <button
              type="button"
              class="secondary"
              data-close="forgotModal"
              @click="closeForgotModal"
            >
              ยกเลิก</button
            ><button type="submit" class="primary">ส่งลิงก์</button>
          </div>
        </form>
      </section>
    </div>
    <div class="toast" id="toast" :class="{ show: toastVisible }">{{ toastMessage }}</div>
  </div>
</template>

<style src="../styles/views/staff-login.css"></style>
