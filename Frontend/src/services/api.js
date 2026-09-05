const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

export async function createLostItem(payload) {
  const response = await fetch(`${API_BASE_URL}/lost-found/lost-items`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || "ไม่สามารถส่งรายการของหายได้")
  }

  return response.json()
}

