import { computed, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { setupStaffPassword, validateStaffInvitation } from "../../services/staffInvitationApi.js";
import { passwordRequirements } from "../../services/passwordRules.js";

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
  const checkingLink = ref(false);
  const linkValid = ref(false);
  const linkError = ref("");
  const invitationToken = computed(() =>
    typeof route.query.token === "string" ? route.query.token.trim() : "",
  );
  const invitedEmail = computed(() =>
    typeof route.query.email === "string" ? route.query.email.trim() : "",
  );
  watch(invitationToken, async (token, _previous, onCleanup) => {
    let cancelled = false;
    onCleanup(() => { cancelled = true; });
    linkValid.value = false;
    linkError.value = "";
    if (!token) {
      checkingLink.value = false;
      linkError.value = "ลิงก์นี้ไม่มี Token กรุณาเปิดลิงก์จากอีเมลคำเชิญอีกครั้ง";
      return;
    }
    checkingLink.value = true;
    try {
      const valid = await validateStaffInvitation(token);
      if (!cancelled) {
        linkValid.value = valid;
        if (!valid) linkError.value = "ลิงก์คำเชิญไม่ถูกต้องหรือหมดอายุ กรุณาขอลิงก์ใหม่จากผู้ดูแลระบบ";
      }
    } catch (error) {
      if (!cancelled) {
        linkError.value = [400, 410, 422].includes(error.status)
          ? "ลิงก์คำเชิญไม่ถูกต้องหรือหมดอายุ กรุณาขอลิงก์ใหม่จากผู้ดูแลระบบ"
          : "ไม่สามารถตรวจสอบลิงก์คำเชิญได้ กรุณาลองเปิดหน้านี้อีกครั้ง";
      }
    } finally {
      if (!cancelled) checkingLink.value = false;
    }
  }, { immediate: true });

  const requirements = computed(() => passwordRequirements(password.value));
  const passwordIsValid = computed(() =>
    requirements.value.every((item) => item.passed),
  );
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
      errorMessage.value = linkError.value || "กรุณารอการตรวจสอบลิงก์คำเชิญ";
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
      linkValid.value = false;
      password.value = "";
      confirmPassword.value = "";
    } catch (error) {
      if ([400, 410].includes(error.status)) {
        linkValid.value = false;
        linkError.value = "ลิงก์คำเชิญไม่ถูกต้องหรือหมดอายุ กรุณาขอลิงก์ใหม่จากผู้ดูแลระบบ";
      }
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
    checkingLink, linkValid, linkError,
    requirements, passwordsMatch, canSubmit, handleSubmit,
    goToLogin: () => router.push("/staff-login"),
  };
}
