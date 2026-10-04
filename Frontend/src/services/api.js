import { sortLostFoundItems } from "./lostFoundSearch.js";

// ตัด / ท้าย URL เพื่อให้ต่อ path ได้โดยไม่เกิด // ระหว่าง base URL กับ endpoint
const API_BASE_URL = (import.meta.env?.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1').replace(/\/+$/, '')

// ส่งรายการของหายไปยัง guest API โดยใช้ FormData เป็น payload
export async function createLostItem(payload) {
  // ยกเลิกการรอทั้ง request และ response body เมื่อครบ 30 วินาที เพื่อให้ฟอร์มคืนปุ่มส่ง
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 30_000)
  try {
    const response = await fetch(`${API_BASE_URL}/guest/lost-items`, {
      method: "POST",
      // FormData ไม่ต้องตั้ง Content-Type เพราะ browser จะตั้งให้เอง
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

    // ถ้า response.ok เป็น true ให้ return response.json() เพื่อให้ caller ได้ข้อมูล JSON ของรายการที่สร้างสำเร็จ
    return await response.json()
    // ถ้า response.ok เป็น false จะ throw error และไปจับใน catch block ด้านล่าง
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
// ส่งรายการพบของไปยัง guest API โดยใช้ FormData เป็น payload
export async function createFoundItem(payload) {
  // ยกเลิกการรอทั้ง request และ response body เมื่อครบ 30 วินาที เพื่อให้ฟอร์มคืนปุ่มส่ง
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 30_000)
  // ส่ง request POST ไปยัง endpoint /guest/found-items ของ guest API
  try {
    const response = await fetch(`${API_BASE_URL}/guest/found-items`, {
      method: "POST",
      body: payload,
      signal: controller.signal,
    })
    // ถ้า response.ok เป็น false ให้ throw error พร้อมข้อความจาก response.json() หรือข้อความ default
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
    // ถ้า response.ok เป็น true ให้ return response.json() เพื่อให้ caller ได้ข้อมูล JSON ของรายการที่สร้างสำเร็จ
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
// ดึงรายละเอียดรายการของหายหรือพบของจาก guest API โดยใช้ itemCode และ reportType (lost หรือ found)
export async function getLostFoundItem(itemCode, reportType) {
  // ยกเลิกการรอทั้ง request และ response body เมื่อครบ 15 วินาที เพื่อให้ฟอร์มคืนปุ่มส่ง
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 15_000)
  const collection = reportType === "found" ? "found-items" : "lost-items"

  try {
    const response = await fetch(
      `${API_BASE_URL}/guest/${collection}/${encodeURIComponent(itemCode)}`,
      { signal: controller.signal },
    )
    // ถ้า response.status เป็น 404 ให้ return null เพื่อให้ caller รู้ว่าไม่พบรายการ
    if (response.status === 404) return null
    //  ถ้า response.ok เป็น false ให้ throw error พร้อมข้อความจาก response.json() หรือข้อความ default
    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(
        typeof error.detail === "string"
          ? error.detail
          : "ไม่สามารถโหลดรายละเอียดรายการได้",
      )
    }
    // ถ้า response.ok เป็น true ให้ return response.json() เพื่อให้ caller ได้ข้อมูล JSON ของรายการ
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
// โหลดทั้งสองประเภทครบก่อนส่งผล เพื่อไม่ให้ caller ใช้ข้อมูลเพียงครึ่งชุด
export async function fetchPublicLostFoundItems() {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30_000);
  try {
    const results = await Promise.all(
      ["lost-items", "found-items"].map(async (collection) => {
        const response = await fetch(`${API_BASE_URL}/guest/${collection}`, {
          signal: controller.signal,
        });
        if (!response.ok) throw new Error("ไม่สามารถโหลดประกาศได้ กรุณารีเฟรชอีกครั้ง");
        const result = await response.json();
        if (!Array.isArray(result.items) || result.total !== result.items.length) {
          throw new Error("ได้รับรายการประกาศไม่ครบ กรุณาลองใหม่");
        }
        return result;
      }),
    );
    const items = sortLostFoundItems(results.flatMap((result) => result.items));
    return { items, total: items.length };
  } catch (error) {
    const timedOut = controller.signal.aborted;
    controller.abort();
    if (timedOut) throw new Error("โหลดประกาศนานเกินไป กรุณารีเฟรชอีกครั้ง");
    if (error instanceof TypeError) throw new Error("เชื่อมต่อเซิร์ฟเวอร์ไม่ได้ กรุณาลองใหม่");
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

// ตรวจสอบสถานะของรายการของหายหรือพบของด้วยรหัสและอีเมลของผู้แจ้ง
export async function trackLostFoundItem(itemCode, reporterEmail) {
  // เลือก collection จาก prefix ของรหัสที่ backend สร้าง
  const normalizedCode = itemCode.trim().toUpperCase()

  let collection;

  if (normalizedCode.startsWith("LOST-")) {
    collection = "lost-items"
  } else if (normalizedCode.startsWith("FOUND-")) {
    collection = "found-items"
  } else {
    throw new Error("รหัสประกาศไม่ถูกต้อง")
  }
  // ส่งชื่อ query parameter ให้ตรงกับ reporter_email ของ backend
  const params = new URLSearchParams({
    reporter_email: reporterEmail.trim().toLowerCase(),
  });
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 15_000)

  try {
    // ส่ง request GET ไปยัง endpoint /guest/{collection}/{itemCode} ของ guest API พร้อม query string
    const response = await fetch(
      `${API_BASE_URL}/guest/${collection}/${encodeURIComponent(normalizedCode)}?${params}`,
      { signal: controller.signal },
    )

    if (response.status === 404) {
      return null
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(
        typeof error.detail === "string"
          ? error.detail
          : "ไม่สามารถโหลดรายละเอียดรายการได้",
      )
    }
    // Response มี item_code, report_type, item_name, status และ updated_at
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

// ดึงสถานะคำร้องแจ้งซ่อมหรือทำความสะอาดสำหรับผู้ใช้งานทั่วไป
export async function trackServiceRequest(
  requestCode,
  reporterEmail,
  { fetchImpl = fetch, timeoutMs = 15_000 } = {},
) {
  const normalizedCode = requestCode.trim().toUpperCase();
  const isCleaningCode =
    normalizedCode.startsWith("CLN-");
  const isRepairCode =
    normalizedCode.startsWith("RPR-");
  if (
    !isCleaningCode &&
    !isRepairCode
  ) {
    throw new Error("รหัสคำร้องบริการไม่ถูกต้อง");
  }

  const params = new URLSearchParams({
    reporter_email: reporterEmail.trim().toLowerCase(),
  });
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  const collection = normalizedCode.startsWith("CLN-")
    ? "cleaning-requests"
    : normalizedCode.startsWith("RPR-")
      ? "repair-requests"
    : "service-requests";

  try {
    const response = await fetchImpl(
      `${API_BASE_URL}/guest/${collection}/${encodeURIComponent(normalizedCode)}?${params}`,
      { signal: controller.signal },
    );
    if (response.status === 404) return null;
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(
        typeof error.detail === "string"
          ? error.detail
          : "ไม่สามารถโหลดสถานะคำร้องบริการได้",
      );
    }
    return await response.json();
  } catch (error) {
    if (controller.signal.aborted) {
      throw new Error("ใช้เวลาโหลดสถานะนานเกินไป กรุณาลองใหม่");
    }
    if (error instanceof TypeError) {
      throw new Error("เชื่อมต่อเซิร์ฟเวอร์ไม่ได้ กรุณาลองใหม่");
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

// ส่งคำขอรับสิ่งของคืนของ guest
export async function createFoundItemClaim(itemCode, payload) {
  const normalizedCode = itemCode.trim().toUpperCase();
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30_000);

  if (!normalizedCode.startsWith("FOUND-")) {
    throw new Error("สามารถขอรับคืนได้เฉพาะประกาศพบของ");
  }

  try {
    const response = await fetch(
      `${API_BASE_URL}/guest/found-items/${encodeURIComponent(normalizedCode)}/claims`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      },
    );

    const body = await response.json().catch(() => ({}));

    if (!response.ok) {
      // Backend ส่ง 404 เมื่อหารายการไม่พบ
      // และ 409 เมื่อรับคืนแล้วหรือมีคำขอซ้ำ
      const detail = body.detail;
      throw new Error(
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
            ? detail.map((issue) => issue.msg).filter(Boolean).join("\n")
            : "ไม่สามารถส่งคำขอรับคืนได้",
      );
    }

    return body;
  } catch (error) {
    if (controller.signal.aborted) {
      throw new Error("เซิร์ฟเวอร์ไม่ตอบกลับ กรุณาลองใหม่");
    }

    if (error instanceof TypeError) {
      throw new Error("เชื่อมต่อ Backend ไม่ได้ กรุณาลองใหม่");
    }

    throw error;
  } finally {
    clearTimeout(timeout);
  }
}
