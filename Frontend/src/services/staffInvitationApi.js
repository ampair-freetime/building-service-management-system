const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1"
).replace(/\/+$/, "");

export async function validateStaffInvitation(token) {
  const response = await fetch(`${API_BASE_URL}/auth/activation/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(body.detail || "ไม่สามารถตรวจสอบลิงก์คำเชิญได้");
    error.status = response.status;
    throw error;
  }
  return body.valid === true;
}

export async function setupStaffPassword(token, password) {
  const response = await fetch(`${API_BASE_URL}/auth/setup-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, password }),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(body.detail || "ไม่สามารถตั้งรหัสผ่านได้");
    error.status = response.status;
    throw error;
  }
  return body;
}
