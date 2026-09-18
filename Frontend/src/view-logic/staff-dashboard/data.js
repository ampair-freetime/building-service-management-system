/**
 * สร้าง state เริ่มต้นสำหรับ Staff Dashboard
 * เก็บเฉพาะ configuration ของหน้าจอและ collection ว่างเท่านั้น
 * ข้อมูลรายการจริงต้องถูกโหลดจาก Backend ภายใน useStaffDashboard.js
 */
export function createStaffDashboardData() {
  // ข้อความ สี และเมนูประจำ role เป็น UI configuration ไม่ใช่ข้อมูลจำลอง
  const roleConfig = {
    housekeeper: {
      label: "แม่บ้าน",
      name: "แม่บ้าน",
      staffId: "-",
      avatar: "HK",
      color: "#159a75",
      soft: "#e6f6f1",
      eyebrow: "Housekeeping shift",
      hero: "รับงานจากคิวแม่บ้านร่วม แล้วดูแลงานของตัวเองจนปิดงาน",
      text: "งานทำความสะอาดจากผู้ใช้อาคารจะเข้าคิวแม่บ้านร่วม ทุกคนเห็นได้ แต่ต้องกดรับงานก่อนจึงอัปเดตสถานะและแนบความคืบหน้าได้",
      queue: "คิวรับงานรวมของแม่บ้าน",
      jobTitle: "ศูนย์รับงานรวมของแม่บ้าน",
      jobSubtitle: "กรองตามประเภทที่ผู้ใช้เลือก แล้วรับงานจากคิวกลางของแม่บ้าน",
      primary: "เปิดคิวรับงานแม่บ้าน",
    },
    technician: {
      label: "ช่าง",
      name: "ช่าง",
      staffId: "-",
      avatar: "TC",
      color: "#f97316",
      soft: "#fff0e6",
      eyebrow: "Maintenance shift",
      hero: "รับงานจากคิวช่างร่วม แล้วติดตามการตรวจ ซ่อม และรออะไหล่",
      text: "งานซ่อมจะเข้าคิวช่างร่วมตามประเภทที่ผู้ใช้เลือก ช่างทุกคนเห็นได้และกดรับงานที่เหมาะกับความเชี่ยวชาญของตัวเอง",
      queue: "คิวรับงานรวมของช่าง",
      jobTitle: "ศูนย์รับงานรวมของช่าง",
      jobSubtitle: "กรองประเภทปัญหาที่ผู้ใช้เลือก และรับงานจากคิวกลางของช่าง",
      primary: "เปิดคิวรับงานช่าง",
    },
    clerk: {
      label: "ธุรการ",
      name: "ธุรการ",
      staffId: "-",
      avatar: "OF",
      color: "#2563eb",
      soft: "#e8f0ff",
      eyebrow: "Lost & found desk",
      hero: "อนุมัติหรือไม่อนุมัติรายการ พร้อมจัดการคำขอรับของอย่างเป็นขั้นตอน",
      text: "จัดการของที่รับฝากและประกาศตามหาโดยมีผลอนุมัติหรือไม่อนุมัติชัดเจน พร้อมเปลี่ยนสถานะคำขอรับของและบันทึกเหตุผลทุกครั้ง",
      queue: "รายการที่รออนุมัติและคำขอรับของ",
      jobTitle: "",
      jobSubtitle: "",
      primary: "ตรวจคำขอรับของ",
    },
    admin: {
      label: "แอดมิน",
      name: "แอดมิน",
      staffId: "-",
      avatar: "AD",
      color: "#6757d9",
      soft: "#efedff",
      eyebrow: "Admin command center",
      hero: "เห็นคิวงานทั้งหมด จัดการสิทธิ์ และควบคุมโครงสร้างห้องจากจุดเดียว",
      text: "เข้าถึงงานแม่บ้าน งานช่าง ของหาย–ของได้คืน บัญชี Staff และ QR ห้อง พร้อมมอบหมายหรือแก้ไขข้อมูลตามสิทธิ์แอดมิน",
      queue: "คิวงานรวมที่ยังไม่มีผู้รับผิดชอบ",
      jobTitle: "ศูนย์งานทั้งหมดในระบบ",
      jobSubtitle: "ดูคิวของแม่บ้านและช่าง กรองตามประเภท และจัดการทุกงาน",
      primary: "เปิดศูนย์งานทั้งหมด",
    },
  };

  // ชื่อจริงของผู้ใช้งานปัจจุบันจะถูกแทนค่าจาก buildingCareStaff หลัง login
  const currentUserName = {
    housekeeper: "แม่บ้าน",
    technician: "ช่าง",
    clerk: "ธุรการ",
    admin: "แอดมิน",
  };

  // ข้อมูลจริงจะถูกเติมจาก API เท่านั้น
  const allJobs = [];
  const staffData = [];
  const lostSets = {
    inventory: [],
    lostposts: [],
    claims: [],
  };
  const deletedRecords = [];
  const auditHistory = [];
  const workHistory = [];
  const notificationSets = {
    housekeeper: [],
    technician: [],
    clerk: [],
    admin: [],
  };
  const announcements = [];

  // ตัวเลือกหมวดหมู่เป็นค่าคงที่ของฟอร์ม ไม่ใช่ข้อมูลรายการ
  const categories = {
    housekeeper: [
      "all",
      "พื้นเปียก/คราบสกปรก",
      "ขยะ/กลิ่น",
      "ห้องน้ำ/อุปกรณ์สิ้นเปลือง",
      "ทำความสะอาดทั่วไป",
    ],
    technician: [
      "all",
      "เครื่องปรับอากาศ",
      "ไฟฟ้า/แสงสว่าง",
      "ประปา/สุขาภิบาล",
      "อาคาร/เฟอร์นิเจอร์",
    ],
    admin: [
      "all",
      "พื้นเปียก/คราบสกปรก",
      "ขยะ/กลิ่น",
      "ห้องน้ำ/อุปกรณ์สิ้นเปลือง",
      "ทำความสะอาดทั่วไป",
      "เครื่องปรับอากาศ",
      "ไฟฟ้า/แสงสว่าง",
      "ประปา/สุขาภิบาล",
      "อาคาร/เฟอร์นิเจอร์",
    ],
  };

  return {
    roleConfig,
    currentUserName,
    allJobs,
    staffData,
    lostSets,
    deletedRecords,
    auditHistory,
    workHistory,
    selectedOverviewStaff: "",
    currentHistoryView: "activity",
    notificationSets,
    announcements,
    categories,
  };
}
