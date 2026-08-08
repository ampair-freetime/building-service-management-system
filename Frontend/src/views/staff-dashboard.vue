<script setup>
import { onMounted } from "vue";

function loadQrCodeLibrary() {
  if (window.QRCode) return Promise.resolve();

  return new Promise((resolve, reject) => {
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

onMounted(async () => {
  try {
    await loadQrCodeLibrary();
  } catch (error) {
    console.warn(
      "QR Code library could not be loaded. QR fallback will be used.",
      error
    );
  }

  const roleConfig = {
    housekeeper: {
      label: "แม่บ้าน",
      name: "อรทัย แม่บ้าน",
      staffId: "STF-001",
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
      name: "ธีรภัทร ช่างอาคาร",
      staffId: "STF-004",
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
      name: "ชนาภา ธุรการ",
      staffId: "STF-006",
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
      name: "พิมพ์ชนก แอดมิน",
      staffId: "ADM-001",
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
  const currentUserName = {
    housekeeper: "อรทัย ใจดี",
    technician: "ธีรภัทร วงศ์คำ",
    clerk: "ชนาภา มณีวงศ์",
    admin: "พิมพ์ชนก วัฒนา",
  };
  let allJobs = [
    {
      id: "CL-184",
      type: "cleaning",
      category: "พื้นเปียก/คราบสกปรก",
      title: "พื้นห้องเรียนมีคราบน้ำและลื่น",
      room: "CSB-307",
      reporter: "ผู้ใช้งานทั่วไป",
      time: "วันนี้ 09:14",
      status: "รอรับงาน",
      priority: "เร่งด่วน",
      detail: "มีน้ำหกบริเวณทางเข้าห้อง อาจทำให้ลื่นล้ม",
      photo: "รูปพื้นที่",
      assignee: null,
    },
    {
      id: "CL-183",
      type: "cleaning",
      category: "ขยะ/กลิ่น",
      title: "ถังขยะเต็มบริเวณโถง",
      room: "CSB ชั้น 2",
      reporter: "ผู้ใช้งานทั่วไป",
      time: "วันนี้ 08:42",
      status: "รอรับงาน",
      priority: "ปกติ",
      detail: "ถังขยะ 2 จุดใกล้ลิฟต์เต็มและมีกลิ่น",
      photo: "รูปพื้นที่",
      assignee: null,
    },
    {
      id: "CL-181",
      type: "cleaning",
      category: "ห้องน้ำ/อุปกรณ์สิ้นเปลือง",
      title: "ห้องน้ำต้องเติมสบู่ล้างมือ",
      room: "ห้องน้ำหญิง ชั้น 1",
      reporter: "ผู้ใช้งานทั่วไป",
      time: "วันนี้ 08:05",
      status: "กำลังดำเนินการ",
      priority: "ปกติ",
      detail: "สบู่ล้างมือหมดทั้งสองอ่าง",
      photo: "รูปพื้นที่",
      assignee: "อรทัย ใจดี",
    },
    {
      id: "CL-176",
      type: "cleaning",
      category: "ทำความสะอาดทั่วไป",
      title: "คราบฝุ่นในห้องประชุม",
      room: "CSB-201",
      reporter: "เจ้าหน้าที่คณะ",
      time: "เมื่อวาน 16:20",
      status: "รอตรวจสอบ",
      priority: "ปกติ",
      detail: "ทำความสะอาดแล้ว รอหัวหน้าตรวจพื้นที่",
      photo: "รูปพื้นที่",
      assignee: "ปวีณา คำปัน",
    },
    {
      id: "RP-291",
      type: "repair",
      category: "เครื่องปรับอากาศ",
      title: "เครื่องปรับอากาศไม่เย็น",
      room: "CSB-405",
      reporter: "อาจารย์ผู้ใช้งาน",
      time: "วันนี้ 10:05",
      status: "รอรับงาน",
      priority: "เร่งด่วน",
      detail: "เปิดแล้วมีลม แต่ไม่เย็นและมีเสียงดังเป็นช่วง",
      photo: "รูปเครื่อง",
      assignee: null,
    },
    {
      id: "RP-290",
      type: "repair",
      category: "ไฟฟ้า/แสงสว่าง",
      title: "ปลั๊กไฟมีประกายเมื่อเสียบอุปกรณ์",
      room: "LAB-2",
      reporter: "นักศึกษา",
      time: "วันนี้ 09:35",
      status: "รอรับงาน",
      priority: "เร่งด่วน",
      detail: "พบประกายไฟเล็กน้อยและมีกลิ่นไหม้",
      photo: "รูปจุดชำรุด",
      assignee: null,
    },
    {
      id: "RP-288",
      type: "repair",
      category: "ไฟฟ้า/แสงสว่าง",
      title: "หลอดไฟกะพริบบริเวณบันได",
      room: "บันไดหนีไฟ ชั้น 3",
      reporter: "ผู้ใช้งานทั่วไป",
      time: "วันนี้ 08:55",
      status: "กำลังดำเนินการ",
      priority: "สูง",
      detail: "กำลังตรวจชุดบัลลาสต์และสายไฟ",
      photo: "รูปจุดชำรุด",
      assignee: "ธีรภัทร วงศ์คำ",
    },
    {
      id: "RP-279",
      type: "repair",
      category: "ประปา/สุขาภิบาล",
      title: "ก๊อกน้ำรั่วตลอดเวลา",
      room: "Pantry ชั้น 2",
      reporter: "เจ้าหน้าที่คณะ",
      time: "เมื่อวาน 14:35",
      status: "รอตรวจสอบ",
      priority: "ปกติ",
      detail: "เปลี่ยนยางแล้ว รอตรวจการรั่วซ้ำ",
      photo: "รูปก๊อกน้ำ",
      assignee: "ณัฐดนัย ใจแก้ว",
    },
  ];
  let staffData = [
    {
      name: "อรทัย ใจดี",
      id: "STF-001",
      role: "แม่บ้าน",
      zone: "CSB ชั้น 1–3",
      status: "ใช้งาน",
    },
    {
      name: "ปวีณา คำปัน",
      id: "STF-002",
      role: "แม่บ้าน",
      zone: "CSB ชั้น 4–5",
      status: "ใช้งาน",
    },
    {
      name: "สุรีย์พร แสงดี",
      id: "STF-003",
      role: "แม่บ้าน",
      zone: "อาคารส่วนกลาง",
      status: "พักงาน",
    },
    {
      name: "ธีรภัทร วงศ์คำ",
      id: "STF-004",
      role: "ช่าง",
      zone: "ระบบไฟฟ้า / แอร์",
      status: "ใช้งาน",
    },
    {
      name: "ณัฐดนัย ใจแก้ว",
      id: "STF-005",
      role: "ช่าง",
      zone: "ประปา / อาคาร",
      status: "ใช้งาน",
    },
    {
      name: "ชนาภา มณีวงศ์",
      id: "STF-006",
      role: "ธุรการ",
      zone: "ประชาสัมพันธ์ ชั้น 1",
      status: "ใช้งาน",
    },
    {
      name: "พิมพ์ชนก วัฒนา",
      id: "ADM-001",
      role: "แอดมิน",
      zone: "ทุกพื้นที่",
      status: "ใช้งาน",
    },
  ];
  const lostSets = {
    inventory: [
      {
        id: "FD-081",
        title: "กระเป๋าผ้าสีดำ",
        place: "พบที่ CSB ชั้น 3",
        custody: "ประชาสัมพันธ์ชั้น 1",
        status: "รออนุมัติรับฝาก",
        decisionReason: "",
        assignee: "ชนาภา มณีวงศ์",
      },
      {
        id: "FD-079",
        title: "กุญแจพร้อมพวงกุญแจ",
        place: "พบที่โรงอาหาร",
        custody: "ตู้รับฝากช่อง B-04",
        status: "อนุมัติรับฝาก",
        decisionReason: "ตรวจของจริงและบันทึกเข้าตู้รับฝากแล้ว",
      },
      {
        id: "FD-075",
        title: "บัตรนักศึกษา",
        place: "พบหน้าห้อง CSB-201",
        custody: "ประชาสัมพันธ์ชั้น 1",
        status: "รออนุมัติรับฝาก",
        decisionReason: "",
      },
    ],
    lostposts: [
      {
        id: "LS-109",
        title: "หูฟังไร้สายสีขาว",
        place: "คาดว่าหายที่ห้อง CSB-405",
        custody: "ส่งประกาศเมื่อ 2 ชั่วโมงก่อน",
        status: "รออนุมัติเผยแพร่",
        decisionReason: "",
      },
      {
        id: "LS-106",
        title: "กระเป๋าสตางค์สีน้ำตาล",
        place: "คาดว่าหายบริเวณลิฟต์",
        custody: "ประกาศเมื่อวาน",
        status: "อนุมัติเผยแพร่",
        decisionReason: "ข้อมูลครบและไม่มีข้อมูลส่วนตัวที่ต้องปกปิด",
      },
      {
        id: "LS-101",
        title: "แฟลชไดรฟ์สีดำ",
        place: "คาดว่าหายที่ห้อง LAB-2",
        custody: "ส่งประกาศ 2 วันก่อน",
        status: "รออนุมัติเผยแพร่",
        decisionReason: "",
      },
    ],
    claims: [
      {
        id: "CM-034",
        title: "คำขอรับกุญแจ FD-079",
        place: "ผู้ขอระบุพวงกุญแจและจำนวนดอก",
        custody: "หลักฐานใหม่ · รอ 38 นาที",
        status: "รอตรวจสอบ",
        assignee: "ชนาภา มณีวงศ์",
      },
      {
        id: "CM-032",
        title: "คำขอรับบัตรนักศึกษา FD-075",
        place: "ชื่อและเลขท้ายตรงกับข้อมูลลับ",
        custody: "พร้อมนัดรับ",
        status: "อนุมัติ",
      },
      {
        id: "CM-029",
        title: "คำขอรับกระเป๋า FD-071",
        place: "รายละเอียดภายในไม่ตรงกัน",
        custody: "ต้องติดต่อผู้ขอ",
        status: "ขอข้อมูลเพิ่ม",
      },
    ],
  };
  let deletedRecords = [];
  let auditHistory = [
    {
      id: "AU-1005",
      source: "jobs",
      action: "อัปเดตสถานะ",
      itemId: "RP-288",
      title: "หลอดไฟกะพริบบริเวณบันได",
      actor: "ธีรภัทร วงศ์คำ",
      detail: "เปลี่ยนสถานะเป็น “กำลังดำเนินการ”",
      time: "วันนี้ 10:18",
    },
    {
      id: "AU-1004",
      source: "lost",
      action: "อนุมัติ",
      itemId: "FD-079",
      title: "กุญแจพร้อมพวงกุญแจ",
      actor: "ชนาภา มณีวงศ์",
      detail: "อนุมัติรับฝากและบันทึกเข้าตู้ B-04",
      time: "วันนี้ 09:52",
    },
    {
      id: "AU-1003",
      source: "staff",
      action: "ระงับบัญชี",
      itemId: "STF-003",
      title: "สุรีย์พร แสงดี",
      actor: "พิมพ์ชนก วัฒนา",
      detail: "เปลี่ยนสถานะบัญชีเป็นพักงาน",
      time: "วันนี้ 09:10",
    },
    {
      id: "AU-1002",
      source: "lost",
      action: "อัปเดตคำขอ",
      itemId: "CM-032",
      title: "คำขอรับบัตรนักศึกษา",
      actor: "ชนาภา มณีวงศ์",
      detail: "เปลี่ยนสถานะเป็น “อนุมัติ”",
      time: "เมื่อวาน 16:45",
    },
    {
      id: "AU-1001",
      source: "qr",
      action: "สร้าง QR",
      itemId: "ROOM-CSB-307",
      title: "ห้อง CSB-307",
      actor: "พิมพ์ชนก วัฒนา",
      detail: "สร้าง QR สำหรับหน้ารายงานของห้อง",
      time: "เมื่อวาน 14:30",
    },
  ];
  let workHistory = [
    {
      uid: "WH-001",
      staff: "อรทัย ใจดี",
      role: "แม่บ้าน",
      itemId: "CL-181",
      title: "ห้องน้ำต้องเติมสบู่ล้างมือ",
      category: "ห้องน้ำ/อุปกรณ์สิ้นเปลือง",
      action: "อัปเดตสถานะ",
      status: "กำลังดำเนินการ",
      detail: "เติมสบู่แล้วหนึ่งจุดและกำลังตรวจอุปกรณ์อีกจุด",
      date: "2026-07-30",
      time: "10:12",
    },
    {
      uid: "WH-002",
      staff: "อรทัย ใจดี",
      role: "แม่บ้าน",
      itemId: "CL-170",
      title: "ทำความสะอาดคราบกาแฟในห้องประชุม",
      category: "พื้นเปียก/คราบสกปรก",
      action: "ปิดงาน",
      status: "เสร็จสิ้น",
      detail: "ทำความสะอาดและแนบรูปหลังดำเนินการแล้ว",
      date: "2026-07-29",
      time: "15:40",
    },
    {
      uid: "WH-003",
      staff: "อรทัย ใจดี",
      role: "แม่บ้าน",
      itemId: "CL-168",
      title: "ทำความสะอาดกระจกภายนอกชั้น 5",
      category: "ทำความสะอาดทั่วไป",
      action: "คืนงาน",
      status: "คืนเข้ากองกลาง",
      detail: "อยู่นอกพื้นที่รับผิดชอบ — งานต้องใช้อุปกรณ์ทำงานบนที่สูง",
      date: "2026-07-28",
      time: "11:18",
    },
    {
      uid: "WH-004",
      staff: "ธีรภัทร วงศ์คำ",
      role: "ช่าง",
      itemId: "RP-288",
      title: "หลอดไฟกะพริบบริเวณบันได",
      category: "ไฟฟ้า/แสงสว่าง",
      action: "อัปเดตสถานะ",
      status: "กำลังดำเนินการ",
      detail: "กำลังตรวจชุดบัลลาสต์และสายไฟ",
      date: "2026-07-30",
      time: "10:18",
    },
    {
      uid: "WH-005",
      staff: "ธีรภัทร วงศ์คำ",
      role: "ช่าง",
      itemId: "RP-270",
      title: "เครื่องปรับอากาศมีน้ำหยด",
      category: "เครื่องปรับอากาศ",
      action: "ปิดงาน",
      status: "เสร็จสิ้น",
      detail: "ล้างท่อน้ำทิ้งและทดสอบระบบแล้ว",
      date: "2026-07-29",
      time: "14:05",
    },
    {
      uid: "WH-006",
      staff: "ธีรภัทร วงศ์คำ",
      role: "ช่าง",
      itemId: "RP-266",
      title: "ประตูอลูมิเนียมฝืด",
      category: "อาคาร/เฟอร์นิเจอร์",
      action: "คืนงาน",
      status: "คืนเข้ากองกลาง",
      detail: "ไม่มีทักษะหรืออุปกรณ์ที่จำเป็น — ต้องส่งต่อช่างประตูเฉพาะทาง",
      date: "2026-07-27",
      time: "09:42",
    },
    {
      uid: "WH-007",
      staff: "ชนาภา มณีวงศ์",
      role: "ธุรการ",
      itemId: "FD-079",
      title: "กุญแจพร้อมพวงกุญแจ",
      category: "ของที่รับฝาก",
      action: "อนุมัติ",
      status: "อนุมัติรับฝาก",
      detail: "ตรวจของจริงและบันทึกเข้าตู้รับฝาก B-04",
      date: "2026-07-30",
      time: "09:52",
    },
    {
      uid: "WH-008",
      staff: "ชนาภา มณีวงศ์",
      role: "ธุรการ",
      itemId: "CM-032",
      title: "คำขอรับบัตรนักศึกษา",
      category: "คำขอรับของ",
      action: "อัปเดตคำขอ",
      status: "อนุมัติ",
      detail: "ชื่อและเลขท้ายตรงกับข้อมูลลับ พร้อมนัดรับ",
      date: "2026-07-29",
      time: "16:45",
    },
    {
      uid: "WH-009",
      staff: "ชนาภา มณีวงศ์",
      role: "ธุรการ",
      itemId: "LS-098",
      title: "ประกาศตามหาโทรศัพท์สีดำ",
      category: "ประกาศตามหา",
      action: "ไม่อนุมัติ",
      status: "ไม่อนุมัติเผยแพร่",
      detail: "เป็นรายการซ้ำและมีข้อมูลส่วนตัวเกินจำเป็น",
      date: "2026-07-28",
      time: "13:20",
    },
  ];
  let selectedOverviewStaff = "";
  let currentHistoryView = "activity";
  const notificationSets = {
    housekeeper: [
      {
        id: "n-h1",
        symbol: "!",
        title: "งานเร่งด่วนเข้าคิวแม่บ้าน",
        text: "CL-184 พื้นเปียกที่ CSB-307 ยังไม่มีผู้รับงาน",
        time: "3 นาที",
        unread: true,
      },
      {
        id: "n-h2",
        symbol: "↳",
        title: "มีงานใหม่ประเภทขยะ/กลิ่น",
        text: "CL-183 ถังขยะเต็มบริเวณโถงชั้น 2",
        time: "18 นาที",
        unread: true,
      },
      {
        id: "n-h3",
        symbol: "✓",
        title: "งานของคุณรอตรวจสอบ",
        text: "CL-181 อัปเดตความคืบหน้าล่าสุดแล้ว",
        time: "1 ชม.",
        unread: false,
      },
    ],
    technician: [
      {
        id: "n-t1",
        symbol: "!",
        title: "งานไฟฟ้าเร่งด่วนเข้าคิว",
        text: "RP-290 มีประกายไฟที่ปลั๊กห้อง LAB-2",
        time: "5 นาที",
        unread: true,
      },
      {
        id: "n-t2",
        symbol: "↳",
        title: "งานแอร์ใหม่ยังไม่มีผู้รับ",
        text: "RP-291 เครื่องปรับอากาศไม่เย็นที่ CSB-405",
        time: "12 นาที",
        unread: true,
      },
      {
        id: "n-t3",
        symbol: "•",
        title: "ผู้แจ้งเพิ่มรายละเอียด",
        text: "แนบคลิปเสียงของเครื่องปรับอากาศเพิ่มเติม",
        time: "42 นาที",
        unread: true,
      },
    ],
    clerk: [
      {
        id: "n-c1",
        symbol: "?",
        title: "คำขอรับของใหม่",
        text: "CM-034 ขอรับกุญแจ FD-079 พร้อมข้อมูลยืนยัน",
        time: "4 นาที",
        unread: true,
      },
      {
        id: "n-c2",
        symbol: "+",
        title: "มีของนำมาฝากใหม่",
        text: "กระเป๋าผ้าสีดำถูกนำมาฝากที่ประชาสัมพันธ์",
        time: "26 นาที",
        unread: true,
      },
      {
        id: "n-c3",
        symbol: "✓",
        title: "คำขอพร้อมนัดรับ",
        text: "CM-032 ผ่านการตรวจหลักฐานแล้ว",
        time: "1 ชม.",
        unread: false,
      },
    ],
    admin: [
      {
        id: "n-a1",
        symbol: "!",
        title: "มีงานเร่งด่วนยังไม่มีผู้รับ",
        text: "งานแม่บ้าน 1 งาน และงานช่าง 2 งานกำลังรอรับ",
        time: "2 นาที",
        unread: true,
      },
      {
        id: "n-a2",
        symbol: "?",
        title: "คำขอรับของรอตรวจ",
        text: "ธุรการมีคำขอใหม่ 1 รายการ",
        time: "14 นาที",
        unread: true,
      },
      {
        id: "n-a3",
        symbol: "•",
        title: "บัญชี Staff ถูกระงับ",
        text: "STF-003 ยังอยู่ในสถานะพักงาน",
        time: "2 ชม.",
        unread: false,
      },
    ],
  };
  let announcements = [
    {
      id: "AN-031",
      title: "ปิดปรับปรุงลิฟต์โดยสาร",
      content: "อาคาร 30 ชั้น 1–5 ปิดให้บริการวันที่ 1–2 สิงหาคม",
      audience: "ผู้ใช้งานทุกคน",
      start: "2026-08-01",
      end: "2026-08-02",
      pinned: true,
      status: "เผยแพร่",
    },
    {
      id: "AN-030",
      title: "ตรวจระบบไฟฟ้าประจำเดือน",
      content: "เจ้าหน้าที่จะเข้าตรวจพื้นที่ส่วนกลางช่วง 17:00 น.",
      audience: "เจ้าหน้าที่ทุก Role",
      start: "2026-08-03",
      end: "2026-08-03",
      pinned: false,
      status: "เผยแพร่",
    },
    {
      id: "AN-029",
      title: "แนวทางแจ้งงานเร่งด่วน",
      content: "โปรดระบุสถานที่และรูปภาพให้ชัดเจน",
      audience: "ผู้ใช้งานทุกคน",
      start: "2026-08-05",
      end: "2026-08-31",
      pinned: false,
      status: "Draft",
    },
  ];
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
  let currentRole = localStorage.getItem("buildingCareRole") || "admin";
  let currentLostTab = "inventory";
  let currentBoardView = "unassigned";
  let selectedJobId = "";
  let pendingConfirmAction = null;
  let lastModalTrigger = null;
  const $ = (s) => document.querySelector(s),
    $$ = (s) => [...document.querySelectorAll(s)];
  function toast(message) {
    const el = $("#toast");
    el.textContent = message;
    el.classList.add("show");
    clearTimeout(window.toastTimer);
    window.toastTimer = setTimeout(() => el.classList.remove("show"), 2300);
  }
  function todayISO() {
    return new Intl.DateTimeFormat("en-CA", {
      timeZone: "Asia/Bangkok",
    }).format(new Date());
  }
  function currentTimeHM() {
    return new Intl.DateTimeFormat("th-TH", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
      timeZone: "Asia/Bangkok",
    })
      .format(new Date())
      .replace(".", ":");
  }
  function escapeHtml(value) {
    return String(value ?? "").replace(
      /[&<>"']/g,
      (ch) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#039;",
        }[ch])
    );
  }
  function isTerminalStatus(status) {
    return [
      "เสร็จสิ้น",
      "คืนของแล้ว",
      "ปิดประกาศ",
      "ไม่อนุมัติรับฝาก",
      "ไม่อนุมัติเผยแพร่",
    ].some((x) => String(status).includes(x));
  }
  function recordWorkHistory({
    staff = activeStaffName(),
    role = roleConfig[currentRole].label,
    itemId,
    title,
    category = "งานทั่วไป",
    action,
    status,
    detail,
    date = todayISO(),
    time = currentTimeHM(),
  }) {
    workHistory.unshift({
      uid: `WH-${Date.now()}-${Math.random().toString(16).slice(2)}`,
      staff,
      role,
      itemId,
      title,
      category,
      action,
      status,
      detail,
      date,
      time,
    });
    renderMyHistory();
    renderStaffOverview();
  }
  function roleAllows(element, role) {
    const roles = element.dataset.roles;
    return roles === "all" || roles.split(",").includes(role);
  }
  function roleJobs() {
    if (currentRole === "housekeeper")
      return allJobs.filter((j) => j.type === "cleaning");
    if (currentRole === "technician")
      return allJobs.filter((j) => j.type === "repair");
    return allJobs;
  }
  function activeStaffName() {
    return currentUserName[currentRole];
  }
  function badgeClass(status) {
    if (
      ["ไม่อนุมัติ", "ข้อมูลไม่ตรง", "ลบแล้ว"].some((s) => status.includes(s))
    )
      return "danger";
    if (
      ["เสร็จสิ้น", "คืนของแล้ว", "อนุมัติ", "หลักฐานผ่าน", "กู้คืนแล้ว"].some(
        (s) => status.includes(s)
      )
    )
      return "done";
    if (
      ["กำลัง", "รับงานแล้ว", "นัดรับ", "อาจพบ"].some((s) => status.includes(s))
    )
      return "progress";
    return "wait";
  }
  function populateCategoryFilter() {
    const select = $("#categoryFilter");
    const list = categories[currentRole] || ["all"];
    select.innerHTML = list
      .map(
        (c) =>
          `<option value="${c}">${
            c === "all" ? "ทุกประเภทที่ผู้ใช้เลือก" : c
          }</option>`
      )
      .join("");
  }
  function setRole(role) {
    currentRole = role;
    localStorage.setItem("buildingCareRole", role);
    const c = roleConfig[role];
    document.documentElement.style.setProperty("--role", c.color);
    document.documentElement.style.setProperty("--role-soft", c.soft);
    $("#roleSwitcher").value = role;
    $("#staffName").textContent = c.name;
    $("#staffRoleLabel").textContent = c.label;
    $("#avatar").textContent = c.avatar;
    $("#eyebrow").textContent = c.eyebrow;
    $("#heroEyebrow").textContent = c.eyebrow;
    $("#heroTitle").textContent = c.hero;
    $("#heroText").textContent = c.text;
    $("#queueTitle").textContent = c.queue;
    $("#jobsTitle").textContent = c.jobTitle || "ศูนย์รับงานรวม";
    $("#jobsSubtitle").textContent = c.jobSubtitle || "";
    $("#heroPrimary").textContent = c.primary;
    $$(".role-demo-btn").forEach((button) => {
      const active = button.dataset.roleSwitch === role;
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", String(active));
    });
    $("#headerAvatar").textContent = c.avatar;
    $("#headerName").textContent = currentUserName[role].split(" ")[0];
    $("#headerRole").textContent = c.label;
    $("#profileAvatar").textContent = c.avatar;
    $("#profileName").textContent = currentUserName[role];
    $("#profileStaffId").textContent = c.staffId;
    $("#profileRole").textContent = c.label;
    $("#profileDepartment").textContent =
      role === "technician"
        ? "งานอาคารและซ่อมบำรุง"
        : role === "housekeeper"
        ? "งานดูแลความสะอาด"
        : role === "clerk"
        ? "ธุรการและของหาย"
        : "บริหารระบบ";
    $("#jobsNavLabel").textContent =
      role === "housekeeper"
        ? "รับงานแม่บ้าน"
        : role === "technician"
        ? "รับงานช่าง"
        : "ศูนย์งานทั้งหมด";
    $("#queueExplainerTitle").textContent =
      role === "admin"
        ? "คิวรวมของแม่บ้านและช่าง"
        : `คิวนี้เป็นคิวร่วมของ${c.label}`;
    $$(".nav-item").forEach((n) =>
      n.classList.toggle("role-hidden", !roleAllows(n, role))
    );
    const active = $(".nav-item.active");
    if (active && !roleAllows(active, role)) navigate("dashboard");
    populateCategoryFilter();
    populateMyHistoryTypes();
    renderMetrics();
    renderQueue();
    renderActivities();
    renderJobs();
    renderNotifications();
    renderLost();
    renderMyHistory();
    renderStaffOverview();
    renderHistory();
    renderAnnouncements();
    renderMobileQuickActions();
    renderDashboardQuickActions();
  }
  function navigate(page) {
    const target = $(`.nav-item[data-page="${page}"]`);
    if (target && target.classList.contains("role-hidden")) {
      toast("บทบาทนี้ไม่มีสิทธิ์เข้าถึงเมนูดังกล่าว");
      return;
    }
    const destination = $(`#page-${page}`);
    if (!destination) {
      toast("ไม่พบหน้าที่เลือก");
      return;
    }
    $$(".page").forEach((p) => p.classList.remove("active"));
    destination.classList.add("active");
    $$(".nav-item").forEach((n) =>
      n.classList.toggle("active", n.dataset.page === page)
    );
    $$("[data-mobile-page]").forEach((n) =>
      n.classList.toggle("active", n.dataset.mobilePage === page)
    );
    const titles = {
      dashboard: "ภาพรวมการปฏิบัติงาน",
      jobs: roleConfig[currentRole].jobTitle,
      "my-history": "ประวัติงานของฉัน",
      lost: "ศูนย์ของหายและรับฝาก",
      "staff-overview": "ภาพรวมงาน Staff",
      staff: "จัดการบัญชีเจ้าหน้าที่",
      history: "ประวัติและรายการที่ลบ",
      qr: "QR ประจำห้อง",
      announcements: "ประกาศอาคาร",
    };
    $("#pageTitle").textContent = titles[page] || "Staff Operations";
    if (page === "my-history") renderMyHistory();
    if (page === "staff-overview") renderStaffOverview();
    if (page === "history") renderHistory();
    if (page === "announcements") renderAnnouncements();
    closeSidebar();
    window.scrollTo({
      top: 0,
      behavior: matchMedia("(prefers-reduced-motion: reduce)").matches
        ? "auto"
        : "smooth",
    });
  }
  function renderMetrics() {
    const jobs = roleJobs(),
      unassigned = jobs.filter((j) => !j.assignee).length,
      mine = jobs.filter((j) => j.assignee === activeStaffName()).length,
      team = jobs.filter(
        (j) => j.assignee && j.assignee !== activeStaffName()
      ).length,
      urgent = jobs.filter(
        (j) => j.priority === "เร่งด่วน" && j.status !== "เสร็จสิ้น"
      ).length;
    const completed = jobs.filter((j) => j.status === "เสร็จสิ้น").length,
      waitingParts = jobs.filter((j) => j.status === "รออะไหล่").length;
    let values;
    if (currentRole === "clerk")
      values = [
        [
          "ของที่พบใหม่",
          String(
            lostSets.inventory.filter((x) => x.status.includes("รอ")).length
          ),
          "รอตรวจสอบ",
        ],
        [
          "ของหายที่กำลังตามหา",
          String(lostSets.lostposts.length),
          "ประกาศทั้งหมด",
        ],
        ["คำขอรับคืน", String(lostSets.claims.length), "รอดำเนินการ"],
        ["นัดหมายวันนี้", "1", "พร้อมส่งมอบ"],
        [
          "คืนของสำเร็จ",
          String(
            lostSets.claims.filter((x) => x.status === "คืนของแล้ว").length
          ),
          "เดือนนี้",
        ],
      ];
    else if (currentRole === "admin")
      values = [
        ["งานทั้งหมด", String(jobs.length), "ทุกประเภท"],
        ["งานรอรับ", String(unassigned), "ยังไม่มอบหมาย"],
        [
          "กำลังดำเนินการ",
          String(jobs.filter((j) => j.status.includes("กำลัง")).length),
          "ติดตามได้",
        ],
        ["งานเสร็จวันนี้", String(completed), "ปิดงานแล้ว"],
        ["งานเกินกำหนด", "2", "ควรตรวจสอบ"],
        [
          "Staff ปฏิบัติงาน",
          String(staffData.filter((s) => s.status === "ใช้งาน").length),
          "ออนไลน์ขณะนี้",
        ],
      ];
    else if (currentRole === "technician")
      values = [
        ["งานใหม่", String(unassigned), "คิวงานซ่อม"],
        ["งานของฉัน", String(mine), "กำลังรับผิดชอบ"],
        ["งานเร่งด่วน", String(urgent), "ควรรับก่อน"],
        ["งานรออะไหล่", String(waitingParts), "ติดตามอะไหล่"],
        ["งานเสร็จวันนี้", String(completed), "ปิดงานแล้ว"],
      ];
    else
      values = [
        ["งานทำความสะอาดใหม่", String(unassigned), "คิวงานใหม่"],
        ["งานของฉัน", String(mine), "กำลังรับผิดชอบ"],
        ["งานเร่งด่วน", String(urgent), "ควรรับก่อน"],
        ["งานตามกำหนดเวลา", String(team), "ของทีมวันนี้"],
        ["งานเสร็จวันนี้", String(completed), "ปิดงานแล้ว"],
      ];
    $("#metricGrid").innerHTML = values
      .map(
        (v, i) =>
          `<article class="metric ${
            v[0].includes("เร่ง") || v[0].includes("เกิน") ? "warn" : ""
          }"><span>${v[0]}</span><strong>${v[1]}</strong><small>${
            v[2]
          }</small></article>`
      )
      .join("");
  }
  function renderQueue() {
    let items;
    if (currentRole === "clerk")
      items = lostSets.claims
        .slice(0, 3)
        .map((x) => [x.id, x.title, x.custody, x.status]);
    else
      items = roleJobs()
        .filter((j) => !j.assignee)
        .sort(
          (a, b) =>
            (a.priority === "เร่งด่วน" ? -1 : 1) -
            (b.priority === "เร่งด่วน" ? -1 : 1)
        )
        .slice(0, 3)
        .map((j) => [j.id, j.title, `${j.category} · ${j.room}`, j.status]);
    $("#priorityQueue").innerHTML = items.length
      ? items
          .map(
            (x) =>
              `<article class="queue-item"><div class="queue-code">${
                x[0]
              }</div><div><strong>${x[1]}</strong><p>${
                x[2]
              }</p></div><span class="badge ${badgeClass(x[3])}">${
                x[3]
              }</span></article>`
          )
          .join("")
      : '<div class="empty">ไม่มีรายการรอรับในขณะนี้</div>';
  }
  function renderActivities() {
    const content =
      currentRole === "clerk"
        ? [
            [
              "เปลี่ยนสถานะคำขอได้จากการ์ด",
              "เลือกสถานะใหม่แล้วกดบันทึกโดยไม่ต้องเปิดหน้าอื่น",
            ],
            [
              "มีของเข้าจุดรับฝาก",
              "ระบบเก็บจุดจัดเก็บและผู้รับฝากไว้ในประวัติ",
            ],
            [
              "แจ้งเตือนเฉพาะธุรการ",
              "กระดิ่งจะแสดงคำขอและรายการ Lost & Found เท่านั้น",
            ],
          ]
        : [
            [
              "คิวงานเป็นคิวร่วมของ Role",
              "งานใหม่ยังไม่ใช่ของบุคคลใดจนกว่าจะกดรับ",
            ],
            ["รับงานก่อนจึงอัปเดตได้", "งานจะย้ายไป “งานของฉัน” หลังรับสำเร็จ"],
            [
              "กรองตามประเภทที่ผู้ใช้เลือก",
              "Dropdown แสดงหมวดงานที่ตรงกับ Role ปัจจุบัน",
            ],
          ];
    $("#activityList").innerHTML = content
      .map(
        (x) =>
          `<div class="activity-item"><div class="activity-dot"></div><div><strong>${x[0]}</strong><p>${x[1]}</p></div></div>`
      )
      .join("");
  }
  function jobMatchesView(job) {
    if (currentRole === "admin" && currentBoardView === "mine")
      return job.assignee === activeStaffName();
    if (currentBoardView === "unassigned") return !job.assignee;
    if (currentBoardView === "mine") return job.assignee === activeStaffName();
    if (currentBoardView === "team")
      return !!job.assignee && job.assignee !== activeStaffName();
    return true;
  }
  function statusOptions(job) {
    const list =
      job.type === "repair"
        ? [
            "รับงานแล้ว",
            "กำลังดำเนินการ",
            "รอข้อมูลเพิ่มเติม",
            "รออะไหล่",
            "เสร็จสิ้น",
            "ยกเลิก",
          ]
        : [
            "รับงานแล้ว",
            "กำลังดำเนินการ",
            "รอข้อมูลเพิ่มเติม",
            "เสร็จสิ้น",
            "ยกเลิก",
          ];
    return list
      .map((s) => `<option ${job.status === s ? "selected" : ""}>${s}</option>`)
      .join("");
  }
  function renderJobs() {
    if (currentRole === "clerk") return;
    const query = $("#jobSearch").value.trim().toLowerCase(),
      category = $("#categoryFilter").value || "all",
      status = $("#jobStatusFilter").value || "all";
    const data = roleJobs().filter(
      (j) =>
        jobMatchesView(j) &&
        (category === "all" || j.category === category) &&
        (status === "all" || j.status === status) &&
        `${j.id} ${j.title} ${j.room} ${j.detail} ${j.category}`
          .toLowerCase()
          .includes(query)
    );
    $("#jobList").innerHTML = data.length
      ? data
          .map((j) => {
            const isMine = j.assignee === activeStaffName(),
              isUnassigned = !j.assignee,
              canEdit = isMine || currentRole === "admin";
            let actions;
            if (isUnassigned && currentRole !== "admin")
              actions = `<button class="accept-btn" type="button" data-job-action="accept" data-job-id="${j.id}">รับงาน</button>`;
            else if (isUnassigned && currentRole === "admin")
              actions = `<button class="accept-btn" type="button" data-job-action="assign" data-job-id="${j.id}">มอบหมายงาน</button>`;
            else if (canEdit) {
              actions = `<button class="update-btn" type="button" data-job-action="status" data-job-id="${
                j.id
              }">อัปเดตสถานะ</button>${
                currentRole === "admin"
                  ? `<button class="secondary" type="button" data-job-action="assign" data-job-id="${j.id}">เปลี่ยนผู้รับผิดชอบ</button>`
                  : ""
              }`;
            } else
              actions = `<div class="read-only">รับโดย ${escapeHtml(
                j.assignee
              )}</div>`;
            const icon = j.type === "repair" ? "#i-tools" : "#i-broom";
            return `<article class="job-card ${
              isMine ? "owned" : ""
            }" tabindex="0" data-job-card="${
              j.id
            }"><div class="job-photo"><svg class="icon"><use href="${icon}"/></svg></div><div><div class="job-meta"><span class="badge ${
              j.priority === "เร่งด่วน" ? "danger" : "wait"
            }">${j.priority}</span><span class="badge neutral">${
              j.category
            }</span><span class="badge ${badgeClass(j.status)}">${
              j.status
            }</span></div><h3>${
              j.title
            }</h3><div class="job-detail"><span>เลขงาน ${j.id}</span><span>${
              j.room
            }</span><span>${
              j.time
            }</span><span class="assignee"><span class="assignee-dot"></span>${
              j.assignee || "ยังไม่มีผู้รับผิดชอบ"
            }</span></div></div><div class="job-actions">${actions}<button class="small-btn" type="button" data-job-action="detail" data-job-id="${
              j.id
            }">ดูรายละเอียด</button></div></article>`;
          })
          .join("")
      : '<div class="empty">ไม่พบงานที่ตรงกับมุมมองหรือตัวกรองนี้</div>';
  }
  function appendJobTimeline(job, title, detail) {
    job.timeline = job.timeline || [];
    job.timeline.push({ title, detail, time: nowThai() });
  }
  function requestAcceptJob(id, trigger = document.activeElement) {
    const job = allJobs.find((item) => item.id === id);
    if (!job || job.assignee) {
      toast("งานนี้มีเจ้าหน้าที่คนอื่นรับแล้ว");
      return;
    }
    requestConfirmation(
      "ยืนยันการรับงาน",
      "เมื่อรับงานแล้ว งานนี้จะย้ายไปอยู่ในงานของฉัน และ Staff คนอื่นจะไม่สามารถแก้ไขงานนี้ได้",
      () => {
        acceptJob(id);
        appendJobTimeline(job, "รับงาน", `รับผิดชอบโดย ${activeStaffName()}`);
        toast("รับงานเรียบร้อย");
      },
      "ยืนยันรับงาน"
    );
  }
  function acceptJob(id) {
    const job = allJobs.find((j) => j.id === id);
    if (!job || job.assignee) {
      toast("งานนี้มีเจ้าหน้าที่คนอื่นรับแล้ว");
      renderJobs();
      return;
    }
    job.assignee = activeStaffName();
    job.status = "รับงานแล้ว";
    job.returnReason = "";
    currentBoardView = "mine";
    $$("#boardTabs .board-tab").forEach((t) =>
      t.classList.toggle("active", t.dataset.view === "mine")
    );
    addAudit("jobs", "รับงาน", id, job.title, `รับผิดชอบโดย ${job.assignee}`);
    recordWorkHistory({
      itemId: id,
      title: job.title,
      category: job.category,
      action: "รับงาน",
      status: job.status,
      detail: `รับงานจากคิวร่วม · ${job.room}`,
    });
    toast(`รับงาน ${id} แล้ว งานย้ายไป “งานของฉัน”`);
    renderJobs();
    renderMetrics();
    renderQueue();
    addNotification(
      currentRole,
      `รับงาน ${id} สำเร็จ`,
      `คุณเป็นผู้รับผิดชอบงาน “${job.title}” แล้ว`
    );
  }
  function assignDemoJob(id) {
    const job = allJobs.find((j) => j.id === id);
    job.assignee = job.type === "repair" ? "ธีรภัทร วงศ์คำ" : "อรทัย ใจดี";
    job.status = "รับงานแล้ว";
    addAudit("jobs", "มอบหมายงาน", id, job.title, `มอบหมายให้ ${job.assignee}`);
    toast(`มอบหมาย ${id} ให้ ${job.assignee} แล้ว`);
    renderJobs();
    renderMetrics();
    renderQueue();
    renderStaffOverview();
  }
  function updateJob(id, button) {
    const job = allJobs.find((j) => j.id === id);
    const previous = job.status;
    job.status = button.parentElement.querySelector("select").value;
    const action = isTerminalStatus(job.status) ? "ปิดงาน" : "อัปเดตสถานะ";
    addAudit(
      "jobs",
      action,
      id,
      job.title,
      `เปลี่ยนจาก “${previous}” เป็น “${job.status}”`
    );
    const creditedStaff = job.assignee || activeStaffName(),
      creditedRole =
        staffData.find((s) => s.name === creditedStaff)?.role ||
        roleConfig[currentRole].label;
    recordWorkHistory({
      staff: creditedStaff,
      role: creditedRole,
      itemId: id,
      title: job.title,
      category: job.category,
      action,
      status: job.status,
      detail: `เปลี่ยนสถานะจาก “${previous}” เป็น “${job.status}” · ${
        job.room
      }${currentRole === "admin" ? " · อัปเดตโดย Admin" : ""}`,
    });
    toast(`อัปเดต ${id} เป็น “${job.status}” แล้ว`);
    renderJobs();
    renderMetrics();
    renderQueue();
  }
  function openReturnJob(id) {
    const job = allJobs.find((j) => j.id === id);
    if (
      !job ||
      job.assignee !== activeStaffName() ||
      !["housekeeper", "technician"].includes(currentRole)
    ) {
      toast("คุณไม่มีสิทธิ์คืนงานรายการนี้");
      return;
    }
    $("#returnJobId").value = id;
    $("#returnReason").value = "";
    $("#returnNote").value = "";
    $("#returnJobModalTitle").textContent = `คืนงาน ${id} · ${job.title}`;
    openModal("returnJobModal");
  }
  function nowThai() {
    return new Intl.DateTimeFormat("th-TH", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date());
  }
  function sourceLabel(source) {
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
  function addAudit(
    source,
    action,
    itemId,
    title,
    detail,
    actor = activeStaffName()
  ) {
    auditHistory.unshift({
      id: `AU-${Date.now()}`,
      source,
      action,
      itemId,
      title,
      actor,
      detail,
      time: nowThai(),
    });
    renderHistory();
  }
  function storeDeletedRecord(source, record, collectionKey, title) {
    deletedRecords.unshift({
      uid: `DEL-${Date.now()}-${Math.random().toString(16).slice(2)}`,
      source,
      collectionKey,
      record: structuredClone(record),
      itemId: record.id,
      title: title || record.title || record.name,
      deletedBy: activeStaffName(),
      deletedAt: nowThai(),
    });
    addAudit(
      source,
      "ลบ",
      record.id,
      title || record.title || record.name,
      "ย้ายรายการไปยังถังเก็บแบบ Soft Delete"
    );
  }
  function deleteJob(id) {
    if (currentRole !== "admin") {
      toast("เฉพาะ Admin เท่านั้นที่ลบงานได้");
      return;
    }
    const index = allJobs.findIndex((j) => j.id === id);
    if (index < 0) return;
    requestConfirmation(
      "ยืนยันลบงาน",
      `ลบงาน ${id} แบบ Soft Delete หรือไม่? รายการยังกู้คืนได้จากหน้าประวัติ`,
      () => {
        const [record] = allJobs.splice(index, 1);
        storeDeletedRecord("jobs", record, "allJobs", record.title);
        toast(`ย้ายงาน ${id} ไปยังรายการที่ลบแล้ว`);
        renderJobs();
        renderMetrics();
        renderQueue();
        renderStaffOverview();
        renderHistory();
      }
    );
  }
  function claimStatusOptions(item) {
    const list = [
      "รอตรวจสอบ",
      "ขอข้อมูลเพิ่มเติม",
      "ผ่านการตรวจสอบ",
      "ไม่ผ่านการตรวจสอบ",
      "นัดหมายแล้ว",
      "คืนของแล้ว",
    ];
    return list
      .map(
        (s) => `<option ${item.status === s ? "selected" : ""}>${s}</option>`
      )
      .join("");
  }
  function decisionButtons(tab, item) {
    const approveLabel =
      tab === "inventory" ? "อนุมัติรับฝาก" : "อนุมัติเผยแพร่";
    return `<div class="approval-actions"><button class="approve-btn" type="button" data-lost-action="approve" data-tab="${tab}" data-item-id="${item.id}">${approveLabel}</button><button class="reject-btn" type="button" data-lost-action="reject" data-tab="${tab}" data-item-id="${item.id}">ไม่อนุมัติ</button></div>`;
  }
  function renderLost() {
    const data = lostSets[currentLostTab];
    $("#lostGrid").innerHTML = data.length
      ? data
          .map((i) => {
            const note = i.decisionReason
              ? `<div class="approval-note"><strong>${
                  i.status.includes("ไม่อนุมัติ")
                    ? "เหตุผลที่ไม่อนุมัติ"
                    : "บันทึกการอนุมัติ"
                }:</strong> ${i.decisionReason}</div>`
              : "";
            const adminDelete =
              currentRole === "admin"
                ? `<div class="admin-delete-row"><button class="small-btn delete" type="button" data-lost-action="delete" data-tab="${currentLostTab}" data-item-id="${i.id}">ลบรายการ</button></div>`
                : "";
            const controls =
              currentLostTab === "claims"
                ? `<div class="claim-controls"><button type="button" class="primary" data-lost-action="claim-detail" data-tab="claims" data-item-id="${i.id}">ดูรายละเอียดคำขอ</button></div>`
                : `${note}<div class="lost-foot"><span class="custody">${i.custody}</span><button class="small-btn" type="button" data-lost-action="detail" data-tab="${currentLostTab}" data-item-id="${i.id}">ดูรายละเอียด</button></div>`;
            return `<article class="lost-card" tabindex="0" data-lost-card="${
              i.id
            }"><div class="lost-image"><svg class="icon"><use href="#i-box"/></svg></div><div class="lost-content"><span class="badge ${badgeClass(
              i.status
            )}">${i.status}</span><h3>${i.id} · ${i.title}</h3><p>${
              i.place
            }</p>${controls}${adminDelete}</div></article>`;
          })
          .join("")
      : '<div class="empty" style="grid-column:1/-1">ไม่มีรายการในหมวดนี้</div>';
  }
  function approveLostItem(tab, id) {
    const item = lostSets[tab].find((x) => x.id === id);
    if (!item) return;
    requestConfirmation(
      "ยืนยันการอนุมัติ",
      `ตรวจสอบข้อมูลของ ${item.id} · ${item.title} แล้วใช่หรือไม่?`,
      () => finalizeApproveLostItem(tab, id),
      "อนุมัติ"
    );
  }
  function finalizeApproveLostItem(tab, id) {
    const item = lostSets[tab].find((x) => x.id === id);
    if (!item) return;
    const nextStatus = tab === "inventory" ? "อนุมัติรับฝาก" : "อนุมัติเผยแพร่";
    item.status = nextStatus;
    item.decisionReason =
      tab === "inventory"
        ? "ตรวจสอบสิ่งของจริงและข้อมูลรับฝากแล้ว"
        : "ตรวจสอบข้อมูลประกาศ รูป และข้อมูลส่วนตัวแล้ว";
    item.decidedBy = activeStaffName();
    item.decidedAt = nowThai();
    item.assignee = activeStaffName();
    addAudit(
      "lost",
      "อนุมัติ",
      id,
      item.title,
      `เปลี่ยนสถานะเป็น “${nextStatus}”`
    );
    recordWorkHistory({
      itemId: id,
      title: item.title,
      category: tab === "inventory" ? "ของที่รับฝาก" : "ประกาศตามหา",
      action: "อนุมัติ",
      status: nextStatus,
      detail: item.decisionReason,
    });
    addNotification(
      "clerk",
      `${id} อนุมัติแล้ว`,
      `${item.title} เปลี่ยนเป็น ${nextStatus}`,
      false
    );
    if (currentRole === "admin")
      addNotification(
        "admin",
        `${id} อนุมัติแล้ว`,
        `Admin อนุมัติรายการ ${item.title}`,
        false
      );
    toast(`อนุมัติ ${id} แล้ว`);
    renderLost();
    renderMetrics();
    renderQueue();
  }
  function openReject(tab, id) {
    const item = lostSets[tab].find((x) => x.id === id);
    if (!item) return;
    $("#rejectSource").value = tab;
    $("#rejectItemId").value = id;
    $("#rejectReason").value = "";
    $("#rejectNote").value = "";
    $("#rejectModalTitle").textContent = `ไม่อนุมัติ ${id} · ${item.title}`;
    openModal("rejectModal");
  }
  function updateClaimStatus(id, button) {
    const item = lostSets.claims.find((x) => x.id === id),
      nextStatus = button.previousElementSibling.value;
    if (!item) return;
    if (["ผ่านการตรวจสอบ", "ไม่ผ่านการตรวจสอบ"].includes(nextStatus)) {
      requestConfirmation(
        nextStatus === "ผ่านการตรวจสอบ"
          ? "ยืนยันอนุมัติคำขอ"
          : "ยืนยันไม่อนุมัติคำขอ",
        `${nextStatus} สำหรับ ${id} หรือไม่?`,
        () => finalizeClaimStatus(item, nextStatus)
      );
      return;
    }
    finalizeClaimStatus(item, nextStatus);
  }
  function finalizeClaimStatus(item, nextStatus) {
    const previous = item.status;
    item.status = nextStatus;
    item.custody =
      item.status === "คืนของแล้ว"
        ? "ปิดกระบวนการและบันทึกผู้ส่งมอบ"
        : item.status === "นัดหมายแล้ว"
        ? "ยืนยันวันและเวลารับแล้ว"
        : item.status === "ขอข้อมูลเพิ่มเติม"
        ? "รอผู้ขอส่งรายละเอียดเพิ่ม"
        : "อัปเดตโดยธุรการ";
    item.assignee = activeStaffName();
    const historyAction =
      item.status === "คืนของแล้ว" ? "ปิดคำขอ" : "อัปเดตคำขอ";
    addAudit(
      "lost",
      historyAction,
      item.id,
      item.title,
      `เปลี่ยนจาก “${previous}” เป็น “${item.status}”`
    );
    recordWorkHistory({
      itemId: item.id,
      title: item.title,
      category: "คำขอรับของ",
      action: historyAction,
      status: item.status,
      detail: `เปลี่ยนจาก “${previous}” เป็น “${item.status}” · ${item.custody}`,
    });
    toast(`เปลี่ยน ${item.id} เป็น “${item.status}” แล้ว`);
    renderLost();
    renderMetrics();
    addNotification(
      "clerk",
      `อัปเดต ${item.id} แล้ว`,
      `สถานะคำขอเปลี่ยนเป็น ${item.status}`,
      false
    );
  }
  function deleteLostRecord(tab, id) {
    if (currentRole !== "admin") {
      toast("เฉพาะ Admin เท่านั้นที่ลบรายการได้");
      return;
    }
    const index = lostSets[tab].findIndex((x) => x.id === id);
    if (index < 0) return;
    requestConfirmation(
      "ยืนยันลบรายการ",
      `ลบ ${id} แบบ Soft Delete หรือไม่?`,
      () => {
        const [record] = lostSets[tab].splice(index, 1);
        storeDeletedRecord("lost", record, tab, record.title);
        toast(`ย้าย ${id} ไปยังรายการที่ลบแล้ว`);
        renderLost();
        renderMetrics();
        renderQueue();
        renderHistory();
      }
    );
  }
  function populateMyHistoryTypes() {
    const select = $("#myHistoryType");
    if (!select) return;
    const base =
      currentRole === "clerk"
        ? [
            "all",
            "อนุมัติ",
            "ไม่อนุมัติ",
            "อัปเดตคำขอ",
            "ปิดคำขอ",
            "รับฝากรายการใหม่",
          ]
        : ["all", "รับงาน", "อัปเดตสถานะ", "ปิดงาน", "คืนงาน"];
    select.innerHTML = base
      .map(
        (x) => `<option value="${x}">${x === "all" ? "ทุกกิจกรรม" : x}</option>`
      )
      .join("");
  }
  function inDateRange(date, from, to) {
    return (!from || date >= from) && (!to || date <= to);
  }
  function renderMyHistory() {
    const list = $("#myHistoryList"),
      summary = $("#myHistorySummary");
    if (!list || !summary) return;
    const staff = activeStaffName(),
      from = $("#myHistoryFrom")?.value || "",
      to = $("#myHistoryTo")?.value || "",
      type = $("#myHistoryType")?.value || "all",
      q = ($("#myHistorySearch")?.value || "").trim().toLowerCase();
    const own = workHistory.filter((x) => x.staff === staff),
      rows = own
        .filter(
          (x) =>
            inDateRange(x.date, from, to) &&
            (type === "all" || x.action === type) &&
            `${x.itemId} ${x.title} ${x.category} ${x.action} ${x.status} ${x.detail}`
              .toLowerCase()
              .includes(q)
        )
        .sort((a, b) =>
          `${b.date} ${b.time}`.localeCompare(`${a.date} ${a.time}`)
        );
    const closed = own.filter(
        (x) =>
          ["ปิดงาน", "ปิดคำขอ"].includes(x.action) || isTerminalStatus(x.status)
      ).length,
      returned = own.filter((x) => x.action === "คืนงาน").length,
      decisions = own.filter((x) =>
        ["อนุมัติ", "ไม่อนุมัติ"].includes(x.action)
      ).length;
    summary.innerHTML = [
      [own.length, "กิจกรรมทั้งหมด", "รวมทุกวันที่บันทึก"],
      [closed, "งาน/คำขอที่ปิด", "ดำเนินการถึงสถานะสุดท้าย"],
      [returned, "คืนเข้ากองกลาง", "มีเหตุผลบันทึกไว้"],
      [decisions, "การตัดสินใจ", "อนุมัติหรือไม่อนุมัติ"],
    ]
      .map(
        (v, i) =>
          `<article class="metric ${i === 2 ? "warn" : ""}"><span>${
            v[1]
          }</span><strong>${v[0]}</strong><small>${v[2]}</small></article>`
      )
      .join("");
    list.innerHTML = rows.length
      ? rows
          .map(
            (x) =>
              `<article class="work-history-card"><div class="work-history-date">${new Intl.DateTimeFormat(
                "th-TH",
                { dateStyle: "medium" }
              ).format(new Date(`${x.date}T00:00:00`))}<small>${
                x.time
              } น.</small></div><div class="work-history-main"><div><span class="badge ${badgeClass(
                x.action
              )}">${x.action}</span> <span class="badge neutral">${
                x.category
              }</span></div><h3>${x.itemId} · ${x.title}</h3><p>${escapeHtml(
                x.detail
              )}</p><div class="work-history-meta"><span class="badge ${badgeClass(
                x.status
              )}">${x.status}</span><span class="custody">บันทึกโดย ${
                x.staff
              }</span></div></div><button class="small-btn" type="button" data-history-detail="${
                x.itemId
              }">ดูรายละเอียด</button></article>`
          )
          .join("")
      : '<div class="empty">ไม่พบประวัติงานในช่วงวันที่หรือตัวกรองที่เลือก</div>';
  }
  function activeWorkCountForStaff(staff) {
    const jobs = allJobs.filter(
      (j) => j.assignee === staff.name && !isTerminalStatus(j.status)
    ).length;
    const lost =
      staff.role === "ธุรการ"
        ? [
            ...lostSets.inventory,
            ...lostSets.lostposts,
            ...lostSets.claims,
          ].filter(
            (i) =>
              i.assignee === staff.name &&
              !isTerminalStatus(i.status) &&
              i.status !== "คืนของแล้ว"
          ).length
        : 0;
    return jobs + lost;
  }
  function latestHistoryFor(staffName, from = "", to = "") {
    return workHistory
      .filter((x) => x.staff === staffName && inDateRange(x.date, from, to))
      .sort((a, b) =>
        `${b.date} ${b.time}`.localeCompare(`${a.date} ${a.time}`)
      )[0];
  }
  function staffOverviewStats(staff, from = "", to = "") {
    const rows = workHistory.filter(
      (x) => x.staff === staff.name && inDateRange(x.date, from, to)
    );
    const closedItems = new Set(
      rows
        .filter(
          (x) =>
            ["ปิดงาน", "ปิดคำขอ"].includes(x.action) ||
            isTerminalStatus(x.status)
        )
        .map((x) => x.itemId)
    );
    const returnedItems = new Set(
      rows.filter((x) => x.action === "คืนงาน").map((x) => x.itemId)
    );
    return {
      active: activeWorkCountForStaff(staff),
      closed: closedItems.size,
      returned: returnedItems.size,
      latest: latestHistoryFor(staff.name, from, to),
    };
  }
  function renderStaffOverview() {
    const table = $("#staffOverviewTable"),
      summary = $("#staffOverviewSummary");
    if (!table || !summary) return;
    const role = $("#overviewRoleFilter")?.value || "all",
      from = $("#overviewFrom")?.value || "",
      to = $("#overviewTo")?.value || "",
      q = ($("#overviewSearch")?.value || "").trim().toLowerCase();
    const staffRows = staffData.filter(
      (s) =>
        s.role !== "แอดมิน" &&
        (role === "all" || s.role === role) &&
        `${s.name} ${s.id} ${s.role} ${s.zone}`.toLowerCase().includes(q)
    );
    const totals = staffRows.map((s) => staffOverviewStats(s, from, to));
    summary.innerHTML = [
      [
        totals.reduce((n, x) => n + x.active, 0),
        "กำลังรับผิดชอบ",
        "งานที่ยังไม่ถึงสถานะสุดท้าย",
      ],
      [totals.reduce((n, x) => n + x.closed, 0), "ปิดแล้ว", "นับตามงานไม่ซ้ำ"],
      [
        totals.reduce((n, x) => n + x.returned, 0),
        "คืนเข้ากองกลาง",
        "มีเหตุผลประกอบทุกครั้ง",
      ],
      [staffRows.length, "Staff ในมุมมอง", "ตาม Role และคำค้น"],
    ]
      .map(
        (v, i) =>
          `<article class="metric ${i === 2 ? "warn" : ""}"><span>${
            v[1]
          }</span><strong>${v[0]}</strong><small>${v[2]}</small></article>`
      )
      .join("");
    table.innerHTML = staffRows.length
      ? staffRows
          .map((s) => {
            const st = staffOverviewStats(s, from, to),
              latest = st.latest;
            return `<tr><td><div class="overview-staff-name"><div class="person-avatar">${s.name.slice(
              0,
              2
            )}</div><div><strong>${s.name}</strong><br><small>${
              s.id
            }</small></div></div></td><td><span class="badge neutral">${
              s.role
            }</span></td><td><span class="overview-number">${
              st.active
            }</span></td><td><span class="overview-number">${
              st.closed
            }</span></td><td><span class="overview-number">${
              st.returned
            }</span></td><td>${
              latest
                ? `<strong>${latest.action}</strong><br><small>${latest.itemId} · ${latest.date}</small>`
                : '<span class="custody">ยังไม่มีกิจกรรม</span>'
            }</td><td><button class="small-btn" type="button" data-staff-overview="${escapeHtml(
              s.name
            )}">ดูรายละเอียด</button></td></tr>`;
          })
          .join("")
      : '<tr><td colspan="7" class="history-empty">ไม่พบ Staff ที่ตรงกับตัวกรอง</td></tr>';
    if (
      selectedOverviewStaff &&
      !staffRows.some((s) => s.name === selectedOverviewStaff)
    )
      selectedOverviewStaff = "";
    renderStaffOverviewDetail();
  }
  function showStaffOverview(name) {
    selectedOverviewStaff = name;
    renderStaffOverviewDetail();
    $("#staffOverviewDetail").scrollIntoView({
      behavior: "smooth",
      block: "center",
    });
  }
  function renderStaffOverviewDetail() {
    const box = $("#staffOverviewDetail"),
      title = $("#overviewDetailTitle"),
      count = $("#overviewDetailCount");
    if (!box || !title || !count) return;
    if (!selectedOverviewStaff) {
      title.textContent = "เลือก Staff เพื่อดูรายละเอียดงาน";
      count.textContent = "0 รายการ";
      box.innerHTML =
        '<div class="empty">กด “ดูรายละเอียด” จากตารางด้านบน</div>';
      return;
    }
    const from = $("#overviewFrom")?.value || "",
      to = $("#overviewTo")?.value || "";
    const rows = workHistory
      .filter(
        (x) =>
          x.staff === selectedOverviewStaff && inDateRange(x.date, from, to)
      )
      .sort((a, b) =>
        `${b.date} ${b.time}`.localeCompare(`${a.date} ${a.time}`)
      );
    title.textContent = `รายละเอียดงาน · ${selectedOverviewStaff}`;
    count.textContent = `${rows.length} รายการ`;
    box.innerHTML = rows.length
      ? rows
          .map(
            (x) =>
              `<article class="overview-detail-item"><div><strong>${
                x.date
              }</strong><p>${x.time} น.</p></div><div><strong>${x.itemId} · ${
                x.title
              }</strong><p>${escapeHtml(
                x.detail
              )}</p></div><span class="badge ${badgeClass(x.action)}">${
                x.action
              }</span></article>`
          )
          .join("")
      : '<div class="empty">ไม่มีประวัติในช่วงวันที่เลือก</div>';
  }
  function renderHistory() {
    const summary = $("#historySummary"),
      table = $("#historyTable"),
      head = $("#historyHead");
    if (!summary || !table || !head) return;
    const approvals = auditHistory.filter(
        (x) => x.action.includes("อนุมัติ") && !x.action.includes("ไม่")
      ).length,
      rejections = auditHistory.filter((x) =>
        x.action.includes("ไม่อนุมัติ")
      ).length;
    summary.innerHTML = [
      [auditHistory.length, "เหตุการณ์ทั้งหมด", "ทุกการเปลี่ยนแปลง"],
      [approvals, "การอนุมัติ", "ผ่านการตรวจสอบ"],
      [rejections, "ไม่อนุมัติ", "มีเหตุผลกำกับ"],
      [deletedRecords.length, "รายการที่ลบแล้ว", "สามารถกู้คืนได้"],
    ]
      .map(
        (v, i) =>
          `<article class="metric ${i === 3 ? "warn" : ""}"><span>${
            v[1]
          }</span><strong>${v[0]}</strong><small>${v[2]}</small></article>`
      )
      .join("");
    const q = ($("#historySearch")?.value || "").trim().toLowerCase(),
      source = $("#historySourceFilter")?.value || "all",
      action = $("#historyActionFilter")?.value || "all";
    if (currentHistoryView === "deleted") {
      head.innerHTML =
        "<tr><th>รายการ</th><th>ส่วนของระบบ</th><th>ผู้ลบ</th><th>เวลาที่ลบ</th><th>จัดการ</th></tr>";
      const rows = deletedRecords.filter(
        (x) =>
          (source === "all" || x.source === source) &&
          `${x.itemId} ${x.title} ${x.deletedBy} ${sourceLabel(x.source)}`
            .toLowerCase()
            .includes(q)
      );
      table.innerHTML = rows.length
        ? rows
            .map(
              (x) =>
                `<tr><td><strong>${x.itemId}</strong><br><small>${
                  x.title
                }</small></td><td><span class="history-source">${sourceLabel(
                  x.source
                )}</span></td><td>${x.deletedBy}</td><td>${
                  x.deletedAt
                }</td><td><div class="row-actions"><button class="small-btn restore-btn" type="button" data-history-action="restore" data-history-uid="${
                  x.uid
                }">กู้คืน</button><button class="small-btn permanent-btn" type="button" data-history-action="permanent-delete" data-history-uid="${
                  x.uid
                }">ลบถาวร</button></div></td></tr>`
            )
            .join("")
        : '<tr><td colspan="5" class="history-empty">ไม่พบรายการที่ลบแล้ว</td></tr>';
      return;
    }
    head.innerHTML =
      "<tr><th>เวลา</th><th>ผู้ดำเนินการ</th><th>การดำเนินการ</th><th>รายการ</th><th>รายละเอียด</th></tr>";
    const rows = auditHistory.filter(
      (x) =>
        (source === "all" || x.source === source) &&
        (action === "all" || x.action.includes(action)) &&
        `${x.itemId} ${x.title} ${x.actor} ${x.action} ${x.detail}`
          .toLowerCase()
          .includes(q)
    );
    table.innerHTML = rows.length
      ? rows
          .map(
            (x) =>
              `<tr><td>${x.time}</td><td>${
                x.actor
              }</td><td><span class="badge ${badgeClass(
                x.action
              )} history-action">${
                x.action
              }</span><br><span class="history-source">${sourceLabel(
                x.source
              )}</span></td><td><strong>${x.itemId}</strong><br><small>${
                x.title
              }</small></td><td class="history-detail">${x.detail}</td></tr>`
          )
          .join("")
      : '<tr><td colspan="5" class="history-empty">ไม่พบประวัติที่ตรงกับตัวกรอง</td></tr>';
  }
  function restoreDeleted(uid) {
    const index = deletedRecords.findIndex((x) => x.uid === uid);
    if (index < 0) return;
    const item = deletedRecords[index];
    if (item.collectionKey === "allJobs") allJobs.unshift(item.record);
    else if (item.collectionKey === "staffData") staffData.unshift(item.record);
    else if (lostSets[item.collectionKey])
      lostSets[item.collectionKey].unshift(item.record);
    deletedRecords.splice(index, 1);
    addAudit(
      item.source,
      "กู้คืน",
      item.itemId,
      item.title,
      "กู้คืนรายการจาก Soft Delete"
    );
    toast(`กู้คืน ${item.itemId} แล้ว`);
    renderJobs();
    renderLost();
    renderStaff();
    renderMetrics();
    renderQueue();
    renderHistory();
  }
  function permanentDelete(uid) {
    const index = deletedRecords.findIndex((x) => x.uid === uid);
    if (index < 0) return;
    const item = deletedRecords[index];
    requestConfirmation(
      "ยืนยันลบถาวร",
      `ลบ ${item.itemId} ถาวรหรือไม่? การกระทำนี้ย้อนกลับไม่ได้ใน Demo`,
      () => {
        deletedRecords.splice(index, 1);
        addAudit(
          item.source,
          "ลบถาวร",
          item.itemId,
          item.title,
          "นำข้อมูลออกจากรายการ Soft Delete"
        );
        toast(`ลบ ${item.itemId} ถาวรแล้ว`);
        renderHistory();
      }
    );
  }
  function renderNotifications() {
    const list = notificationSets[currentRole] || [],
      unread = list.filter((n) => n.unread).length;
    $(
      "#notificationTitle"
    ).textContent = `การแจ้งเตือนของ${roleConfig[currentRole].label}`;
    [$("#notificationCount"), $("#mobileNotificationCount")].forEach(
      (badge) => {
        badge.textContent = unread;
        badge.style.display = unread ? "grid" : "none";
      }
    );
    if (!list.length) {
      $("#notificationList").innerHTML =
        '<div class="notification-empty">ไม่มีการแจ้งเตือน</div>';
      return;
    }
    const groups = [
      ["วันนี้", list.filter((_, index) => index < 2)],
      ["เมื่อวาน", list.filter((_, index) => index === 2)],
      ["ก่อนหน้านี้", list.filter((_, index) => index > 2)],
    ];
    $("#notificationList").innerHTML = groups
      .filter((group) => group[1].length)
      .map(
        (group) =>
          `<div class="notification-group-label">${group[0]}</div>${group[1]
            .map(
              (n) =>
                `<button type="button" class="notification-item ${
                  n.unread ? "unread" : ""
                }" data-notification-id="${
                  n.id
                }"><div class="notification-symbol"><svg class="icon"><use href="#i-bell"/></svg></div><div><strong>${escapeHtml(
                  n.title
                )}</strong><p>${escapeHtml(
                  n.text
                )}</p><div class="notification-actions"><span>เปิดรายละเอียด</span><span data-hide-notification="${
                  n.id
                }">ซ่อน</span></div></div><time>${escapeHtml(
                  n.time
                )}</time></button>`
            )
            .join("")}`
      )
      .join("");
  }
  function addNotification(role, title, text, unread = true) {
    notificationSets[role].unshift({
      id: `n-${Date.now()}`,
      symbol: "•",
      title,
      text,
      time: "เมื่อสักครู่",
      unread,
    });
    if (role === currentRole) renderNotifications();
  }
  function markNotificationsRead() {
    notificationSets[currentRole].forEach((n) => (n.unread = false));
    renderNotifications();
    toast("ทำเครื่องหมายว่าอ่านทั้งหมดแล้ว");
  }
  function renderStaff() {
    const roleColors = {
      แม่บ้าน: "#159a75",
      ช่าง: "#f97316",
      ธุรการ: "#2563eb",
      แอดมิน: "#6757d9",
    };
    $("#staffTable").innerHTML = staffData
      .map((s, i) => {
        const stats = staffOverviewStats(s);
        return `<tr><td><div class="person"><div class="person-avatar" style="background:${
          roleColors[s.role]
        }18;color:${roleColors[s.role]}">${s.name.slice(
          0,
          2
        )}</div><div><strong>${s.name}</strong><br><small>${
          s.status === "ใช้งาน" ? "staff@building.local" : "บัญชีระงับ"
        }</small></div></div></td><td>${
          s.id
        }</td><td><span class="badge neutral">${s.role}</span></td><td>${
          s.zone || "-"
        }<br><small>ปัจจุบัน ${stats.active} · เสร็จ ${stats.closed} · คืน ${
          stats.returned
        }</small></td><td><span class="badge ${
          s.status === "ใช้งาน" ? "done" : "wait"
        }">${
          s.status
        }</span></td><td><div class="row-actions"><button class="small-btn" type="button" data-staff-action="detail" data-staff-index="${i}">ดูรายละเอียด</button><button class="small-btn" type="button" data-staff-action="edit" data-staff-index="${i}">แก้ไข Staff</button><button class="small-btn" type="button" data-staff-action="toggle" data-staff-index="${i}">${
          s.status === "ใช้งาน" ? "ปิดบัญชี" : "เปิดใช้"
        }</button><button class="small-btn delete" type="button" data-staff-action="remove" data-staff-index="${i}">ลบ</button></div></td></tr>`;
      })
      .join("");
    $("#staffTotal").textContent = staffData.length;
  }
  function openEditStaff(index, trigger = document.activeElement) {
    const staff = staffData[index];
    if (!staff) return;
    $("#editStaffIndex").value = index;
    $("#editStaffName").value = staff.name;
    $("#editStaffEmail").value = "staff@building.local";
    $("#editStaffRole").value = staff.role;
    $("#editStaffZone").value = staff.zone || "";
    openModal("editStaffModal", trigger);
  }
  function changeStaffRole(i, value) {
    const old = staffData[i].role;
    staffData[i].role = value;
    addAudit(
      "staff",
      "อัปเดต Role",
      staffData[i].id,
      staffData[i].name,
      `เปลี่ยนจาก ${old} เป็น ${value}`
    );
    toast(`เปลี่ยน Role ของ ${staffData[i].name} เป็น ${value} แล้ว`);
  }
  function toggleStaff(i) {
    const staff = staffData[i];
    requestConfirmation(
      staff.status === "ใช้งาน" ? "ยืนยันปิดบัญชี" : "ยืนยันเปิดบัญชี",
      `${staff.status === "ใช้งาน" ? "ปิด" : "เปิด"}การใช้งานบัญชี ${
        staff.name
      } หรือไม่?`,
      () => {
        staff.status = staff.status === "ใช้งาน" ? "พักงาน" : "ใช้งาน";
        addAudit(
          "staff",
          "อัปเดตสถานะ",
          staff.id,
          staff.name,
          `เปลี่ยนสถานะบัญชีเป็น ${staff.status}`
        );
        renderStaff();
        toast("อัปเดตสถานะบัญชีแล้ว");
      }
    );
  }
  function removeStaff(i) {
    if (currentRole !== "admin") return;
    const staff = staffData[i];
    requestConfirmation(
      "ยืนยันลบบัญชี",
      `ลบบัญชี ${staff.name} แบบ Soft Delete หรือไม่?`,
      () => {
        const [record] = staffData.splice(i, 1);
        storeDeletedRecord("staff", record, "staffData", record.name);
        renderStaff();
        renderHistory();
        toast("ย้ายบัญชี Staff ไปยังรายการที่ลบแล้ว");
      }
    );
  }
  function makeRoomUrl() {
    const base = $("#baseUrl").value.trim(),
      service = $("#service").value,
      params = new URLSearchParams({
        building: $("#building").value.trim(),
        floor: $("#floor").value.trim(),
        room: $("#room").value.trim(),
      });
    if (service !== "report") params.set("service", service);
    return `${base}?${params.toString()}`;
  }
  function fallbackQrPng(text) {
    const canvas = document.createElement("canvas");
    canvas.width = 168;
    canvas.height = 168;
    const context = canvas.getContext("2d");
    if (!context) return "";
    context.fillStyle = "#fff";
    context.fillRect(0, 0, 168, 168);
    let seed = [...text].reduce((sum, char) => sum + char.charCodeAt(0), 0);
    context.fillStyle = "#17202b";
    for (let row = 0; row < 21; row++)
      for (let col = 0; col < 21; col++) {
        seed = (seed * 9301 + 49297) % 233280;
        if (seed / 233280 > 0.52) context.fillRect(col * 8, row * 8, 8, 8);
      }
    return canvas.toDataURL("image/png");
  }
  function generateQr(addToList = false) {
    const url = makeRoomUrl();
    $("#qrRoomName").textContent = $("#room").value.trim();
    $("#qrUrlText").textContent = url;
    const box = $("#qrCode");
    box.innerHTML = "";
    if (window.QRCode)
      new QRCode(box, {
        text: url,
        width: 168,
        height: 168,
        colorDark: "#17202b",
        colorLight: "#ffffff",
        correctLevel: QRCode.CorrectLevel.M,
      });
    else
      box.innerHTML =
        '<div class="qr-fallback" aria-label="ตัวอย่าง QR"></div>';
    if (addToList) {
      const item = document.createElement("div");
      item.className = "room-item";
      item.innerHTML = `<div class="mini-qr"></div><div><strong>${escapeHtml(
        $("#room").value.trim()
      )} · ${escapeHtml(
        $("#building").value.trim()
      )}</strong><small>ชั้น ${escapeHtml(
        $("#floor").value.trim()
      )} · ${escapeHtml(
        $("#service").selectedOptions[0].text
      )}</small></div><button class="small-btn" type="button" data-copy-room-url="${encodeURIComponent(
        url
      )}">คัดลอกลิงก์</button>`;
      $("#roomList").prepend(item);
      toast("สร้าง QR และเพิ่มห้องแล้ว");
    }
  }
  function openModal(id, trigger = document.activeElement) {
    const modal = $(`#${id}`);
    if (!modal) return;
    $$(".modal.open").forEach((item) => closeModal(item.id, false));
    lastModalTrigger = trigger instanceof HTMLElement ? trigger : null;
    modal.classList.add("open");
    modal.removeAttribute("aria-hidden");
    document.body.classList.add("modal-open");
    requestAnimationFrame(() =>
      modal
        .querySelector(
          'input:not([type="hidden"]),select,textarea,button:not([disabled])'
        )
        ?.focus()
    );
  }
  function closeModal(id, restoreFocus = true) {
    const modal = $(`#${id}`);
    if (!modal) return;
    modal.classList.remove("open");
    modal.setAttribute("aria-hidden", "true");
    if (!$(".modal.open")) document.body.classList.remove("modal-open");
    if (restoreFocus && lastModalTrigger && document.contains(lastModalTrigger))
      lastModalTrigger.focus();
  }
  function closeSidebar() {
    $("#sidebar").classList.remove("open");
    $("#sidebarBackdrop").classList.remove("open");
    $("#menuToggle").setAttribute("aria-expanded", "false");
  }
  function toggleSidebar() {
    const open = !$("#sidebar").classList.contains("open");
    $("#sidebar").classList.toggle("open", open);
    $("#sidebarBackdrop").classList.toggle("open", open);
    $("#menuToggle").setAttribute("aria-expanded", String(open));
  }
  function requestConfirmation(title, text, action, label = "ยืนยัน") {
    pendingConfirmAction = action;
    $("#confirmModalTitle").textContent = title;
    $("#confirmModalText").textContent = text;
    $("#confirmActionButton").textContent = label;
    openModal("confirmModal");
  }
  function showSuccess(message) {
    $("#successModalText").textContent = message;
    openModal("successModal");
  }
  function renderAssignStaff() {
    const query = ($("#assignSearch").value || "").trim().toLowerCase(),
      role = $("#assignRole").value;
    const options = staffData.filter(
      (staff) =>
        staff.role === role &&
        staff.status === "ใช้งาน" &&
        `${staff.name} ${staff.zone}`.toLowerCase().includes(query)
    );
    $("#assignStaffList").innerHTML = options.length
      ? options
          .map((staff) => {
            const stats = staffOverviewStats(staff);
            return `<button type="button" class="staff-choice ${
              $("#assignStaff").value === staff.name ? "selected" : ""
            }" data-assign-staff="${escapeHtml(
              staff.name
            )}"><span><strong>${escapeHtml(
              staff.name
            )}</strong><small>${escapeHtml(staff.zone || "-")} · งานปัจจุบัน ${
              stats.active
            }</small></span><span class="badge done">พร้อมทำงาน</span></button>`;
          })
          .join("")
      : '<div class="empty">ไม่พบ Staff ที่พร้อมทำงาน</div>';
  }
  function openAssignJob(id, trigger = document.activeElement) {
    const job = allJobs.find((item) => item.id === id);
    if (!job) return;
    $("#assignJobId").value = id;
    $("#assignNote").value = "";
    $("#assignSearch").value = "";
    $("#assignRole").value = job.type === "repair" ? "ช่าง" : "แม่บ้าน";
    $("#assignStaff").value = "";
    renderAssignStaff();
    $("#assignModalTitle").textContent = job.assignee
      ? `เปลี่ยนผู้รับผิดชอบ · ${id}`
      : `มอบหมาย ${id}`;
    openModal("assignModal", trigger);
  }
  function jobTimeline(job) {
    const steps = [
      ["สร้างคำร้อง", job.time],
      ["ผู้รับผิดชอบ", job.assignee || "ยังไม่มีผู้รับผิดชอบ"],
      ...(job.timeline || []).map((item) => [
        item.title,
        `${item.detail} · ${item.time}`,
      ]),
      ["สถานะปัจจุบัน", job.status],
    ];
    return steps
      .map(
        (step) =>
          `<div class="timeline-item"><span class="timeline-dot"></span><div><strong>${escapeHtml(
            step[0]
          )}</strong><small>${escapeHtml(step[1])}</small></div></div>`
      )
      .join("");
  }
  function renderJobQuickActions(job) {
    const isMine = job.assignee === activeStaffName(),
      canEdit = isMine || currentRole === "admin",
      buttons = [];
    if (!job.assignee && currentRole !== "admin")
      buttons.push(["accept", "รับงาน", "primary-action"]);
    if (!job.assignee && currentRole === "admin")
      buttons.push(["assign", "มอบหมายงาน", "primary-action"]);
    if (canEdit && !isTerminalStatus(job.status)) {
      buttons.push(
        ["start", "เริ่มดำเนินการ", "primary-action"],
        ["status", "อัปเดตสถานะ", ""],
        ["note", "เพิ่มหมายเหตุ", ""],
        ["upload", "เพิ่มรูป", ""],
        ["complete", "เสร็จสิ้น", ""]
      );
      if (isMine && currentRole !== "admin")
        buttons.push(["return", "คืนงานเข้าคิวกลาง", ""]);
      if (currentRole === "admin")
        buttons.push(["assign", "เปลี่ยนผู้รับผิดชอบ", ""]);
    }
    $("#jobQuickActions").innerHTML = buttons.length
      ? buttons
          .map(
            (item) =>
              `<button type="button" class="quick-action ${item[2]}" data-detail-action="${item[0]}">${item[1]}</button>`
          )
          .join("")
      : '<div class="read-only" style="grid-column:1/-1">ดูรายละเอียดได้ แต่ไม่มีสิทธิ์แก้ไขงานนี้</div>';
  }
  function openJobDetail(id, trigger = document.activeElement) {
    const job = allJobs.find((item) => item.id === id);
    if (!job) return;
    selectedJobId = id;
    $("#jobDetailCode").textContent = `${id} · ${job.category}`;
    $("#jobDetailTitle").textContent = job.title;
    $("#jobDetailDescription").textContent = job.detail;
    $("#jobDetailRoom").textContent = job.room;
    $("#jobDetailReporter").textContent = job.reporter;
    $("#jobDetailContact").textContent = "building.user@cmu.ac.th";
    $("#jobDetailAssignee").textContent =
      job.assignee || "ยังไม่มีผู้รับผิดชอบ";
    $("#jobDetailBadges").innerHTML = `<span class="badge ${
      job.priority === "เร่งด่วน" ? "danger" : "wait"
    }">${job.priority}</span><span class="badge ${badgeClass(job.status)}">${
      job.status
    }</span><span class="badge neutral">${job.time}</span>`;
    $("#jobDetailIcon use").setAttribute(
      "href",
      job.type === "repair" ? "#i-tools" : "#i-broom"
    );
    $("#jobTimeline").innerHTML = jobTimeline(job);
    $("#jobDetailNotes").textContent = job.note || "ยังไม่มีหมายเหตุ";
    renderJobQuickActions(job);
    openModal("jobDetailModal", trigger);
  }
  function openStatusUpdate(id, trigger = document.activeElement) {
    const job = allJobs.find((item) => item.id === id);
    if (!job) return;
    const options =
      currentRole === "technician"
        ? ["กำลังดำเนินการ", "รอข้อมูลเพิ่มเติม", "รออะไหล่", "เสร็จสิ้น"]
        : currentRole === "housekeeper"
        ? ["กำลังดำเนินการ", "พักงาน", "รอข้อมูลเพิ่มเติม", "เสร็จสิ้น"]
        : currentRole === "clerk"
        ? [
            "กำลังตรวจสอบ",
            "ขอข้อมูลเพิ่มเติม",
            "อนุมัติ",
            "ไม่อนุมัติ",
            "นัดหมายแล้ว",
            "คืนของแล้ว",
          ]
        : job.type === "repair"
        ? ["กำลังดำเนินการ", "รอข้อมูลเพิ่มเติม", "รออะไหล่", "เสร็จสิ้น"]
        : ["กำลังดำเนินการ", "พักงาน", "รอข้อมูลเพิ่มเติม", "เสร็จสิ้น"];
    $("#statusJobId").value = id;
    $("#newJobStatus").innerHTML = options
      .map((value) => `<option>${value}</option>`)
      .join("");
    $("#statusNote").value = "";
    $("#statusImage").value = "";
    $("#statusTime").value = nowThai();
    $("#statusUpdateTitle").textContent = `อัปเดตสถานะ · ${id}`;
    openModal("statusUpdateModal", trigger);
  }
  function openNoteModal(id, trigger = document.activeElement) {
    $("#noteJobId").value = id;
    $("#noteText").value = "";
    $("#notePrivate").checked = true;
    openModal("noteModal", trigger);
  }
  function openUploadModal(id, trigger = document.activeElement) {
    $("#uploadJobId").value = id;
    $("#uploadForm").reset();
    $("#uploadJobId").value = id;
    resetUploadPreview();
    openModal("uploadModal", trigger);
  }
  function openCompleteModal(id, trigger = document.activeElement) {
    $("#completeJobId").value = id;
    $("#completeResult").value = "";
    $("#completeNote").value = "";
    $("#completeImage").value = "";
    $("#completeDate").value = todayISO();
    openModal("completeModal", trigger);
  }
  function changeJobFromDetail(action) {
    const job = allJobs.find((item) => item.id === selectedJobId);
    if (!job) return;
    closeModal("jobDetailModal", false);
    if (action === "accept") {
      requestAcceptJob(job.id);
      return;
    }
    if (action === "assign") {
      openAssignJob(job.id);
      return;
    }
    if (action === "return") {
      openReturnJob(job.id);
      return;
    }
    if (action === "note") {
      openNoteModal(job.id);
      return;
    }
    if (action === "upload") {
      openUploadModal(job.id);
      return;
    }
    if (action === "complete") {
      openCompleteModal(job.id);
      return;
    }
    if (action === "status") {
      openStatusUpdate(job.id);
      return;
    }
    if (action === "start") {
      requestConfirmation(
        "ยืนยันเริ่มดำเนินการ",
        `เริ่มดำเนินการงาน ${job.id} หรือไม่?`,
        () => applyJobStatus(job, "กำลังดำเนินการ", "เริ่มดำเนินการ")
      );
      return;
    }
  }
  function applyJobStatus(job, next, note) {
    const previous = job.status;
    job.status = next;
    job.note = note || job.note;
    appendJobTimeline(
      job,
      "อัปเดตสถานะ",
      `${previous} → ${next}${note ? ` · ${note}` : ""}`
    );
    addAudit(
      "jobs",
      next === "เสร็จสิ้น" ? "ปิดงาน" : "อัปเดตสถานะ",
      job.id,
      job.title,
      `เปลี่ยนจาก “${previous}” เป็น “${next}”`
    );
    recordWorkHistory({
      itemId: job.id,
      title: job.title,
      category: job.category,
      action: next === "เสร็จสิ้น" ? "ปิดงาน" : "อัปเดตสถานะ",
      status: next,
      detail: `${previous} → ${next} · ${note || job.room}`,
    });
    renderJobs();
    renderMetrics();
    renderQueue();
    renderStaffOverview();
  }
  function openLostDetail(tab, id, trigger = document.activeElement) {
    const item = lostSets[tab]?.find((record) => record.id === id);
    if (!item) return;
    selectedJobId = "";
    $("#jobDetailCode").textContent = `${id} · ของหาย–ของได้คืน`;
    $("#jobDetailTitle").textContent = item.title;
    $("#jobDetailDescription").textContent = item.place;
    $("#jobDetailRoom").textContent = item.place;
    $("#jobDetailReporter").textContent = "ผู้แจ้งรายการ";
    $("#jobDetailContact").textContent = "ติดต่อผ่านระบบ Building Care";
    $("#jobDetailAssignee").textContent = item.assignee || "ธุรการส่วนกลาง";
    $("#jobDetailBadges").innerHTML = `<span class="badge ${badgeClass(
      item.status
    )}">${item.status}</span>`;
    $("#jobDetailIcon use").setAttribute("href", "#i-box");
    $("#jobTimeline").innerHTML = [
      ["สร้างรายการ", "บันทึกในระบบแล้ว"],
      ["ตรวจสอบข้อมูล", item.status],
      ["ส่งมอบ", item.status === "คืนของแล้ว" ? "คืนของแล้ว" : "ยังไม่เสร็จ"],
    ]
      .map(
        (step) =>
          `<div class="timeline-item"><span class="timeline-dot"></span><div><strong>${step[0]}</strong><small>${step[1]}</small></div></div>`
      )
      .join("");
    $("#jobDetailNotes").textContent =
      item.decisionReason || "ยังไม่มีหมายเหตุ";
    $(
      "#jobQuickActions"
    ).innerHTML = `<button type="button" class="quick-action primary-action" data-lost-detail-action="approve" data-tab="${tab}" data-item-id="${id}">ตรวจสอบและอนุมัติ</button><button type="button" class="quick-action" data-lost-detail-action="reject" data-tab="${tab}" data-item-id="${id}">ไม่อนุมัติ</button>`;
    openModal("jobDetailModal", trigger);
  }
  function openClaimDetail(id, trigger = document.activeElement) {
    const item = lostSets.claims.find((record) => record.id === id);
    if (!item) return;
    $("#claimDetailCode").textContent = `${id} · ${item.status}`;
    $("#claimDetailTitle").textContent = item.title;
    $("#claimRequester").textContent = item.requester || "กิตติพงษ์ ศรีสุข";
    $("#claimContact").textContent = item.contact || "089-123-4567";
    $("#claimDate").textContent = item.requestDate || "วันนี้ 09:20";
    $("#claimAppointment").textContent = item.custody || "ยังไม่มีนัดหมาย";
    $("#claimEvidence").textContent =
      item.evidence || `${item.place} · ให้รายละเอียดสี ตำหนิ และสิ่งของภายใน`;
    $("#claimSecret").textContent =
      item.secret || "รหัสซิปและสิ่งของภายในใช้ตรวจสอบต่อหน้าเจ้าหน้าที่";
    $("#claimTimeline").innerHTML = [
      ["ส่งคำขอ", $("#claimDate").textContent],
      ["ตรวจสอบล่าสุด", item.status],
      ["ผู้รับผิดชอบ", item.assignee || "ธุรการส่วนกลาง"],
    ]
      .map(
        (step) =>
          `<div class="timeline-item"><span class="timeline-dot"></span><div><strong>${step[0]}</strong><small>${step[1]}</small></div></div>`
      )
      .join("");
    $("#claimActions").innerHTML = [
      ["more", "ขอข้อมูลเพิ่มเติม", ""],
      ["approve", "อนุมัติ", "primary-action"],
      ["reject", "ไม่อนุมัติ", ""],
      ["appointment", "สร้างนัดหมาย", ""],
    ]
      .map(
        (action) =>
          `<button type="button" class="quick-action ${action[2]}" data-claim-action="${action[0]}" data-claim-id="${id}">${action[1]}</button>`
      )
      .join("");
    openModal("claimDetailModal", trigger);
  }
  function updateClaimWithConfirmation(id, action, trigger) {
    const item = lostSets.claims.find((record) => record.id === id);
    if (!item) return;
    if (action === "appointment") {
      closeModal("claimDetailModal", false);
      openAppointment(id, trigger);
      return;
    }
    const map = {
      more: ["ขอข้อมูลเพิ่มเติม", "ขอข้อมูลเพิ่มเติม"],
      approve: ["ยืนยันอนุมัติคำขอ", "ผ่านการตรวจสอบ"],
      reject: ["ยืนยันไม่อนุมัติคำขอ", "ไม่ผ่านการตรวจสอบ"],
    };
    const [title, status] = map[action];
    closeModal("claimDetailModal", false);
    requestConfirmation(
      title,
      `ยืนยันการดำเนินการกับคำขอ ${id} หรือไม่?`,
      () => {
        item.status = status;
        item.assignee = activeStaffName();
        addAudit("lost", title, id, item.title, `เปลี่ยนสถานะเป็น ${status}`);
        recordWorkHistory({
          itemId: id,
          title: item.title,
          category: "คำขอรับของ",
          action: title,
          status,
          detail: `ตรวจสอบโดย ${activeStaffName()}`,
        });
        renderLost();
        showSuccess(`อัปเดตคำขอ ${id} แล้ว`);
      }
    );
  }
  function openAppointment(id, trigger = document.activeElement) {
    const item = lostSets.claims.find((record) => record.id === id);
    if (!item) return;
    $("#appointmentItemId").value = id;
    $("#appointmentTitle").textContent = `นัดหมายรับของ · ${id}`;
    $("#appointmentDate").value = todayISO();
    $("#appointmentTime").value = "10:00";
    $("#appointmentNote").value = "";
    openModal("appointmentModal", trigger);
  }
  function renderAnnouncements() {
    const list = $("#announcementList");
    if (!list) return;
    list.innerHTML = announcements.length
      ? announcements
          .map(
            (item) =>
              `<article class="announcement-card"><div><div class="job-meta"><span class="badge ${
                item.status === "เผยแพร่" ? "done" : "wait"
              }">${item.status}</span>${
                item.pinned ? '<span class="badge progress">ปักหมุด</span>' : ""
              }<span class="badge neutral">${escapeHtml(
                item.audience
              )}</span></div><h3>${escapeHtml(item.title)}</h3><p>${escapeHtml(
                item.content
              )}</p><small>${item.start} – ${
                item.end
              }</small></div><div class="row-actions"><button type="button" class="small-btn" data-announcement-action="edit" data-announcement-id="${
                item.id
              }">แก้ไข</button><button type="button" class="small-btn delete" data-announcement-action="delete" data-announcement-id="${
                item.id
              }">ลบ</button></div></article>`
          )
          .join("")
      : '<div class="empty">ยังไม่มีประกาศ</div>';
    $("#publishedCount").textContent = announcements.filter(
      (item) => item.status === "เผยแพร่"
    ).length;
    $("#draftCount").textContent = announcements.filter(
      (item) => item.status === "Draft"
    ).length;
    $("#pinnedCount").textContent = announcements.filter(
      (item) => item.pinned
    ).length;
  }
  function openAnnouncementEditor(
    item = null,
    trigger = document.activeElement
  ) {
    $("#announcementForm").reset();
    $("#announcementId").value = item?.id || "";
    $("#announcementModalTitle").textContent = item
      ? "แก้ไขประกาศ"
      : "สร้างประกาศ";
    $("#announcementTitle").value = item?.title || "";
    $("#announcementContent").value = item?.content || "";
    $("#announcementAudience").value = item?.audience || "ผู้ใช้งานทุกคน";
    $("#announcementStart").value = item?.start || todayISO();
    $("#announcementEnd").value = item?.end || todayISO();
    $("#announcementPinned").checked = Boolean(item?.pinned);
    openModal("announcementModal", trigger);
  }
  function saveAnnouncement(status) {
    const form = $("#announcementForm");
    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }
    const id =
      $("#announcementId").value ||
      `AN-${String(32 + announcements.length).padStart(3, "0")}`;
    const record = {
      id,
      title: $("#announcementTitle").value.trim(),
      content: $("#announcementContent").value.trim(),
      audience: $("#announcementAudience").value,
      start: $("#announcementStart").value,
      end: $("#announcementEnd").value,
      pinned: $("#announcementPinned").checked,
      status,
    };
    const index = announcements.findIndex((item) => item.id === id);
    if (index >= 0) announcements[index] = record;
    else announcements.unshift(record);
    addAudit(
      "announcement",
      index >= 0 ? "แก้ไขประกาศ" : "สร้างประกาศ",
      id,
      record.title,
      `สถานะ ${status}`
    );
    closeModal("announcementModal", false);
    renderAnnouncements();
    showSuccess(
      status === "เผยแพร่" ? "เผยแพร่ประกาศแล้ว" : "บันทึกฉบับร่างแล้ว"
    );
  }
  function renderMobileQuickActions() {
    const actions =
      currentRole === "technician"
        ? [
            ["new-jobs", "ดูงานเข้าใหม่"],
            ["mine", "งานของฉัน"],
            ["scan", "สแกน QR ห้อง"],
          ]
        : currentRole === "housekeeper"
        ? [
            ["new-jobs", "ดูงานเข้าใหม่"],
            ["mine", "งานของฉัน"],
            ["schedule", "ดูตารางงาน"],
          ]
        : currentRole === "clerk"
        ? [
            ["found", "ของที่พบใหม่"],
            ["claims", "คำขอรับคืน"],
            ["appointments", "นัดหมายวันนี้"],
          ]
        : [
            ["announcement", "สร้างประกาศ"],
            ["add-staff", "เพิ่ม Staff"],
            ["qr", "สร้าง QR"],
            ["assign", "มอบหมายงาน"],
          ];
    $("#mobileQuickActions").innerHTML = actions
      .map(
        (item) =>
          `<button type="button" class="quick-action" data-quick-action="${item[0]}">${item[1]}</button>`
      )
      .join("");
  }
  function renderDashboardQuickActions() {
    const actions =
      currentRole === "technician"
        ? [
            "รับงาน",
            "เริ่มดำเนินการ",
            "อัปเดตความคืบหน้า",
            "แจ้งรออะไหล่",
            "ปิดงาน",
            "คืนงานเข้าคิวกลาง",
          ]
        : currentRole === "housekeeper"
        ? [
            "รับงาน",
            "เริ่มทำความสะอาด",
            "พักงาน",
            "อัปเดตความคืบหน้า",
            "เสร็จสิ้น",
            "คืนงานเข้าคิวกลาง",
          ]
        : currentRole === "clerk"
        ? [
            "รับเคส",
            "ตรวจสอบข้อมูล",
            "อนุมัติรับคืน",
            "ไม่อนุมัติ",
            "นัดหมายรับของ",
            "ยืนยันคืนของแล้ว",
          ]
        : [
            "ดูงานทั้งหมด",
            "มอบหมายงาน",
            "จัดการ Staff",
            "สร้าง QR",
            "สร้างประกาศ",
            "ดู Activity Log",
          ];
    $("#dashboardQuickActions").innerHTML = actions
      .map(
        (label, index) =>
          `<button type="button" class="quick-action ${
            index === 0 ? "primary-action" : ""
          }" data-dashboard-action="${index}">${label}</button>`
      )
      .join("");
  }
  $$(".nav-item").forEach((button) =>
    button.addEventListener("click", () => navigate(button.dataset.page))
  );
  $$("[data-go]").forEach((button) =>
    button.addEventListener("click", () => navigate(button.dataset.go))
  );
  $$("[data-role-switch]").forEach((button) =>
    button.addEventListener("click", () => setRole(button.dataset.roleSwitch))
  );
  $("#menuToggle").addEventListener("click", toggleSidebar);
  $("#sidebarBackdrop").addEventListener("click", closeSidebar);
  $("#sidebarCollapse").addEventListener("click", () => {
    $(".app").classList.toggle("sidebar-collapsed");
    $("#sidebarCollapse use").setAttribute(
      "href",
      $(".app").classList.contains("sidebar-collapsed")
        ? "#i-menu"
        : "#i-chevron"
    );
  });
  $("#dashboardQuickActions").addEventListener("click", (event) => {
    const button = event.target.closest("[data-dashboard-action]");
    if (!button) return;
    const index = Number(button.dataset.dashboardAction);
    if (currentRole === "clerk") {
      navigate("lost");
      currentLostTab = index < 2 ? "inventory" : "claims";
      $$("#lostTabs .tab").forEach((tab) =>
        tab.classList.toggle("active", tab.dataset.tab === currentLostTab)
      );
      renderLost();
      if (index === 4 && lostSets.claims[0])
        openAppointment(lostSets.claims[0].id, button);
      return;
    }
    if (currentRole === "admin") {
      navigate(
        ["jobs", "jobs", "staff", "qr", "announcements", "history"][index]
      );
      return;
    }
    currentBoardView = index === 0 ? "unassigned" : "mine";
    $$("#boardTabs .board-tab").forEach((tab) =>
      tab.classList.toggle("active", tab.dataset.view === currentBoardView)
    );
    navigate("jobs");
    renderJobs();
    const candidate = roleJobs().find((job) =>
      index === 0 ? !job.assignee : job.assignee === activeStaffName()
    );
    if (candidate && index > 0) openJobDetail(candidate.id, button);
  });
  function confirmLogout() {
    requestConfirmation(
      "ออกจากระบบ?",
      "ต้องการออกจากระบบเจ้าหน้าที่บนอุปกรณ์นี้หรือไม่?",
      () => {
        localStorage.removeItem("buildingCareRole");
        location.href = "staff-login.html";
      },
      "ออกจากระบบ"
    );
  }
  $("#logoutBtn").addEventListener("click", confirmLogout);
  $("#profileLogout").addEventListener("click", confirmLogout);
  $("#profileButton").addEventListener("click", (event) =>
    openModal("profileModal", event.currentTarget)
  );
  $("#mobileProfile").addEventListener("click", (event) =>
    openModal("profileModal", event.currentTarget)
  );
  $("#changePassword").addEventListener("click", () =>
    toast("ส่งลิงก์เปลี่ยนรหัสผ่านไปยังอีเมลเจ้าหน้าที่แล้ว")
  );
  $("#notificationSettings").addEventListener("click", () =>
    toast("บันทึกการตั้งค่าการแจ้งเตือนแล้ว")
  );
  $$("[data-mobile-page]").forEach((button) =>
    button.addEventListener("click", () =>
      navigate(
        currentRole === "clerk" && button.dataset.mobilePage === "jobs"
          ? "lost"
          : button.dataset.mobilePage
      )
    )
  );
  $("#mobileQuickAction").addEventListener("click", (event) =>
    openModal("quickActionModal", event.currentTarget)
  );
  $("#mobileQuickActions").addEventListener("click", (event) => {
    const button = event.target.closest("[data-quick-action]");
    if (!button) return;
    const action = button.dataset.quickAction;
    closeModal("quickActionModal", false);
    if (action === "new-jobs") {
      currentBoardView = "unassigned";
      navigate("jobs");
      renderJobs();
    } else if (action === "mine") {
      currentBoardView = "mine";
      navigate("jobs");
      renderJobs();
    } else if (action === "scan") toast("เปิดกล้องสแกน QR ห้องแล้ว");
    else if (action === "schedule") {
      navigate("jobs");
      toast("แสดงตารางงานวันนี้แล้ว");
    } else if (action === "found") {
      navigate("lost");
      currentLostTab = "inventory";
      renderLost();
      openModal("foundModal", button);
    } else if (action === "claims" || action === "appointments") {
      navigate("lost");
      currentLostTab = "claims";
      renderLost();
      if (action === "appointments" && lostSets.claims[0])
        openAppointment(lostSets.claims[0].id, button);
    } else if (action === "announcement") openAnnouncementEditor(null, button);
    else if (action === "add-staff") openModal("staffModal", button);
    else if (action === "qr") {
      navigate("qr");
      openModal("qrFormModal", button);
    } else if (action === "assign") {
      navigate("jobs");
      const job = allJobs.find((item) => !item.assignee);
      if (job) openAssignJob(job.id, button);
      else toast("ไม่มีงานรอมอบหมาย");
    }
  });
  $("#myHistoryFrom").addEventListener("change", renderMyHistory);
  $("#myHistoryTo").addEventListener("change", renderMyHistory);
  $("#myHistoryType").addEventListener("change", renderMyHistory);
  $("#myHistorySearch").addEventListener("input", renderMyHistory);
  $("#resetMyHistoryFilters").addEventListener("click", () => {
    $("#myHistoryFrom").value = "";
    $("#myHistoryTo").value = "";
    $("#myHistoryType").value = "all";
    $("#myHistorySearch").value = "";
    renderMyHistory();
  });
  $("#overviewRoleFilter").addEventListener("change", renderStaffOverview);
  $("#overviewFrom").addEventListener("change", renderStaffOverview);
  $("#overviewTo").addEventListener("change", renderStaffOverview);
  $("#overviewSearch").addEventListener("input", renderStaffOverview);
  $("#resetOverviewFilters").addEventListener("click", () => {
    $("#overviewRoleFilter").value = "all";
    $("#overviewFrom").value = "";
    $("#overviewTo").value = "";
    $("#overviewSearch").value = "";
    selectedOverviewStaff = "";
    renderStaffOverview();
  });
  $("#jobSearch").addEventListener("input", renderJobs);
  $("#categoryFilter").addEventListener("change", renderJobs);
  $("#jobStatusFilter").addEventListener("change", renderJobs);
  $("#boardTabs").addEventListener("click", (event) => {
    const button = event.target.closest(".board-tab");
    if (!button) return;
    currentBoardView = button.dataset.view;
    $$("#boardTabs .board-tab").forEach((tab) =>
      tab.classList.toggle("active", tab === button)
    );
    renderJobs();
  });
  $("#jobList").addEventListener("click", (event) => {
    const actionButton = event.target.closest("[data-job-action]");
    if (actionButton) {
      event.stopPropagation();
      const id = actionButton.dataset.jobId,
        action = actionButton.dataset.jobAction;
      if (action === "accept") requestAcceptJob(id, actionButton);
      if (action === "assign") openAssignJob(id, actionButton);
      if (action === "delete") deleteJob(id);
      if (action === "return") openReturnJob(id);
      if (action === "status") openStatusUpdate(id, actionButton);
      if (action === "detail") openJobDetail(id, actionButton);
      return;
    }
    const card = event.target.closest("[data-job-card]");
    if (card) openJobDetail(card.dataset.jobCard, card);
  });
  $("#jobList").addEventListener("keydown", (event) => {
    const card = event.target.closest("[data-job-card]");
    if (card && (event.key === "Enter" || event.key === " ")) {
      event.preventDefault();
      openJobDetail(card.dataset.jobCard, card);
    }
  });
  $("#jobQuickActions").addEventListener("click", (event) => {
    const jobAction = event.target.closest("[data-detail-action]");
    if (jobAction) {
      changeJobFromDetail(jobAction.dataset.detailAction);
      return;
    }
    const lostAction = event.target.closest("[data-lost-detail-action]");
    if (!lostAction) return;
    closeModal("jobDetailModal", false);
    if (lostAction.dataset.lostDetailAction === "approve")
      approveLostItem(lostAction.dataset.tab, lostAction.dataset.itemId);
    else if (lostAction.dataset.lostDetailAction === "reject")
      openReject(lostAction.dataset.tab, lostAction.dataset.itemId);
    else {
      currentLostTab = "claims";
      renderLost();
      navigate("lost");
    }
  });
  $("#assignForm").addEventListener("submit", (event) => {
    event.preventDefault();
    if (!$("#assignStaff").value) {
      toast("กรุณาเลือก Staff ที่รับผิดชอบ");
      return;
    }
    const job = allJobs.find((item) => item.id === $("#assignJobId").value);
    if (!job) return;
    const previous = job.assignee;
    job.assignee = $("#assignStaff").value;
    job.status = "รับงานแล้ว";
    job.note = $("#assignNote").value.trim();
    appendJobTimeline(
      job,
      previous ? "เปลี่ยนผู้รับผิดชอบ" : "มอบหมายงาน",
      `${previous ? `${previous} → ` : ""}${job.assignee}`
    );
    addAudit(
      "jobs",
      "มอบหมายงาน",
      job.id,
      job.title,
      `มอบหมายให้ ${job.assignee}`
    );
    closeModal("assignModal", false);
    renderJobs();
    renderMetrics();
    renderQueue();
    renderStaffOverview();
    showSuccess(`มอบหมาย ${job.id} ให้ ${job.assignee} แล้ว`);
  });
  $("#assignSearch").addEventListener("input", renderAssignStaff);
  $("#assignRole").addEventListener("change", () => {
    $("#assignStaff").value = "";
    renderAssignStaff();
  });
  $("#assignStaffList").addEventListener("click", (event) => {
    const button = event.target.closest("[data-assign-staff]");
    if (!button) return;
    $("#assignStaff").value = button.dataset.assignStaff;
    renderAssignStaff();
  });
  function validImage(file) {
    return (
      file &&
      ["image/jpeg", "image/png", "image/webp"].includes(file.type) &&
      file.size <= 5242880
    );
  }
  function resetUploadPreview() {
    const preview = $("#progressPreview"),
      img = preview.querySelector("img");
    if (img.src?.startsWith("blob:")) URL.revokeObjectURL(img.src);
    img.removeAttribute("src");
    preview.querySelector("span").textContent = "";
    preview.classList.remove("visible");
  }
  function previewProgressFile(file) {
    if (!validImage(file)) {
      toast("รองรับ JPG, PNG หรือ WebP ไม่เกิน 5 MB");
      $("#progressImage").value = "";
      resetUploadPreview();
      return false;
    }
    const preview = $("#progressPreview");
    preview.querySelector("img").src = URL.createObjectURL(file);
    preview.querySelector("span").textContent = `${file.name} · ${(
      file.size / 1048576
    ).toFixed(1)} MB`;
    preview.classList.add("visible");
    return true;
  }
  $("#progressImage").addEventListener("change", (event) => {
    if (event.target.files[0]) previewProgressFile(event.target.files[0]);
  });
  $("#removeProgressImage").addEventListener("click", () => {
    $("#progressImage").value = "";
    resetUploadPreview();
  });
  ["dragenter", "dragover"].forEach((type) =>
    $("#uploadDropZone").addEventListener(type, (event) => {
      event.preventDefault();
      $("#uploadDropZone").classList.add("dragging");
    })
  );
  ["dragleave", "drop"].forEach((type) =>
    $("#uploadDropZone").addEventListener(type, (event) => {
      event.preventDefault();
      $("#uploadDropZone").classList.remove("dragging");
    })
  );
  $("#uploadDropZone").addEventListener("drop", (event) => {
    const file = event.dataTransfer.files[0];
    if (!validImage(file)) {
      toast("รองรับ JPG, PNG หรือ WebP ไม่เกิน 5 MB");
      return;
    }
    const transfer = new DataTransfer();
    transfer.items.add(file);
    $("#progressImage").files = transfer.files;
    previewProgressFile(file);
  });
  $("#statusUpdateForm").addEventListener("submit", (event) => {
    event.preventDefault();
    if (!event.currentTarget.checkValidity()) {
      event.currentTarget.reportValidity();
      return;
    }
    const job = allJobs.find((item) => item.id === $("#statusJobId").value);
    if (!job) return;
    const file = $("#statusImage").files[0];
    if (file && !validImage(file)) {
      toast("รองรับ JPG, PNG หรือ WebP ไม่เกิน 5 MB");
      return;
    }
    const next = $("#newJobStatus").value,
      note = $("#statusNote").value.trim();
    closeModal("statusUpdateModal", false);
    if (next === "เสร็จสิ้น") {
      openCompleteModal(job.id);
      $("#completeResult").value = note;
      return;
    }
    applyJobStatus(job, next, note);
    toast("บันทึกสถานะเรียบร้อย");
  });
  $("#noteForm").addEventListener("submit", (event) => {
    event.preventDefault();
    if (!event.currentTarget.checkValidity()) {
      event.currentTarget.reportValidity();
      return;
    }
    const job = allJobs.find((item) => item.id === $("#noteJobId").value);
    if (!job) return;
    const note = $("#noteText").value.trim(),
      scope = $("#notePrivate").checked ? "เฉพาะ Staff" : "ผู้เกี่ยวข้อง";
    job.note = note;
    appendJobTimeline(job, "เพิ่มหมายเหตุ", `${note} · ${scope}`);
    addAudit("jobs", "เพิ่มหมายเหตุ", job.id, job.title, note);
    recordWorkHistory({
      itemId: job.id,
      title: job.title,
      category: job.category,
      action: "เพิ่มหมายเหตุ",
      status: job.status,
      detail: `${note} · ${scope}`,
    });
    closeModal("noteModal", false);
    toast("บันทึกหมายเหตุแล้ว");
  });
  $("#uploadForm").addEventListener("submit", (event) => {
    event.preventDefault();
    const file = $("#progressImage").files[0];
    if (!event.currentTarget.checkValidity()) {
      event.currentTarget.reportValidity();
      return;
    }
    if (!validImage(file)) {
      toast("รองรับ JPG, PNG หรือ WebP ไม่เกิน 5 MB");
      return;
    }
    const job = allJobs.find((item) => item.id === $("#uploadJobId").value);
    if (!job) return;
    job.progressPhotos = job.progressPhotos || [];
    job.progressPhotos.push({
      name: file.name,
      description: $("#uploadDescription").value.trim(),
      time: nowThai(),
    });
    appendJobTimeline(
      job,
      "เพิ่มรูปความคืบหน้า",
      $("#uploadDescription").value.trim()
    );
    addAudit(
      "jobs",
      "เพิ่มรูป",
      job.id,
      job.title,
      $("#uploadDescription").value.trim()
    );
    closeModal("uploadModal", false);
    toast("อัปโหลดรูปเรียบร้อย");
  });
  $("#completeForm").addEventListener("submit", (event) => {
    event.preventDefault();
    if (!event.currentTarget.checkValidity()) {
      event.currentTarget.reportValidity();
      return;
    }
    const job = allJobs.find((item) => item.id === $("#completeJobId").value);
    if (!job) return;
    const file = $("#completeImage").files[0];
    if (file && !validImage(file)) {
      toast("รองรับ JPG, PNG หรือ WebP ไม่เกิน 5 MB");
      return;
    }
    const summary = `${$("#completeResult").value.trim()} · ${$(
      "#completeNote"
    ).value.trim()}`;
    applyJobStatus(job, "เสร็จสิ้น", summary);
    appendJobTimeline(job, "ปิดงาน", `เสร็จวันที่ ${$("#completeDate").value}`);
    closeModal("completeModal", false);
    showSuccess(`ปิดงาน ${job.id} เรียบร้อย งานถูกย้ายไปประวัติแล้ว`);
  });
  $("#historySearch").addEventListener("input", renderHistory);
  $("#historySourceFilter").addEventListener("change", renderHistory);
  $("#historyActionFilter").addEventListener("change", renderHistory);
  $("#historyTabs").addEventListener("click", (event) => {
    const button = event.target.closest(".board-tab");
    if (!button) return;
    currentHistoryView = button.dataset.historyView;
    $$("#historyTabs .board-tab").forEach((tab) =>
      tab.classList.toggle("active", tab === button)
    );
    renderHistory();
  });
  $("#myHistoryList").addEventListener("click", (event) => {
    const button = event.target.closest("[data-history-detail]");
    if (!button) return;
    const job = allJobs.find(
      (item) => item.id === button.dataset.historyDetail
    );
    if (job) openJobDetail(job.id, button);
    else toast(`แสดงรายละเอียด ${button.dataset.historyDetail} จากประวัติแล้ว`);
  });
  $("#historyTable").addEventListener("click", (event) => {
    const button = event.target.closest("[data-history-action]");
    if (!button) return;
    if (button.dataset.historyAction === "restore")
      restoreDeleted(button.dataset.historyUid);
    else permanentDelete(button.dataset.historyUid);
  });
  $("#staffOverviewTable").addEventListener("click", (event) => {
    const button = event.target.closest("[data-staff-overview]");
    if (button) showStaffOverview(button.dataset.staffOverview);
  });
  $("#staffTable").addEventListener("click", (event) => {
    const button = event.target.closest("[data-staff-action]");
    if (!button) return;
    const index = Number(button.dataset.staffIndex);
    if (button.dataset.staffAction === "toggle") toggleStaff(index);
    if (button.dataset.staffAction === "remove") removeStaff(index);
    if (button.dataset.staffAction === "edit") openEditStaff(index, button);
    if (button.dataset.staffAction === "detail") {
      selectedOverviewStaff = staffData[index].name;
      navigate("staff-overview");
      renderStaffOverviewDetail();
    }
  });
  $("#lostTabs").addEventListener("click", (event) => {
    const button = event.target.closest(".tab");
    if (!button) return;
    $$(".tab").forEach((tab) => tab.classList.toggle("active", tab === button));
    currentLostTab = button.dataset.tab;
    renderLost();
  });
  $("#lostGrid").addEventListener("click", (event) => {
    const button = event.target.closest("[data-lost-action]");
    if (!button) return;
    event.stopPropagation();
    const action = button.dataset.lostAction,
      tab = button.dataset.tab || "claims",
      id = button.dataset.itemId;
    if (action === "approve") approveLostItem(tab, id);
    if (action === "reject") openReject(tab, id);
    if (action === "delete") deleteLostRecord(tab, id);
    if (action === "appointment") openAppointment(id, button);
    if (action === "detail") openLostDetail(tab, id, button);
    if (action === "claim-detail") openClaimDetail(id, button);
  });
  function toggleNotificationPanel(trigger) {
    const panel = $("#notificationPanel"),
      open = !panel.classList.contains("open");
    panel.classList.toggle("open", open);
    $("#notificationButton").setAttribute("aria-expanded", String(open));
    if (open) panel.querySelector("button")?.focus();
  }
  $("#notificationButton").addEventListener("click", (event) => {
    event.stopPropagation();
    toggleNotificationPanel(event.currentTarget);
  });
  $("#mobileNotification").addEventListener("click", (event) => {
    event.stopPropagation();
    toggleNotificationPanel(event.currentTarget);
  });
  $("#notificationPanel").addEventListener("click", (event) => {
    event.stopPropagation();
    const hide = event.target.closest("[data-hide-notification]");
    if (hide) {
      const list = notificationSets[currentRole],
        index = list.findIndex(
          (item) => item.id === hide.dataset.hideNotification
        );
      if (index >= 0) list.splice(index, 1);
      renderNotifications();
      toast("ซ่อนการแจ้งเตือนแล้ว");
      return;
    }
    const itemButton = event.target.closest("[data-notification-id]");
    if (!itemButton) return;
    const item = notificationSets[currentRole].find(
      (entry) => entry.id === itemButton.dataset.notificationId
    );
    if (!item) return;
    item.unread = false;
    renderNotifications();
    $("#notificationPanel").classList.remove("open");
    const match = item.text.match(/(?:CL|RP)-\d+/);
    if (match) openJobDetail(match[0], itemButton);
    else if (currentRole === "clerk") navigate("lost");
    else toast(item.title);
  });
  document.addEventListener("click", () => {
    $("#notificationPanel").classList.remove("open");
    $("#notificationButton").setAttribute("aria-expanded", "false");
  });
  $("#markAllRead").addEventListener("click", markNotificationsRead);
  $("#openStaffModal").addEventListener("click", (event) =>
    openModal("staffModal", event.currentTarget)
  );
  $("#addFoundBtn").addEventListener("click", (event) =>
    openModal("foundModal", event.currentTarget)
  );
  $("#openAnnouncementModal").addEventListener("click", (event) =>
    openAnnouncementEditor(null, event.currentTarget)
  );
  $$("[data-close]").forEach((button) =>
    button.addEventListener("click", () => closeModal(button.dataset.close))
  );
  $$(".modal").forEach((modal) => {
    modal.setAttribute("aria-hidden", "true");
    modal.addEventListener("click", (event) => {
      if (event.target === modal) closeModal(modal.id);
    });
  });
  document.addEventListener("keydown", (event) => {
    const modal = $(".modal.open");
    if (event.key === "Escape") {
      if (modal) closeModal(modal.id);
      else closeSidebar();
      return;
    }
    if (event.key === "Tab" && modal) {
      const focusable = $$(
        'button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])'
      ).filter(
        (element) => modal.contains(element) && element.offsetParent !== null
      );
      if (!focusable.length) return;
      const first = focusable[0],
        last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
  });
  $("#confirmActionButton").addEventListener("click", () => {
    const action = pendingConfirmAction;
    pendingConfirmAction = null;
    closeModal("confirmModal", false);
    if (typeof action === "function") action();
  });
  $("#staffForm").addEventListener("submit", (event) => {
    event.preventDefault();
    if (!event.currentTarget.checkValidity()) {
      event.currentTarget.reportValidity();
      return;
    }
    const record = {
      name: $("#newName").value,
      id: $("#newId").value,
      role: $("#newRole").value,
      zone: $("#newZone").value,
      status: "ใช้งาน",
    };
    staffData.push(record);
    addAudit(
      "staff",
      "สร้างบัญชี",
      record.id,
      record.name,
      `สร้างบัญชี Role ${record.role}`
    );
    renderStaff();
    closeModal("staffModal", false);
    event.currentTarget.reset();
    showSuccess("สร้างบัญชี Staff แล้ว");
  });
  $("#editStaffForm").addEventListener("submit", (event) => {
    event.preventDefault();
    if (!event.currentTarget.checkValidity()) {
      event.currentTarget.reportValidity();
      return;
    }
    const index = Number($("#editStaffIndex").value),
      staff = staffData[index];
    if (!staff) return;
    staff.name = $("#editStaffName").value.trim();
    staff.role = $("#editStaffRole").value;
    staff.zone = $("#editStaffZone").value.trim();
    addAudit(
      "staff",
      "แก้ไข Staff",
      staff.id,
      staff.name,
      `Role ${staff.role} · ${staff.zone}`
    );
    closeModal("editStaffModal", false);
    renderStaff();
    showSuccess("บันทึกข้อมูล Staff แล้ว");
  });
  $("#claimActions").addEventListener("click", (event) => {
    const button = event.target.closest("[data-claim-action]");
    if (button)
      updateClaimWithConfirmation(
        button.dataset.claimId,
        button.dataset.claimAction,
        button
      );
  });
  $("#foundForm").addEventListener("submit", (event) => {
    event.preventDefault();
    if (!event.currentTarget.checkValidity()) {
      event.currentTarget.reportValidity();
      return;
    }
    const record = {
      id: `FD-${82 + lostSets.inventory.length}`,
      title: $("#foundName").value,
      place: `พบที่ ${$("#foundLocation").value}`,
      custody: $("#custodyPoint").value,
      status: "รออนุมัติรับฝาก",
      decisionReason: "",
      assignee: activeStaffName(),
    };
    lostSets.inventory.unshift(record);
    addAudit(
      "lost",
      "สร้างรายการรับฝาก",
      record.id,
      record.title,
      "บันทึกรายการใหม่และรออนุมัติรับฝาก"
    );
    recordWorkHistory({
      itemId: record.id,
      title: record.title,
      category: "ของที่รับฝาก",
      action: "รับฝากรายการใหม่",
      status: record.status,
      detail: `${record.place} · จุดเก็บ ${record.custody}`,
    });
    currentLostTab = "inventory";
    renderLost();
    closeModal("foundModal", false);
    event.currentTarget.reset();
    showSuccess("บันทึกรับฝากของแล้ว");
  });
  $("#rejectForm").addEventListener("submit", (event) => {
    event.preventDefault();
    if (!event.currentTarget.checkValidity()) {
      event.currentTarget.reportValidity();
      return;
    }
    const tab = $("#rejectSource").value,
      id = $("#rejectItemId").value,
      item = lostSets[tab].find((x) => x.id === id);
    if (!item) return;
    const reason = $("#rejectReason").value,
      note = $("#rejectNote").value.trim();
    item.status =
      tab === "inventory" ? "ไม่อนุมัติรับฝาก" : "ไม่อนุมัติเผยแพร่";
    item.decisionReason = note ? `${reason} — ${note}` : reason;
    item.decidedBy = activeStaffName();
    item.decidedAt = nowThai();
    item.assignee = activeStaffName();
    addAudit("lost", "ไม่อนุมัติ", id, item.title, item.decisionReason);
    recordWorkHistory({
      itemId: id,
      title: item.title,
      category: tab === "inventory" ? "ของที่รับฝาก" : "ประกาศตามหา",
      action: "ไม่อนุมัติ",
      status: item.status,
      detail: item.decisionReason,
    });
    closeModal("rejectModal", false);
    renderLost();
    renderMetrics();
    renderQueue();
    showSuccess(`ไม่อนุมัติ ${id} แล้ว`);
  });
  $("#returnJobForm").addEventListener("submit", (event) => {
    event.preventDefault();
    if (!event.currentTarget.checkValidity()) {
      event.currentTarget.reportValidity();
      return;
    }
    const id = $("#returnJobId").value,
      reason = $("#returnReason").value,
      note = $("#returnNote").value.trim();
    closeModal("returnJobModal", false);
    requestConfirmation(
      "ยืนยันคืนงานเข้าคิวกลาง",
      `ยืนยันคืนงาน ${id} เพราะ “${reason}” หรือไม่?`,
      () => {
        const job = allJobs.find((item) => item.id === id);
        if (!job || job.assignee !== activeStaffName()) {
          toast("งานนี้ไม่อยู่ในความรับผิดชอบของคุณแล้ว");
          renderJobs();
          return;
        }
        const fullReason = `${reason} — ${note}`;
        job.returnReason = fullReason;
        job.returnedBy = activeStaffName();
        job.returnedAt = nowThai();
        appendJobTimeline(
          job,
          "คืนงานเข้าคิวกลาง",
          `${activeStaffName()} · ${fullReason}`
        );
        job.assignee = null;
        job.status = "รอรับงาน";
        addAudit("jobs", "คืนงานเข้าคิวกลาง", id, job.title, fullReason);
        recordWorkHistory({
          itemId: id,
          title: job.title,
          category: job.category,
          action: "คืนงาน",
          status: "คืนเข้าคิวกลาง",
          detail: fullReason,
        });
        addNotification(currentRole, `มีงาน ${id} กลับเข้าคิวร่วม`, fullReason);
        addNotification(
          "admin",
          `${id} ถูกคืนเข้าคิวกลาง`,
          `${activeStaffName()} · ${fullReason}`
        );
        currentBoardView = "unassigned";
        renderJobs();
        renderMetrics();
        renderQueue();
        renderStaffOverview();
        toast("คืนงานเข้าคิวกลางเรียบร้อย");
      },
      "ยืนยันคืนงาน"
    );
  });
  $("#appointmentForm").addEventListener("submit", (event) => {
    event.preventDefault();
    if (!event.currentTarget.checkValidity()) {
      event.currentTarget.reportValidity();
      return;
    }
    const item = lostSets.claims.find(
      (record) => record.id === $("#appointmentItemId").value
    );
    if (!item) return;
    item.status = "นัดหมายแล้ว";
    item.assignee = activeStaffName();
    item.custody = `นัด ${$("#appointmentDate").value} เวลา ${
      $("#appointmentTime").value
    } · ${$("#appointmentPlace").value.trim()}`;
    const note = $("#appointmentNote").value.trim();
    if (note) item.custody += ` · ${note}`;
    addAudit("lost", "สร้างนัดหมาย", item.id, item.title, item.custody);
    recordWorkHistory({
      itemId: item.id,
      title: item.title,
      category: "คำขอรับของ",
      action: "สร้างนัดหมาย",
      status: item.status,
      detail: item.custody,
    });
    closeModal("appointmentModal", false);
    renderLost();
    renderMetrics();
    showSuccess(`สร้างนัดหมาย ${item.id} แล้ว`);
  });
  $("#openQrModal").addEventListener("click", (event) =>
    openModal("qrFormModal", event.currentTarget)
  );
  $("#qrForm").addEventListener("submit", (event) => {
    event.preventDefault();
    if (!event.currentTarget.checkValidity()) {
      event.currentTarget.reportValidity();
      return;
    }
    generateQr(true);
    addAudit(
      "qr",
      "สร้าง QR",
      `ROOM-${$("#room").value.trim()}`,
      $("#room").value.trim(),
      `สร้าง QR สำหรับ ${$("#building").value.trim()} ชั้น ${$(
        "#floor"
      ).value.trim()}`
    );
    closeModal("qrFormModal", false);
    showSuccess("สร้าง QR และเพิ่มห้องแล้ว");
  });
  $("#downloadQr").addEventListener("click", () => {
    const canvas = $("#qrCode canvas"),
      img = $("#qrCode img");
    let href = canvas ? canvas.toDataURL("image/png") : img?.src;
    if (!href) href = fallbackQrPng($("#qrUrlText").textContent);
    if (!href) {
      toast("เบราว์เซอร์นี้ไม่รองรับการดาวน์โหลด QR");
      return;
    }
    const link = document.createElement("a");
    link.href = href;
    link.download = `QR-${$("#room").value.trim()}.png`;
    link.click();
    toast("ดาวน์โหลด QR แล้ว");
  });
  $("#roomList").addEventListener("click", (event) => {
    const button = event.target.closest("[data-copy-room-url]");
    if (!button) return;
    navigator.clipboard?.writeText(
      decodeURIComponent(button.dataset.copyRoomUrl)
    );
    toast("คัดลอกลิงก์ห้องแล้ว");
  });
  $("#bulkQr").addEventListener("click", (event) =>
    openModal("bulkQrModal", event.currentTarget)
  );
  $("#bulkQrForm").addEventListener("submit", (event) => {
    event.preventDefault();
    if (!event.currentTarget.checkValidity()) {
      event.currentTarget.reportValidity();
      return;
    }
    const rooms = $("#bulkRooms")
      .value.split(",")
      .map((room) => room.trim())
      .filter(Boolean);
    rooms.forEach((room) => {
      const item = document.createElement("div");
      item.className = "room-item";
      item.innerHTML = `<div class="mini-qr"></div><div><strong>${escapeHtml(
        room
      )}</strong><small>สร้างพร้อมกัน · ${escapeHtml(
        $("#building").value
      )}</small></div>`;
      $("#roomList").prepend(item);
    });
    closeModal("bulkQrModal", false);
    event.currentTarget.reset();
    showSuccess(`สร้าง QR ${rooms.length} ห้องแล้ว`);
  });
  $("#printQr").addEventListener("click", () => {
    toast("เปิดหน้าต่างพิมพ์ QR แล้ว");
    window.print();
  });
  $("#announcementForm").addEventListener("submit", (event) => {
    event.preventDefault();
    saveAnnouncement("เผยแพร่");
  });
  $("#saveAnnouncementDraft").addEventListener("click", () =>
    saveAnnouncement("Draft")
  );
  $("#announcementList").addEventListener("click", (event) => {
    const button = event.target.closest("[data-announcement-action]");
    if (!button) return;
    const item = announcements.find(
      (entry) => entry.id === button.dataset.announcementId
    );
    if (button.dataset.announcementAction === "edit")
      openAnnouncementEditor(item, button);
    else
      requestConfirmation(
        "ยืนยันลบประกาศ",
        `ลบประกาศ “${item.title}” หรือไม่?`,
        () => {
          announcements = announcements.filter((entry) => entry.id !== item.id);
          renderAnnouncements();
          toast("ลบประกาศแล้ว");
        }
      );
  });
  $("#heroPrimary").addEventListener("click", () =>
    navigate(currentRole === "clerk" ? "lost" : "jobs")
  );
  const date = new Intl.DateTimeFormat("th-TH", { dateStyle: "medium" }).format(
    new Date()
  );
  $("#today").textContent = date;
  renderStaff();
  setRole(
    ["housekeeper", "technician", "clerk", "admin"].includes(currentRole)
      ? currentRole
      : "admin"
  );
  setTimeout(() => {
    generateQr(false);
    $(".loading-mask")?.remove();
  }, 320);
});
</script>

