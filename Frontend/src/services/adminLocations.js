// กำหนด URL หลักของ Admin Location API
const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1"
).replace(/\/+$/, "");

const ADMIN_LOCATIONS_URL = `${API_BASE_URL}/admin/locations`;

// สร้าง headers พร้อม access token ของ Admin
function authHeaders(includeJson = false) {
  const headers = {
    Authorization: `Bearer ${localStorage.getItem("buildingCareAccessToken") || ""}`,
  };
  if (includeJson) headers["Content-Type"] = "application/json";
  return headers;
}

// อ่าน JSON และแปลง API error เป็น Error
async function parseResponse(response, fallbackMessage) {
  const data = await response.json().catch(() => ({}));
  if (response.ok) return data;
  const detail = Array.isArray(data.detail)
    ? data.detail.map((item) => item.msg).filter(Boolean).join(", ")
    : data.detail;
  const error = new Error(detail || fallbackMessage);
  error.status = response.status;
  throw error;
}

// โหลดสถานที่ทั้งหมดรวมรายการที่ปิดใช้งาน
export async function fetchAdminLocations() {
  const response = await fetch(`${ADMIN_LOCATIONS_URL}?include_inactive=true`, {
    headers: authHeaders(),
  });
  return parseResponse(response, "ไม่สามารถโหลดรายการสถานที่ได้");
}

// สร้างสถานที่ใหม่จากชั้นและพื้นที่
export async function createAdminLocation(payload) {
  const response = await fetch(ADMIN_LOCATIONS_URL, {
    method: "POST",
    headers: authHeaders(true),
    body: JSON.stringify(payload),
  });
  return parseResponse(response, "ไม่สามารถเพิ่มสถานที่ได้");
}

// ขอให้ Backend สร้าง token และ URL ของ QR
export async function generateAdminLocationQr(locationId) {
  const response = await fetch(
    `${ADMIN_LOCATIONS_URL}/${encodeURIComponent(locationId)}/qr/generate`,
    {
      method: "POST",
      headers: authHeaders(),
    },
  );
  return parseResponse(response, "ไม่สามารถสร้าง QR Code ได้");
}

// เปิดหรือปิดใช้งานสถานที่โดยไม่ลบข้อมูล
export async function setAdminLocationActive(locationId, isActive) {
  const response = await fetch(
    `${ADMIN_LOCATIONS_URL}/${encodeURIComponent(locationId)}/status`,
    {
      method: "PATCH",
      headers: authHeaders(true),
      body: JSON.stringify({ is_active: isActive }),
    },
  );
  return parseResponse(response, "ไม่สามารถเปลี่ยนสถานะสถานที่ได้");
}
