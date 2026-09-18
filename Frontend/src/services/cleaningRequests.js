const API_BASE_URL = (import.meta.env?.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1")
  .replace(/\/+$/, "");
const CLEANING_REQUEST_URL = import.meta.env?.VITE_CLEANING_REQUEST_URL
  || `${API_BASE_URL}/guest/cleaning-requests`;

export async function uploadCleaningRequest(payload, {
  requestId,
  endpoint = CLEANING_REQUEST_URL,
  fetchImpl = fetch,
  timeoutMs = 60_000,
} = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetchImpl(endpoint, {
      method: "POST",
      headers: { "Idempotency-Key": requestId },
      body: payload,
      signal: controller.signal,
    });
    const body = await response.json().catch(() => null);
    if (!response.ok) {
      const detail = body?.detail;
      const message = typeof detail === "string" ? detail
        : Array.isArray(detail) ? detail.map(issue => issue.msg).filter(Boolean).join(" / ") : "";
      throw new Error(message || (response.status === 413
        ? "ไฟล์แนบมีขนาดรวมเกินที่ระบบรองรับ กรุณาลดจำนวนหรือขนาดรูปแล้วลองใหม่"
        : "ส่งคำขอไม่สำเร็จ ข้อมูลและรูปยังอยู่ กรุณาลองส่งอีกครั้ง"));
    }
    // Require a receipt: an HTML fallback or empty response is not confirmation.
    if (!body?.request_code || typeof body.request_code !== "string") {
      throw new Error("ยังยืนยันผลการบันทึกไม่ได้ กรุณาลองส่งอีกครั้งด้วยข้อมูลเดิม");
    }
    return body;
  } catch (error) {
    if (controller.signal.aborted) {
      throw new Error("การส่งใช้เวลานานเกินไป ยังยืนยันผลไม่ได้ กรุณาลองส่งอีกครั้งด้วยข้อมูลเดิม");
    }
    if (error instanceof TypeError) {
      throw new Error("เชื่อมต่อระบบไม่ได้ กรุณาตรวจสอบอินเทอร์เน็ตแล้วลองส่งอีกครั้ง");
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}
