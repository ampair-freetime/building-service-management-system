// ตัด / ท้าย URL เพื่อให้ต่อ path ได้โดยไม่เกิด // ระหว่าง base URL กับ endpoint
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1').replace(/\/+$/, '')

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
// ค้นหารายการของหายและพบของจาก guest API โดยใช้ search query และ type (lost, found, all)
export async function searchLostFoundItems({
  type = "all",
  search = "",
}) {
  // endpoint ของ guest API สำหรับ lost-items และ found-items
  const collections = {
    lost: "lost-items",
    found: "found-items",
  };
  // ถ้า type เป็น "all" ให้ค้นหาทั้ง lost และ found, ถ้าไม่ใช่ให้ค้นหาเฉพาะประเภทนั้น
  const types = type === "all" ? ["lost", "found"] : [type];

  // สร้าง query string สำหรับ search, limit, offset
  const params = new URLSearchParams({
    search: search.trim(),
    limit: "20",
    offset: "0",
  });
  // ใช้ Promise.all เพื่อรัน fetch ทั้งหมดพร้อมกัน และรอผลลัพธ์ทั้งหมด
  const results = await Promise.all(
    types.map(async (kind) => {
      const response = await fetch(
        `${API_BASE_URL}/guest/${collections[kind]}?${params}`,
      );

      if (!response.ok) {
        throw new Error("ไม่สามารถค้นหาประกาศได้");
      }

      return response.json();
    }),
  );
  // รวมผลลัพธ์จากทั้ง lost และ found items, เรียงตามวันที่สร้างใหม่สุด และรวม total ของแต่ละประเภท
  return {
    items: results
      .flatMap((result) => result.items)
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at)),
    total: results.reduce((sum, result) => sum + result.total, 0),
  };
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
