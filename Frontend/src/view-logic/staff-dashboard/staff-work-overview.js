const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1"
).replace(/\/+$/, "");

const ENDPOINT = `${API_BASE_URL}/staff-work-overview`;

function headers() {
  return { Authorization: `Bearer ${localStorage.getItem("buildingCareAccessToken") || ""}` };
}

async function readResponse(response) {
  const body = await response.json().catch(() => ({}));
  if (response.ok) return body;
  const error = new Error(typeof body.detail === "string" ? body.detail : "ไม่สามารถโหลดสถิติงานได้");
  error.status = response.status;
  throw error;
}

export async function fetchStaffWorkOverview({ role = "all", search = "" } = {}) {
  const params = new URLSearchParams();
  if (role === "แม่บ้าน") params.set("role", "cleaning");
  if (role === "ช่าง") params.set("role", "repair");
  if (search.trim()) params.set("search", search.trim());
  const query = params.toString();
  return readResponse(await fetch(`${ENDPOINT}${query ? `?${query}` : ""}`, { headers: headers() }));
}

export async function fetchStaffCurrentWork(staffId) {
  return readResponse(await fetch(
    `${ENDPOINT}/${encodeURIComponent(staffId)}/current-work`,
    { headers: headers() },
  ));
}