<template>
  <div class="staff-dashboard-page">
    <svg
      aria-hidden="true"
      width="0"
      height="0"
      style="position: absolute; overflow: hidden"
    >
      <symbol id="i-menu" viewBox="0 0 24 24">
        <path d="M4 7h16M4 12h16M4 17h16" />
      </symbol>
      <symbol id="i-bell" viewBox="0 0 24 24">
        <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M14 21h-4" />
      </symbol>
      <symbol id="i-user" viewBox="0 0 24 24">
        <circle cx="12" cy="8" r="4" />
        <path d="M4 21a8 8 0 0 1 16 0" />
      </symbol>
      <symbol id="i-home" viewBox="0 0 24 24">
        <path d="m3 11 9-8 9 8v9h-6v-6H9v6H3z" />
      </symbol>
      <symbol id="i-list" viewBox="0 0 24 24">
        <path d="M9 6h11M9 12h11M9 18h11M4 6h.01M4 12h.01M4 18h.01" />
      </symbol>
      <symbol id="i-plus" viewBox="0 0 24 24">
        <path d="M12 5v14M5 12h14" />
      </symbol>
      <symbol id="i-history" viewBox="0 0 24 24">
        <path d="M3 12a9 9 0 1 0 3-6.7L3 8M3 3v5h5M12 7v5l3 2" />
      </symbol>
      <symbol id="i-tools" viewBox="0 0 24 24">
        <path
          d="m14.7 6.3 3-3a5 5 0 0 1-6.4 6.4l-6.7 6.7a2 2 0 0 0 3 3l6.7-6.7a5 5 0 0 0 6.4-6.4l-3 3-3-3Z"
        />
        <path d="m5 4 4 4" />
      </symbol>
      <symbol id="i-broom" viewBox="0 0 24 24">
        <path d="m14 11 6-8M12 10l4 3-5 8H4l5-11zM7 16h6M6 19h5" />
      </symbol>
      <symbol id="i-box" viewBox="0 0 24 24">
        <path d="m3 7 9-4 9 4-9 4-9-4ZM3 7l9 4 9-4v10l-9 4-9-4V7Zm9 4v10" />
      </symbol>
      <symbol id="i-close" viewBox="0 0 24 24">
        <path d="m6 6 12 12M18 6 6 18" />
      </symbol>
      <symbol id="i-check" viewBox="0 0 24 24">
        <path d="m5 12 4 4L19 6" />
      </symbol>
      <symbol id="i-upload" viewBox="0 0 24 24">
        <path d="M12 16V4m0 0L7 9m5-5 5 5M4 16v4h16v-4" />
      </symbol>
      <symbol id="i-chevron" viewBox="0 0 24 24">
        <path d="m9 18 6-6-6-6" />
      </symbol>
      <symbol id="i-log-out" viewBox="0 0 24 24">
        <path d="M10 5H5v14h5M14 8l4 4-4 4M8 12h10" />
      </symbol>
      <symbol id="i-megaphone" viewBox="0 0 24 24">
        <path
          d="M3 11v2a2 2 0 0 0 2 2h3l9 4V5L8 9H5a2 2 0 0 0-2 2ZM8 15l1 5h3M21 9v6"
        />
      </symbol>
    </svg>
    <div class="loading-mask" aria-label="กำลังโหลด">
      <div class="loading-card">
        <span class="skeleton"></span><span class="skeleton"></span
        ><span class="skeleton"></span>
      </div>
    </div>
    <div class="app">
      <aside class="sidebar" id="sidebar">
        <div class="brand">
          <div class="brand-mark">BC</div>
          <div>
            <strong>Building Care</strong><span>Staff operations portal</span>
          </div>
        </div>
        <button
          class="sidebar-collapse"
          id="sidebarCollapse"
          type="button"
          aria-label="ยุบแถบเมนู"
        >
          <svg class="icon"><use href="#i-chevron" /></svg>
        </button>
        <section class="shift-card">
          <div class="shift-top">
            <div class="avatar" id="avatar">AD</div>
            <div>
              <strong id="staffName">พิมพ์ชนก แอดมิน</strong
              ><small id="staffRoleLabel">แอดมิน</small>
            </div>
          </div>
          <div class="role-demo">
            <input type="hidden" id="roleSwitcher" value="admin" />
            <div class="role-demo-grid">
              <button
                type="button"
                class="role-demo-btn"
                data-role-switch="technician"
              >
                ช่าง</button
              ><button
                type="button"
                class="role-demo-btn"
                data-role-switch="housekeeper"
              >
                แม่บ้าน</button
              ><button
                type="button"
                class="role-demo-btn"
                data-role-switch="clerk"
              >
                ธุรการ</button
              ><button
                type="button"
                class="role-demo-btn"
                data-role-switch="admin"
              >
                แอดมิน
              </button>
            </div>
            <small class="demo-caption"
              >การสลับบทบาทใช้สำหรับสาธิต UI เท่านั้น</small
            >
          </div>
        </section>
        <div class="nav-label">Operations</div>
        <nav class="nav-list" aria-label="เมนูเจ้าหน้าที่">
          <button
            class="nav-item active"
            data-page="dashboard"
            data-roles="all"
          >
            <span class="nav-icon">01</span>ภาพรวมงาน
          </button>
          <button
            class="nav-item"
            data-page="jobs"
            data-roles="housekeeper,technician,admin"
          >
            <span class="nav-icon">02</span
            ><span id="jobsNavLabel">ศูนย์รับงานรวม</span>
          </button>
          <button
            class="nav-item"
            data-page="my-history"
            data-roles="housekeeper,technician,clerk"
          >
            <span class="nav-icon">H</span>ประวัติงานของฉัน
          </button>
          <button class="nav-item" data-page="lost" data-roles="clerk,admin">
            <span class="nav-icon">03</span>ของหายและรับฝาก
          </button>
          <button
            class="nav-item"
            data-page="staff-overview"
            data-roles="admin"
          >
            <span class="nav-icon">WO</span>ภาพรวมงาน Staff
          </button>
          <button class="nav-item" data-page="staff" data-roles="admin">
            <span class="nav-icon">04</span>บัญชีเจ้าหน้าที่
          </button>
          <button class="nav-item" data-page="history" data-roles="admin">
            <span class="nav-icon">05</span>ประวัติและรายการที่ลบ
          </button>
          <button class="nav-item" data-page="qr" data-roles="admin">
            <span class="nav-icon">QR</span>QR ประจำห้อง
          </button>
          <button class="nav-item" data-page="announcements" data-roles="admin">
            <span class="nav-icon">AN</span>ประกาศอาคาร
          </button>
        </nav>
        <div class="sidebar-foot">
          <div class="security-note">
            <strong>Demo role switcher</strong><br />ระบบจริงต้องรับ Role และ
            Staff ID จาก Server หลังตรวจ Session ห้ามให้ผู้ใช้เลือก Role เอง
          </div>
          <button class="logout" id="logoutBtn">ออกจากระบบ</button>
        </div>
      </aside>
      <button
        type="button"
        class="sidebar-backdrop"
        id="sidebarBackdrop"
        aria-label="ปิดเมนู"
      ></button>

      <main>
        <div class="pull-indicator">↓ ดึงลงเพื่อรีเฟรช</div>
        <header class="topbar">
          <div>
            <div class="eyebrow" id="eyebrow">Admin command center</div>
            <h1 id="pageTitle">ภาพรวมการปฏิบัติงาน</h1>
          </div>
          <div class="top-actions">
            <span class="ready-pill">พร้อมปฏิบัติงาน</span>
            <button
              class="icon-btn menu-toggle"
              id="menuToggle"
              aria-label="เปิดเมนู"
              aria-expanded="false"
            >
              <svg class="icon"><use href="#i-menu" /></svg>
            </button>
            <div class="notification-wrap">
              <button
                class="icon-btn"
                id="notificationButton"
                aria-label="เปิดการแจ้งเตือน"
                aria-expanded="false"
              >
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  aria-hidden="true"
                >
                  <path
                    d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"
                  ></path>
                  <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                </svg>
                <span class="notification-count" id="notificationCount">3</span>
              </button>
              <section
                class="notification-panel"
                id="notificationPanel"
                aria-label="รายการแจ้งเตือน"
              >
                <div class="notification-head">
                  <h3 id="notificationTitle">การแจ้งเตือนของแอดมิน</h3>
                  <button id="markAllRead">อ่านทั้งหมดแล้ว</button>
                </div>
                <div class="notification-list" id="notificationList"></div>
              </section>
            </div>
            <div class="date-chip" id="today"></div>
            <button
              class="header-profile"
              id="profileButton"
              type="button"
              aria-label="เปิดโปรไฟล์"
            >
              <span class="avatar" id="headerAvatar">AD</span
              ><span
                ><strong id="headerName">พิมพ์ชนก</strong
                ><small id="headerRole">แอดมิน</small></span
              >
            </button>
          </div>
        </header>

        <section class="page active" id="page-dashboard">
          <div class="hero">
            <article class="hero-main">
              <div class="eyebrow" id="heroEyebrow">งานทั้งหมดของอาคาร</div>
              <h2 id="heroTitle">
                เห็นภาพรวม ตัดสินใจเร็ว และส่งงานถึงคนที่รับผิดชอบ
              </h2>
              <p id="heroText">
                ติดตามงานแจ้งซ่อม งานทำความสะอาด และของหาย–ของได้คืนจากจุดเดียว
              </p>
              <div class="hero-actions">
                <button class="primary" id="heroPrimary" type="button">
                  ดูงานเร่งด่วน
                </button>
              </div>
            </article>
            <aside class="hero-side">
              <h3>สถานะคิวปัจจุบัน</h3>
              <div class="pulse">
                <div class="pulse-ring">
                  <strong id="completion">68%</strong>
                </div>
                <div class="pulse-copy">
                  <strong id="pulseHeadline">17 จาก 25 งาน</strong
                  ><span id="pulseSub">มีผู้รับผิดชอบแล้ว</span>
                </div>
              </div>
              <div class="badge progress" id="shiftBadge">
                กะปัจจุบัน · 08:00–17:00
              </div>
            </aside>
          </div>
          <div class="metrics" id="metricGrid"></div>
          <section class="panel" style="margin-bottom: 20px">
            <div class="panel-head">
              <div>
                <h3>ดำเนินการด่วน</h3>
                <p>เลือกสิ่งที่ต้องทำต่อจากสถานะงานปัจจุบัน</p>
              </div>
            </div>
            <div class="panel-body">
              <div class="quick-action-grid" id="dashboardQuickActions"></div>
            </div>
          </section>
          <div class="grid-2">
            <section class="panel">
              <div class="panel-head">
                <div>
                  <h3 id="queueTitle">คิวงานรวมที่ควรรับก่อน</h3>
                  <p>งานที่ยังไม่มีผู้รับผิดชอบ เรียงตามความเร่งด่วน</p>
                </div>
                <button class="text-btn" data-go="jobs">
                  เปิดศูนย์รับงาน →
                </button>
              </div>
              <div class="panel-body">
                <div class="queue" id="priorityQueue"></div>
              </div>
            </section>
            <section class="panel">
              <div class="panel-head">
                <div>
                  <h3>กิจกรรมล่าสุด</h3>
                  <p>การเปลี่ยนแปลงใน Role ของคุณ</p>
                </div>
              </div>
              <div class="panel-body">
                <div class="activity" id="activityList"></div>
              </div>
            </section>
          </div>
        </section>

        <section class="page" id="page-jobs">
          <div class="section-title">
            <div>
              <div class="eyebrow">Shared work queue</div>
              <h2 id="jobsTitle">ศูนย์รับงานรวม</h2>
              <p id="jobsSubtitle">
                Staff ทุกคนใน Role เห็นงานใหม่ร่วมกัน และกดรับงานก่อนอัปเดตสถานะ
              </p>
            </div>
            <div class="toolbar">
              <input
                class="field-compact search"
                id="jobSearch"
                placeholder="ค้นหาเลขงาน ห้อง หรือรายละเอียด"
              />
              <select
                class="field-compact"
                id="categoryFilter"
                aria-label="กรองประเภทงานที่ผู้ใช้เลือก"
              ></select>
              <select class="field-compact" id="jobStatusFilter">
                <option value="all">ทุกสถานะ</option>
                <option value="รอรับงาน">รอรับงาน</option>
                <option value="รับงานแล้ว">รับงานแล้ว</option>
                <option value="กำลังดำเนินการ">กำลังดำเนินการ</option>
                <option value="รอข้อมูลเพิ่มเติม">รอข้อมูลเพิ่มเติม</option>
                <option value="รออะไหล่">รออะไหล่</option>
                <option value="เสร็จสิ้น">เสร็จสิ้น</option>
                <option value="ยกเลิก">ยกเลิก</option>
                <option value="คืนเข้าคิวกลาง">คืนเข้าคิวกลาง</option>
              </select>
            </div>
          </div>
          <div class="queue-explainer">
            <div class="queue-explainer-icon">↳</div>
            <div>
              <strong id="queueExplainerTitle"
                >คิวนี้เป็นคิวร่วมของ Role</strong
              >
              <p>
                งานใหม่ยังไม่มีเจ้าของ ทุกคนใน Role สามารถเห็นและกดรับได้
                คนที่รับสำเร็จจะเป็นผู้แก้ไขสถานะงานนั้น
              </p>
            </div>
          </div>
          <div class="board-tabs" id="boardTabs">
            <button class="board-tab active" data-view="unassigned">
              งานรอรับร่วม
            </button>
            <button class="board-tab" data-view="mine">งานของฉัน</button>
            <button class="board-tab" data-view="team">งานของทีม</button>
            <button class="board-tab" data-view="all">ทั้งหมด</button>
          </div>
          <div class="job-list" id="jobList"></div>
        </section>

        <section class="page" id="page-my-history">
          <div class="section-title">
            <div>
              <div class="eyebrow">Personal work record</div>
              <h2>ประวัติงานของฉัน</h2>
              <p>
                ดูงานที่เคยรับ อัปเดต ปิดงาน หรือคืนกลับเข้ากองกลาง
                พร้อมกรองช่วงวันที่ได้
              </p>
            </div>
          </div>
          <div class="history-summary" id="myHistorySummary"></div>
          <div class="history-filter-panel">
            <input
              class="field-compact"
              id="myHistoryFrom"
              type="date"
              aria-label="วันที่เริ่มต้น"
            />
            <input
              class="field-compact"
              id="myHistoryTo"
              type="date"
              aria-label="วันที่สิ้นสุด"
            />
            <select
              class="field-compact"
              id="myHistoryType"
              aria-label="กรองประเภทกิจกรรม"
            >
              <option value="all">ทุกกิจกรรม</option>
            </select>
            <input
              class="field-compact search"
              id="myHistorySearch"
              placeholder="ค้นหาเลขงาน ชื่องาน หรือรายละเอียด"
            />
            <button class="secondary" id="resetMyHistoryFilters" type="button">
              ล้างตัวกรอง
            </button>
          </div>
          <div class="work-history-list" id="myHistoryList"></div>
        </section>

        <section class="page" id="page-lost">
          <div class="section-title">
            <div>
              <div class="eyebrow">Lost &amp; found custody</div>
              <h2>ของหาย จุดรับฝาก และคำขอรับคืน</h2>
              <p>ตรวจสอบรายการและบันทึกเหตุผลทุกการตัดสินใจ</p>
            </div>
            <button class="primary" id="addFoundBtn" type="button">
              + รับฝากของใหม่
            </button>
          </div>
          <div class="tabs" id="lostTabs">
            <button class="tab active" data-tab="inventory">ของที่รับฝาก</button
            ><button class="tab" data-tab="lostposts">ประกาศตามหา</button
            ><button class="tab" data-tab="claims">คำขอรับของ</button>
          </div>
          <div class="lost-grid" id="lostGrid"></div>
        </section>

        <section class="page" id="page-staff-overview">
          <div class="section-title">
            <div>
              <div class="eyebrow">Staff work overview</div>
              <h2>ภาพรวมภาระงานของเจ้าหน้าที่</h2>
              <p>
                ดูว่า Staff แต่ละคนกำลังรับผิดชอบงานใด ปิดงานไปแล้วกี่งาน
                และคืนงานเข้ากองกลางกี่ครั้ง
              </p>
            </div>
          </div>
          <div class="history-summary" id="staffOverviewSummary"></div>
          <div class="history-filter-panel">
            <select class="field-compact" id="overviewRoleFilter">
              <option value="all">ทุก Role</option>
              <option>แม่บ้าน</option>
              <option>ช่าง</option>
              <option>ธุรการ</option>
            </select>
            <input
              class="field-compact"
              id="overviewFrom"
              type="date"
              aria-label="วันที่เริ่มต้นของภาพรวม"
            />
            <input
              class="field-compact"
              id="overviewTo"
              type="date"
              aria-label="วันที่สิ้นสุดของภาพรวม"
            />
            <input
              class="field-compact search"
              id="overviewSearch"
              placeholder="ค้นหาชื่อ Staff หรือ Staff ID"
            />
            <button class="secondary" id="resetOverviewFilters" type="button">
              ล้างตัวกรอง
            </button>
          </div>
          <div class="table-wrap">
            <table class="data-table">
              <thead>
                <tr>
                  <th>เจ้าหน้าที่</th>
                  <th>Role</th>
                  <th>กำลังรับผิดชอบ</th>
                  <th>ปิดแล้ว</th>
                  <th>คืนเข้ากองกลาง</th>
                  <th>กิจกรรมล่าสุด</th>
                  <th>รายละเอียด</th>
                </tr>
              </thead>
              <tbody id="staffOverviewTable"></tbody>
            </table>
          </div>
          <section class="panel overview-detail-panel">
            <div class="panel-body">
              <div class="overview-detail-head">
                <h3 id="overviewDetailTitle">
                  เลือก Staff เพื่อดูรายละเอียดงาน
                </h3>
                <span class="badge neutral" id="overviewDetailCount"
                  >0 รายการ</span
                >
              </div>
              <div class="overview-detail-list" id="staffOverviewDetail">
                <div class="empty">กด “ดูรายละเอียด” จากตารางด้านบน</div>
              </div>
            </div>
          </section>
        </section>

        <section class="page" id="page-staff">
          <div class="section-title">
            <div>
              <div class="eyebrow">Access administration</div>
              <h2>บัญชีและสิทธิ์เจ้าหน้าที่</h2>
              <p>สร้างบัญชี เปลี่ยน Role ปิดใช้งาน หรือลบบัญชีออกจากระบบ</p>
            </div>
            <button class="primary" id="openStaffModal">
              + สร้างบัญชี Staff
            </button>
          </div>
          <div class="metrics">
            <article class="metric">
              <span>บัญชีทั้งหมด</span><strong id="staffTotal">7</strong
              ><small>ใช้งาน 6 บัญชี</small>
            </article>
            <article class="metric">
              <span>แม่บ้าน</span><strong>3</strong
              ><small>พร้อมรับงาน 2 คน</small>
            </article>
            <article class="metric">
              <span>ช่าง</span><strong>2</strong
              ><small>กำลังปฏิบัติงาน 2 คน</small>
            </article>
            <article class="metric warn">
              <span>บัญชีถูกระงับ</span><strong>1</strong
              ><small>รอตรวจสอบ</small>
            </article>
          </div>
          <div class="table-wrap">
            <table class="data-table">
              <thead>
                <tr>
                  <th>เจ้าหน้าที่</th>
                  <th>Staff ID</th>
                  <th>Role</th>
                  <th>พื้นที่รับผิดชอบ</th>
                  <th>สถานะ</th>
                  <th>จัดการ</th>
                </tr>
              </thead>
              <tbody id="staffTable"></tbody>
            </table>
          </div>
        </section>

        <section class="page" id="page-history">
          <div class="section-title">
            <div>
              <div class="eyebrow">Audit &amp; recovery center</div>
              <h2>ประวัติทั้งหมดและรายการที่ลบแล้ว</h2>
              <p>ตรวจสอบกิจกรรมและกู้คืนรายการที่ถูกลบแบบ Soft Delete</p>
            </div>
          </div>
          <div class="history-summary" id="historySummary"></div>
          <div class="board-tabs" id="historyTabs">
            <button class="board-tab active" data-history-view="activity">
              กิจกรรมทั้งหมด
            </button>
            <button class="board-tab" data-history-view="deleted">
              รายการที่ลบแล้ว
            </button>
          </div>
          <div class="history-controls">
            <input
              class="field-compact search"
              id="historySearch"
              placeholder="ค้นหารหัส รายการ ผู้ดำเนินการ หรือรายละเอียด"
            />
            <select class="field-compact" id="historySourceFilter">
              <option value="all">ทุกส่วนของระบบ</option>
              <option value="jobs">งานแม่บ้านและช่าง</option>
              <option value="lost">ของหาย–ของได้คืน</option>
              <option value="staff">บัญชี Staff</option>
              <option value="qr">QR และห้อง</option>
            </select>
            <select class="field-compact" id="historyActionFilter">
              <option value="all">ทุกการดำเนินการ</option>
              <option value="อนุมัติ">อนุมัติ</option>
              <option value="ไม่อนุมัติ">ไม่อนุมัติ</option>
              <option value="อัปเดต">อัปเดต</option>
              <option value="ลบ">ลบ</option>
              <option value="กู้คืน">กู้คืน</option>
            </select>
          </div>
          <div class="table-wrap">
            <table class="data-table history-table">
              <thead id="historyHead"></thead>
              <tbody id="historyTable"></tbody>
            </table>
          </div>
        </section>

        <section class="page" id="page-qr">
          <div class="section-title">
            <div>
              <div class="eyebrow">Room identity system</div>
              <h2>สร้าง QR ประจำห้อง</h2>
              <p>
                QR แต่ละห้องพาผู้ใช้ไปยังหน้ารายงานที่เติมชื่ออาคาร ชั้น
                และห้องให้อัตโนมัติ
              </p>
            </div>
          </div>
          <section class="qr-launch">
            <div>
              <h3>จัดการ QR ประจำห้อง</h3>
              <p class="compact-card-copy">
                สร้าง QR ใหม่หรือจัดการรายการห้องโดยไม่แสดงฟอร์มยาวค้างในหน้า
              </p>
            </div>
            <div class="row-actions">
              <button class="primary" id="openQrModal" type="button">
                สร้าง QR</button
              ><button class="secondary" id="bulkQr" type="button">
                สร้างหลายห้อง</button
              ><button class="secondary" id="printQr" type="button">
                พิมพ์ QR
              </button>
            </div>
          </section>
          <div class="qr-layout compact">
            <section class="qr-preview">
              <div class="qr-card">
                <div>
                  <div class="qr-code" id="qrCode">
                    <div class="qr-fallback"></div>
                  </div>
                  <h3 id="qrRoomName">CSB-307</h3>
                  <p id="qrUrlText">
                    https://building-care.example/report?room=CSB-307
                  </p>
                  <button class="secondary" id="downloadQr" type="button">
                    ดาวน์โหลด PNG
                  </button>
                </div>
              </div>
              <div class="room-list" id="roomList"></div>
            </section>
          </div>
        </section>

        <section class="page" id="page-announcements">
          <div class="section-title">
            <div>
              <div class="eyebrow">Announcement management</div>
              <h2>ประกาศอาคาร</h2>
              <p>สร้างและจัดการประกาศที่แสดงกับผู้ใช้งาน</p>
            </div>
            <button class="primary" id="openAnnouncementModal" type="button">
              สร้างประกาศ
            </button>
          </div>
          <div class="metrics">
            <article class="metric">
              <span>เผยแพร่แล้ว</span><strong id="publishedCount">2</strong
              ><small>กำลังแสดงกับผู้ใช้</small>
            </article>
            <article class="metric">
              <span>ฉบับร่าง</span><strong id="draftCount">1</strong
              ><small>รอตรวจสอบ</small>
            </article>
            <article class="metric">
              <span>ปักหมุด</span><strong id="pinnedCount">1</strong
              ><small>แสดงเป็นลำดับแรก</small>
            </article>
            <article class="metric">
              <span>สิ้นสุดเดือนนี้</span><strong>1</strong
              ><small>ตรวจวันหมดอายุ</small>
            </article>
          </div>
          <div class="announcement-list" id="announcementList"></div>
        </section>
      </main>
    </div>

    <nav class="bottom-nav" aria-label="เมนูด้านล่าง">
      <button type="button" class="active" data-mobile-page="dashboard">
        <svg class="icon"><use href="#i-home" /></svg><span>ภาพรวม</span>
      </button>
      <button type="button" data-mobile-page="jobs">
        <svg class="icon"><use href="#i-list" /></svg><span>งาน</span>
      </button>
      <button type="button" class="new-action" id="mobileQuickAction">
        <svg class="icon"><use href="#i-plus" /></svg><span>ดำเนินการ</span>
      </button>
      <button type="button" id="mobileNotification">
        <svg class="icon"><use href="#i-bell" /></svg><span>แจ้งเตือน</span
        ><span class="notification-count" id="mobileNotificationCount">3</span>
      </button>
      <button type="button" id="mobileProfile">
        <svg class="icon"><use href="#i-user" /></svg><span>โปรไฟล์</span>
      </button>
    </nav>

    <div
      class="modal"
      id="staffModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="staffModalTitle"
    >
      <div class="modal-card">
        <div class="modal-head">
          <h3 id="staffModalTitle">สร้างบัญชี Staff</h3>
          <button class="close" data-close="staffModal" aria-label="ปิด">
            ×
          </button>
        </div>
        <form id="staffForm">
          <div class="form-row">
            <div class="field">
              <label for="newName">ชื่อ-นามสกุล</label
              ><input id="newName" required />
            </div>
            <div class="field">
              <label for="newId">Staff ID</label
              ><input id="newId" placeholder="STF-009" required />
            </div>
          </div>
          <div class="field">
            <label for="newEmail">อีเมล</label
            ><input id="newEmail" type="email" required />
          </div>
          <div class="form-row">
            <div class="field">
              <label for="newRole">Role</label
              ><select id="newRole">
                <option>แม่บ้าน</option>
                <option>ช่าง</option>
                <option>ธุรการ</option>
                <option>แอดมิน</option>
              </select>
            </div>
            <div class="field">
              <label for="newZone">พื้นที่รับผิดชอบ</label
              ><input id="newZone" placeholder="เช่น CSB ชั้น 1–3" />
            </div>
          </div>
          <button class="primary" style="width: 100%">สร้างบัญชี</button>
        </form>
      </div>
    </div>
    <div
      class="modal"
      id="foundModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="foundModalTitle"
    >
      <div class="modal-card">
        <div class="modal-head">
          <h3 id="foundModalTitle">รับฝากของใหม่</h3>
          <button class="close" data-close="foundModal" aria-label="ปิด">
            ×
          </button>
        </div>
        <form id="foundForm">
          <div class="field">
            <label for="foundName">ชื่อสิ่งของ</label
            ><input id="foundName" placeholder="เช่น กระเป๋าผ้าสีดำ" required />
          </div>
          <div class="form-row">
            <div class="field">
              <label for="foundLocation">สถานที่พบ</label
              ><input id="foundLocation" required />
            </div>
            <div class="field">
              <label for="custodyPoint">จุดรับฝาก</label
              ><input id="custodyPoint" value="ประชาสัมพันธ์ชั้น 1" required />
            </div>
          </div>
          <div class="field">
            <label for="privateDetail">รายละเอียดลับสำหรับยืนยันเจ้าของ</label
            ><textarea
              id="privateDetail"
              placeholder="ข้อมูลที่ไม่แสดงต่อสาธารณะ"
            ></textarea>
          </div>
          <button class="primary" style="width: 100%">บันทึกรับฝาก</button>
        </form>
      </div>
    </div>
    <div
      class="modal"
      id="rejectModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="rejectModalTitle"
    >
      <div class="modal-card">
        <div class="modal-head">
          <h3 id="rejectModalTitle">ไม่อนุมัติรายการ</h3>
          <button class="close" data-close="rejectModal" aria-label="ปิด">
            ×
          </button>
        </div>
        <form id="rejectForm">
          <input type="hidden" id="rejectSource" /><input
            type="hidden"
            id="rejectItemId"
          />
          <div class="field">
            <label for="rejectReason">เหตุผลที่ไม่อนุมัติ</label
            ><select id="rejectReason" required>
              <option value="">เลือกเหตุผล</option>
              <option>ข้อมูลไม่ตรงกับสิ่งของจริง</option>
              <option>ไม่พบสิ่งของหรือหลักฐานตามที่แจ้ง</option>
              <option>ข้อมูลไม่ครบหรือไม่สามารถยืนยันได้</option>
              <option>เป็นรายการซ้ำ</option>
              <option>มีข้อมูลส่วนตัวหรือเนื้อหาไม่เหมาะสม</option>
              <option>อยู่นอกขอบเขตการรับฝาก</option>
              <option>เหตุผลอื่น</option>
            </select>
          </div>
          <div class="field">
            <label for="rejectNote">หมายเหตุเพิ่มเติม</label
            ><textarea
              id="rejectNote"
              placeholder="อธิบายสิ่งที่ตรวจพบ เพื่อให้ตรวจสอบย้อนหลังได้"
            ></textarea>
          </div>
          <button class="danger" style="width: 100%" type="submit">
            ยืนยันไม่อนุมัติ
          </button>
        </form>
      </div>
    </div>
    <div
      class="modal"
      id="returnJobModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="returnJobModalTitle"
    >
      <div class="modal-card">
        <div class="modal-head">
          <h3 id="returnJobModalTitle">คืนงานเข้าคิวกลาง</h3>
          <button class="close" data-close="returnJobModal" aria-label="ปิด">
            ×
          </button>
        </div>
        <form id="returnJobForm">
          <input type="hidden" id="returnJobId" />
          <div class="field">
            <label for="returnReason">เหตุผลในการคืนงาน</label
            ><select id="returnReason" required>
              <option value="">เลือกเหตุผล</option>
              <option>รับงานผิดประเภท</option>
              <option>ไม่สามารถเข้าพื้นที่ได้</option>
              <option>ต้องใช้ผู้เชี่ยวชาญอื่น</option>
              <option>งานเกินขอบเขตหน้าที่</option>
              <option>อื่น ๆ</option>
            </select>
          </div>
          <div class="field">
            <label for="returnNote">รายละเอียดเพิ่มเติม</label
            ><textarea
              id="returnNote"
              required
              placeholder="ข้อมูลสำหรับ Staff คนถัดไป"
            ></textarea>
          </div>
          <div class="security-note" style="margin-bottom: 14px">
            ระบบจะขอยืนยันอีกครั้งก่อนคืนงาน ประวัติเดิมทั้งหมดจะยังอยู่
          </div>
          <button class="return-btn" style="width: 100%" type="submit">
            ดำเนินการต่อ
          </button>
        </form>
      </div>
    </div>

    <div
      class="modal job-detail-modal"
      id="jobDetailModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="jobDetailTitle"
    >
      <section class="modal-card">
        <header class="modal-head">
          <div>
            <span class="eyebrow" id="jobDetailCode">JOB-000</span>
            <h3 id="jobDetailTitle">รายละเอียดงาน</h3>
          </div>
          <button
            type="button"
            class="close"
            data-close="jobDetailModal"
            aria-label="ปิด"
          >
            <svg class="icon"><use href="#i-close" /></svg>
          </button>
        </header>
        <div class="detail-layout">
          <div>
            <div class="detail-photo">
              <svg class="icon" id="jobDetailIcon"><use href="#i-tools" /></svg>
            </div>
            <div class="timeline" id="jobTimeline"></div>
          </div>
          <div>
            <div class="job-meta" id="jobDetailBadges"></div>
            <p id="jobDetailDescription"></p>
            <div class="detail-meta">
              <div>
                <small>สถานที่</small><strong id="jobDetailRoom">–</strong>
              </div>
              <div>
                <small>ผู้แจ้ง</small><strong id="jobDetailReporter">–</strong>
              </div>
              <div>
                <small>ติดต่อ</small
                ><strong id="jobDetailContact">staff@cmu.ac.th</strong>
              </div>
              <div>
                <small>ผู้รับผิดชอบ</small
                ><strong id="jobDetailAssignee">–</strong>
              </div>
            </div>
            <div class="detail-notes">
              <strong>หมายเหตุล่าสุด</strong
              ><small id="jobDetailNotes">ยังไม่มีหมายเหตุ</small>
            </div>
            <div class="quick-action-grid" id="jobQuickActions"></div>
          </div>
        </div>
      </section>
    </div>

    <div
      class="modal"
      id="assignModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="assignModalTitle"
    >
      <section class="modal-card">
        <header class="modal-head">
          <h3 id="assignModalTitle">มอบหมายงาน</h3>
          <button
            type="button"
            class="close"
            data-close="assignModal"
            aria-label="ปิด"
          >
            <svg class="icon"><use href="#i-close" /></svg>
          </button>
        </header>
        <form id="assignForm">
          <input type="hidden" id="assignJobId" /><input
            type="hidden"
            id="assignStaff"
            required
          />
          <div class="form-row">
            <div class="field">
              <label for="assignSearch">ค้นหา Staff</label
              ><input id="assignSearch" placeholder="ค้นหาชื่อหรือพื้นที่" />
            </div>
            <div class="field">
              <label for="assignRole">Role</label
              ><select id="assignRole">
                <option>ช่าง</option>
                <option>แม่บ้าน</option>
                <option>ธุรการ</option>
                <option>แอดมิน</option>
              </select>
            </div>
          </div>
          <div class="staff-choice-list" id="assignStaffList"></div>
          <div class="field">
            <label for="assignNote">หมายเหตุ</label
            ><textarea
              id="assignNote"
              placeholder="ข้อมูลที่เจ้าหน้าที่ควรทราบ"
            ></textarea>
          </div>
          <button type="submit" class="primary" style="width: 100%">
            ยืนยันมอบหมาย
          </button>
        </form>
      </section>
    </div>

    <div
      class="modal"
      id="editStaffModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="editStaffTitle"
    >
      <section class="modal-card">
        <header class="modal-head">
          <h3 id="editStaffTitle">แก้ไข Staff</h3>
          <button
            type="button"
            class="close"
            data-close="editStaffModal"
            aria-label="ปิด"
          >
            <svg class="icon"><use href="#i-close" /></svg>
          </button>
        </header>
        <form id="editStaffForm">
          <input type="hidden" id="editStaffIndex" />
          <div class="field">
            <label for="editStaffName">ชื่อ-นามสกุล</label
            ><input id="editStaffName" required />
          </div>
          <div class="field">
            <label for="editStaffEmail">อีเมล</label
            ><input id="editStaffEmail" type="email" required />
          </div>
          <div class="form-row">
            <div class="field">
              <label for="editStaffRole">Role</label
              ><select id="editStaffRole">
                <option>แม่บ้าน</option>
                <option>ช่าง</option>
                <option>ธุรการ</option>
                <option>แอดมิน</option>
              </select>
            </div>
            <div class="field">
              <label for="editStaffZone">พื้นที่รับผิดชอบ</label
              ><input id="editStaffZone" />
            </div>
          </div>
          <button type="submit" class="primary" style="width: 100%">
            บันทึกข้อมูล
          </button>
        </form>
      </section>
    </div>

    <div
      class="modal"
      id="statusUpdateModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="statusUpdateTitle"
    >
      <section class="modal-card">
        <header class="modal-head">
          <h3 id="statusUpdateTitle">อัปเดตสถานะ</h3>
          <button
            type="button"
            class="close"
            data-close="statusUpdateModal"
            aria-label="ปิด"
          >
            <svg class="icon"><use href="#i-close" /></svg>
          </button>
        </header>
        <form id="statusUpdateForm">
          <input type="hidden" id="statusJobId" />
          <div class="field">
            <label for="newJobStatus">สถานะใหม่</label
            ><select id="newJobStatus" required></select>
          </div>
          <div class="field">
            <label for="statusNote">หมายเหตุ</label
            ><textarea
              id="statusNote"
              required
              placeholder="สรุปความคืบหน้า"
            ></textarea>
          </div>
          <div class="field">
            <label for="statusImage">รูปความคืบหน้า (ถ้ามี)</label
            ><input
              id="statusImage"
              type="file"
              accept="image/jpeg,image/png,image/webp"
            />
          </div>
          <div class="field">
            <label for="statusTime">วันที่และเวลา</label
            ><input id="statusTime" readonly />
          </div>
          <button type="submit" class="primary" style="width: 100%">
            บันทึกสถานะ
          </button>
        </form>
      </section>
    </div>

    <div
      class="modal"
      id="noteModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="noteModalTitle"
    >
      <section class="modal-card">
        <header class="modal-head">
          <h3 id="noteModalTitle">เพิ่มหมายเหตุ</h3>
          <button
            type="button"
            class="close"
            data-close="noteModal"
            aria-label="ปิด"
          >
            <svg class="icon"><use href="#i-close" /></svg>
          </button>
        </header>
        <form id="noteForm">
          <input type="hidden" id="noteJobId" />
          <div class="field">
            <label for="noteText">หมายเหตุ</label
            ><textarea
              id="noteText"
              required
              placeholder="เขียนข้อมูลที่ช่วยให้ทีมทำงานต่อได้"
            ></textarea>
          </div>
          <label class="remember"
            ><input id="notePrivate" type="checkbox" /> แสดงเฉพาะ Staff</label
          >
          <div class="modal-actions">
            <button type="button" class="secondary" data-close="noteModal">
              ยกเลิก</button
            ><button type="submit" class="primary">บันทึก</button>
          </div>
        </form>
      </section>
    </div>

    <div
      class="modal"
      id="uploadModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="uploadModalTitle"
    >
      <section class="modal-card">
        <header class="modal-head">
          <h3 id="uploadModalTitle">เพิ่มรูปความคืบหน้า</h3>
          <button
            type="button"
            class="close"
            data-close="uploadModal"
            aria-label="ปิด"
          >
            <svg class="icon"><use href="#i-close" /></svg>
          </button>
        </header>
        <form id="uploadForm">
          <input type="hidden" id="uploadJobId" /><label
            class="drop-zone"
            id="uploadDropZone"
            for="progressImage"
            ><input
              id="progressImage"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              required
            /><span
              ><svg class="icon" style="margin: auto">
                <use href="#i-upload" /></svg
              ><strong>ลากรูปมาวาง หรือเลือกจากเครื่อง</strong
              ><small>JPG, PNG, WebP · ไม่เกิน 5 MB</small></span
            ></label
          >
          <div class="upload-preview" id="progressPreview">
            <img alt="ตัวอย่างรูปความคืบหน้า" /><span></span
            ><button type="button" class="small-btn" id="removeProgressImage">
              ลบรูป
            </button>
          </div>
          <div class="field">
            <label for="uploadDescription">คำอธิบายรูป</label
            ><textarea
              id="uploadDescription"
              required
              placeholder="รูปนี้แสดงความคืบหน้าอะไร"
            ></textarea>
          </div>
          <button type="submit" class="primary" style="width: 100%">
            อัปโหลดรูป
          </button>
        </form>
      </section>
    </div>

    <div
      class="modal"
      id="completeModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="completeModalTitle"
    >
      <section class="modal-card">
        <header class="modal-head">
          <h3 id="completeModalTitle">สรุปและปิดงาน</h3>
          <button
            type="button"
            class="close"
            data-close="completeModal"
            aria-label="ปิด"
          >
            <svg class="icon"><use href="#i-close" /></svg>
          </button>
        </header>
        <form id="completeForm">
          <input type="hidden" id="completeJobId" />
          <div class="field">
            <label for="completeResult">ผลการดำเนินงาน</label
            ><textarea id="completeResult" required></textarea>
          </div>
          <div class="field">
            <label for="completeNote">หมายเหตุปิดงาน</label
            ><textarea id="completeNote" required></textarea>
          </div>
          <div class="field">
            <label for="completeImage">รูปหลังดำเนินการ</label
            ><input
              id="completeImage"
              type="file"
              accept="image/jpeg,image/png,image/webp"
            />
          </div>
          <div class="field">
            <label for="completeDate">วันที่เสร็จ</label
            ><input id="completeDate" type="date" required />
          </div>
          <button type="submit" class="primary" style="width: 100%">
            ยืนยันปิดงาน
          </button>
        </form>
      </section>
    </div>

    <div
      class="modal job-detail-modal"
      id="claimDetailModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="claimDetailTitle"
    >
      <section class="modal-card">
        <header class="modal-head">
          <div>
            <span class="eyebrow" id="claimDetailCode">CLM-000</span>
            <h3 id="claimDetailTitle">รายละเอียดคำขอรับคืน</h3>
          </div>
          <button
            type="button"
            class="close"
            data-close="claimDetailModal"
            aria-label="ปิด"
          >
            <svg class="icon"><use href="#i-close" /></svg>
          </button>
        </header>
        <div class="inline-summary">
          <div>
            <small>ผู้ขอรับ</small><strong id="claimRequester">–</strong>
          </div>
          <div><small>ติดต่อ</small><strong id="claimContact">–</strong></div>
          <div>
            <small>วันที่ส่งคำขอ</small><strong id="claimDate">–</strong>
          </div>
          <div>
            <small>นัดหมาย</small
            ><strong id="claimAppointment">ยังไม่มีนัดหมาย</strong>
          </div>
        </div>
        <h4>หลักฐานและรายละเอียด</h4>
        <p id="claimEvidence"></p>
        <div class="claim-secret">
          <strong>ข้อมูลลับสำหรับตรวจสอบ</strong>
          <p id="claimSecret"></p>
        </div>
        <div class="timeline" id="claimTimeline"></div>
        <div class="quick-action-grid" id="claimActions"></div>
      </section>
    </div>

    <div
      class="modal"
      id="qrFormModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="qrFormModalTitle"
    >
      <section class="modal-card">
        <header class="modal-head">
          <h3 id="qrFormModalTitle">สร้าง QR ประจำห้อง</h3>
          <button
            type="button"
            class="close"
            data-close="qrFormModal"
            aria-label="ปิด"
          >
            <svg class="icon"><use href="#i-close" /></svg>
          </button>
        </header>
        <form id="qrForm">
          <div class="field">
            <label for="building">อาคาร</label
            ><input id="building" value="อาคารเรียนรวม CSB" required />
          </div>
          <div class="form-row">
            <div class="field">
              <label for="floor">ชั้น</label
              ><input id="floor" value="3" required />
            </div>
            <div class="field">
              <label for="room">ชื่อ/เลขห้อง</label
              ><input id="room" value="CSB-307" required />
            </div>
          </div>
          <div class="field">
            <label for="service">หน้าปลายทาง</label
            ><select id="service">
              <option value="report">เลือกประเภทบริการภายหลัง</option>
              <option value="repair">แจ้งซ่อม</option>
              <option value="cleaning">แจ้งทำความสะอาด</option>
              <option value="lost">ของหาย–ของได้คืน</option>
            </select>
          </div>
          <div class="field">
            <label for="baseUrl">Base URL</label
            ><input
              id="baseUrl"
              value="https://building-care.example/report"
              required
            />
          </div>
          <button class="primary" style="width: 100%">
            สร้าง QR และเพิ่มห้อง
          </button>
        </form>
      </section>
    </div>

    <div
      class="modal"
      id="confirmModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirmModalTitle"
    >
      <section class="modal-card confirmation">
        <header class="modal-head">
          <span></span
          ><button
            type="button"
            class="close"
            data-close="confirmModal"
            aria-label="ปิด"
          >
            <svg class="icon"><use href="#i-close" /></svg>
          </button>
        </header>
        <div class="confirm-icon">
          <svg class="icon"><use href="#i-check" /></svg>
        </div>
        <h3 id="confirmModalTitle">ยืนยันการดำเนินการ</h3>
        <p id="confirmModalText">กรุณาตรวจสอบข้อมูลก่อนยืนยัน</p>
        <div class="modal-actions">
          <button type="button" class="secondary" data-close="confirmModal">
            ยกเลิก</button
          ><button type="button" class="danger" id="confirmActionButton">
            ยืนยัน
          </button>
        </div>
      </section>
    </div>

    <div
      class="modal"
      id="profileModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="profileModalTitle"
    >
      <section class="modal-card">
        <header class="modal-head">
          <h3 id="profileModalTitle">โปรไฟล์เจ้าหน้าที่</h3>
          <button
            type="button"
            class="close"
            data-close="profileModal"
            aria-label="ปิด"
          >
            <svg class="icon"><use href="#i-close" /></svg>
          </button>
        </header>
        <div class="profile-grid">
          <div class="profile-avatar-large" id="profileAvatar">AD</div>
          <div class="profile-data">
            <div>
              <small>ชื่อ</small
              ><strong id="profileName">พิมพ์ชนก วัฒนา</strong>
            </div>
            <div>
              <small>อีเมล</small
              ><strong id="profileEmail">staff@building.local</strong>
            </div>
            <div>
              <small>รหัสเจ้าหน้าที่</small
              ><strong id="profileStaffId">ADM-001</strong>
            </div>
            <div>
              <small>Role</small><strong id="profileRole">แอดมิน</strong>
            </div>
            <div>
              <small>แผนก</small
              ><strong id="profileDepartment">บริหารระบบ</strong>
            </div>
            <div>
              <small>สถานะ</small
              ><strong style="color: #258745">พร้อมปฏิบัติงาน</strong>
            </div>
          </div>
        </div>
        <div class="modal-actions">
          <button type="button" class="secondary" id="notificationSettings">
            ตั้งค่าการแจ้งเตือน</button
          ><button type="button" class="secondary" id="changePassword">
            เปลี่ยนรหัสผ่าน</button
          ><button type="button" class="danger" id="profileLogout">
            ออกจากระบบ
          </button>
        </div>
      </section>
    </div>

    <div
      class="modal"
      id="announcementModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="announcementModalTitle"
    >
      <section class="modal-card">
        <header class="modal-head">
          <h3 id="announcementModalTitle">สร้างประกาศ</h3>
          <button
            type="button"
            class="close"
            data-close="announcementModal"
            aria-label="ปิด"
          >
            <svg class="icon"><use href="#i-close" /></svg>
          </button>
        </header>
        <form id="announcementForm">
          <input type="hidden" id="announcementId" />
          <div class="field">
            <label for="announcementTitle">หัวข้อ</label
            ><input id="announcementTitle" required />
          </div>
          <div class="field">
            <label for="announcementContent">เนื้อหา</label
            ><textarea id="announcementContent" required></textarea>
          </div>
          <div class="field">
            <label for="announcementAudience">กลุ่มผู้เห็นประกาศ</label
            ><select id="announcementAudience">
              <option>ผู้ใช้งานทุกคน</option>
              <option>เจ้าหน้าที่ทุก Role</option>
              <option>เฉพาะผู้ใช้อาคาร 30</option>
            </select>
          </div>
          <div class="form-row">
            <div class="field">
              <label for="announcementStart">วันที่เริ่ม</label
              ><input id="announcementStart" type="date" required />
            </div>
            <div class="field">
              <label for="announcementEnd">วันที่สิ้นสุด</label
              ><input id="announcementEnd" type="date" required />
            </div>
          </div>
          <label class="remember"
            ><input id="announcementPinned" type="checkbox" />
            ปักหมุดประกาศ</label
          >
          <div class="modal-actions">
            <button type="button" class="secondary" id="saveAnnouncementDraft">
              บันทึก Draft</button
            ><button type="submit" class="primary">Publish</button>
          </div>
        </form>
      </section>
    </div>

    <div
      class="modal"
      id="quickActionModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="quickActionTitle"
    >
      <section class="modal-card">
        <header class="modal-head">
          <h3 id="quickActionTitle">ดำเนินการด่วน</h3>
          <button
            type="button"
            class="close"
            data-close="quickActionModal"
            aria-label="ปิด"
          >
            <svg class="icon"><use href="#i-close" /></svg>
          </button>
        </header>
        <div class="service-choice-grid" id="mobileQuickActions"></div>
      </section>
    </div>

    <div
      class="modal"
      id="bulkQrModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="bulkQrTitle"
    >
      <section class="modal-card">
        <header class="modal-head">
          <h3 id="bulkQrTitle">สร้าง QR หลายห้อง</h3>
          <button
            type="button"
            class="close"
            data-close="bulkQrModal"
            aria-label="ปิด"
          >
            <svg class="icon"><use href="#i-close" /></svg>
          </button>
        </header>
        <form id="bulkQrForm">
          <div class="field">
            <label for="bulkRooms">เลขห้อง</label
            ><textarea
              id="bulkRooms"
              required
              placeholder="เช่น CSB-301, CSB-302, CSB-303"
            ></textarea>
          </div>
          <button type="submit" class="primary" style="width: 100%">
            สร้าง QR ทุกห้อง
          </button>
        </form>
      </section>
    </div>

    <div
      class="modal"
      id="appointmentModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="appointmentTitle"
    >
      <section class="modal-card">
        <header class="modal-head">
          <h3 id="appointmentTitle">นัดหมายรับของ</h3>
          <button
            type="button"
            class="close"
            data-close="appointmentModal"
            aria-label="ปิด"
          >
            <svg class="icon"><use href="#i-close" /></svg>
          </button>
        </header>
        <form id="appointmentForm">
          <input type="hidden" id="appointmentItemId" />
          <div class="form-row">
            <div class="field">
              <label for="appointmentDate">วันที่รับของ</label
              ><input id="appointmentDate" type="date" required />
            </div>
            <div class="field">
              <label for="appointmentTime">เวลา</label
              ><input id="appointmentTime" type="time" required />
            </div>
          </div>
          <div class="field">
            <label for="appointmentPlace">จุดรับของ</label
            ><input
              id="appointmentPlace"
              value="ประชาสัมพันธ์ ชั้น 1"
              required
            />
          </div>
          <div class="field">
            <label for="appointmentNote">หมายเหตุ</label
            ><textarea
              id="appointmentNote"
              placeholder="เอกสารที่ต้องนำมาแสดง"
            ></textarea>
          </div>
          <button type="submit" class="primary" style="width: 100%">
            ยืนยันนัดหมาย
          </button>
        </form>
      </section>
    </div>

    <div
      class="modal"
      id="successModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="successModalTitle"
    >
      <section class="modal-card confirmation">
        <header class="modal-head">
          <span></span
          ><button
            type="button"
            class="close"
            data-close="successModal"
            aria-label="ปิด"
          >
            <svg class="icon"><use href="#i-close" /></svg>
          </button>
        </header>
        <div class="success-check">
          <svg class="icon"><use href="#i-check" /></svg>
        </div>
        <h3 id="successModalTitle">บันทึกสำเร็จ</h3>
        <p id="successModalText">ระบบบันทึกข้อมูลเรียบร้อยแล้ว</p>
        <button type="button" class="primary" data-close="successModal">
          ตกลง
        </button>
      </section>
    </div>
    <div class="toast" id="toast" role="status"></div>
  </div>
