export function loadQrCodeLibrary() {
  if (window.QRCode) return Promise.resolve();

  return new Promise((resolve, reject) => {
    // ถ้ามี script ที่กำลังโหลดอยู่ ให้รออันเดิมแทนการเพิ่ม script ซ้ำ
    const existing = document.querySelector("script[data-qrcodejs]");
    if (existing) {
      existing.addEventListener("load", resolve, { once: true });
      existing.addEventListener("error", reject, { once: true });
      return;
    }

    const script = document.createElement("script");
    script.src =
      "https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js";
    script.defer = true;
    script.dataset.qrcodejs = "true";
    script.onload = resolve;
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

// ใช้วันที่ตามเวลาไทย เพราะการตัดวันที่จาก ISO UTC อาจได้วันก่อนหน้าในช่วงเช้ามืด
export function todayISO() {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Bangkok",
  }).format(new Date());
}

export function currentTimeHM() {
  return new Intl.DateTimeFormat("th-TH", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "Asia/Bangkok",
  })
    .format(new Date())
    .replace(".", ":");
}

// แปลงอักขระพิเศษก่อนนำข้อความไปแทรกใน HTML เพื่อไม่ให้ข้อความถูกตีความเป็นแท็ก
export function escapeHtml(value) {
  return String(value ?? "").replace(
    /[&<>"']/g,
    (character) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;",
      })[character]
  );
}

export function isTerminalStatus(status) {
  return [
    "เสร็จสิ้น",
    "คืนของแล้ว",
    "ปิดประกาศ",
    "ไม่อนุมัติรับฝาก",
    "ไม่อนุมัติเผยแพร่",
  ].some((value) => String(status).includes(value));
}

// ตรวจคำปฏิเสธก่อนคำว่าอนุมัติ เพราะ "ไม่อนุมัติ" มีคำว่า "อนุมัติ" อยู่ด้วย
export function badgeClass(status) {
  if (["ไม่อนุมัติ", "ข้อมูลไม่ตรง", "ลบแล้ว"].some((value) => status.includes(value)))
    return "danger";
  if (
    ["เสร็จสิ้น", "คืนของแล้ว", "อนุมัติ", "หลักฐานผ่าน", "กู้คืนแล้ว"].some(
      (value) => status.includes(value)
    )
  )
    return "done";
  if (["กำลัง", "รับงานแล้ว", "นัดรับ", "อาจพบ"].some((value) => status.includes(value)))
    return "progress";
  return "wait";
}

export function nowThai() {
  return new Intl.DateTimeFormat("th-TH", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date());
}

export function sourceLabel(source) {
  return (
    {
      jobs: "งานแม่บ้าน/ช่าง",
      lost: "ของหาย–ของได้คืน",
      staff: "บัญชี Staff",
      qr: "QR และห้อง",
      announcement: "ประกาศอาคาร",
    }[source] || source
  );
}

export function validImage(file) {
  return Boolean(
    file &&
      ["image/jpeg", "image/png", "image/webp"].includes(file.type) &&
      file.size <= 5242880
  );
}
