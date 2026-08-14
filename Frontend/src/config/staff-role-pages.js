/**
 * เมนูและลำดับหน้าที่แต่ละ Role เข้าถึงได้
 * แต่ละ Role มีชุดหน้าและประวัติของตัวเอง ตัวสลับ Role มีไว้สำหรับ demo เท่านั้น
 */
export const STAFF_ROLE_PAGES = {
  housekeeper: [
    { id: "dashboard", label: "ภาพรวมงาน" },
    { id: "jobs", label: "คิวงานทำความสะอาด" },
    { id: "my-history", label: "ประวัติงานของฉัน" },
  ],
  technician: [
    { id: "dashboard", label: "ภาพรวมงาน" },
    { id: "jobs", label: "คิวงานแจ้งซ่อม" },
    { id: "my-history", label: "ประวัติงานของฉัน" },
  ],
  clerk: [
    { id: "dashboard", label: "ภาพรวมงาน" },
    { id: "lost", label: "ของหาย จุดรับฝาก และคำขอรับคืน" },
    { id: "my-history", label: "ประวัติงานของฉัน" },
  ],
  admin: [
    { id: "dashboard", label: "ภาพรวมระบบ" },
    { id: "jobs", label: "ศูนย์งานทั้งหมด" },
    { id: "lost", label: "ของหายและรับฝาก" },
    { id: "staff-overview", label: "ภาพรวมงาน Staff" },
    { id: "staff", label: "บัญชีเจ้าหน้าที่" },
    { id: "history", label: "ประวัติและรายการที่ลบ" },
    { id: "qr", label: "QR ประจำห้อง" },
    { id: "announcements", label: "ประกาศอาคาร" },
  ],
};

export function canRoleOpenPage(role, pageId) {
  return (STAFF_ROLE_PAGES[role] ?? []).some((page) => page.id === pageId);
}
