<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();

const identifier = ref("");
const password = ref("");
const rememberMe = ref(false);
const showPassword = ref(false);
const loading = ref(false);

const forgotModalOpen = ref(false);
const resetEmail = ref("");
const toastMessage = ref("");
const toastVisible = ref(false);

onMounted(() => {

  //เคยมี remember account รึป่าว
  const savedId = localStorage.getItem("buildingCareStaffId");
  if (savedId) {
    identifier.value = savedId;
    rememberMe.value = true;
  }
});

const togglePassword = () => {showPassword.value = !showPassword.value;};
const openForgotModal = () => {forgotModalOpen.value = true;};
const closeForgotModal = () => {forgotModalOpen.value = false;};

const handleForgotPassword = () => {
  if (!resetEmail.value.trim()) {
    showToast("กรุณากรอกอีเมลเจ้าหน้าที่ของคุณ");
    return;
  }
  closeForgotModal();
  resetEmail.value = "";
  showToast("ส่งรหัสผ่านใหม่ไปยังอีเมลของคุณแล้ว");
};

const handleLogin = async () => {
  if (!identifier.value.trim() || !password.value) {
    showToast("กรุณากรอกอีเมลหรือรหัสเจ้าหน้าที่ และรหัสผ่าน");
    return;
  }

  loading.value = true;

  try {
    const response = await fetch("http://localhost:8000/api/v1/auth/login",{
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        identifier: identifier.value.trim(),
        password: password.value,
      }),
    });

    let data = {};

    try {
      data = await response.json();
    } catch {
      data = {};
    }

    if (!response.ok) {
      showToast(data.detail || "อีเมล/รหัสเจ้าหน้าที่ หรือรหัสผ่านไม่ถูกต้อง");
      return;
    }

    localStorage.setItem("buildingCareAccessToken",data.access_token);
    localStorage.setItem("buildingCareStaff",JSON.stringify(data.staff));
    localStorage.setItem("buildingCareRole",data.staff.role);

    if (rememberMe.value) {
      localStorage.setItem("buildingCareStaffId" ,identifier.value.trim());
    } else {
      localStorage.removeItem("buildingCareStaffId");
    }

    const role = data.staff?.role?.toLowerCase();

    if (role === "admin") {
      router.push("/admin-dashboard");
    } else {
      router.push("/staff-dashboard");
    }

  } catch (error) {
    console.error("Login failed:", error);
    showToast("ไม่สามารถเชื่อมต่อข้อมูลได้");
  } finally {
    loading.value = false;
  }
};

// const loginWithGoogle = () => {

// };

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
    <main class="login-shell">
      <section class="login-visual" aria-label="Building Care Staff Portal">
        <div class="visual-brand">
          <span class="brand-mark">BC</span><span>Building Care</span>
        </div>
        <div class="visual-copy">
          <small>Staff Portal</small>
          <h1>ดูแลงานอาคาร<br />ได้ง่ายกว่าเดิม</h1>
          <p>รับงาน อัปเดตความคืบหน้า และประสานงานได้จากพื้นที่เดียว</p>
        </div>
        <div class="building-art" aria-hidden="true">
          <svg viewBox="0 0 440 240">
            <path
              d="M20 220h400M55 220V110h90v110M145 220V48h150v172M295 220V92h90v128M188 48V22h64v26M80 138h20m20 0h10M80 170h20m20 0h10M180 82h25m28 0h25M180 120h25m28 0h25M180 158h25m28 0h25M325 125h18m16 0h10M325 160h18m16 0h10M215 220v-44h30v44"
              fill="none"
              stroke="currentColor"
              stroke-width="7"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </div>
      </section>
      <section class="login-panel">
        <div class="login-card">
          <RouterLink class="back-link" to="/"
            >← กลับหน้าเลือกพื้นที่ใช้งาน</RouterLink
          >
          <header class="login-head">
            <div class="eyebrow">สำหรับเจ้าหน้าที่</div>
            <h2>เข้าสู่ระบบเจ้าหน้าที่</h2>
            <p>ใช้บัญชีเจ้าหน้าที่ของคุณเพื่อดำเนินการต่อ</p>
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
            <div class="divider">หรือ</div>
            <button
              class="google-button"
              id="googleLogin"
              type="button"
              @click="loginWithGoogle"
            >
              <span class="google-logo">G</span> เข้าสู่ระบบด้วย Google
            </button>
          </form>
          <p class="user-link">
            <RouterLink to="/">กลับหน้าเลือกพื้นที่ใช้งาน</RouterLink>
          </p>
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

