const API_BASE_URL = (
  import.meta.env?.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1"
).replace(/\/+$/, "");

async function postJson(path, payload, fallbackMessage) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(typeof body.detail === "string" ? body.detail : fallbackMessage);
    error.status = response.status;
    throw error;
  }
  return body;
}

// Backend ตอบ 202 ข้อความเดียวกันทุกกรณี จึงไม่มีทางรู้ว่าอีเมลนี้มีบัญชีหรือไม่
export function requestPasswordReset(email) {
  return postJson(
    "/auth/password-reset-requests",
    { email },
    "ไม่สามารถส่งคำขอรีเซ็ตรหัสผ่านได้",
  );
}

export async function validatePasswordResetToken(token) {
  const body = await postJson(
    "/auth/password-reset/validate",
    { token },
    "ไม่สามารถตรวจสอบลิงก์รีเซ็ตรหัสผ่านได้",
  );
  return body.valid === true;
}

export function confirmPasswordReset(token, newPassword) {
  return postJson(
    "/auth/password-reset/confirm",
    { token, new_password: newPassword },
    "ไม่สามารถตั้งรหัสผ่านใหม่ได้",
  );
}
