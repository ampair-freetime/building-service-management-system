import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

const LOGIN_ENDPOINT = "http://localhost:8000/api/v1/auth/login";

export function useStaffLogin() {
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
    }, 2400);
  }

  function togglePassword() {
    showPassword.value = !showPassword.value;
  }

  function openForgotModal() {
    forgotModalOpen.value = true;
  }

  function closeForgotModal() {
    forgotModalOpen.value = false;
  }

  function handleForgotPassword() {
    if (!resetEmail.value.trim()) {
      showToast("กรุณากรอกอีเมลเจ้าหน้าที่ของคุณ");
      return;
    }
    closeForgotModal();
    resetEmail.value = "";
    showToast("ส่งรหัสผ่านใหม่ไปยังอีเมลของคุณแล้ว");
  }

  async function handleLogin() {
    if (!identifier.value.trim() || !password.value) {
      showToast("กรุณากรอกอีเมลหรือรหัสเจ้าหน้าที่ และรหัสผ่าน");
      return;
    }

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
        showToast(data.detail || "อีเมล/รหัสเจ้าหน้าที่ หรือรหัสผ่านไม่ถูกต้อง");
        return;
      }

      localStorage.setItem("buildingCareAccessToken", data.access_token);
      localStorage.setItem("buildingCareStaff", JSON.stringify(data.staff));
      localStorage.setItem("buildingCareRole", data.staff.role);
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
    identifier, password, rememberMe, showPassword, loading,
    forgotModalOpen, resetEmail, toastMessage, toastVisible,
    togglePassword, openForgotModal, closeForgotModal,
    handleForgotPassword, handleLogin, loginWithGoogle,
  };
}
