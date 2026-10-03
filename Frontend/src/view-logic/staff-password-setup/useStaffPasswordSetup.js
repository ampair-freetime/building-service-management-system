import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { setupStaffPassword } from "../../services/staffInvitationApi.js";

export function useStaffPasswordSetup() {
  const route = useRoute();
  const router = useRouter();
  const password = ref("");
  const confirmPassword = ref("");
  const showPassword = ref(false);
  const showConfirmPassword = ref(false);
  const loading = ref(false);
  const submitted = ref(false);
  const success = ref(false);
  const errorMessage = ref("");
  const invitationToken = computed(() =>
    typeof route.query.token === "string" ? route.query.token.trim() : "",
  );
  const invitedEmail = computed(() =>
    typeof route.query.email === "string" ? route.query.email.trim() : "",
  );
  const requirements = computed(() => [
    { label: "อย่างน้อย 8 ตัวอักษร", passed: password.value.length >= 8 },
    { label: "มีตัวพิมพ์ใหญ่", passed: /[A-Z]/.test(password.value) },
    { label: "มีตัวพิมพ์เล็ก", passed: /[a-z]/.test(password.value) },
    { label: "มีตัวเลข", passed: /\d/.test(password.value) },
    { label: "มีอักขระพิเศษ", passed: /[^A-Za-z0-9]/.test(password.value) },
  ]);
  const passwordIsValid = computed(() =>
    requirements.value.every((item) => item.passed),
  );
  const passwordsMatch = computed(
    () => confirmPassword.value.length > 0 && password.value === confirmPassword.value,
  );
  const canSubmit = computed(
    () => Boolean(invitationToken.value && passwordIsValid.value &&
      passwordsMatch.value && !loading.value),
  );

  async function handleSubmit() {
    submitted.value = true;
    errorMessage.value = "";
    if (!invitationToken.value) {
      errorMessage.value = "ลิงก์ตั้งรหัสผ่านไม่ถูกต้องหรือไม่มี Token";
      return;
    }
    if (!passwordIsValid.value) {
      errorMessage.value = "กรุณาตั้งรหัสผ่านให้ครบตามเงื่อนไข";
      return;
    }
    if (!passwordsMatch.value) {
      errorMessage.value = "รหัสผ่านทั้งสองช่องไม่ตรงกัน";
      return;
    }
    loading.value = true;
    try {
      await setupStaffPassword(invitationToken.value, password.value);
      success.value = true;
      password.value = "";
      confirmPassword.value = "";
    } catch (error) {
      errorMessage.value =
        [400, 410].includes(error.status)
          ? "ลิงก์ตั้งรหัสผ่านไม่ถูกต้องหรือหมดอายุแล้ว"
          : error.status === 404
            ? "ระบบตั้งรหัสผ่านยังไม่พร้อมใช้งาน"
            : error.message || "ไม่สามารถตั้งรหัสผ่านได้ กรุณาลองใหม่";
    } finally {
      loading.value = false;
    }
  }

  return {
    password, confirmPassword, showPassword, showConfirmPassword,
    loading, submitted, success, errorMessage, invitationToken, invitedEmail,
    requirements, passwordsMatch, canSubmit, handleSubmit,
    goToLogin: () => router.push("/staff-login"),
  };
}
