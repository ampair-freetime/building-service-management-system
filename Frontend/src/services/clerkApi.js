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

export async function getApprovedLostFoundItems() {
  const params = new URLSearchParams({ limit: "200", offset: "0" });
  const [foundResponse, lostResponse] = await Promise.all([
    fetch(`${API_BASE_URL}/guest/found-items?${params}`),
    fetch(`${API_BASE_URL}/guest/lost-items?${params}`),
  ]);

  const found = await parseResponse(
    foundResponse,
    "ไม่สามารถโหลดรายการของที่รับฝากได้",
  );
  const lost = await parseResponse(
    lostResponse,
    "ไม่สามารถโหลดประกาศของหายได้",
  );

  return {
    foundItems: found.items || [],
    lostItems: lost.items || [],
  };
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

// โหลดคำร้องขอรับของคืนทั้งหมดที่รอให้เจ้าหน้าที่ตรวจสอบ
export async function getPendingOwnershipRequests() {
  const controller = new AbortController();

  try {
    const response = await fetch(
      `${API_BASE_URL}/lost-found/ownership-requests`,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("buildingCareAccessToken") || ""}`,
        },
        signal: controller.signal,
      },
    );

    return await parseResponse(
      response,
      "ไม่สามารถโหลดคำขอแสดงความเป็นเจ้าของได้",
    );
  } catch (error) {
    if (controller.signal.aborted) {
      throw new ClerkApiError("ใช้เวลาโหลดคำขอนานเกินไป กรุณาลองใหม่");
    }
    if (error instanceof TypeError) {
      throw new ClerkApiError("เชื่อมต่อ Backend ไม่ได้ กรุณาลองใหม่");
    }
    throw error;
  }
}

export async function getOwnershipRequestDetail(claimId) {
  const controller = new AbortController();

  try{
    const response = await fetch(`${API_BASE_URL}/lost-found/ownership-requests/${encodeURIComponent(claimId)}`,{
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

export async function approveOwnershipRequest(claimId) {
  const response = await fetch(
    `${API_BASE_URL}/lost-found/ownership-requests/${encodeURIComponent(claimId)}/approve`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${localStorage.getItem("buildingCareAccessToken") || ""}`,
      },
    },
  );

  return await parseResponse(response, "ไม่สามารถอนุมัติคำขอรับของได้");
}

export async function requestOwnershipAdditionalInfo(claimId, message) {
  const response = await fetch(
    `${API_BASE_URL}/lost-found/ownership-requests/${encodeURIComponent(claimId)}/request-additional-info`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${localStorage.getItem("buildingCareAccessToken") || ""}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message }),
    },
  );

  return await parseResponse(response, "ไม่สามารถขอข้อมูลเพิ่มเติมได้");
}

export async function updateOwnershipReturnStatus(claimId, returnStatus) {
  const response = await fetch(
    `${API_BASE_URL}/lost-found/ownership-requests/${encodeURIComponent(claimId)}/return-status`,
    {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${localStorage.getItem("buildingCareAccessToken") || ""}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ return_status: returnStatus }),
    },
  );

  return await parseResponse(response, "ไม่สามารถอัปเดตสถานะการคืนของได้");
}

export async function scheduleOwnershipPickup(claimId, appointment) {
  const response = await fetch(
    `${API_BASE_URL}/lost-found/ownership-requests/${encodeURIComponent(claimId)}/schedule-pickup`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${localStorage.getItem("buildingCareAccessToken") || ""}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        pickup_date: appointment.date,
        pickup_time: appointment.time,
        pickup_location: appointment.location,
        note: appointment.note || null,
      }),
    },
  );

  return await parseResponse(response, "ไม่สามารถสร้างนัดหมายรับของได้");
}


export async function approveFoundItem(itemId) {
  const response = await fetch(
    `${API_BASE_URL}/lost-found/found-items/${encodeURIComponent(itemId)}/approve`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${
          localStorage.getItem("buildingCareAccessToken") || ""
        }`,
      },
    },
  );

  return await parseResponse(response, "ไม่สามารถอนุมัติรายการได้");
}

export async function approveLostItemAnnouncement(itemId) {
  const response = await fetch(
    `${API_BASE_URL}/lost-found/lost-items/${encodeURIComponent(itemId)}/approve`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${
          localStorage.getItem("buildingCareAccessToken") || ""
        }`,
      },
    },
  );

  return await parseResponse(response, "ไม่สามารถอนุมัติประกาศของหายได้");
}

export async function rejectFoundItem(itemId, reason) {
  const response = await fetch(
    `${API_BASE_URL}/lost-found/found-items/${encodeURIComponent(itemId)}/reject`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${
          localStorage.getItem("buildingCareAccessToken") || ""
        }`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ reason }),
    },
  );

  return await parseResponse(response, "ไม่สามารถปฏิเสธรายการได้");
}

export async function rejectLostItemAnnouncement(itemId, reason) {
  const response = await fetch(
    `${API_BASE_URL}/lost-found/lost-items/${encodeURIComponent(itemId)}/reject`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${
          localStorage.getItem("buildingCareAccessToken") || ""
        }`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ reason }),
    },
  );

  return await parseResponse(
    response,
    "ไม่สามารถปฏิเสธประกาศของหายได้",
  );
}
