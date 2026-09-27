<script setup>
import { useStaffPasswordSetup } from "../view-logic/staff-password-setup/useStaffPasswordSetup.js";
const {
  password, confirmPassword, showPassword, showConfirmPassword, loading,
  submitted, success, errorMessage, invitationToken, invitedEmail,
  requirements, passwordsMatch, canSubmit, handleSubmit, goToLogin,
} = useStaffPasswordSetup();
</script>

<template>
  <div class="staff-login-page password-setup-page">
    <svg aria-hidden="true" width="0" height="0" class="setup-symbols">
      <symbol id="i-eye" viewBox="0 0 24 24">
        <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z" />
        <circle cx="12" cy="12" r="2.5" />
      </symbol>
      <symbol id="i-eye-off" viewBox="0 0 24 24">
        <path d="m3 3 18 18M10.6 6.2A11 11 0 0 1 12 6c6.5 0 10 6 10 6a16 16 0 0 1-2.2 3M6.7 6.7C3.7 8.4 2 12 2 12s3.5 6 10 6c1 0 1.9-.1 2.8-.4M9.9 9.9a3 3 0 0 0 4.2 4.2" />
      </symbol>
      <symbol id="i-check" viewBox="0 0 24 24"><path d="m5 12 4 4L19 6" /></symbol>
    </svg>
    <div class="visual-brand"><span class="brand-mark">CS</span><span>CS Building Care</span></div>
    <div class="page-visual" aria-hidden="true"></div>
    <main class="login-shell">
      <section class="login-panel" aria-label="ตั้งรหัสผ่านเจ้าหน้าที่">
        <div class="login-card">
          <div v-if="success" class="login-content setup-success" role="status">
            <div class="setup-success-icon"><svg class="icon"><use href="#i-check" /></svg></div>
            <div class="eyebrow">ตั้งรหัสผ่านสำเร็จ</div>
            <h2>บัญชีของคุณพร้อมใช้งานแล้ว</h2>
            <p>เข้าสู่ระบบด้วยอีเมลและรหัสผ่านใหม่ของคุณได้ทันที</p>
            <button class="login-button" type="button" @click="goToLogin">ไปหน้าเข้าสู่ระบบ</button>
          </div>
          <div v-else class="login-content">
            <header class="login-head">
              <div class="eyebrow">Staff invitation</div>
              <h2>ตั้งรหัสผ่านของคุณ</h2>
              <p>{{ invitedEmail ? `สำหรับบัญชี ${invitedEmail}` : "สร้างรหัสผ่านสำหรับเข้าสู่ระบบเจ้าหน้าที่" }}</p>
            </header>
            <div v-if="!invitationToken" class="setup-alert" role="alert">
              ลิงก์นี้ไม่มี Token กรุณาเปิดลิงก์จากอีเมลคำเชิญอีกครั้ง
            </div>
            <form class="login-form" @submit.prevent="handleSubmit">
              <div class="field">
                <label for="setup-password">รหัสผ่านใหม่</label>
                <div class="password-wrap">
                  <input id="setup-password" v-model="password"
                    :type="showPassword ? 'text' : 'password'" autocomplete="new-password"
                    placeholder="กรอกรหัสผ่านใหม่" :aria-invalid="String(submitted && !canSubmit)" />
                  <button class="password-toggle" type="button"
                    :aria-label="showPassword ? 'ซ่อนรหัสผ่าน' : 'แสดงรหัสผ่าน'"
                    @click="showPassword = !showPassword">
                    <svg class="icon"><use :href="showPassword ? '#i-eye-off' : '#i-eye'" /></svg>
                  </button>
                </div>
              </div>
              <ul class="password-requirements" aria-label="เงื่อนไขรหัสผ่าน">
                <li v-for="item in requirements" :key="item.label" :class="{ passed: item.passed }">
                  <span aria-hidden="true">{{ item.passed ? "✓" : "○" }}</span>{{ item.label }}
                </li>
              </ul>
              <div class="field">
                <label for="setup-password-confirm">ยืนยันรหัสผ่านใหม่</label>
                <div class="password-wrap">
                  <input id="setup-password-confirm" v-model="confirmPassword"
                    :type="showConfirmPassword ? 'text' : 'password'" autocomplete="new-password"
                    placeholder="กรอกรหัสผ่านอีกครั้ง"
                    :aria-invalid="String(submitted && !passwordsMatch)" />
                  <button class="password-toggle" type="button"
                    :aria-label="showConfirmPassword ? 'ซ่อนรหัสผ่าน' : 'แสดงรหัสผ่าน'"
                    @click="showConfirmPassword = !showConfirmPassword">
                    <svg class="icon"><use :href="showConfirmPassword ? '#i-eye-off' : '#i-eye'" /></svg>
                  </button>
                </div>
                <small v-if="confirmPassword && !passwordsMatch" class="field-error">รหัสผ่านไม่ตรงกัน</small>
              </div>
              <div v-if="errorMessage" class="setup-alert" role="alert">{{ errorMessage }}</div>
              <button class="login-button" type="submit" :disabled="!canSubmit">
                {{ loading ? "กำลังตั้งรหัสผ่าน…" : "ตั้งรหัสผ่าน" }}
              </button>
              <button class="setup-login-link" type="button" @click="goToLogin">กลับไปหน้าเข้าสู่ระบบ</button>
            </form>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>
<style src="../styles/views/staff-login.css"></style>
