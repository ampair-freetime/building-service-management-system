const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1"
).replace(/\/+$/, "");

export class TechnicianApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "TechnicianApiError";
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
    throw new TechnicianApiError(body.detail || fallbackMessage, response.status);
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

/** โหลดคิวงานซ่อมและรายละเอียดงานจาก Backend */
export async function getRepairRequests() {
  const response = await fetch(`${API_BASE_URL}/repair-requests`, {
    method: "GET",
    headers: authHeaders(),
  });
  return parseResponse(response, "ไม่สามารถโหลดรายการงานซ่อมได้");
}

export async function getRepairRequestDetail(requestId) {
  const response = await fetch(
    `${API_BASE_URL}/repair-requests/${encodeURIComponent(requestId)}`,
    { method: "GET", headers: authHeaders() },
  );
  return parseResponse(response, "ไม่สามารถโหลดรายละเอียดงานซ่อมได้");
}

/** บันทึกว่าการแจ้งเตือนหนึ่งรายการถูกอ่านแล้ว */
export async function markStaffNotificationRead(notificationId) {
  const response = await fetch(
    `${API_BASE_URL}/notifications/${encodeURIComponent(notificationId)}/read`,
    { method: "PATCH", headers: authHeaders() },
  );
  return parseResponse(response, "ไม่สามารถอัปเดตการแจ้งเตือนได้");
}

/** ให้ช่างที่ login รับ Repair Requests ที่ยังไม่มีผู้รับผิดชอบ */
export async function acceptRepairRequest(requestId) {
  const response = await fetch(
    `${API_BASE_URL}/repair-requests/${encodeURIComponent(requestId)}/accept`,
    { method: "PATCH", headers: authHeaders() },
  );
  return parseResponse(response, "ไม่สามารถรับงานซ่อมได้");
}

/** อัปเดต Repair Requests ตามลำดับสถานะที่ Backend อนุญาต */
export async function updateRepairRequestStatus(requestId, status) {
  const response = await fetch(
    `${API_BASE_URL}/repair-requests/${encodeURIComponent(requestId)}/status`,
    {
      method: "PATCH",
      headers: {
        ...authHeaders(),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ status }),
    },
  );
  return parseResponse(response, "ไม่สามารถอัปเดตสถานะงานซ่อมได้");
}

/** งานซ่อมต้องปิดผ่าน endpoint แยกหลังเข้าสู่ in_progress */
export async function completeRepairRequest(requestId) {
  const response = await fetch(
    `${API_BASE_URL}/repair-requests/${encodeURIComponent(requestId)}/complete`,
    { method: "PATCH", headers: authHeaders() },
  );
  return parseResponse(response, "ไม่สามารถปิดงานซ่อมได้");
}

/** บันทึกหมายเหตุสรุปหลังงานเสร็จ */
export async function addRepairCompletionNote(requestId, note) {
  const response = await fetch(
    `${API_BASE_URL}/repair-requests/${encodeURIComponent(requestId)}/completion-note`,
    {
      method: "POST",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ note }),
    },
  );
  return parseResponse(response, "ไม่สามารถบันทึกหมายเหตุปิดงานได้");
}

/** อัปโหลดรูปหลังดำเนินการหนึ่งหรือหลายรูป */
export async function uploadRepairCompletionPhotos(requestId, files) {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  const response = await fetch(
    `${API_BASE_URL}/repair-requests/${encodeURIComponent(requestId)}/completion-photos`,
    {
      method: "POST",
      headers: authHeaders(),
      body: formData,
    },
  );
  return parseResponse(response, "ไม่สามารถอัปโหลดรูปหลังดำเนินการได้");
}

/** โหลดประวัติของ Repair request ที่คนปัจจุบันรับผิดชอบ */
export async function getRepairRequestHistory(requestId) {
  const response = await fetch(
    `${API_BASE_URL}/repair-requests/${encodeURIComponent(requestId)}/history`,
    { method: "GET", headers: authHeaders() },
  );
  return parseResponse(response, "ไม่สามารถโหลดประวัติงานได้");
}
