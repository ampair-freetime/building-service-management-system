// Configure this endpoint after the backend exposes the repair-request contract.
export async function uploadRepairRequest(payload, {
  requestId,
  endpoint = import.meta.env?.VITE_REPAIR_REQUEST_URL,
  fetchImpl = fetch,
  timeoutMs = 60_000,
} = {}) {
  if (!endpoint) {
    throw new Error("ระบบรับคำขอซ่อมยังไม่พร้อมใช้งาน ข้อมูลและรูปยังอยู่ในหน้านี้ กรุณาลองใหม่ภายหลัง");
  }

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
      const message = typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((issue) => issue.msg).filter(Boolean).join(" / ")
          : "";
      throw new Error(message || (response.status === 413
        ? "ไฟล์แนบมีขนาดรวมเกินที่ระบบรองรับ กรุณาลดจำนวนหรือขนาดรูปแล้วลองใหม่"
        : "ส่งคำขอซ่อมไม่สำเร็จ ข้อมูลและรูปยังอยู่ กรุณาลองส่งอีกครั้ง"));
    }
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
