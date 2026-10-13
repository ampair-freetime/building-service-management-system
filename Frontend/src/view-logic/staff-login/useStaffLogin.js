import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { requestPasswordReset } from "../../services/staffPasswordResetApi.js";

const API_BASE_URL = (
  import.meta.env?.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1"
).replace(/\/+$/, "");
const LOGIN_ENDPOINT = `${API_BASE_URL}/auth/login`;

export function useStaffLogin() {
  const router = useRouter();
  const identifier = ref("");
  const password = ref("");
  const identifierError = ref("");
  const passwordError = ref("");
  const rememberMe = ref(false);
  const showPassword = ref(false);
  const loading = ref(false);
  const forgotModalOpen = ref(false);
  const resetEmail = ref("");
  const resetEmailError = ref("");
  const resetLoading = ref(false);
  const toastMessage = ref("");
  const toastVisible = ref(false);
  let toastTimer;

  onMounted(() => {
    const savedId = localStorage.getItem("buildingCareStaffId");
    if (savedId) {
      identifier.value = savedId;
      rememberMe.value = true;
    }
  });

  function showToast(message) {
    window.clearTimeout(toastTimer);
    toastMessage.value = message;
    toastVisible.value = true;
    toastTimer = window.setTimeout(() => {
      toastVisible.value = false;
    }, 3600);
  }

  function closeToast() {
    window.clearTimeout(toastTimer);
    toastVisible.value = false;
  }

  function togglePassword() {
    showPassword.value = !showPassword.value;
  }

  function validateIdentifier() {
    identifierError.value = identifier.value.trim()
      ? ""
      : "กรุณากรอกอีเมลหรือรหัสเจ้าหน้าที่";
    return !identifierError.value;
  }

  function validatePassword() {
    passwordError.value = password.value ? "" : "กรุณากรอกรหัสผ่าน";
    return !passwordError.value;
  }

  function validateResetEmail() {
    const email = resetEmail.value.trim();
    resetEmailError.value = !email
      ? "กรุณากรอกอีเมลเจ้าหน้าที่ของคุณ"
      : /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
        ? ""
        : "รูปแบบอีเมลไม่ถูกต้อง";
    return !resetEmailError.value;
  }

  function openForgotModal() {
    forgotModalOpen.value = true;
  }

  function closeForgotModal() {
    forgotModalOpen.value = false;
  }

  // ขอลิงก์รีเซ็ตรหัสผ่านทางอีเมล; Backend ตอบเหมือนกันทุกกรณีเพื่อไม่เปิดเผยว่าอีเมลมีบัญชีไหม
  async function handleForgotPassword() {
    const email = resetEmail.value.trim();
    if (!validateResetEmail()) return;
    if (resetLoading.value) return;
    resetLoading.value = true;
    try {
      await requestPasswordReset(email);
    } catch (error) {
      // 422 = รูปแบบอีเมลไม่ถูกต้อง; ไม่มี status = เชื่อมต่อไม่ได้
      if (error.status === 422) {
        resetEmailError.value = "รูปแบบอีเมลไม่ถูกต้อง";
        return;
      }
      if (!error.status) {
        showToast("ไม่สามารถเชื่อมต่อระบบได้ กรุณาลองใหม่");
        return;
      }
    } finally {
      resetLoading.value = false;
    }
    closeForgotModal();
    resetEmail.value = "";
    resetEmailError.value = "";
    showToast("ถ้าอีเมลนี้มีบัญชี ระบบจะส่งลิงก์ตั้งรหัสผ่านใหม่ให้ภายในไม่กี่นาที (ตรวจในกล่อง Spam ด้วย)");
  }

  async function handleLogin() {
    if (![validateIdentifier(), validatePassword()].every(Boolean)) return;

    loading.value = true;
    try {
      const response = await fetch(LOGIN_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          identifier: identifier.value.trim(),
          password: password.value,
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        passwordError.value = data.detail || "อีเมล/รหัสเจ้าหน้าที่ หรือรหัสผ่านไม่ถูกต้อง";
        return;
      }

      // เก็บ token สำหรับแนบ Bearer ในคำขอถัดไป; โปรไฟล์และ role ใช้ประกอบการแสดงผล
      localStorage.setItem("buildingCareAccessToken", data.access_token);
      localStorage.setItem("buildingCareStaff", JSON.stringify(data.staff));
      localStorage.setItem("buildingCareRole", data.staff.role);
      // rememberMe จำเฉพาะอีเมล/รหัสเจ้าหน้าที่ ไม่ได้เก็บรหัสผ่าน
      if (rememberMe.value) {
        localStorage.setItem("buildingCareStaffId", identifier.value.trim());
      } else {
        localStorage.removeItem("buildingCareStaffId");
      }

      const destination = data.staff?.role?.toLowerCase() === "admin"
        ? "/admin-dashboard"
        : "/staff-dashboard";
      await router.push(destination);
    } catch (error) {
      console.error("Login failed:", error);
      showToast("ไม่สามารถเชื่อมต่อข้อมูลได้");
    } finally {
      loading.value = false;
    }
  }

  function loginWithGoogle() {
    showToast("ระบบเข้าสู่ระบบด้วย Google ยังไม่เปิดใช้งาน");
  }

  return {
    identifier, password, identifierError, passwordError, rememberMe, showPassword, loading,
    forgotModalOpen, resetEmail, resetEmailError, resetLoading, toastMessage, toastVisible,
    togglePassword, openForgotModal, closeForgotModal, closeToast,
    validateIdentifier, validatePassword, validateResetEmail,
    handleForgotPassword, handleLogin, loginWithGoogle,
  };
}
