const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1"
).replace(/\/+$/, "");

const ENDPOINT = `${API_BASE_URL}/clerk-work-overview`;

function authHeaders() {
  return { Authorization: `Bearer ${localStorage.getItem("buildingCareAccessToken") || ""}` };
}

function filtersQuery(filters = {}) {
  const params = new URLSearchParams();
  if (filters.dateFrom) params.set("date_from", filters.dateFrom);
  if (filters.dateTo) params.set("date_to", filters.dateTo);
  if (filters.announcementType) params.set("announcement_type", filters.announcementType);
  return params;
}

async function readResponse(response) {
  const body = await response.json().catch(() => ({}));
  if (response.ok) return body;
  const detail = body.detail;
  const message = typeof detail === "string"
    ? detail
    : "ไม่สามารถโหลดข้อมูลภาพรวมงานอนุมัติได้";
  const error = new Error(message);
  error.status = response.status;
  throw error;
}

export async function fetchAdminClerkOverview(filters) {
  const query = filtersQuery(filters).toString();
  return readResponse(await fetch(`${ENDPOINT}${query ? `?${query}` : ""}`, {
    headers: authHeaders(),
  }));
}

export async function fetchAdminClerkAnnouncements(metric, filters) {
  const params = filtersQuery(filters);
  params.set("metric", metric);
  return readResponse(await fetch(`${ENDPOINT}/announcements?${params}`, {
    headers: authHeaders(),
  }));
}
