import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  confirmPasswordReset,
  validatePasswordResetToken,
} from "../../services/staffPasswordResetApi.js";
import { passwordRequirements } from "../../services/passwordRules.js";

const INVALID_LINK_MESSAGE =
  "ลิงก์รีเซ็ตรหัสผ่านไม่ถูกต้อง หมดอายุ หรือถูกใช้ไปแล้ว กรุณาขอลิงก์ใหม่จากหน้าเข้าสู่ระบบ";

export function useStaffResetPassword() {
  const route = useRoute();
  const router = useRouter();
  // อ่าน token ครั้งเดียวแล้วเก็บไว้ในหน่วยความจำเท่านั้น (ไม่เก็บใน localStorage)
  const resetToken = ref(typeof route.query.token === "string" ? route.query.token.trim() : "");
  const password = ref("");
  const confirmPassword = ref("");
  const showPassword = ref(false);
  const showConfirmPassword = ref(false);
  const loading = ref(false);
  const submitted = ref(false);
  const success = ref(false);
  const errorMessage = ref("");
  const checkingLink = ref(false);
  const linkValid = ref(false);
  const linkError = ref("");

  onMounted(async () => {
    // ลบ token ออกจาก URL เพื่อไม่ให้ค้างในประวัติเบราว์เซอร์หรือถูกแนบไปกับ Referer
    if (route.query.token !== undefined) {
      const { token: _token, ...query } = route.query;
      router.replace({ query });
    }
    if (!resetToken.value) {
      linkError.value = "ลิงก์นี้ไม่มี Token กรุณาเปิดลิงก์จากอีเมลรีเซ็ตรหัสผ่านอีกครั้ง";
      return;
    }
    checkingLink.value = true;
    try {
      linkValid.value = await validatePasswordResetToken(resetToken.value);
      if (!linkValid.value) linkError.value = INVALID_LINK_MESSAGE;
    } catch (error) {
      linkError.value = [400, 422].includes(error.status)
        ? INVALID_LINK_MESSAGE
        : "ไม่สามารถตรวจสอบลิงก์ได้ กรุณาเปิดลิงก์จากอีเมลอีกครั้ง";
    } finally {
      checkingLink.value = false;
    }
  });

  const requirements = computed(() => passwordRequirements(password.value));
  const passwordIsValid = computed(() => requirements.value.every((item) => item.passed));
  const passwordsMatch = computed(
    () => confirmPassword.value.length > 0 && password.value === confirmPassword.value,
  );
  const canSubmit = computed(
    () => Boolean(linkValid.value && passwordIsValid.value &&
      passwordsMatch.value && !loading.value),
  );

  async function handleSubmit() {
    submitted.value = true;
    errorMessage.value = "";
    if (!linkValid.value) {
      errorMessage.value = linkError.value || "กรุณารอการตรวจสอบลิงก์";
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
      await confirmPasswordReset(resetToken.value, password.value);
      success.value = true;
      linkValid.value = false;
      resetToken.value = "";
      password.value = "";
      confirmPassword.value = "";
      // session เดิมทุกเครื่องถูกตัดสิทธิ์แล้ว ล้าง token ที่อาจค้างในเครื่องนี้ด้วย
      localStorage.removeItem("buildingCareAccessToken");
      localStorage.removeItem("buildingCareStaff");
      localStorage.removeItem("buildingCareRole");
    } catch (error) {
      if (error.status === 400) {
        linkValid.value = false;
        linkError.value = INVALID_LINK_MESSAGE;
        errorMessage.value = INVALID_LINK_MESSAGE;
      } else if (error.status === 422) {
        errorMessage.value = "รหัสผ่านยังไม่ผ่านเงื่อนไข กรุณาตรวจสอบอีกครั้ง";
      } else {
        errorMessage.value = "ไม่สามารถตั้งรหัสผ่านใหม่ได้ กรุณาลองใหม่";
      }
    } finally {
      loading.value = false;
    }
  }

  return {
    password, confirmPassword, showPassword, showConfirmPassword,
    loading, submitted, success, errorMessage,
    checkingLink, linkValid, linkError,
    requirements, passwordsMatch, canSubmit, handleSubmit,
    goToLogin: () => router.push("/staff-login"),
  };
}