<style>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+Thai:wght@400;500;600;700;800&display=swap");

:root {
  --primary: #6d5df6;
  --primary-dark: #5647df;
  --primary-soft: #f0edff;
  --ink: #1b1926;
  --muted: #716d7d;
  --line: #e9e7ef;
  --canvas: #f7f7fb;
  --danger: #dc4c4c;
  --shadow: 0 18px 50px rgba(46, 37, 91, 0.1);
  --font: "Inter", "Noto Sans Thai", system-ui, sans-serif;
}
* {
  box-sizing: border-box;
}
html {
  scroll-behavior: smooth;
}
body {
  margin: 0;
  min-height: 100vh;
  background: linear-gradient(145deg, #f1edff, #fff 45%, #f7f7fb);
  color: var(--ink);
  font-family: var(--font);
  font-size: 15px;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}
button,
input {
  font: inherit;
}
button {
  cursor: pointer;
  min-height: 44px;
  transition: transform 0.16s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}
button:active {
  transform: scale(0.97);
}
button:focus-visible,
input:focus-visible,
a:focus-visible {
  outline: 3px solid rgba(109, 93, 246, 0.28);
  outline-offset: 3px;
}
.icon {
  width: 22px;
  height: 22px;
  display: block;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.9;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.login-shell {
  width: min(1180px, calc(100% - 40px));
  min-height: 700px;
  margin: 30px auto;
  display: grid;
  grid-template-columns: minmax(380px, 0.9fr) minmax(520px, 1.1fr);
  background: #fff;
  border-radius: 30px;
  overflow: hidden;
  box-shadow: var(--shadow);
}
.login-visual {
  position: relative;
  overflow: hidden;
  padding: 44px;
  background: linear-gradient(145deg, #5c4be9, #7a6cf8 66%, #9a8eff);
  color: #fff;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.login-visual:before {
  content: "";
  position: absolute;
  width: 420px;
  height: 420px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 50%;
  right: -190px;
  top: -160px;
}
.visual-brand {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 800;
}
.brand-mark {
  width: 48px;
  height: 48px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.24);
}
.visual-copy {
  position: relative;
  max-width: 440px;
}
.visual-copy small {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #ded9ff;
}
.visual-copy h1 {
  font-size: 42px;
  line-height: 1.18;
  margin: 10px 0 14px;
}
.visual-copy p {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.78);
  max-width: 390px;
}
.building-art {
  position: relative;
  height: 220px;
  color: rgba(255, 255, 255, 0.34);
}
.building-art svg {
  width: 100%;
  height: 100%;
}
.login-panel {
  padding: 42px 54px;
  display: flex;
  align-items: center;
}
.login-card {
  width: 100%;
  max-width: 570px;
  margin: auto;
}
.login-head {
  margin-bottom: 25px;
}
.eyebrow {
  color: var(--primary);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}
.login-head h2 {
  font-size: 32px;
  margin: 6px 0 5px;
}
.login-head p {
  font-size: 12px;
  color: var(--muted);
  margin: 0;
}
.login-form {
  display: grid;
  gap: 17px;
}
.field {
  display: grid;
  gap: 7px;
}
.field label,
.field-label {
  font-size: 12px;
  font-weight: 750;
}
.field input {
  width: 100%;
  min-height: 50px;
  border: 1px solid var(--line);
  border-radius: 15px;
  background: #fafafd;
  padding: 0 14px;
  color: var(--ink);
}
.field input:focus {
  border-color: var(--primary);
  background: #fff;
}
.password-wrap {
  position: relative;
}
.password-wrap input {
  padding-right: 52px;
}
.password-toggle {
  position: absolute;
  right: 6px;
  top: 5px;
  width: 40px;
  min-height: 40px;
  border: 0;
  border-radius: 12px;
  background: transparent;
  color: var(--muted);
  display: grid;
  place-items: center;
}
.role-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}
.role-card {
  position: relative;
  border: 1px solid var(--line);
  border-radius: 18px;
  background: #fff;
  padding: 14px;
  display: grid;
  grid-template-columns: 42px 1fr;
  align-items: center;
  gap: 11px;
  text-align: left;
  color: var(--ink);
}
.role-card.selected {
  border-color: var(--primary);
  background: var(--primary-soft);
  box-shadow: 0 0 0 3px rgba(109, 93, 246, 0.09);
}
.role-icon {
  width: 42px;
  height: 42px;
  border-radius: 13px;
  background: #f5f3fb;
  color: var(--primary);
  display: grid;
  place-items: center;
}
.role-card.selected .role-icon {
  background: var(--primary);
  color: #fff;
}
.role-card strong,
.role-card small {
  display: block;
}
.role-card strong {
  font-size: 13px;
}
.role-card small {
  font-size: 9px;
  color: var(--muted);
  margin-top: 1px;
}
.selected-mark {
  position: absolute;
  right: 9px;
  top: 8px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: none;
  place-items: center;
  background: var(--primary);
  color: #fff;
}
.role-card.selected .selected-mark {
  display: grid;
}
.selected-mark .icon {
  width: 12px;
  height: 12px;
}
.form-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
  font-size: 11px;
}
.remember {
  display: flex;
  align-items: center;
  gap: 7px;
  color: var(--muted);
}
.remember input {
  width: 17px;
  height: 17px;
  accent-color: var(--primary);
}
.link-button {
  border: 0;
  background: transparent;
  color: var(--primary);
  font-weight: 800;
  padding: 0 3px;
  min-height: 44px;
}
.login-button {
  width: 100%;
  border: 0;
  border-radius: 16px;
  background: linear-gradient(135deg, var(--primary), #8173f8);
  color: #fff;
  font-weight: 800;
  min-height: 52px;
  box-shadow: 0 12px 26px rgba(109, 93, 246, 0.24);
}
.login-button:disabled {
  opacity: 0.7;
  cursor: wait;
}
.divider {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #aaa5b3;
  font-size: 10px;
}
.divider:before,
.divider:after {
  content: "";
  height: 1px;
  flex: 1;
  background: var(--line);
}
.google-button {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 16px;
  background: #fff;
  color: var(--ink);
  font-weight: 750;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}
.google-logo {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: conic-gradient(
    from -45deg,
    #4285f4 0 25%,
    #34a853 0 50%,
    #fbbc05 0 75%,
    #ea4335 0
  );
  color: #fff;
  font-size: 10px;
  font-weight: 900;
}
.demo-note {
  border-radius: 14px;
  background: var(--primary-soft);
  padding: 11px 13px;
  color: #645b9c;
  font-size: 9px;
  text-align: center;
}
.user-link {
  text-align: center;
  font-size: 11px;
  color: var(--muted);
  margin: 16px 0 0;
}
.user-link a {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  color: var(--primary);
  font-weight: 800;
  text-decoration: none;
}
.modal {
  position: fixed;
  inset: 0;
  z-index: 30;
  display: grid;
  place-items: center;
  padding: 18px;
  background: rgba(25, 20, 45, 0.42);
  backdrop-filter: blur(7px);
  opacity: 0;
  visibility: hidden;
  transition: 0.2s;
}
.modal.open {
  opacity: 1;
  visibility: visible;
}
.modal-card {
  width: min(440px, 100%);
  max-height: 88vh;
  overflow: auto;
  border-radius: 24px;
  background: #fff;
  padding: 22px;
  box-shadow: 0 28px 80px rgba(35, 27, 68, 0.25);
  transform: translateY(14px);
  transition: 0.2s;
}
.modal.open .modal-card {
  transform: translateY(0);
}
.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}
.modal-head h3 {
  font-size: 20px;
  margin: 0;
}
.modal-close {
  width: 42px;
  border: 0;
  border-radius: 13px;
  background: #f2f0f7;
  color: var(--ink);
  display: grid;
  place-items: center;
}
.modal-copy {
  font-size: 12px;
  color: var(--muted);
  margin: 0 0 15px;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}
