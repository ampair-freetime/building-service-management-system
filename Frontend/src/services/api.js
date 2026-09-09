// ตัด / ท้าย URL เพื่อให้ต่อ path ได้โดยไม่เกิด // ระหว่าง base URL กับ endpoint
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1').replace(/\/+$/, '')

export async function createLostItem(payload) {
  // ยกเลิกการรอทั้ง request และ response body เมื่อครบ 30 วินาที เพื่อให้ฟอร์มคืนปุ่มส่ง
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 30_000)
  try {
    const response = await fetch(`${API_BASE_URL}/guest/lost-items`, {
      method: "POST",
      // payload เป็น FormData: ให้เบราว์เซอร์ตั้ง Content-Type พร้อม multipart boundary เอง
      body: payload,
      signal: controller.signal,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      // FastAPI ส่ง detail ได้ทั้งข้อความ และรายการ validation errors (422) จึงรวมเป็นข้อความก่อนแสดง
      const detail = error.detail
      const message = typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((issue) => issue.msg).filter(Boolean).join("\n")
          : ""
      throw new Error(message || "ไม่สามารถส่งรายการของหายได้")
    }

    // await เพื่อให้ finally ล้าง timer หลังอ่าน response body เสร็จแล้วเท่านั้น
    return await response.json()
  } catch (error) {
    if (controller.signal.aborted) {
      throw new Error("เซิร์ฟเวอร์ไม่ตอบกลับภายใน 30 วินาที ยังยืนยันไม่ได้ว่าบันทึกสำเร็จ กรุณาตรวจสอบกับเจ้าหน้าที่ก่อนส่งซ้ำ")
    }
    if (error instanceof TypeError) {
      throw new Error("เชื่อมต่อเซิร์ฟเวอร์ไม่ได้ กรุณาตรวจสอบการเชื่อมต่อและสถานะ Backend")
    }
    throw error
  } finally {
    clearTimeout(timeout)
  }
}

export async function createFoundItem(payload) {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 30_000)

  try {
    const response = await fetch(`${API_BASE_URL}/guest/found-items`, {
      method: "POST",
      body: payload,
      signal: controller.signal,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      const detail = error.detail
      const message = typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((issue) => issue.msg).filter(Boolean).join("\n")
          : ""
      throw new Error(message || "ไม่สามารถส่งรายการพบของได้")
    }

    return await response.json()
  } catch (error) {
    if (controller.signal.aborted) {
      throw new Error("เซิร์ฟเวอร์ไม่ตอบกลับภายใน 30 วินาที ยังยืนยันไม่ได้ว่าบันทึกสำเร็จ กรุณาตรวจสอบกับเจ้าหน้าที่ก่อนส่งซ้ำ")
    }
    if (error instanceof TypeError) {
      throw new Error("เชื่อมต่อเซิร์ฟเวอร์ไม่ได้ กรุณาตรวจสอบการเชื่อมต่อและสถานะ Backend")
    }
    throw error
  } finally {
    clearTimeout(timeout)
  }
}

export async function getLostFoundItem(itemCode, reportType) {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 15_000)
  const collection = reportType === "found" ? "found-items" : "lost-items"

  try {
    const response = await fetch(
      `${API_BASE_URL}/guest/${collection}/${encodeURIComponent(itemCode)}`,
      { signal: controller.signal },
    )

    if (response.status === 404) return null

    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(
        typeof error.detail === "string"
          ? error.detail
          : "ไม่สามารถโหลดรายละเอียดรายการได้",
      )
    }

    return await response.json()
  } catch (error) {
    if (controller.signal.aborted) {
      throw new Error("ใช้เวลาโหลดรายละเอียดนานเกินไป กรุณาลองใหม่")
    }
    if (error instanceof TypeError) {
      throw new Error("เชื่อมต่อเซิร์ฟเวอร์ไม่ได้ กรุณาลองใหม่")
    }
    throw error
  } finally {
    clearTimeout(timeout)
  }
}
