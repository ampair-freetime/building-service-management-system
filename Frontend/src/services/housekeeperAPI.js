const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1"
).replace(/\/+$/, "");

export class HousekeeperApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "HousekeeperApiError";
    this.status = status;
  }
}

function authHeaders() {
  return {
    Authorization: `Bearer ${localStorage.getItem("buildingCareAccessToken") || ""}`,
  };
}

async function parseResponse(response, fallbackMessage) {
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new HousekeeperApiError(body.detail || fallbackMessage, response.status);
  }
  return body;
}

/** โหลดการแจ้งเตือนของ Staff ที่กำลังเข้าสู่ระบบ */
export async function getStaffNotifications() {
  const response = await fetch(`${API_BASE_URL}/notifications`, {
    headers: authHeaders(),
  });
  return parseResponse(response, "ไม่สามารถโหลดการแจ้งเตือนได้");
}

/** บันทึกว่าการแจ้งเตือนหนึ่งรายการถูกอ่านแล้ว */
export async function markStaffNotificationRead(notificationId) {
  const response = await fetch(
    `${API_BASE_URL}/notifications/${encodeURIComponent(notificationId)}/read`,
    { method: "PATCH", headers: authHeaders() },
  );
  return parseResponse(response, "ไม่สามารถอัปเดตการแจ้งเตือนได้");
}