</template>

<style>
:root {
  --primary: #6d5df6;
  --primary-2: #8a7cff;
  --primary-soft: #f0edff;
  --ink: #191724;
  --muted: #74717f;
  --line: #eceaf2;
  --surface: #fff;
  --canvas: #f7f7fb;
  --repair: #ff8a45;
  --repair-soft: #fff2e8;
  --clean: #48b86a;
  --clean-soft: #ebf8ed;
  --lost: #edae20;
  --lost-soft: #fff7df;
  --info: #4285f4;
  --info-soft: #eaf2ff;
  --danger: #ef5350;
  --danger-soft: #fff0ef;
  --shadow: 0 12px 36px rgba(42, 35, 85, 0.08);
  --shadow-sm: 0 6px 20px rgba(42, 35, 85, 0.07);
  --radius: 24px;
  --radius-sm: 18px;
  --font: "Inter", "Noto Sans Thai", system-ui, sans-serif;
}
* {
  box-sizing: border-box;
}
html {
  scroll-behavior: smooth;
}
body {
  margin: 0;
  background: var(--canvas);
  color: var(--ink);
  font-family: var(--font);
  font-size: 15px;
  line-height: 1.55;
  -webkit-font-smoothing: antialiased;
}
button,
input,
select,
textarea {
  font: inherit;
}
button {
  cursor: pointer;
}
button:focus-visible,
input:focus-visible,
select:focus-visible,
textarea:focus-visible {
  outline: 3px solid rgba(109, 93, 246, 0.22);
  outline-offset: 2px;
}
a {
  color: inherit;
}
.primary-btn,
.primary,
.submit-btn {
  border: 0;
  border-radius: 16px;
  background: linear-gradient(135deg, var(--primary), #806ff8);
  color: #fff;
  font-weight: 800;
  min-height: 50px;
  padding: 0 22px;
  box-shadow: 0 10px 24px rgba(109, 93, 246, 0.24);
  transition: 0.2s ease;
}
.primary-btn:hover,
.primary:hover,
.submit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 30px rgba(109, 93, 246, 0.28);
}
.ghost-btn,
.secondary,
.text-btn,
.small-btn {
  border: 1px solid var(--line);
  background: #fff;
  color: var(--ink);
  border-radius: 14px;
  font-weight: 700;
  min-height: 44px;
  padding: 0 16px;
}
.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--primary);
  font-size: 11px;
  font-weight: 800;
}
h1,
h2,
h3,
h4,
p {
  margin-top: 0;
}
h1,
h2,
h3,
h4 {
  line-height: 1.25;
}
p {
  color: var(--muted);
}
.badge,
.status,
.post-type {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
  white-space: nowrap;
}
.field {
  display: grid;
  gap: 7px;
}
.field label {
  font-size: 13px;
  font-weight: 750;
  color: #45414f;
}
.field input,
.field select,
.field textarea,
.field-compact {
  width: 100%;
  border: 1px solid var(--line);
  background: #fafafd;
  color: var(--ink);
  border-radius: 15px;
  min-height: 50px;
  padding: 12px 14px;
  transition: 0.2s;
}
.field textarea {
  min-height: 108px;
  resize: vertical;
}
.field input:focus,
.field select:focus,
.field textarea:focus,
.field-compact:focus {
  border-color: var(--primary);
  background: #fff;
  box-shadow: 0 0 0 4px rgba(109, 93, 246, 0.08);
}
.empty {
  padding: 36px 20px;
  text-align: center;
  color: var(--muted);
  border: 1px dashed #d8d4e8;
  border-radius: 18px;
  background: #fbfaff;
}
.toast {
  border-radius: 16px !important;
  background: #211d35 !important;
  color: #fff !important;
  box-shadow: var(--shadow) !important;
}
.skeleton {
  overflow: hidden;
  background: #eeeaf8;
  position: relative;
}
.skeleton:after {
  content: "";
  position: absolute;
  inset: 0;
  transform: translateX(-100%);
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.75),
    transparent
  );
  animation: shimmer 1.5s infinite;
}
@keyframes shimmer {
  to {
    transform: translateX(100%);
  }
}
@media (prefers-reduced-motion: reduce) {
  *,
  *:before,
  *:after {
    scroll-behavior: auto !important;
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
body {
  background: linear-gradient(145deg, #f7f5ff, #f8f8fb 45%, #fff);
  min-height: 100vh;
}
.app {
  max-width: 1600px;
  margin: auto;
}
.sidebar {
  position: fixed;
  z-index: 40;
  left: 22px;
  top: 22px;
  bottom: 22px;
  width: 250px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(20px);
  border: 1px solid #fff;
  border-radius: 28px;
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 3px 4px 18px;
}
.brand-mark {
  width: 45px;
  height: 45px;
  display: grid;
  place-items: center;
  border-radius: 15px;
  background: linear-gradient(145deg, var(--primary), #8e7fff);
  color: #fff;
  font-weight: 900;
  box-shadow: 0 9px 20px rgba(109, 93, 246, 0.25);
}
.brand strong,
.brand span {
  display: block;
}
.brand span {
  font-size: 10px;
  color: var(--muted);
}
.shift-card {
  background: linear-gradient(145deg, #f4f1ff, #faf9ff);
  border: 1px solid #e9e4ff;
  border-radius: 20px;
  padding: 14px;
  margin-bottom: 18px;
}
.shift-top {
  display: flex;
  align-items: center;
  gap: 10px;
}
.avatar {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  background: var(--primary);
  color: #fff;
  display: grid;
  place-items: center;
  font-weight: 900;
}
.shift-top strong,
.shift-top small {
  display: block;
}
.shift-top strong {
  font-size: 12px;
}
.shift-top small {
  font-size: 10px;
  color: var(--muted);
}
.role-select {
  width: 100%;
  margin-top: 11px;
  min-height: 38px;
  border: 0;
  border-radius: 12px;
  background: #fff;
  color: var(--primary);
  padding: 0 10px;
  font-size: 11px;
  font-weight: 800;
}
.nav-label {
  margin: 0 11px 8px;
  color: var(--muted);
  font-size: 9px;
  font-weight: 900;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}
.nav-list {
  display: grid;
  gap: 5px;
}
.nav-item {
  border: 0;
  background: transparent;
  color: #6f6b78;
  min-height: 43px;
  border-radius: 14px;
  padding: 0 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  font-weight: 750;
  text-align: left;
}
.nav-item:hover,
.nav-item.active {
  background: var(--primary-soft);
  color: var(--primary);
}
.nav-icon {
  width: 25px;
  color: currentColor;
  font-size: 9px;
  font-weight: 900;
}
.sidebar-foot {
  margin-top: auto;
}
.security-note {
  font-size: 10px;
  color: var(--muted);
  background: #f7f6fa;
  border-radius: 14px;
  padding: 11px;
}
.logout {
  width: 100%;
  min-height: 42px;
  margin-top: 9px;
  border: 0;
  border-radius: 13px;
  background: var(--danger-soft);
  color: var(--danger);
  font-weight: 800;
}
.app main {
  margin-left: 294px;
  padding: 0 34px 70px;
  min-width: 0;
}
.topbar {
  position: sticky;
  z-index: 20;
  top: 0;
  min-height: 92px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  background: rgba(248, 248, 251, 0.86);
  backdrop-filter: blur(18px);
  padding: 13px 0;
}
.topbar h1 {
  font-size: 27px;
  margin: 3px 0;
}
.top-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
.icon-btn {
  position: relative;
  width: 46px;
  height: 46px;
  border: 1px solid #fff;
  background: #fff;
  border-radius: 15px;
  display: grid;
  place-items: center;
  box-shadow: var(--shadow-sm);
}
.icon-btn svg {
  width: 19px;
}
.menu-toggle {
  display: none;
}
.notification-count {
  position: absolute;
  right: -4px;
  top: -4px;
  min-width: 20px;
  height: 20px;
  padding: 0 5px;
  border-radius: 999px;
  background: var(--danger);
  color: #fff;
  font-size: 10px;
  display: grid;
  place-items: center;
  border: 2px solid #fff;
}
.notification-wrap {
  position: relative;
}
.notification-panel {
  display: none;
  position: absolute;
  right: 0;
  top: 56px;
  width: min(390px, calc(100vw - 28px));
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 22px;
  box-shadow: 0 24px 60px rgba(34, 29, 66, 0.18);
  overflow: hidden;
}
.notification-panel.open {
  display: block;
  animation: panelIn 0.2s ease;
}
@keyframes panelIn {
  from {
    opacity: 0;
    transform: translateY(-7px);
  }
}
.notification-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 17px;
  border-bottom: 1px solid var(--line);
}
.notification-head h3 {
  font-size: 15px;
  margin: 0;
}
.notification-head button {
  border: 0;
  background: transparent;
  color: var(--primary);
  font-size: 11px;
  font-weight: 800;
}
.notification-list {
  max-height: 430px;
  overflow: auto;
}
.notification-item {
  display: grid;
  grid-template-columns: 38px 1fr;
  gap: 11px;
  padding: 14px 17px;
  border-bottom: 1px solid var(--line);
}
.notification-item.unread {
  background: #f7f5ff;
}
.notification-symbol {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  background: var(--primary-soft);
  display: grid;
  place-items: center;
}
.notification-item strong,
.notification-item small {
  display: block;
}
.notification-item small {
  color: var(--muted);
  font-size: 10px;
}
.date-chip {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 9px 14px;
  color: var(--muted);
  font-size: 11px;
}
.page {
  display: none;
  max-width: 1240px;
  margin: auto;
  animation: pageIn 0.3s ease;
}
.page.active {
  display: block;
}
@keyframes pageIn {
  from {
    opacity: 0;
    transform: translateY(7px);
  }
}
.hero {
  display: grid;
  grid-template-columns: minmax(0, 1.55fr) minmax(250px, 0.65fr);
  gap: 18px;
  margin: 12px 0 20px;
}
.hero-main,
.hero-side {
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
}
.hero-main {
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #fff, #f2efff);
  padding: 30px;
}
.hero-main:after {
  content: "";
  position: absolute;
  right: -60px;
  top: -70px;
  width: 240px;
  height: 240px;
  border-radius: 50%;
  background: radial-gradient(
    circle,
    rgba(109, 93, 246, 0.18),
    transparent 66%
  );
}
.hero-main h2 {
  max-width: 610px;
  font-size: 28px;
  margin: 7px 0;
}
.hero-main p {
  max-width: 670px;
  font-size: 12px;
}
.hero-actions {
  position: relative;
  z-index: 1;
}
.hero-side {
  background: #fff;
  padding: 23px;
}
.hero-side h3 {
  font-size: 14px;
}
.pulse {
  display: flex;
  align-items: center;
  gap: 14px;
}
.pulse-ring {
  width: 78px;
  height: 78px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: conic-gradient(var(--primary) 68%, #ece9f6 0);
  position: relative;
}
.pulse-ring:before {
  content: "";
  position: absolute;
  inset: 8px;
  border-radius: 50%;
  background: #fff;
}
.pulse-ring strong {
  position: relative;
  font-size: 18px;
}
.pulse-copy strong,
.pulse-copy span {
  display: block;
}
.pulse-copy span {
  font-size: 10px;
  color: var(--muted);
}
.hero-side .badge {
  margin-top: 16px;
  background: var(--info-soft);
  color: var(--info);
}
.metrics,
.history-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 20px;
}
.metric {
  position: relative;
  overflow: hidden;
  background: #fff;
  border: 1px solid #fff;
  border-radius: 21px;
  padding: 19px;
  box-shadow: var(--shadow-sm);
}
.metric:before {
  content: "";
  position: absolute;
  width: 6px;
  left: 0;
  top: 14px;
  bottom: 14px;
  border-radius: 0 8px 8px 0;
  background: var(--primary);
}
.metric:nth-child(2):before {
  background: var(--info);
}
.metric:nth-child(3):before {
  background: var(--clean);
}
.metric:nth-child(4):before,
.metric.warn:before {
  background: var(--lost);
}
.metric span,
.metric small {
  display: block;
  color: var(--muted);
  font-size: 10px;
}
.metric strong {
  display: block;
  font-size: 28px;
  margin: 4px 0;
}
.grid-2 {
  display: grid;
  grid-template-columns: 1.25fr 0.75fr;
  gap: 18px;
}
.panel,
.table-wrap,
.queue-explainer,
.history-filter-panel,
.history-controls,
.qr-preview,
.form-panel {
  background: #fff;
  border: 1px solid #fff;
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
}
.panel {
  overflow: hidden;
}
.panel-head {
  padding: 20px 21px 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.panel-head h3 {
  font-size: 16px;
  margin: 0;
}
.panel-head p {
  font-size: 10px;
  margin: 3px 0;
}
.panel-body {
  padding: 0 21px 20px;
}
.queue-item,
.activity-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 0;
  border-bottom: 1px solid var(--line);
}
.queue-item:last-child,
.activity-item:last-child {
  border-bottom: 0;
}
.queue-code {
  font-size: 10px;
  font-weight: 900;
  color: var(--primary);
  background: var(--primary-soft);
  border-radius: 10px;
  padding: 7px;
}
.activity-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--primary);
  box-shadow: 0 0 0 5px var(--primary-soft);
}
.section-title {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 20px;
  margin: 16px 0 21px;
}
.section-title h2 {
  font-size: 27px;
  margin: 4px 0;
}
.section-title p {
  font-size: 11px;
  margin: 0;
  max-width: 690px;
}
.toolbar,
.history-controls,
.history-filter-panel {
  display: flex;
  gap: 9px;
  align-items: center;
  flex-wrap: wrap;
}
.toolbar .search,
.history-controls .search,
.history-filter-panel .search {
  min-width: 230px;
  flex: 1;
}
.queue-explainer {
  display: flex;
  gap: 14px;
  padding: 16px;
  margin-bottom: 14px;
  background: linear-gradient(135deg, #f4f1ff, #fff);
}
.queue-explainer-icon {
  width: 40px;
  height: 40px;
  flex: 0 0 40px;
  border-radius: 13px;
  background: var(--primary);
  color: #fff;
  display: grid;
  place-items: center;
}
.queue-explainer p {
  font-size: 10px;
  margin: 2px 0;
}
.board-tabs,
.tabs {
  display: flex;
  gap: 7px;
  overflow: auto;
  margin: 14px 0;
}
.board-tab,
.tab {
  border: 0;
  background: #eceaf2;
  color: #65616e;
  min-height: 40px;
  padding: 0 16px;
  border-radius: 999px;
  white-space: nowrap;
  font-size: 11px;
  font-weight: 800;
}
.board-tab.active,
.tab.active {
  background: var(--primary);
  color: #fff;
}
.job-list,
.work-history-list,
.lost-grid {
  display: grid;
  gap: 13px;
}
.job-card,
.work-history-card,
.lost-card {
  background: #fff;
  border: 1px solid #fff;
  border-radius: 21px;
  padding: 19px;
  box-shadow: var(--shadow-sm);
  transition: 0.2s;
}
.job-card:hover,
.lost-card:hover {
  transform: translateY(-2px);
}
.job-card {
  display: grid;
  grid-template-columns: 56px minmax(0, 1fr) auto;
  gap: 15px;
  align-items: center;
}
.job-photo,
.lost-image {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: var(--primary-soft);
  display: grid;
  place-items: center;
  font-size: 24px;
}
.job-detail h3,
.lost-content h3 {
  font-size: 15px;
  margin: 3px 0;
}
.job-meta,
.work-history-meta,
.lost-foot {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  color: var(--muted);
  font-size: 10px;
}
.job-actions,
.approval-actions,
.row-actions {
  display: flex;
  gap: 7px;
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
}
.accept-btn,
.update-btn,
.approve-btn,
.reject-btn,
.return-btn,
.danger,
.permanent-btn,
.restore-btn {
  border: 0;
  border-radius: 12px;
  min-height: 40px;
  padding: 0 13px;
  font-size: 11px;
  font-weight: 850;
}
.accept-btn,
.update-btn,
.approve-btn {
  background: var(--primary);
  color: #fff;
}
.reject-btn,
.danger,
.permanent-btn {
  background: var(--danger-soft);
  color: var(--danger);
}
.return-btn {
  background: var(--lost-soft);
  color: #a36c00;
}
.restore-btn {
  background: var(--clean-soft);
  color: var(--clean);
}
.badge.progress,
.badge.in-progress {
  background: var(--info-soft);
  color: var(--info);
}
.badge.done {
  background: var(--clean-soft);
  color: var(--clean);
}
.badge.wait,
.badge.warn {
  background: var(--lost-soft);
  color: #aa7300;
}
.badge.danger {
  background: var(--danger-soft);
  color: var(--danger);
}
.badge.neutral {
  background: #f0eff4;
  color: #716d79;
}
.assignee {
  font-size: 10px;
  color: var(--muted);
}
.assignee-dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--clean);
  margin-right: 4px;
}
.work-history-card {
  display: grid;
  grid-template-columns: 100px 1fr auto;
  align-items: center;
  gap: 15px;
}
.work-history-date {
  font-size: 10px;
  color: var(--muted);
}
.work-history-main strong,
.work-history-main small {
  display: block;
}
.work-history-main small {
  font-size: 10px;
  color: var(--muted);
}
.lost-grid {
  grid-template-columns: repeat(3, 1fr);
}
.lost-card {
  display: grid;
  gap: 13px;
}
.lost-image {
  width: 100%;
  height: 110px;
  font-size: 34px;
  background: var(--lost-soft);
}
.approval-note,
.return-note {
  border-radius: 13px;
  padding: 10px;
  background: #f8f7fb;
  color: var(--muted);
  font-size: 10px;
}
.history-filter-panel,
.history-controls {
  padding: 13px;
  margin-bottom: 14px;
}
.history-summary .metric {
  box-shadow: none;
  border: 1px solid var(--line);
}
.table-wrap {
  overflow: auto;
  margin-bottom: 17px;
}
.data-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 780px;
}
.data-table th {
  padding: 13px 15px;
  background: #f8f7fb;
  text-align: left;
  font-size: 9px;
  color: var(--muted);
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.data-table td {
  padding: 14px 15px;
  border-top: 1px solid var(--line);
  font-size: 11px;
}
.person {
  display: flex;
  align-items: center;
  gap: 9px;
}
.person-avatar {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  background: var(--primary-soft);
  color: var(--primary);
  display: grid;
  place-items: center;
  font-weight: 900;
}
.history-action,
.history-source {
  font-weight: 800;
}
.history-detail {
  color: var(--muted);
}
.overview-detail-panel {
  margin-top: 15px;
}
.overview-detail-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.overview-detail-item,
.room-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 13px 0;
  border-top: 1px solid var(--line);
}
.overview-number {
  font-size: 24px;
  font-weight: 900;
  color: var(--primary);
}
.qr-layout {
  display: grid;
  grid-template-columns: minmax(300px, 0.85fr) 1.15fr;
  gap: 18px;
}
.form-panel {
  padding: 22px;
}
.form-panel form {
  display: grid;
  gap: 14px;
}
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.qr-preview {
  padding: 22px;
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 20px;
}
.qr-card {
  display: grid;
  place-items: center;
  text-align: center;
  background: linear-gradient(145deg, #f4f1ff, #fff);
  border-radius: 20px;
  padding: 20px;
}
.qr-code {
  width: 184px;
  height: 184px;
  display: grid;
  place-items: center;
  background: #fff;
  border-radius: 18px;
  padding: 8px;
}
.qr-code img,
.qr-code canvas {
  max-width: 100%;
}
.qr-fallback,
.mini-qr {
  background: repeating-conic-gradient(#211c39 0 25%, #fff 0 50%) 50% / 16px
    16px;
}
.qr-fallback {
  width: 160px;
  height: 160px;
}
.mini-qr {
  width: 42px;
  height: 42px;
  border: 5px solid #fff;
}
.room-list {
  min-width: 0;
}
.modal {
  position: fixed;
  inset: 0;
  z-index: 70;
  background: rgba(27, 22, 48, 0.42);
  backdrop-filter: blur(8px);
  display: none;
  place-items: center;
  padding: 18px;
}
.modal.open {
  display: grid;
}
.modal-card {
  width: min(600px, 100%);
  max-height: 90vh;
  overflow: auto;
  background: #fff;
  border-radius: 26px;
  padding: 23px;
  box-shadow: 0 30px 80px rgba(21, 16, 45, 0.25);
  animation: modalIn 0.2s ease;
}
@keyframes modalIn {
  from {
    opacity: 0;
    transform: scale(0.97);
  }
}
.modal-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
}
.modal-head h3 {
  margin: 0;
}
.close {
  border: 0;
  width: 38px;
  height: 38px;
  border-radius: 12px;
  background: #f1eff5;
  font-size: 22px;
}
.modal form {
  display: grid;
  gap: 14px;
}
@media (max-width: 1050px) {
  .sidebar {
    left: -280px;
    transition: 0.25s;
  }
  .sidebar.open {
    left: 14px;
  }
  .app main {
    margin-left: 0;
    padding: 0 22px 60px;
  }
  .menu-toggle {
    display: grid;
  }
  .grid-2 {
    grid-template-columns: 1fr;
  }
  .lost-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 720px) {
  .app main {
    padding: 0 14px 90px;
  }
  .topbar {
    min-height: 77px;
  }
  .topbar h1 {
    font-size: 20px;
  }
  .topbar .eyebrow {
    display: none;
  }
  .date-chip {
    display: none;
  }
  .hero {
    grid-template-columns: 1fr;
  }
  .hero-main {
    padding: 22px;
  }
  .hero-main h2 {
    font-size: 22px;
  }
  .hero-main p {
    display: none;
  }
  .hero-side {
    display: none;
  }
  .metrics,
  .history-summary {
    grid-template-columns: repeat(2, 1fr);
    gap: 9px;
  }
  .metric {
    padding: 15px;
    border-radius: 17px;
  }
  .metric strong {
    font-size: 23px;
  }
  .grid-2 {
    gap: 13px;
  }
  .panel {
    border-radius: 21px;
  }
  .section-title {
    display: block;
    margin-top: 11px;
  }
  .section-title h2 {
    font-size: 23px;
  }
  .section-title .primary {
    width: 100%;
    margin-top: 13px;
  }
  .toolbar {
    margin-top: 13px;
  }
  .toolbar > * {
    width: 100%;
  }
  .job-card {
    grid-template-columns: 48px 1fr;
    align-items: start;
  }
  .job-photo {
    width: 48px;
    height: 48px;
  }
  .job-actions {
    grid-column: 1/-1;
    justify-content: stretch;
  }
  .job-actions > * {
    flex: 1;
  }
  .work-history-card {
    grid-template-columns: 1fr;
    gap: 7px;
  }
  .lost-grid {
    grid-template-columns: 1fr;
  }
  .history-filter-panel,
  .history-controls {
    display: grid;
    grid-template-columns: 1fr 1fr;
  }
  .history-filter-panel .search,
  .history-controls .search {
    grid-column: 1/-1;
    min-width: 0;
  }
  .qr-layout {
    grid-template-columns: 1fr;
  }
  .qr-preview {
    grid-template-columns: 1fr;
  }
  .form-row {
    grid-template-columns: 1fr;
  }
  .notification-panel {
    position: fixed;
    right: 14px;
    top: 70px;
  }
  .table-wrap {
    border-radius: 18px;
  }
  .data-table {
    min-width: 700px;
  }
  .security-note {
    font-size: 9px;
  }
}
body,
button,
input,
select,
textarea,
h1,
h2,
h3,
h4,
.eyebrow,
.brand,
.brand * {
  font-family: "Inter", "Noto Sans Thai", system-ui, sans-serif !important;
}
.pull-indicator {
  display: none;
  text-align: center;
  color: var(--muted);
  font-size: 10px;
  font-weight: 700;
  padding: 5px;
}
.loading-mask {
  position: fixed;
  inset: 0;
  z-index: 100;
  background: var(--canvas);
  display: grid;
  place-items: center;
  animation: maskAway 0.3s 0.55s forwards;
  pointer-events: none;
}
.loading-card {
  width: min(420px, calc(100% - 32px));
  background: #fff;
  border-radius: 24px;
  padding: 22px;
  box-shadow: var(--shadow);
}
.loading-card span {
  display: block;
  height: 14px;
  border-radius: 999px;
  margin: 12px 0;
}
.loading-card span:first-child {
  width: 38%;
  height: 24px;
}
.loading-card span:nth-child(2) {
  width: 82%;
}
.loading-card span:nth-child(3) {
  width: 63%;
}
@keyframes maskAway {
  to {
    opacity: 0;
    visibility: hidden;
  }
}
@media (max-width: 720px) {
  .pull-indicator {
    display: block;
  }
}
.role-hidden {
  display: none !important;
}
.job-card.owned {
  border-color: #d8d1ff;
  box-shadow: 0 12px 34px rgba(109, 93, 246, 0.1);
}
.notification-item {
  grid-template-columns: 38px 1fr auto;
}
.notification-item p {
  font-size: 10px;
  margin: 3px 0;
  color: var(--muted);
}
.notification-item time {
  font-size: 9px;
  color: var(--muted);
  white-space: nowrap;
}
.toast {
  position: fixed;
  right: 22px;
  bottom: 22px;
  z-index: 120;
  opacity: 0;
  transform: translateY(12px);
  pointer-events: none;
  transition: 0.22s;
  padding: 12px 16px;
}
.toast.show {
  opacity: 1;
  transform: translateY(0);
}
.status-select {
  width: 100%;
  min-height: 40px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #fff;
  padding: 0 10px;
}
.read-only {
  padding: 10px;
  border-radius: 12px;
  background: #f3f2f7;
  color: var(--muted);
  font-size: 10px;
  text-align: center;
}
.claim-controls {
  display: grid;
  gap: 8px;
}
.claim-controls select {
  min-height: 42px;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 0 10px;
}
.custody,
.history-empty {
  font-size: 10px;
  color: var(--muted);
}
.history-empty {
  padding: 36px;
  text-align: center;
}
.admin-delete-row {
  display: flex;
  justify-content: flex-end;
}
.delete {
  color: var(--danger);
}
@media (max-width: 720px) {
  .notification-item {
    grid-template-columns: 38px 1fr;
  }
  .notification-item time {
    grid-column: 2;
  }
  .toast {
    left: 14px;
    right: 14px;
    bottom: 14px;
    text-align: center;
  }
}

:root {
  --primary: #6d5df6;
  --primary-soft: #f0edff;
  --canvas: #f7f7fb;
  --surface: #fff;
  --ink: #1b1926;
  --muted: #716d7d;
  --line: #e9e7ef;
  --role: #6d5df6;
  --role-soft: #f0edff;
  --shadow: 0 12px 36px rgba(42, 35, 85, 0.08);
}
body {
  background: linear-gradient(145deg, #f3f0ff 0, #fff 35%, #f7f7fb 100%);
  color: var(--ink);
}
button {
  min-height: 44px;
  cursor: pointer;
  transition: transform 0.16s ease, box-shadow 0.2s ease,
    background-color 0.2s ease;
}
button:active {
  transform: scale(0.97);
}
button:focus-visible,
input:focus-visible,
select:focus-visible,
textarea:focus-visible,
[tabindex]:focus-visible {
  outline: 3px solid rgba(109, 93, 246, 0.28);
  outline-offset: 3px;
}
.icon {
  width: 22px;
  height: 22px;
  display: block;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.9;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.page {
  animation: pageEnter 0.2s ease;
}
.app main {
  max-width: none;
}
.app main > .page,
.topbar {
  max-width: 1200px;
  margin-left: auto;
  margin-right: auto;
}
.sidebar {
  transition: width 0.2s ease, left 0.22s ease;
}
.sidebar-backdrop {
  position: fixed;
  inset: 0;
  z-index: 39;
  border: 0;
  background: rgba(24, 20, 42, 0.38);
  opacity: 0;
  visibility: hidden;
  transition: 0.2s;
}
.sidebar-backdrop.open {
  opacity: 1;
  visibility: visible;
}
.sidebar-collapse {
  position: absolute;
  right: -15px;
  top: 76px;
  width: 34px;
  height: 34px;
  min-height: 34px;
  border: 1px solid var(--line);
  border-radius: 50%;
  background: #fff;
  box-shadow: var(--shadow);
  display: grid;
  place-items: center;
}
.app.sidebar-collapsed .sidebar {
  width: 88px;
}
.app.sidebar-collapsed main {
  margin-left: 112px;
}
.app.sidebar-collapsed .brand > div:last-child,
.app.sidebar-collapsed .shift-card > div:not(.shift-top),
.app.sidebar-collapsed .shift-top > div:last-child,
.app.sidebar-collapsed .nav-label,
.app.sidebar-collapsed .nav-item > span:last-child,
.app.sidebar-collapsed .nav-item:not(:has(span:last-child)),
.app.sidebar-collapsed .sidebar-foot {
  display: none;
}
.app.sidebar-collapsed .nav-item {
  justify-content: center;
  padding: 0;
}
.app.sidebar-collapsed .brand {
  justify-content: center;
}
.role-demo {
  display: grid;
  gap: 8px;
  margin-top: 12px;
}
.role-demo-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 7px;
}
.role-demo-btn {
  min-height: 39px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #fff;
  font-size: 10px;
  font-weight: 800;
  color: var(--muted);
}
.role-demo-btn.active {
  border-color: var(--role);
  background: var(--role-soft);
  color: var(--role);
}
.demo-caption {
  font-size: 8px;
  line-height: 1.35;
  color: var(--muted);
  text-align: center;
}
.ready-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 34px;
  padding: 0 11px;
  border-radius: 999px;
  background: #ebf8ed;
  color: #258745;
  font-size: 10px;
  font-weight: 800;
}
.ready-pill:before {
  content: "";
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #35ac5a;
}
.header-profile {
  display: flex;
  align-items: center;
  gap: 9px;
  border: 0;
  border-radius: 15px;
  background: #fff;
  padding: 5px 10px 5px 5px;
  color: var(--ink);
  box-shadow: 0 5px 18px rgba(42, 35, 85, 0.06);
}
.header-profile .avatar {
  width: 36px;
  height: 36px;
}
.header-profile strong,
.header-profile small {
  display: block;
  text-align: left;
}
.header-profile strong {
  font-size: 10px;
}
.header-profile small {
  font-size: 8px;
  color: var(--role);
}
.notification-panel {
  max-height: min(620px, 75vh);
  overflow: auto;
}
.notification-item {
  border: 0;
  background: transparent;
  width: 100%;
  text-align: left;
}
.notification-actions {
  display: flex;
  gap: 6px;
  margin-top: 7px;
}
.notification-actions button {
  min-height: 32px;
  padding: 0 9px;
  border: 0;
  border-radius: 10px;
  background: #f1eff7;
  font-size: 9px;
}
.notification-group-label {
  margin: 12px 0 4px;
  font-size: 9px;
  font-weight: 800;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.notification-count {
  animation: badgePulse 0.45s ease 1;
}
.job-card {
  cursor: pointer;
}
.job-photo,
.lost-image {
  display: grid;
  place-items: center;
  color: var(--role);
  background: var(--role-soft);
}
.job-photo .icon,
.lost-image .icon {
  width: 40px;
  height: 40px;
}
.job-actions {
  position: relative;
  z-index: 2;
}
.job-detail-modal .modal-card {
  width: min(820px, 100%);
}
.detail-layout {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 18px;
}
.detail-photo {
  min-height: 210px;
  border-radius: 18px;
  background: var(--role-soft);
  color: var(--role);
  display: grid;
  place-items: center;
}
.detail-photo .icon {
  width: 72px;
  height: 72px;
}
.detail-meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 9px;
}
.detail-meta div {
  padding: 11px;
  border-radius: 13px;
  background: #f8f7fb;
}
.detail-meta small,
.detail-meta strong {
  display: block;
}
.detail-meta small {
  font-size: 9px;
  color: var(--muted);
}
.timeline {
  display: grid;
  gap: 0;
  margin-top: 16px;
}
.timeline-item {
  display: grid;
  grid-template-columns: 18px 1fr;
  gap: 9px;
  position: relative;
  padding-bottom: 13px;
}
.timeline-item:before {
  content: "";
  position: absolute;
  left: 6px;
  top: 15px;
  bottom: 0;
  width: 1px;
  background: var(--line);
}
.timeline-item:last-child:before {
  display: none;
}
.timeline-dot {
  width: 13px;
  height: 13px;
  border-radius: 50%;
  margin-top: 3px;
  background: var(--role);
  box-shadow: 0 0 0 4px var(--role-soft);
}
.timeline-item strong,
.timeline-item small {
  display: block;
}
.timeline-item small {
  font-size: 9px;
  color: var(--muted);
}
.quick-action-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 14px;
}
.quick-action {
  border: 1px solid var(--line);
  border-radius: 13px;
  background: #fff;
  padding: 9px;
  font-size: 10px;
  font-weight: 800;
}
.quick-action.primary-action {
  background: var(--role);
  border-color: var(--role);
  color: #fff;
}
.progress-upload {
  border: 1px dashed #cbc6de;
  border-radius: 14px;
  padding: 14px;
  display: grid;
  justify-items: center;
  gap: 5px;
  background: #faf9fd;
}
.progress-upload input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}
.progress-preview {
  display: none;
  align-items: center;
  gap: 9px;
  margin-top: 9px;
}
.progress-preview.visible {
  display: flex;
}
.progress-preview img {
  width: 58px;
  height: 58px;
  border-radius: 11px;
  object-fit: cover;
}
.progress-preview span {
  flex: 1;
  font-size: 10px;
  color: var(--muted);
}
.modal-open {
  overflow: hidden;
}
.modal {
  opacity: 0;
  visibility: hidden;
  display: grid;
  transition: opacity 0.2s ease;
}
.modal.open {
  opacity: 1;
  visibility: visible;
}
.modal-card {
  transform: translateY(14px);
  transition: transform 0.2s ease;
}
.modal.open .modal-card {
  transform: translateY(0);
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}
.modal-actions > * {
  min-width: 112px;
}
.confirm-icon {
  width: 64px;
  height: 64px;
  border-radius: 20px;
  background: var(--primary-soft);
  color: var(--primary);
  display: grid;
  place-items: center;
  margin: 0 auto 13px;
}
.confirm-icon .icon {
  width: 34px;
  height: 34px;
}
.confirmation {
  text-align: center;
}
.profile-grid {
  display: grid;
  grid-template-columns: 100px 1fr;
  gap: 16px;
}
.profile-avatar-large {
  width: 92px;
  height: 92px;
  border-radius: 25px;
  background: var(--role-soft);
  color: var(--role);
  display: grid;
  place-items: center;
  font-size: 25px;
  font-weight: 900;
}
.profile-data {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 9px;
}
.profile-data div {
  padding: 11px;
  border-radius: 13px;
  background: #f8f7fb;
}
.profile-data small,
.profile-data strong {
  display: block;
}
.profile-data small {
  font-size: 9px;
  color: var(--muted);
}
.announcement-list {
  display: grid;
  gap: 10px;
}
.announcement-card {
  border: 1px solid var(--line);
  border-radius: 18px;
  background: #fff;
  padding: 16px;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 12px;
}
.announcement-card h3 {
  margin: 0 0 3px;
}
.announcement-card p {
  font-size: 11px;
  margin: 0;
}
.announcement-card .row-actions {
  align-self: center;
}
.bottom-nav {
  display: none;
}
.toast {
  border-radius: 14px !important;
  background: #211d35 !important;
}
.close {
  display: grid;
  place-items: center;
}
.success-check {
  width: 74px;
  height: 74px;
  border-radius: 50%;
  background: #ebf8ed;
  color: #258745;
  display: grid;
  place-items: center;
  margin: 0 auto 14px;
  animation: successPop 0.36s ease;
}
.success-check .icon {
  width: 38px;
  height: 38px;
}
.loading-mask {
  pointer-events: none;
  animation: none;
}
.loading-mask.hide {
  opacity: 0;
  visibility: hidden;
}
.empty {
  min-height: 120px;
  display: grid;
  place-items: center;
}
.table-wrap {
  border-radius: 20px;
}
.data-table button,
.data-table select {
  min-height: 40px;
}
@keyframes pageEnter {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
}
@keyframes badgePulse {
  50% {
    transform: scale(1.12);
  }
}
@keyframes successPop {
  from {
    opacity: 0;
    transform: scale(0.65);
  }
}
@media (hover: hover) and (pointer: fine) {
  .job-card:hover,
  .lost-card:hover,
  .metric:hover,
  .announcement-card:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow);
  }
}
@media (max-width: 1024px) {
  .sidebar-collapse {
    display: none;
  }
  .app.sidebar-collapsed main {
    margin-left: 0;
  }
  .ready-pill {
    display: none;
  }
  .header-profile span {
    display: none;
  }
  .sidebar-backdrop.open {
    display: block;
  }
  .detail-layout {
    grid-template-columns: 1fr;
  }
  .app main > .page,
  .topbar {
    max-width: 100%;
  }
}
@media (max-width: 720px) {
  main {
    padding-bottom: 96px !important;
  }
  .topbar {
    align-items: center;
  }
  .topbar > div:first-child .eyebrow {
    display: none;
  }
  .topbar h1 {
    font-size: 20px;
  }
  .date-chip {
    display: none;
  }
  .top-actions {
    gap: 6px;
  }
  .header-profile {
    padding: 4px;
  }
  .header-profile .avatar {
    margin: 0;
  }
  .bottom-nav {
    position: fixed;
    z-index: 35;
    left: 0;
    right: 0;
    bottom: 0;
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    height: 78px;
    padding: 7px 4px max(7px, env(safe-area-inset-bottom));
    border-top: 1px solid var(--line);
    background: rgba(255, 255, 255, 0.96);
    backdrop-filter: blur(18px);
    box-shadow: 0 -8px 28px rgba(35, 28, 66, 0.08);
  }
  .bottom-nav button {
    position: relative;
    border: 0;
    background: transparent;
    color: #76717f;
    display: grid;
    place-items: center;
    align-content: center;
    gap: 2px;
    font-size: 8px;
  }
  .bottom-nav button.active {
    color: var(--role);
  }
  .bottom-nav .icon {
    width: 21px;
    height: 21px;
  }
  .bottom-nav .new-action {
    width: 56px;
    height: 56px;
    min-height: 56px;
    border-radius: 50%;
    align-self: end;
    justify-self: center;
    margin-bottom: 13px;
    background: var(--role);
    color: #fff;
    box-shadow: 0 10px 24px color-mix(in srgb, var(--role) 32%, transparent);
  }
  .bottom-nav .new-action span {
    display: none;
  }
  .modal {
    align-items: end;
    padding: 0;
  }
  .modal-card,
  .job-detail-modal .modal-card {
    width: 100%;
    max-height: 90vh;
    border-radius: 24px 24px 0 0;
    padding: 19px 17px max(24px, env(safe-area-inset-bottom));
  }
  .quick-action-grid {
    grid-template-columns: 1fr 1fr;
  }
  .profile-grid {
    grid-template-columns: 1fr;
    text-align: center;
  }
  .profile-avatar-large {
    margin: auto;
  }
  .profile-data {
    grid-template-columns: 1fr;
    text-align: left;
  }
  .modal-actions {
    display: grid;
    grid-template-columns: 1fr;
  }
  .modal-actions > * {
    width: 100%;
  }
  .table-wrap .data-table thead {
    display: none;
  }
  .table-wrap .data-table,
  .table-wrap .data-table tbody,
  .table-wrap .data-table tr,
  .table-wrap .data-table td {
    display: block;
    width: 100%;
  }
  .table-wrap .data-table tr {
    border: 1px solid var(--line);
    border-radius: 17px;
    margin-bottom: 10px;
    padding: 12px;
    background: #fff;
  }
  .table-wrap .data-table td {
    border: 0;
    padding: 7px;
  }
  .announcement-card {
    grid-template-columns: 1fr;
  }
  .announcement-card .row-actions {
    justify-content: flex-start;
  }
}
@media (prefers-reduced-motion: reduce) {
  *,
  *:before,
  *:after {
    scroll-behavior: auto !important;
    animation: none !important;
    transition: none !important;
  }
}

