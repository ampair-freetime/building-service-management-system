const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1").replace(/\/+$/, "");

export class ClerkApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ClerkApiError";
    this.status = status;
  }
}

async function parseResponse(response, fallbackMessage) {
  const body = await response.json().catch(() => ({}));

  if (!response.ok) {
    const detail = body.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((issue) => issue.msg).filter(Boolean).join("\n")
          : fallbackMessage;
    throw new ClerkApiError(message, response.status);
  }

  return body;
}

export async function getPendingFoundItems() {
  const controller = new AbortController();

  try {
    const response = await fetch(
      `${API_BASE_URL}/lost-found/pending-found-items`,
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("buildingCareAccessToken") || ""}`,
        },
        signal: controller.signal,
      },
    );
    return await parseResponse(response, "ไม่สามารถโหลดรายงานของที่พบได้");
  } catch (error) {
    if (controller.signal.aborted) {
      throw new ClerkApiError("ใช้เวลาโหลดรายการนานเกินไป กรุณาลองใหม่");
    }
    if (error instanceof TypeError) {
      throw new ClerkApiError("เชื่อมต่อ Backend ไม่ได้ กรุณาลองใหม่");
    }
    throw error;
  }
}

export async function getFoundItemDetail(itemId) {
  const controller = new AbortController();

  try {
    const response = await fetch(
      `${API_BASE_URL}/lost-found/found-items/${encodeURIComponent(itemId)}`,
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("buildingCareAccessToken") || ""}`,
        },
        signal: controller.signal,
      },
    );
    return await parseResponse(
      response,
      "ไม่สามารถโหลดรายละเอียดของที่พบได้",
    );
  } catch (error) {
    if (controller.signal.aborted) {
      throw new ClerkApiError("ใช้เวลาโหลดรายละเอียดนานเกินไป กรุณาลองใหม่");
    }
    if (error instanceof TypeError) {
      throw new ClerkApiError("เชื่อมต่อ Backend ไม่ได้ กรุณาลองใหม่");
    }
    throw error;
  }
}

export async function getPendingLostItems() {
  const controller = new AbortController();

  try {
    const response = await fetch(
      `${API_BASE_URL}/lost-found/pending-lost-items`,
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("buildingCareAccessToken") || ""}`,
        },
        signal: controller.signal,
      },
    );
    return await parseResponse(
      response,
      "ไม่สามารถโหลดประกาศของหายที่รอตรวจสอบได้",
    );
  } catch (error) {
    if (controller.signal.aborted) {
      throw new ClerkApiError("ใช้เวลาโหลดประกาศของหายนานเกินไป กรุณาลองใหม่");
    }
    if (error instanceof TypeError) {
      throw new ClerkApiError("เชื่อมต่อ Backend ไม่ได้ กรุณาลองใหม่");
    }
    throw error;
  } 
}

export async function getLostItemDetail(itemId) {
  const controller = new AbortController();

  try {
    const response = await fetch(
      `${API_BASE_URL}/lost-found/lost-items/${encodeURIComponent(itemId)}`,
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("buildingCareAccessToken") || ""}`,
        },
        signal: controller.signal,
      },
    );
    return await parseResponse(
      response,
      "ไม่สามารถโหลดรายละเอียดประกาศของหายได้",
    );
  } catch (error) {
    if (controller.signal.aborted) {
      throw new ClerkApiError("ใช้เวลาโหลดรายละเอียดนานเกินไป กรุณาลองใหม่");
    }
    if (error instanceof TypeError) {
      throw new ClerkApiError("เชื่อมต่อ Backend ไม่ได้ กรุณาลองใหม่");
    }
    throw error;
  }
}

export async function getPendingOwnershipRequests() {
  const controller = new AbortController();

  try{
    const response = await fetch(`${API_BASE_URL}/lost-found/`,{
      method : "GET",
      headers: {
          Authorization: `Bearer ${localStorage.getItem("buildingCareAccessToken") || ""}`,
        },
        signal: controller.signal,
    });
    return await parseResponse(
      response,
      "ไม่สามารถโหลดรายละเอียดประกาศของหายได้",
    );
  }catch (error) {
    if (controller.signal.aborted) {
      throw new ClerkApiError("ใช้เวลาโหลดคำขอนานเกินไป กรุณาลองใหม่",);
  }
  if (error instanceof TypeError) {
      throw new ClerkApiError("เชื่อมต่อ Backend ไม่ได้ กรุณาลองใหม่",);
    }
    throw error;
  }
}

export async function reviewFoundItem(itemId, status, reason) {
  const controller = new AbortController();

  try {
    const response = await fetch(
      `${API_BASE_URL}/lost-found/found-items/${encodeURIComponent(itemId)}/review`,
      {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${
            localStorage.getItem("buildingCareAccessToken") || ""
          }`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          status,
          reason,
        }),
        signal: controller.signal,
      },
    );

    return await parseResponse(
      response,
      "ไม่สามารถบันทึกผลการตรวจสอบได้",
    );
  } catch (error) {
    if (controller.signal.aborted) {
      throw new ClerkApiError(
        "ใช้เวลาบันทึกผลนานเกินไป กรุณาลองใหม่",
      );
    }

    if (error instanceof TypeError) {
      throw new ClerkApiError(
        "เชื่อมต่อ Backend ไม่ได้ กรุณาลองใหม่",
      );
    }
    throw error;
  }
}

export function approveFoundItem(itemId) {
  return reviewFoundItem(
    itemId,
    "approved",
    "ตรวจสอบข้อมูลแล้ว",
  );
}

export function rejectFoundItem(itemId, reason) {
  return reviewFoundItem(
    itemId,
    "rejected",
    reason,
  );
}
