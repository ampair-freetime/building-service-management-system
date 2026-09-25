const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1"
).replace(/\/+$/, "");

const STAFF_ENDPOINT = `${API_BASE_URL}/staff`;

const STAFF_ROLE_LABELS = {
  housekeeper: "แม่บ้าน",
  technician: "ช่าง",
  clerk: "ธุรการ",
  admin: "แอดมิน",
};

function authHeaders(includeJson = false) {
  const headers = {
    Authorization: `Bearer ${localStorage.getItem("buildingCareAccessToken") || ""}`,
  };

  if (includeJson) headers["Content-Type"] = "application/json";
  return headers;
}

async function parseResponse(response, fallbackMessage) {
  const data = await response.json().catch(() => ({}));
  if (response.ok) return data;

  const detail = Array.isArray(data.detail)
    ? data.detail.map((item) => item.msg).join(", ")
    : data.detail;
  const error = new Error(detail || fallbackMessage);
  error.status = response.status;
  throw error;
}

export function toDashboardStaff(account) {
  return {
    name: account.full_name,
    id: account.id,
    email: account.email,
    role: STAFF_ROLE_LABELS[account.role] || account.role,
    zone: "-",
    status: account.status === "active" ? "ใช้งาน" : "พักงาน",
  };
}

export async function fetchStaffAccounts() {
  const response = await fetch(STAFF_ENDPOINT, {
    headers: authHeaders(),
  });
  const accounts = await parseResponse(response, "ไม่สามารถโหลดบัญชีเจ้าหน้าที่ได้");
  return accounts.map(toDashboardStaff);
}

export async function createStaffAccount(payload) {
  const response = await fetch(STAFF_ENDPOINT, {
    method: "POST",
    headers: authHeaders(true),
    body: JSON.stringify(payload),
  });
  return parseResponse(response, "สร้างบัญชีไม่สำเร็จ");
}
