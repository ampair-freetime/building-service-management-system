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
    method: "GET",
    headers: authHeaders(),
  });
  return parseResponse(response, "ไม่สามารถโหลดการแจ้งเตือนได้");
}

/** บันทึกว่าการแจ้งเตือนหนึ่งรายการถูกอ่านแล้ว */
export async function markStaffNotificationRead(notificationId) {
  const response = await fetch(
    `${API_BASE_URL}/notifications/${encodeURIComponent(notificationId)}/read`,{
        method: "PATCH",
        headers: authHeaders() },
  );
  return parseResponse(response, "ไม่สามารถอัปเดตการแจ้งเตือนได้");
}

/** ให้แม่บ้านที่ login รับ Cleaning Task ที่ยังไม่มีผู้รับผิดชอบ */
export async function acceptCleaningTask(requestId) {
  const response = await fetch(
    `${API_BASE_URL}/cleaning-tasks/${encodeURIComponent(requestId)}/accept`,
    { method: "PATCH", headers: authHeaders() },
  );
  return parseResponse(response, "ไม่สามารถรับงานทำความสะอาดได้");
}

/** อัปเดต Cleaning Task ตามลำดับสถานะที่ Backend อนุญาต */
export async function updateCleaningTaskStatus(requestId, status) {
  const response = await fetch(
    `${API_BASE_URL}/cleaning-tasks/${encodeURIComponent(requestId)}/status`,
    {
      method: "PATCH",
      headers: {
        ...authHeaders(),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ status }),
    },
  );
  return parseResponse(response, "ไม่สามารถอัปเดตสถานะงานทำความสะอาดได้");
}