.metrics,
.history-summary {
  grid-template-columns: repeat(auto-fit, minmax(145px, 1fr));
}
.service-choice-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 9px;
}
.service-choice-grid .quick-action {
  min-height: 58px;
}
.job-card p {
  display: none;
}
.job-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.job-actions button {
  min-width: 112px;
}
.detail-notes {
  margin-top: 12px;
  padding: 13px;
  border-radius: 14px;
  background: #f8f7fb;
}
.detail-notes strong,
.detail-notes small {
  display: block;
}
.detail-notes small {
  color: var(--muted);
  margin-top: 4px;
}
.drop-zone {
  border: 1.5px dashed #c8c2dc;
  border-radius: 18px;
  background: #faf9fd;
  min-height: 132px;
  padding: 18px;
  display: grid;
  place-items: center;
  text-align: center;
  cursor: pointer;
}
.drop-zone.dragging {
  border-color: var(--role);
  background: var(--role-soft);
}
.drop-zone input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}
.upload-preview {
  display: none;
  grid-template-columns: 72px 1fr auto;
  align-items: center;
  gap: 11px;
  margin-top: 10px;
  padding: 10px;
  border: 1px solid var(--line);
  border-radius: 15px;
}
.upload-preview.visible {
  display: grid;
}
.upload-preview img {
  width: 72px;
  height: 72px;
  object-fit: cover;
  border-radius: 12px;
}
.staff-choice-list {
  display: grid;
  gap: 8px;
  max-height: 280px;
  overflow: auto;
}
.staff-choice {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 15px;
  background: #fff;
  padding: 11px;
  text-align: left;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
}
.staff-choice.selected {
  border-color: var(--role);
  background: var(--role-soft);
}
.staff-choice small {
  display: block;
  color: var(--muted);
}
.inline-summary {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 9px;
}
.inline-summary > div {
  padding: 12px;
  border-radius: 14px;
  background: #f8f7fb;
}
.inline-summary small,
.inline-summary strong {
  display: block;
}
.inline-summary small {
  font-size: 9px;
  color: var(--muted);
}
.modal-subtitle {
  margin: -6px 0 14px;
  color: var(--muted);
  font-size: 11px;
}
.claim-secret {
  border-left: 3px solid var(--role);
  background: var(--role-soft);
  padding: 12px;
  border-radius: 0 14px 14px 0;
}
.qr-launch {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 16px;
  align-items: center;
  padding: 20px;
  border-radius: 22px;
  background: #fff;
  box-shadow: var(--shadow);
  margin-bottom: 16px;
}
.qr-layout.compact {
  grid-template-columns: minmax(260px, 380px) 1fr;
}
.qr-layout.compact .qr-preview {
  grid-column: 1/-1;
}
.danger-outline {
  border: 1px solid #efc3c8;
  background: #fff7f8;
  color: #c93645;
}
.compact-card-copy {
  color: var(--muted);
  font-size: 10px;
}
.lost-card .claim-controls {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.lost-card p {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
@media (max-width: 720px) {
  .inline-summary {
    grid-template-columns: 1fr;
  }
  .upload-preview {
    grid-template-columns: 56px 1fr;
  }
  .upload-preview img {
    width: 56px;
    height: 56px;
  }
  .upload-preview button {
    grid-column: 1/-1;
  }
  .qr-launch {
    grid-template-columns: 1fr;
  }
  .job-actions button {
    flex: 1;
  }
}

html,
body {
  width: 100%;
  max-width: 100%;
  overflow-x: hidden;
}
* {
  box-sizing: border-box;
}
img,
svg {
  max-width: 100%;
}
body {
  margin: 0;
  min-height: 100vh;
  background: radial-gradient(
      circle at 82% 0,
      rgba(109, 93, 246, 0.11),
      transparent 30%
    ),
    linear-gradient(145deg, #f7f5ff 0, #f8f8fb 48%, #fff 100%);
  color: var(--ink);
  font-family: "Inter", "Noto Sans Thai", system-ui, sans-serif;
}
.app {
  width: 100%;
  max-width: none;
  min-height: 100vh;
  margin: 0;
}
.sidebar {
  left: 24px;
  top: 24px;
  bottom: 24px;
  width: 248px;
  max-width: calc(100vw - 32px);
  padding: 20px;
  border: 1px solid rgba(255, 255, 255, 0.86);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 18px 52px rgba(42, 35, 85, 0.1);
  backdrop-filter: blur(22px);
  -webkit-backdrop-filter: blur(22px);
  overflow-y: auto;
  overscroll-behavior: contain;
}
.app main,
.app.sidebar-collapsed main {
  width: auto;
  min-width: 0;
  margin-left: 292px;
  padding: 0 28px 72px;
}
.app main > .page,
.topbar {
  width: 100%;
  max-width: 1160px;
  margin-left: auto;
  margin-right: auto;
}
.topbar {
  min-height: 80px;
  padding: 10px 0;
  background: rgba(248, 248, 252, 0.84);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
}
.topbar h1 {
  font-size: 26px;
}
.page {
  min-width: 0;
}
.page.active {
  display: block;
}
.hero,
.grid-2,
.metrics,
.history-summary,
.qr-layout,
.detail-layout,
.profile-grid {
  min-width: 0;
}
.hero-main,
.hero-side,
.panel,
.metric,
.job-card,
.work-history-card,
.lost-card,
.table-wrap,
.qr-preview,
.qr-launch,
.form-panel,
.queue-explainer,
.history-filter-panel,
.history-controls {
  border-color: rgba(255, 255, 255, 0.9);
  box-shadow: 0 10px 32px rgba(42, 35, 85, 0.075);
}
.panel,
.table-wrap,
.qr-preview,
.form-panel {
  border-radius: 24px;
}
.metric,
.job-card,
.work-history-card,
.lost-card {
  border-radius: 22px;
}
.board-tabs,
.tabs {
  width: 100%;
  max-width: 100%;
  gap: 8px;
  padding: 4px;
  margin: 14px 0 18px;
  overflow-x: auto;
  overscroll-behavior-inline: contain;
  scrollbar-width: none;
}
.board-tabs::-webkit-scrollbar,
.tabs::-webkit-scrollbar {
  display: none;
}
.board-tab,
.tab {
  -webkit-appearance: none;
  appearance: none;
  flex: 0 0 auto;
  min-height: 44px;
  border: 1px solid #e7e4ef;
  border-radius: 999px;
  background: #fff;
  color: #686473;
  padding: 0 17px;
  box-shadow: 0 4px 14px rgba(42, 35, 85, 0.045);
  font-size: 11px;
  font-weight: 800;
  transition: transform 0.16s ease, background-color 0.18s ease,
    border-color 0.18s ease, color 0.18s ease;
}
.board-tab:hover,
.tab:hover {
  border-color: #cfc8ff;
  background: #f5f2ff;
  color: var(--primary);
}
.board-tab.active,
.tab.active {
  border-color: var(--primary);
  background: linear-gradient(135deg, var(--primary), #8173f8);
  color: #fff;
  box-shadow: 0 9px 20px rgba(109, 93, 246, 0.23);
}
.board-tab:active,
.tab:active {
  transform: scale(0.97);
}
.job-list,
.work-history-list,
.lost-grid {
  min-width: 0;
  gap: 14px;
}
.job-card {
  width: 100%;
  min-width: 0;
  grid-template-columns: 60px minmax(0, 1fr) minmax(150px, auto);
  padding: 18px;
  gap: 16px;
  border: 1px solid rgba(234, 232, 241, 0.8);
  background: #fff;
}
.job-card > div {
  min-width: 0;
}
.job-card h3 {
  overflow-wrap: anywhere;
}
.job-photo {
  width: 60px;
  height: 60px;
  border-radius: 18px;
}
.job-detail {
  display: flex;
  align-items: center;
  gap: 8px 13px;
  flex-wrap: wrap;
  color: var(--muted);
  font-size: 10px;
}
.job-actions {
  min-width: 0;
  max-width: 330px;
}
.job-actions button {
  white-space: normal;
}
.lost-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}
.lost-card,
.lost-content {
  min-width: 0;
}
.lost-content h3,
.lost-content p,
.announcement-card h3,
.announcement-card p {
  overflow-wrap: anywhere;
}
.toolbar,
.history-controls,
.history-filter-panel,
.row-actions,
.modal-actions {
  min-width: 0;
}
.toolbar > * {
  max-width: 100%;
}
.field-compact {
  min-width: 0;
}
.table-wrap {
  width: 100%;
  max-width: 100%;
  overflow: auto;
  overscroll-behavior-inline: contain;
}
.data-table {
  max-width: 100%;
}
.modal {
  z-index: 80;
  padding: 20px;
  background: rgba(27, 22, 48, 0.45);
  opacity: 0;
  visibility: hidden;
  display: grid;
  pointer-events: none;
  transition: opacity 180ms ease, visibility 180ms ease;
}
.modal.open {
  opacity: 1;
  visibility: visible;
  pointer-events: auto;
}
.modal-card,
.job-detail-modal .modal-card {
  width: min(620px, 100%);
  max-width: 100%;
  max-height: min(90vh, 820px);
  overflow: auto;
  border: 1px solid rgba(255, 255, 255, 0.9);
  border-radius: 26px;
  background: #fff;
  padding: 24px;
  box-shadow: 0 32px 90px rgba(25, 20, 52, 0.25);
  transform: translateY(14px) scale(0.985);
  opacity: 0;
  animation: none;
  transition: transform 220ms ease, opacity 180ms ease;
}
.job-detail-modal .modal-card {
  width: min(860px, 100%);
}
.modal.open .modal-card {
  transform: translateY(0) scale(1);
  opacity: 1;
}
.modal-head {
  position: sticky;
  z-index: 2;
  top: -24px;
  margin: -24px -24px 18px;
  padding: 20px 24px 14px;
  background: rgba(255, 255, 255, 0.96);
  border-bottom: 1px solid var(--line);
  backdrop-filter: blur(12px);
}
.close {
  flex: 0 0 42px;
  width: 42px;
  height: 42px;
  min-height: 42px;
  border-radius: 14px;
}
.notification-panel {
  z-index: 60;
}
.bottom-nav {
  box-sizing: border-box;
}
.toast {
  z-index: 100;
}
@media (max-width: 1050px) {
  .sidebar {
    left: -290px;
    top: 14px;
    bottom: 14px;
  }
  .sidebar.open {
    left: 14px;
  }
  .app main,
  .app.sidebar-collapsed main {
    width: 100%;
    margin-left: 0;
    padding: 0 22px 84px;
  }
  .sidebar-backdrop {
    display: block;
  }
  .topbar {
    max-width: 100%;
    min-height: 78px;
  }
  .lost-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
@media (max-width: 720px) {
  body {
    background: linear-gradient(180deg, #f5f2ff 0, #fafafd 220px, #f8f8fb 100%);
  }
  .app main,
  .app.sidebar-collapsed main {
    width: 100%;
    margin: 0;
    padding: 0 16px max(112px, calc(96px + env(safe-area-inset-bottom)));
  }
  .topbar {
    min-height: 72px;
    padding: 8px 0;
  }
  .topbar h1 {
    font-size: 20px;
  }
  .top-actions {
    min-width: 0;
  }
  .header-profile {
    max-width: 46px;
  }
  .hero {
    margin-top: 8px;
  }
  .hero-main {
    border-radius: 22px;
  }
  .metrics,
  .history-summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }
  .metric {
    min-width: 0;
    padding: 16px;
  }
  .metric span,
  .metric small {
    white-space: normal;
  }
  .metric strong {
    font-size: 24px;
  }
  .section-title {
    gap: 10px;
  }
  .section-title h2 {
    font-size: 22px;
  }
  .board-tabs,
  .tabs {
    margin-left: -4px;
    margin-right: -4px;
  }
  .job-card {
    grid-template-columns: 52px minmax(0, 1fr);
    padding: 15px;
    gap: 12px;
    border-radius: 20px;
  }
  .job-photo {
    width: 52px;
    height: 52px;
    border-radius: 16px;
  }
  .job-actions {
    grid-column: 1/-1;
    max-width: none;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    width: 100%;
  }
  .job-actions button,
  .job-actions .read-only {
    width: 100%;
    min-width: 0;
  }
  .lost-grid {
    grid-template-columns: 1fr;
  }
  .notification-panel {
    position: fixed;
    left: 12px;
    right: 12px;
    top: 72px;
    width: auto;
    max-height: calc(100vh - 92px);
  }
  .modal {
    align-items: end;
    padding: 0;
  }
  .modal-card,
  .job-detail-modal .modal-card {
    width: 100%;
    max-width: 100%;
    max-height: 92dvh;
    border-radius: 26px 26px 0 0;
    padding: 20px 16px max(24px, env(safe-area-inset-bottom));
    transform: translateY(28px) scale(1);
  }
  .modal.open .modal-card {
    transform: translateY(0) scale(1);
  }
  .modal-head {
    top: -20px;
    margin: -20px -16px 16px;
    padding: 17px 16px 12px;
  }
  .detail-layout,
  .form-row,
  .profile-grid {
    grid-template-columns: 1fr;
  }
  .detail-meta,
  .profile-data {
    grid-template-columns: 1fr 1fr;
  }
  .quick-action-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .quick-action {
    min-width: 0;
  }
  .table-wrap {
    overflow: visible;
    background: transparent;
    border: 0;
    box-shadow: none;
  }
  .data-table,
  .data-table tbody,
  .data-table tr,
  .data-table td {
    display: block;
    width: 100%;
    min-width: 0 !important;
    max-width: 100%;
  }
  .data-table thead {
    display: none;
  }
  .data-table tr {
    margin-bottom: 12px;
    padding: 13px;
    border: 1px solid var(--line);
    border-radius: 18px;
    background: #fff;
    box-shadow: 0 7px 22px rgba(42, 35, 85, 0.055);
  }
  .data-table td {
    padding: 7px 4px;
    border: 0;
    overflow-wrap: anywhere;
  }
  .bottom-nav {
    left: 0;
    right: 0;
    bottom: 0;
    width: 100%;
    height: 84px;
    padding: 8px 4px max(8px, env(safe-area-inset-bottom));
    overflow: visible;
  }
  .bottom-nav button {
    min-width: 0;
  }
  .qr-launch {
    padding: 17px;
  }
  .qr-layout,
  .qr-layout.compact,
  .qr-preview {
    grid-template-columns: 1fr;
  }
  .qr-code {
    max-width: 100%;
    margin: auto;
  }
  .announcement-card {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 390px) {
  .app main,
  .app.sidebar-collapsed main {
    padding-left: 14px;
    padding-right: 14px;
  }
  .metrics,
  .history-summary {
    gap: 8px;
  }
  .metric {
    padding: 14px;
  }
  .job-actions {
    grid-template-columns: 1fr;
  }
  .detail-meta,
  .profile-data,
  .quick-action-grid {
    grid-template-columns: 1fr;
  }
  .service-choice-grid {
    grid-template-columns: 1fr;
  }
  .topbar h1 {
    font-size: 18px;
  }
}
@media (hover: hover) and (pointer: fine) {
  .job-card:hover,
  .lost-card:hover,
  .metric:hover,
  .panel:hover {
    transform: translateY(-3px);
    box-shadow: 0 15px 38px rgba(42, 35, 85, 0.1);
  }
}
@media (prefers-reduced-motion: reduce) {
  *,
  *:before,
  *:after {
    scroll-behavior: auto !important;
    animation: none !important;
    transition: none !important;
  }
}
</style>