.secondary {
  border: 1px solid var(--line);
  border-radius: 14px;
  background: #fff;
  padding: 0 16px;
  font-weight: 750;
}
.primary {
  border: 0;
  border-radius: 14px;
  background: var(--primary);
  color: #fff;
  padding: 0 18px;
  font-weight: 800;
}
.toast {
  position: fixed;
  left: 50%;
  bottom: 24px;
  z-index: 50;
  max-width: calc(100% - 28px);
  padding: 12px 17px;
  border-radius: 14px;
  background: #211d35;
  color: #fff;
  font-size: 12px;
  box-shadow: var(--shadow);
  opacity: 0;
  visibility: hidden;
  transform: translate(-50%, 14px);
  transition: 0.2s;
}
.toast.show {
  opacity: 1;
  visibility: visible;
  transform: translate(-50%, 0);
}
.modal-open {
  overflow: hidden;
}
.field-error {
  display: block;
  min-height: 17px;
  margin-top: -2px;
  color: #d33b49;
  font-size: 10px;
}
.field input[aria-invalid="true"] {
  border-color: #d33b49;
  background: #fff7f8;
}
.back-link {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  margin-bottom: 12px;
  color: var(--primary);
  font-size: 11px;
  font-weight: 800;
  text-decoration: none;
}
@media (hover: hover) and (pointer: fine) {
  .role-card:hover,
  .google-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 22px rgba(42, 35, 85, 0.08);
  }
  .login-button:hover {
    transform: translateY(-2px);
  }
}
@media (max-width: 900px) {
  .login-shell {
    width: 100%;
    min-height: 100vh;
    margin: 0;
    border-radius: 0;
    grid-template-columns: 1fr;
  }
  .login-visual {
    min-height: 235px;
    padding: 28px;
  }
  .visual-copy h1 {
    font-size: 30px;
  }
  .visual-copy p {
    display: none;
  }
  .building-art {
    position: absolute;
    right: 16px;
    bottom: 0;
    width: 42%;
    height: 170px;
    opacity: 0.75;
  }
  .login-panel {
    padding: 34px 24px;
  }
  .login-card {
    max-width: 620px;
  }
}
@media (max-width: 520px) {
  .login-visual {
    min-height: 190px;
  }
  .visual-copy {
    max-width: 68%;
  }
  .visual-copy h1 {
    font-size: 25px;
  }
  .login-panel {
    padding: 28px 18px;
    align-items: flex-start;
  }
  .login-head h2 {
    font-size: 27px;
  }
  .role-grid {
    grid-template-columns: 1fr 1fr;
  }
  .role-card {
    grid-template-columns: 36px 1fr;
    padding: 11px;
  }
  .role-icon {
    width: 36px;
    height: 36px;
  }
  .role-card small {
    display: none;
  }
  .modal {
    align-items: end;
    padding: 0;
  }
  .modal-card {
    border-radius: 24px 24px 0 0;
    padding: 20px 18px max(24px, env(safe-area-inset-bottom));
  }
  .modal-actions {
    display: grid;
    grid-template-columns: 1fr;
  }
  .modal-actions button {
    width: 100%;
  }
}
@media (prefers-reduced-motion: reduce) {
  *,
  *:before,
  *:after {
    scroll-behavior: auto !important;
    animation: none !important;
    transition: none !important;
  }
}
</style>