const serviceStatus = {
  waiting: {
    label: "รอเจ้าหน้าที่รับเรื่อง",
    className: "wait",
    description: "ระบบรับคำร้องแล้ว และกำลังรอเจ้าหน้าที่ตรวจสอบ",
  },
  in_progress: {
    label: "กำลังดำเนินการ",
    className: "progress",
    description: "เจ้าหน้าที่กำลังดำเนินการตามคำร้อง",
  },
  completed: {
    label: "ดำเนินการเสร็จสิ้น",
    className: "done",
    description: "เจ้าหน้าที่ดำเนินการตามคำร้องเสร็จสิ้นแล้ว",
  },
};

const lostFoundStatus = {
  pending: { label: "รอเจ้าหน้าที่ตรวจสอบ", className: "wait" },
  approved: { label: "เผยแพร่แล้ว", className: "done" },
  claimed: { label: "มีผู้ขอรับคืน", className: "progress" },
  closed: { label: "ปิดประกาศแล้ว", className: "done" },
  rejected: { label: "ไม่อนุมัติ", className: "not-found" },
};

const serviceStatusAliases = {
  "รอเจ้าหน้าที่ตรวจสอบ": "waiting",
  "รอเจ้าหน้าที่รับเรื่อง": "waiting",
  "รอรับงาน": "waiting",
  // หากข้อมูลเดิมยังมีสถานะขั้นกลาง ให้รวมเป็นกำลังดำเนินการใน UI สามขั้น
  assigned: "in_progress",
  "มอบหมายเจ้าหน้าที่แล้ว": "in_progress",
  "รับงานแล้ว": "in_progress",
  "กำลังดำเนินการ": "in_progress",
  "ดำเนินการเสร็จสิ้น": "completed",
  "เสร็จสิ้น": "completed",
};

export const SERVICE_PROGRESS_STEPS = [
  { status: "waiting", label: "รับคำร้อง" },
  { status: "in_progress", label: "กำลังดำเนินการ" },
  { status: "completed", label: "เสร็จสิ้น" },
];

export const LOST_FOUND_PROGRESS_STEPS = [
  { status: "pending", label: "รับแจ้ง" },
  { status: "approved", label: "ตรวจสอบ/เผยแพร่" },
  { status: "closed", label: "เสร็จสิ้น" },
];

export function serviceTypeForRequest(item = {}, code = "") {
  const type = String(item.serviceType || item.request_type || "").toLowerCase();
  if (type === "cleaning" || type === "repair") return type;

  const normalizedCode = String(code).toUpperCase();
  if (
    normalizedCode.startsWith("CLN-") ||
    normalizedCode.startsWith("CLEAN-")
  ) return "cleaning";
  if (normalizedCode.startsWith("REPAIR-")) return "repair";

  const requestType = String(item.requestType || "");
  if (requestType.includes("ทำความสะอาด")) return "cleaning";
  if (requestType.includes("ซ่อม")) return "repair";
  return "";
}

export function normalizedServiceStatus(status) {
  const value = String(status || "").trim();
  return serviceStatusAliases[value] || value.toLowerCase() || "waiting";
}

export function requestStatusPresentation(item = {}, code = "") {
  const serviceType = serviceTypeForRequest(item, code);
  if (serviceType) {
    const status = normalizedServiceStatus(item.status);
    const presentation = serviceStatus[status];
    if (presentation) return { ...presentation, status, serviceType, isService: true };
  }

  const status = String(item.status || "").toLowerCase();
  const presentation = lostFoundStatus[status];
  if (presentation) return { ...presentation, status, isService: false };

  return {
    status,
    label: item.status || "–",
    className: item.statusClass || "wait",
    description: "",
    serviceType,
    isService: Boolean(serviceType),
  };
}

export function serviceProgress(item = {}, code = "") {
  const presentation = requestStatusPresentation(item, code);
  if (!presentation.isService) return null;

  const currentIndex = SERVICE_PROGRESS_STEPS.findIndex(
    (step) => step.status === presentation.status,
  );
  return {
    currentIndex: currentIndex < 0 ? 0 : currentIndex,
    steps: SERVICE_PROGRESS_STEPS,
  };
}

export function requestProgress(item = {}, code = "") {
  const service = serviceProgress(item, code);
  if (service) return service;

  const status = String(item.status || "").toLowerCase();
  const currentIndex = {
    pending: 0,
    approved: 1,
    claimed: 1,
    closed: 2,
    rejected: 2,
  }[status];
  if (currentIndex === undefined) return null;

  const normalizedCode = String(code).toUpperCase();
  const reportType = String(item.report_type || "").toLowerCase() ||
    (normalizedCode.startsWith("LOST-")
      ? "lost"
      : normalizedCode.startsWith("FOUND-")
        ? "found"
        : "");
  const completionLabel =
    reportType === "lost"
      ? "พบของแล้ว"
      : reportType === "found"
        ? "คืนเจ้าของแล้ว"
        : "เสร็จสิ้น";
  const lostFoundSteps = [
    LOST_FOUND_PROGRESS_STEPS[0],
    LOST_FOUND_PROGRESS_STEPS[1],
    { ...LOST_FOUND_PROGRESS_STEPS[2], label: completionLabel },
  ];

  return {
    currentIndex,
    steps:
      status === "rejected"
        ? [
            LOST_FOUND_PROGRESS_STEPS[0],
            LOST_FOUND_PROGRESS_STEPS[1],
            { status: "rejected", label: "ไม่อนุมัติ" },
          ]
        : lostFoundSteps,
  };
}
