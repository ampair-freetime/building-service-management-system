const API_BASE_URL = (
  import.meta.env?.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1"
).replace(/\/+$/, "");

const STAFF_ENDPOINT = `${API_BASE_URL}/staff`;
const DELIVERY_CACHE_KEY = "buildingCareInvitationDeliveryResults";

function readDeliveryCache() {
  try {
    const value = JSON.parse(localStorage.getItem(DELIVERY_CACHE_KEY) || "{}");
    return value && typeof value === "object" && !Array.isArray(value) ? value : {};
  } catch {
    return {};
  }
}

export function rememberInvitationDelivery(account, status) {
  if (!account?.id || !account?.email || !["sent", "failed"].includes(status)) return;
  try {
    const cache = readDeliveryCache();
    cache[account.id] = {
      email: account.email.toLowerCase(),
      status,
      recordedAt: new Date().toISOString(),
    };
    localStorage.setItem(DELIVERY_CACHE_KEY, JSON.stringify(cache));
  } catch {
    // Browser storage can be unavailable; the current page can still show the result.
  }
}

export function forgetInvitationDelivery(staffId) {
  try {
    const cache = readDeliveryCache();
    delete cache[staffId];
    localStorage.setItem(DELIVERY_CACHE_KEY, JSON.stringify(cache));
  } catch {
    // Deletion on the server has already succeeded.
  }
}

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
  const serverStatus = account.invitation_delivery_status ||
    (account.email_sent === true ? "sent" : account.email_sent === false ? "failed" : null);
  const cached = readDeliveryCache()[account.id];
  const cachedStatus = cached?.email === String(account.email).toLowerCase() &&
    ["sent", "failed"].includes(cached.status) ? cached.status : null;
  return {
    name: account.full_name,
    id: account.id,
    email: account.email,
    role: STAFF_ROLE_LABELS[account.role] || account.role,
    zone: "-",
    isActivated: account.is_activated === true,
    status: account.status === "active" ? "ใช้งาน" : "พักงาน",
    invitationDeliveryStatus: serverStatus || cachedStatus || "unknown",
    invitationStatusSource: serverStatus ? "server" : cachedStatus ? "browser" : "none",
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

export async function updateStaffProfile(staffId, changes) {
  const response = await fetch(`${STAFF_ENDPOINT}/${encodeURIComponent(staffId)}`, {
    method: "PATCH",
    headers: authHeaders(true),
    body: JSON.stringify(changes),
  });
  return parseResponse(response, "บันทึกข้อมูล Staff ไม่สำเร็จ");
}

export function toUpdatedDashboardStaff(previous, account) {
  const emailChanged = previous.email !== account.email;
  if (emailChanged) forgetInvitationDelivery(account.id);
  const updated = toDashboardStaff(account);
  if (!emailChanged) {
    updated.invitationDeliveryStatus = previous.invitationDeliveryStatus;
    updated.invitationStatusSource = previous.invitationStatusSource;
  }
  return updated;
}

export async function resendStaffInvitation(staffId) {
  const response = await fetch(
    `${STAFF_ENDPOINT}/${encodeURIComponent(staffId)}/resend-invitation`,
    { method: "POST", headers: authHeaders() },
  );
  return parseResponse(response, "ไม่สามารถส่งคำเชิญซ้ำได้");
}

export async function deleteStaffAccount(staffId) {
  const response = await fetch(`${STAFF_ENDPOINT}/${encodeURIComponent(staffId)}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (response.ok) return;

  const body = await response.json().catch(() => ({}));
  const detail = body.detail;
  const message = typeof detail === "string"
    ? detail
    : typeof detail?.message === "string"
      ? detail.message
      : "ไม่สามารถลบบัญชีเจ้าหน้าที่ได้";
  const error = new Error(message);
  error.status = response.status;
  error.unfinishedAssignments = detail?.unfinished_assignments || [];
  throw error;
}
