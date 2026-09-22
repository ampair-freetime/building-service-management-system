import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { buildGuestQrUrl } from "../services/guestQrUrl.js";
import { createStaffDashboardData } from "./staff-dashboard/data.js";
import { STAFF_ROLE_PAGES, canRoleOpenPage } from "../config/staff-role-pages.js";
import {
  getFoundItemDetail,
  getLostItemDetail,
  getPendingFoundItems,
  getPendingLostItems,
  getApprovedLostFoundItems,
  rejectFoundItem,
  rejectLostItemAnnouncement,
  approveFoundItem,
  approveLostItemAnnouncement,
  getPendingOwnershipRequests,
  getOwnershipRequestDetail,
  approveOwnershipRequest,
  requestOwnershipAdditionalInfo,
  scheduleOwnershipPickup,
  updateOwnershipReturnStatus,
} from "../services/clerkApi.js";
import {
  badgeClass,
  currentTimeHM,
  escapeHtml,
  isTerminalStatus,
  loadQrCodeLibrary,
  nowThai,
  todayISO,
  validImage,
} from "./staff-dashboard/utils.js";
import {
  createStaffAccount,
  fetchStaffAccounts,
  toDashboardStaff,
} from "./staff-dashboard/staff-accounts.js";
import {
  acceptCleaningTask,
  addCleaningCompletionNote,
  getCleaningTaskHistory,
  getStaffNotifications,
  markStaffNotificationRead,
  updateCleaningTaskStatus,
  uploadCleaningCompletionPhotos,
} from "../services/housekeeperAPI.js";
import {
  acceptRepairRequest,
  addRepairCompletionNote,
  completeRepairRequest,
  getRepairRequestDetail,
  getRepairRequestHistory,
  getRepairRequests,
  updateRepairRequestStatus,
  uploadRepairCompletionPhotos,
} from "../services/technicianAPI.js";

export function useStaffDashboard() {
  // ---------------------------------------------------------------------------
  // 1) Dashboard lifecycle และ state ที่ Vue component ต้องใช้งาน
  // ---------------------------------------------------------------------------
  const router = useRouter();
  const allowedRoles = ["housekeeper", "technician", "clerk", "admin"];
  const savedRole = localStorage.getItem("buildingCareRole");
  const activeRole = ref(allowedRoles.includes(savedRole) ? savedRole : "clerk");

  async function initializeDashboard() {
    // โหลด dependency ภายนอกก่อนสร้างหน้าจอ หากโหลดไม่ได้จะใช้ QR fallback แทน
    try {
      await loadQrCodeLibrary();
    } catch (error) {
      console.warn(
        "QR Code library could not be loaded. QR fallback will be used.",
        error
      );
    }

    let {
      roleConfig,
      currentUserName,
      allJobs,
      staffData,
      lostSets,
      deletedRecords,
      auditHistory,
      workHistory,
      selectedOverviewStaff,
      notificationSets,
      categories,
    } = createStaffDashboardData();
    let currentRole = activeRole.value;
    try {
      const signedInStaff = JSON.parse(
        localStorage.getItem("buildingCareStaff") || "null"
      );
      if (
        signedInStaff?.full_name &&
        signedInStaff?.staff_code &&
        allowedRoles.includes(signedInStaff.role)
      ) {
        const signedInRole = signedInStaff.role;
        const initials = signedInStaff.full_name
          .split(/\s+/)
          .filter(Boolean)
          .slice(0, 2)
          .map((part) => part.charAt(0).toUpperCase())
          .join("");
        currentUserName[signedInRole] = signedInStaff.full_name;
        roleConfig[signedInRole].name = signedInStaff.full_name;
        roleConfig[signedInRole].staffId = signedInStaff.staff_code;
        roleConfig[signedInRole].avatar = initials || roleConfig[signedInRole].avatar;
      }
    } catch (error) {
      console.warn("Stored staff profile is invalid:", error);
    }

    // ผูกงานจำลองกับชื่อ Staff ที่ login เพื่อทดสอบแท็บ "งานของฉัน"
    allJobs.forEach((job) => {
      if (job.assignee === "__CURRENT_HOUSEKEEPER__") {
        job.assignee = currentUserName.housekeeper;
      }
      if (job.assignee === "__CURRENT_TECHNICIAN__") {
        job.assignee = currentUserName.technician;
      }
    });
    workHistory.forEach((record) => {
      if (record.staff === "__CURRENT_HOUSEKEEPER__") {
        record.staff = currentUserName.housekeeper;
      }
      if (record.staff === "__CURRENT_TECHNICIAN__") {
        record.staff = currentUserName.technician;
      }
    });
    let currentLostTab = "inventory";
    let currentClerkCenterView = "approvals";
    const readClaimNotifications = new Set();
    let currentBoardView = "unassigned";
    let selectedJobId = "";
    let pendingConfirmAction = null;
    let lastModalTrigger = null;
    const $ = (s) => document.querySelector(s),
      $$ = (s) => [...document.querySelectorAll(s)];

    // -------------------------------------------------------------------------
    // 2) Authentication และข้อมูลบัญชี Staff
    // -------------------------------------------------------------------------

    // ล้าง session และพากลับหน้า login เมื่อ access token หมดอายุ
    async function handleUnauthorizedResponse(responseOrStatus) {
      const status =
        typeof responseOrStatus === "number"
          ? responseOrStatus
          : responseOrStatus?.status;
      if (status !== 401) return false;

      localStorage.removeItem("buildingCareAccessToken");
      localStorage.removeItem("buildingCareStaff");
      localStorage.removeItem("buildingCareRole");
      await router.replace("/staff-login");
      return true;
    }
    async function loadStaffAccounts() {
      if (currentRole !== "admin") return;
      try {
        staffData = await fetchStaffAccounts();
        renderStaff();
        renderMetrics();
        renderStaffOverview();
      } catch (error) {
        if (await handleUnauthorizedResponse(error.status)) return;
        console.error("Loading staff accounts failed:", error);
        toast("ไม่สามารถโหลดบัญชีเจ้าหน้าที่จากระบบได้");
      }
    }

    // -------------------------------------------------------------------------
    // 3) โหลดข้อมูล Lost & Found จาก Backend
    // -------------------------------------------------------------------------

    // โหลดรายการสิ่งของที่พบซึ่งกำลังรอธุรการอนุมัติรับฝาก
    async function loadPendingFoundItems() {
      if (currentRole !== "clerk") return;
      try {
        const data = await getPendingFoundItems();
        const pendingFoundItems = data.map((item) => ({
          backendId: item.id,
          id: item.item_code,
          title: item.item_name,
          category: "ของที่พบ",
          place: item.location_detail || "ไม่ระบุสถานที่พบ",
          description: item.description || "ไม่มีรายละเอียดเพิ่มเติม",
          custody: `รายงานเมื่อ ${new Date(item.created_at).toLocaleString("th-TH")}`,
          status: "รออนุมัติรับฝาก",
          assignee: null,
        }));
        const processedItems = lostSets.inventory.filter(
          (item) => approvalGroup(item.status) !== "pending"
        );
        lostSets.inventory = [...pendingFoundItems, ...processedItems];
        renderClerkCenter();
        renderMetrics();
        renderNotifications();
      } catch (error) {
        if (await handleUnauthorizedResponse(error.status)) return;
        console.error("Loading pending found-item reports failed:", error);
        toast(error.message || "ไม่สามารถโหลดรายงานของที่พบได้");
      }
    }

    // โหลดประกาศของหายที่กำลังรอธุรการอนุมัติเผยแพร่
    async function loadPendingLostItems() {
      if (currentRole !== "clerk") return;
      try {
        const data = await getPendingLostItems();
        const pendingLostItems = data.map((item) => ({
          backendId: item.id,
          id: item.item_code,
          title: item.item_name,
          category: "ประกาศตามหา",
          place: item.location_detail || "ไม่ระบุสถานที่คาดว่าหาย",
          description: item.description || "ไม่มีรายละเอียดเพิ่มเติม",
          custody: `ส่งประกาศเมื่อ ${new Date(item.created_at).toLocaleString("th-TH")}`,
          status: "รออนุมัติเผยแพร่",
          assignee: null,
        }));
        const processedItems = lostSets.lostposts.filter(
          (item) => approvalGroup(item.status) !== "pending"
        );
        lostSets.lostposts = [...pendingLostItems, ...processedItems];
        renderClerkCenter();
        renderMetrics();
        renderNotifications();
      } catch (error) {
        if (await handleUnauthorizedResponse(error.status)) return;
        console.error("Loading pending lost-item reports failed:", error);
        toast(error.message || "ไม่สามารถโหลดประกาศของหายได้");
      }
    }

    const completedLostFoundStorageKey = "buildingCareCompletedLostFoundItems";

    // อ่านรหัสรายการที่ปิดงานแล้ว เพื่อไม่ดึงกลับมาแสดงซ้ำ
    function completedLostFoundIds() {
      try {
        return new Set(
          JSON.parse(localStorage.getItem(completedLostFoundStorageKey) || "[]"),
        );
      } catch {
        return new Set();
      }
    }

    // โหลดของพบและประกาศของหายที่ผ่านการอนุมัติแล้ว
    async function loadApprovedLostFoundItems() {
      if (currentRole !== "clerk") return;
      try {
        const { foundItems, lostItems } = await getApprovedLostFoundItems();
        const completedIds = completedLostFoundIds();
        const mapApprovedItem = (item, tab) => ({
          backendId: item.id,
          id: item.item_code,
          title: item.item_name,
          category: item.item_category,
          place: item.location_detail || "ไม่ระบุสถานที่",
          description: item.description || "ไม่มีรายละเอียดเพิ่มเติม",
          custody: tab === "inventory" ? "รับฝากโดยธุรการ" : "เผยแพร่แล้ว",
          status: tab === "inventory" ? "อนุมัติรับฝาก" : "อนุมัติเผยแพร่",
          eventDatetime: item.event_datetime,
          imageUrl: item.images?.[0]?.url || "",
          assignee: null,
        });
        const mergeApproved = (tab, items) => {
          const approved = items
            .filter((item) => !completedIds.has(item.item_code))
            .map((item) => mapApprovedItem(item, tab));
          const approvedIds = new Set(approved.map((item) => item.backendId));
          lostSets[tab] = [
            ...lostSets[tab].filter((item) => !approvedIds.has(item.backendId)),
            ...approved,
          ];
        };
        mergeApproved("inventory", foundItems);
        mergeApproved("lostposts", lostItems);
        renderLost();
        renderMetrics();
      } catch (error) {
        console.error("Loading approved lost-and-found items failed:", error);
        toast(error.message || "ไม่สามารถโหลดรายการที่อนุมัติแล้วได้");
      }
    }

    // โหลดคำร้องขอรับของคืนพร้อมรายละเอียดของแต่ละคำร้อง
    async function loadPendingOwnershipRequests() {
      if (currentRole !== "clerk") return;

      try {
        const summaries = await getPendingOwnershipRequests();
        const data = await Promise.all(
          summaries.map(async (claim) => {
            try {
              return await getOwnershipRequestDetail(claim.id);
            } catch (error) {
              if (error.status === 401 || error.status === 403) throw error;
              console.warn("Loading ownership request detail failed:", error);
              return claim;
            }
          }),
        );

        lostSets.claims = data.map((claim) => ({
          backendId: claim.id,
          foundItemBackendId: claim.found_item_id,
          id: claim.claim_code || claim.id,
          title: `คำขอรับ${claim.item_name || "ของคืน"}`,
          place: claim.proof_detail || "ไม่มีรายละเอียดหลักฐาน",
          custody: "คำขอใหม่",
          backendStatus: claim.status,
          status: ownershipStatusLabel(claim.status),
          returnStatusCode: claim.return_status,
          returnStatus: foundItemReturnStatus(claim.return_status, claim.status),
          requester: claim.claimant_name,
          contact: claim.claimant_email,
          requestDate: new Date(
            claim.created_at,
          ).toLocaleString("th-TH"),
          evidence: claim.proof_detail,
          pickupDate:
            claim.pickup_date || claim.appointment?.pickup_date || "",
          pickupTime:
            claim.pickup_time || claim.appointment?.pickup_time || "",
          pickupLocation:
            claim.pickup_location ||
            claim.appointment?.pickup_location ||
            "",
          pickupNote: claim.pickup_note || claim.appointment?.note || "",
          appointment: claim.pickup_date
            ? `${claim.pickup_date} เวลา ${claim.pickup_time || "–"}`
            : "ยังไม่มีนัดหมาย",
          assignee: null,
        }));

        renderClerkCenter();
        renderMetrics();
        renderNotifications();
      } catch (error) {
        if (await handleUnauthorizedResponse(error.status)) return;

        console.error(
          "Loading pending ownership requests failed:",
          error,
        );

        if (error.status !== 404) {
          toast(
            error.message ||
              "ไม่สามารถโหลดคำขอแสดงความเป็นเจ้าของได้",
          );
        }
      }
    }

    // -------------------------------------------------------------------------
    // 4) Utility ภายใน Dashboard และการกำหนดสิทธิ์ตาม Role
    // -------------------------------------------------------------------------

    // แสดงข้อความแจ้งเตือนชั่วคราวบริเวณด้านล่างของหน้าจอ
    function toast(message) {
      const el = $("#toast");
      if (!el) {
        console.warn(message);
        return;
      }
      el.textContent = message;
      el.classList.add("show");
      clearTimeout(window.toastTimer);
      window.toastTimer = setTimeout(() => el.classList.remove("show"), 2300);
    }

    // เพิ่มกิจกรรมลงประวัติงานของเจ้าหน้าที่ปัจจุบัน
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
      return canRoleOpenPage(role, element.dataset.page);
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

    // แสดงชื่อและรหัสพนักงานจาก assigned_staff ที่ Backend ส่งกลับมา
    function assignedCleanerLabel(job) {
      if (!job.assignee) return "ยังไม่มีผู้รับผิดชอบ";
      return job.assigneeCode
        ? `${job.assignee} (${job.assigneeCode})`
        : job.assignee;
    }

    const cleaningStatusLabels = {
      assigned: "รับงานแล้ว",
      received: "รับทราบงาน",
      in_progress: "กำลังดำเนินการ",
      completed: "เสร็จสิ้น",
    };
    const nextCleaningStatuses = {
      assigned: "received",
      received: "in_progress",
      in_progress: "completed",
    };

    function nextCleaningStatus(job) {
      const backendStatus = nextCleaningStatuses[job.backendStatus];
      return backendStatus
        ? { backendStatus, label: cleaningStatusLabels[backendStatus] }
        : null;
    }
    const repairStatusLabels = {
      waiting: "รอรับงาน",
      assigned: "รับงานแล้ว",
      received: "รับทราบงาน",
      in_progress: "กำลังดำเนินการ",
      completed: "เสร็จสิ้น",
      cancelled: "ยกเลิก",
    };
    function nextRepairStatus(job) {
      const next = { assigned: "received", received: "in_progress" }[
        job.backendStatus
      ];
      return next ? { backendStatus: next, label: repairStatusLabels[next] } : null;
    }
    function repairLocation(location) {
      return [location?.area, location?.floor && `ชั้น ${location.floor}`]
        .filter(Boolean)
        .join(" · ") || "ไม่ระบุสถานที่";
    }
    async function loadRepairRequests() {
      if (currentRole !== "technician") return;
      try {
        const result = await getRepairRequests();
        const staffId = JSON.parse(localStorage.getItem("buildingCareStaff") || "null")?.id;
        const requests = Array.isArray(result.requests) ? result.requests : [];
        const ids = new Set(requests.map((request) => request.id));
        for (const request of requests) {
          let job = allJobs.find((item) => item.backendId === request.id);
          if (!job) {
            job = { type: "repair", category: "งานซ่อม", reporter: "ผู้ใช้งานอาคาร", timeline: [] };
            allJobs.push(job);
          }
          Object.assign(job, {
            backendId: request.id,
            id: request.request_code,
            title: request.title,
            detail: request.description,
            room: repairLocation(request.location),
            priority: request.priority === "urgent" ? "เร่งด่วน" : "ปกติ",
            backendStatus: request.status,
            status: repairStatusLabels[request.status] || request.status,
            assigneeId: request.assigned_staff_id,
            assignee: request.assigned_staff_id
              ? request.assigned_staff_id === staffId ? activeStaffName() : "ช่างผู้รับผิดชอบ"
              : null,
            time: new Date(request.created_at).toLocaleString("th-TH"),
          });
        }
        allJobs = allJobs.filter((job) =>
          job.type !== "repair" || !job.backendId || ids.has(job.backendId),
        );
        renderJobs();
        renderMetrics();
        renderQueue();
      } catch (error) {
        if (await handleUnauthorizedResponse(error.status)) return;
        console.error("Loading repair requests failed:", error);
        toast(error.message || "ไม่สามารถโหลดรายการงานซ่อมได้");
      }
    }
    function populateCategoryFilter() {
      const select = $("#categoryFilter");
      if (!select) return;
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
      activeRole.value = role;
      localStorage.setItem("buildingCareRole", role);

      const c = roleConfig[role];
      if (!c) return;

      document.documentElement.style.setProperty("--role", c.color);
      document.documentElement.style.setProperty("--role-soft", c.soft);

      const roleSwitcher = $("#roleSwitcher");
      if (roleSwitcher) roleSwitcher.value = role;

      const staffName = $("#staffName");
      if (staffName) staffName.textContent = c.name;

      const staffRoleLabel = $("#staffRoleLabel");
      if (staffRoleLabel) staffRoleLabel.textContent = c.label;

      const avatar = $("#avatar");
      if (avatar) avatar.textContent = c.avatar;

      const eyebrow = $("#eyebrow");
      if (eyebrow) eyebrow.textContent = c.eyebrow;

      const heroEyebrow = $("#heroEyebrow");
      if (heroEyebrow) heroEyebrow.textContent = c.eyebrow;

      const heroTitle = $("#heroTitle");
      if (heroTitle) heroTitle.textContent = c.hero;

      const heroText = $("#heroText");
      if (heroText) heroText.textContent = c.text;

      const queueTitle = $("#queueTitle");
      if (queueTitle) queueTitle.textContent = c.queue;

      const jobsTitle = $("#jobsTitle");
      if (jobsTitle) {
        jobsTitle.textContent = c.jobTitle || "ศูนย์รับงานรวม";
      }

      const jobsSubtitle = $("#jobsSubtitle");
      if (jobsSubtitle) {
        jobsSubtitle.textContent = c.jobSubtitle || "";
      }

      const heroPrimary = $("#heroPrimary");
      if (heroPrimary) heroPrimary.textContent = c.primary;

      $$(".role-demo-btn").forEach((button) => {
        const active = button.dataset.roleSwitch === role;
        button.classList.toggle("active", active);
        button.setAttribute("aria-pressed", String(active));
      });

      const headerAvatar = $("#headerAvatar");
      if (headerAvatar) headerAvatar.textContent = c.avatar;

      const headerName = $("#headerName");
      if (headerName) {
        headerName.textContent = currentUserName[role].split(" ")[0];
      }

      const headerRole = $("#headerRole");
      if (headerRole) headerRole.textContent = c.label;

      const profileAvatar = $("#profileAvatar");
      if (profileAvatar) profileAvatar.textContent = c.avatar;

      const profileName = $("#profileName");
      if (profileName) profileName.textContent = currentUserName[role];

      const profileStaffId = $("#profileStaffId");
      if (profileStaffId) profileStaffId.textContent = c.staffId;

      const profileEmail = $("#profileEmail");
      if (profileEmail) {
        try {
          const signedInStaff = JSON.parse(
            localStorage.getItem("buildingCareStaff") || "null"
          );
          if (signedInStaff?.role === role && signedInStaff?.email) {
            profileEmail.textContent = signedInStaff.email;
          }
        } catch (error) {
          console.warn("Stored staff email is invalid:", error);
        }
      }

      const profileRole = $("#profileRole");
      if (profileRole) profileRole.textContent = c.label;

      const profileDepartment = $("#profileDepartment");
      if (profileDepartment) {
        profileDepartment.textContent =
          role === "technician"
            ? "งานอาคารและซ่อมบำรุง"
            : role === "housekeeper"
            ? "งานดูแลความสะอาด"
            : role === "clerk"
            ? "ธุรการและของหาย"
            : "บริหารระบบ";
      }

      const jobsNavLabel = $("#jobsNavLabel");
      if (jobsNavLabel) {
        jobsNavLabel.textContent =
          role === "housekeeper"
            ? "รับงานแม่บ้าน"
            : role === "technician"
            ? "รับงานช่าง"
            : "ศูนย์งานทั้งหมด";
      }

      const queueExplainerTitle = $("#queueExplainerTitle");

      if (queueExplainerTitle) {
        queueExplainerTitle.textContent =
          role === "admin"
            ? "คิวรวมของแม่บ้านและช่าง"
            : `คิวนี้เป็นคิวร่วมของ${c.label}`;
      }

      $$(".nav-item").forEach((n) =>
        n.classList.toggle("role-hidden", !roleAllows(n, role))
      );

      const activePage = $(".page.active")?.id.replace("page-", "");
      if (!canRoleOpenPage(role, activePage)) {
        navigate(STAFF_ROLE_PAGES[role][0].id);
      }

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
      renderMobileQuickActions();
      renderDashboardQuickActions();
    }

    // -------------------------------------------------------------------------
    // 5) Navigation และ Dashboard summary
    // -------------------------------------------------------------------------

    // เปลี่ยนหน้าภายใน Staff Dashboard โดยตรวจสิทธิ์ของ role ก่อนเสมอ
    function navigate(page) {
      if (!canRoleOpenPage(currentRole, page)) {
        toast("บทบาทนี้ไม่มีสิทธิ์เข้าถึงเมนูดังกล่าว");
        return;
      }
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
        "clerk-center": "ศูนย์รับงาน",
        jobs: roleConfig[currentRole].jobTitle,
        "my-history": "ประวัติงานของฉัน",
        lost: "ศูนย์ของหายและรับฝาก",
        "staff-overview": "ภาพรวมงาน Staff",
        staff: "จัดการบัญชีเจ้าหน้าที่",
        history: "ของหายและรับฝาก",
        qr: "QR ประจำห้อง",
      };
      const pageTitle = $("#pageTitle");
      if (pageTitle) pageTitle.textContent = titles[page] || "Staff Operations";
      if (page === "clerk-center") renderClerkCenter();
      if (page === "my-history") renderMyHistory();
      if (page === "staff-overview") renderStaffOverview();
      if (page === "history") renderHistory();
      closeSidebar();
      window.scrollTo({
        top: 0,
        behavior: matchMedia("(prefers-reduced-motion: reduce)").matches
          ? "auto"
          : "smooth",
      });
    }
    function renderMetrics() {
      if (!$("#metricGrid")) return;
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
      if (!$("#priorityQueue")) return;
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
      if (!$("#activityList")) return;
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

    // -------------------------------------------------------------------------
    // 6) ระบบคิวงานแม่บ้านและช่าง
    // -------------------------------------------------------------------------

    // ตรวจว่างานตรงกับ tab และตัวกรองที่ผู้ใช้เลือกหรือไม่
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
      if (!$("#jobList")) return;
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
              const photo = j.completionPhotoUrl
                ? `<div class="job-photo has-image"><img src="${escapeHtml(j.completionPhotoUrl)}" alt="รูปหลังดำเนินการ ${escapeHtml(j.title)}" /></div>`
                : `<div class="job-photo"><svg class="icon"><use href="${icon}"/></svg></div>`;
              return `<article class="job-card ${
                isMine ? "owned" : ""
              }" tabindex="0" data-job-card="${
                j.id
              }">${photo}<div><div class="job-meta"><span class="badge ${
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
                escapeHtml(assignedCleanerLabel(j))
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
        async () => {
          const acceptedJob = await acceptJob(id);
          if (!acceptedJob) return;
          appendJobTimeline(job, "รับงาน", `รับผิดชอบโดย ${activeStaffName()}`);
          if (selectedJobId === id) {
            $("#jobTimeline").innerHTML = jobTimeline(job);
          }
          showSuccess(
            `เลขงาน: ${acceptedJob.id}\nสถานะ: ${acceptedJob.status}\nผู้รับผิดชอบ: ${assignedCleanerLabel(acceptedJob)}`,
            job.type === "repair" ? "รับงานซ่อมสำเร็จ" : "รับงานทำความสะอาดสำเร็จ",
          );
        },
        "ยืนยันรับงาน"
      );
    }
    async function acceptJob(id) {
      const job = allJobs.find((j) => j.id === id);
      if (!job || job.assignee) {
        toast("งานนี้มีเจ้าหน้าที่คนอื่นรับแล้ว");
        renderJobs();
        return false;
      }

      // งานจริงต้องให้ Backend ยืนยันก่อนเปลี่ยน UI
      if (job.backendId && ["cleaning", "repair"].includes(job.type)) {
        try {
          const acceptedTask = job.type === "repair"
            ? await acceptRepairRequest(job.backendId)
            : await acceptCleaningTask(job.backendId);
          job.assignee =
            acceptedTask.assigned_staff?.full_name || activeStaffName();
          job.assigneeCode = acceptedTask.assigned_staff?.staff_code || "";
          job.assigneeId = acceptedTask.assigned_staff?.id || "";
          job.backendStatus = acceptedTask.status;
          job.status = "รับงานแล้ว";
        } catch (error) {
          if (await handleUnauthorizedResponse(error.status)) return false;
          console.error("Accepting staff task failed:", error);
          toast(
            error.status === 409
              ? "งานนี้มีเจ้าหน้าที่คนอื่นรับไปแล้ว"
              : error.message || "ไม่สามารถรับงานได้",
          );
          if (job.type === "repair") await loadRepairRequests();
          else await loadStaffNotifications();
          return false;
        }
      } else {
        job.assignee = activeStaffName();
        job.status = "รับงานแล้ว";
      }
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
      renderJobs();
      renderMetrics();
      renderQueue();
      if (selectedJobId === id) {
        $("#jobDetailAssignee").textContent = assignedCleanerLabel(job);
        $("#jobTimeline").innerHTML = jobTimeline(job);
        renderJobQuickActions(job);
      }
      addNotification(
        currentRole,
        `รับงาน ${id} สำเร็จ`,
        `คุณเป็นผู้รับผิดชอบงาน “${job.title}” แล้ว`
      );
      return job;
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
        `ลบงาน ${id} หรือไม่?`,
        () => {
          const [record] = allJobs.splice(index, 1);
          storeDeletedRecord("jobs", record, "allJobs", record.title);
          toast(`ลบงาน ${id} แล้ว`);
          renderJobs();
          renderMetrics();
          renderQueue();
          renderStaffOverview();
          renderHistory();
        }
      );
    }

    // -------------------------------------------------------------------------
    // 7) ระบบอนุมัติ Lost & Found และคำขอรับของคืน
    // -------------------------------------------------------------------------

    // สร้างตัวเลือกสถานะของคำขอคืนของตามสถานะปัจจุบัน
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
      if (tab === "claims") return "";
      const decision = approvalGroup(item.status);
      if (decision === "rejected") return "";
      if (decision === "approved") {
        return `<div class="decision-strip completed"><button class="approve-btn" type="button" data-lost-action="complete" data-tab="${tab}" data-item-id="${item.id}">สำเร็จแล้ว</button></div>`;
      }
      return `<div class="decision-strip"><button class="approve-btn" type="button" data-lost-action="approve" data-tab="${tab}" data-item-id="${item.id}">อนุมัติ</button><button class="reject-btn" type="button" data-lost-action="reject" data-tab="${tab}" data-item-id="${item.id}">ไม่อนุมัติ</button></div>`;
    }
    function approvalGroup(status = "") {
      if (status.includes("ไม่อนุมัติ") || status.includes("ไม่ผ่าน")) return "rejected";
      if (status.includes("รออนุมัติ")) return "pending";
      return "approved";
    }
    function lostDecisionGroup(tab, item) {
      if (tab !== "claims") return approvalGroup(item.status);
      if (item.backendStatus === "rejected" || item.status.includes("ไม่ผ่าน")) return "rejected";
      if (
        ["approved", "completed"].includes(item.backendStatus) ||
        ["ผ่านการตรวจสอบ", "นัดหมายแล้ว", "คืนของแล้ว"].includes(item.status)
      ) return "approved";
      return "pending";
    }
    function completeLostFoundItem(tab, id) {
      const item = lostSets[tab]?.find((record) => record.id === id);
      if (!item) return;
      requestConfirmation(
        "ยืนยันปิดรายการ",
        `${id} · ยืนยันว่าดำเนินการ “${item.title}” สำเร็จแล้วใช่หรือไม่?`,
        () => {
          const completedIds = completedLostFoundIds();
          completedIds.add(item.id);
          localStorage.setItem(
            completedLostFoundStorageKey,
            JSON.stringify([...completedIds]),
          );
          lostSets[tab] = lostSets[tab].filter((record) => record.id !== id);
          recordWorkHistory({
            itemId: id,
            title: item.title,
            category: tab === "inventory" ? "ของที่รับฝาก" : "ประกาศตามหา",
            action: "ปิดรายการ",
            status: "สำเร็จแล้ว",
            detail: `ปิดรายการโดย ${activeStaffName()}`,
          });
          renderLost();
          renderMetrics();
          showSuccess(`${id} · ${item.title} ถูกปิดเป็นรายการสำเร็จแล้ว`, "ปิดรายการแล้ว");
        },
        "สำเร็จแล้ว",
      );
    }
    function ownershipStatusLabel(status = "") {
      return ({
        pending: "รอตรวจสอบ",
        additional_info_required: "ขอข้อมูลเพิ่มเติม",
        approved: "ผ่านการตรวจสอบ",
        rejected: "ไม่ผ่านการตรวจสอบ",
        completed: "คืนของแล้ว",
      })[status] || status || "ไม่ทราบสถานะ";
    }
    function foundItemReturnStatus(returnStatus = "", claimStatus = "") {
      if (returnStatus === "returned" || claimStatus === "completed") {
        return "ส่งคืนเจ้าของแล้ว";
      }
      if (returnStatus === "ready_for_pickup") return "พร้อมให้เจ้าของรับคืน";
      if (claimStatus === "additional_info_required") return "รอข้อมูลจากผู้ขอ";
      if (claimStatus === "rejected") return "คำขอไม่ผ่านการตรวจสอบ";
      if (claimStatus === "approved") return "ยืนยันเจ้าของแล้ว · รอส่งมอบ";
      if (returnStatus === "pending" || claimStatus === "pending") {
        return "รอตรวจสอบคำขอ";
      }
      return "ไม่ทราบสถานะการคืน";
    }
    function returnStatusForFoundItem(item) {
      const claim = lostSets.claims.find(
        (candidate) => candidate.foundItemBackendId === item.backendId,
      );
      if (claim) {
        return claim.returnStatus || foundItemReturnStatus(
          claim.returnStatusCode,
          claim.backendStatus,
        );
      }
      if (item.status === "คืนของแล้ว") return "ส่งคืนเจ้าของแล้ว";
      return "ยังไม่มีคำขอรับคืน";
    }
    function approvalTypeLabel(tab) {
      return tab === "inventory" ? "ของที่รับฝาก" : tab === "lostposts" ? "ประกาศตามหา" : "คำขอรับของ";
    }
    function findLostItem(tab, id) {
      return lostSets[tab]?.find((item) => item.id === id);
    }
    function pendingApprovalRequests() {
      return ["inventory", "lostposts"].flatMap((tab) =>
        lostSets[tab]
          .filter((item) => approvalGroup(item.status) === "pending")
          .map((item) => ({ approvalId: item.id, tab, title: item.title, text: item.place }))
      );
    }
    function activeClaimNotifications() {
      return lostSets.claims
        .filter((item) => item.status !== "คืนของแล้ว")
        .map((item) => ({ ...item, unread: !readClaimNotifications.has(item.id) }));
    }
    function matchesClerkCenterSearch(...values) {
      const keyword = ($("#clerkCenterSearch")?.value || "").trim().toLocaleLowerCase("th");
      if (!keyword) return true;
      return values
        .filter((value) => value !== null && value !== undefined)
        .some((value) => String(value).toLocaleLowerCase("th").includes(keyword));
    }
    function setClerkCenterView(view) {
      const availableViews = ["approvals", "lost-announcements", "claims"];
      currentClerkCenterView = availableViews.includes(view) ? view : "approvals";
      $$("#clerkCenterTabs [data-clerk-center-view]").forEach((tab) => tab.classList.toggle("active", tab.dataset.clerkCenterView === currentClerkCenterView));
      $$('[data-clerk-center-panel]').forEach((panel) => panel.classList.toggle("active", panel.dataset.clerkCenterPanel === currentClerkCenterView));
    }
    function renderClerkCenter() {
      const pendingList = $("#pendingApprovalList"),
        lostAnnouncementList = $("#pendingLostAnnouncementList"),
        claimList = $("#activeClaimList");
      if (!pendingList || !lostAnnouncementList || !claimList) return;
      const pendingRequests = pendingApprovalRequests();
      const filteredRequests = pendingRequests.filter((item) => {
        const record = findLostItem(item.tab, item.approvalId);
        return matchesClerkCenterSearch(
          item.approvalId,
          item.title,
          item.text,
          record?.category,
          record?.description,
          record?.custody,
          record?.status,
        );
      });
      const approvals = filteredRequests.filter((item) => item.tab === "inventory");
      const lostAnnouncements = filteredRequests.filter((item) => item.tab === "lostposts");
      const claims = lostSets.claims.filter((item) =>
        item.status !== "คืนของแล้ว" && matchesClerkCenterSearch(
          item.id,
          item.title,
          item.place,
          item.requester,
          item.contact,
          item.status,
          item.returnStatus,
          item.evidence,
          item.custody,
        )
      );
      ["#pendingApprovalCount", "#pendingApprovalTabCount"].forEach((id) => $(id).textContent = approvals.length);
      ["#pendingLostAnnouncementCount", "#pendingLostAnnouncementTabCount"].forEach((id) => ($(id).textContent = lostAnnouncements.length));
      ["#activeClaimCount", "#activeClaimTabCount"].forEach((id) => $(id).textContent = claims.length);
      pendingList.innerHTML = approvals.length ? approvals.map((item) => {
        const record = findLostItem(item.tab, item.approvalId);
        return `<article class="clerk-request-card"><div class="clerk-request-top"><div><span class="approval-type ${item.tab}">${approvalTypeLabel(item.tab)}</span><h4>${item.approvalId} · ${escapeHtml(item.title)}</h4></div><span class="badge wait">รออนุมัติ</span></div><p>${escapeHtml(item.text)}</p><div class="clerk-request-meta"><span>${escapeHtml(record?.custody || "รอการตรวจสอบ")}</span></div><div class="clerk-request-actions"><button class="small-btn" type="button" data-center-action="detail" data-tab="${item.tab}" data-item-id="${item.approvalId}">ดูรายละเอียด</button><button class="approve-btn" type="button" data-center-action="approve" data-tab="${item.tab}" data-item-id="${item.approvalId}">อนุมัติ</button><button class="reject-btn" type="button" data-center-action="reject" data-tab="${item.tab}" data-item-id="${item.approvalId}">ไม่อนุมัติ</button></div></article>`;
      }).join("") : '<div class="empty">ไม่มีคำขอที่รออนุมัติ</div>';
      lostAnnouncementList.innerHTML = lostAnnouncements.length ? lostAnnouncements.map((item) => {
        const record = findLostItem(item.tab, item.approvalId);
        return `<article class="clerk-request-card"><div class="clerk-request-top"><div><span class="approval-type lostposts">ประกาศตามหา</span><h4>${item.approvalId} · ${escapeHtml(item.title)}</h4></div><span class="badge wait">รออนุมัติเผยแพร่</span></div><p>${escapeHtml(item.text)}</p><div class="clerk-request-meta"><span>${escapeHtml(record?.custody || "รอการตรวจสอบ")}</span></div><div class="clerk-request-actions"><button class="small-btn" type="button" data-center-action="detail" data-tab="lostposts" data-item-id="${item.approvalId}">ดูรายละเอียด</button><button class="approve-btn" type="button" data-center-action="approve" data-tab="lostposts" data-item-id="${item.approvalId}">อนุมัติเผยแพร่</button><button class="reject-btn" type="button" data-center-action="reject" data-tab="lostposts" data-item-id="${item.approvalId}">ไม่อนุมัติ</button></div></article>`;
        }).join("") : '<div class="empty">ไม่มีคำขอที่รออนุมัติ</div>';
      claimList.innerHTML = claims.length ? claims.map((item) =>
        `<article class="clerk-request-card"><div class="clerk-request-top"><div><span class="approval-type claims">คำขอแสดงความเป็นเจ้าของ</span><h4>${item.id} · ${escapeHtml(item.title)}</h4></div><span class="badge ${badgeClass(item.status)}">${escapeHtml(item.status)}</span></div><p>${escapeHtml(item.place)}</p><div class="clerk-request-meta"><span>ผู้ขอ: ${escapeHtml(item.requester || "ไม่ระบุชื่อ")}</span><span>ส่งคำขอ: ${escapeHtml(item.requestDate || "ไม่ระบุเวลา")}</span><span>สถานะการคืน: ${escapeHtml(item.returnStatus || "ไม่ทราบสถานะ")}</span><span>${escapeHtml(item.custody || "คำขอใหม่")}</span></div><div class="clerk-request-actions"><button class="small-btn" type="button" data-center-action="claim-detail" data-item-id="${item.id}">ดูรายละเอียดคำขอ</button></div></article>`
            ).join("") : '<div class="empty">ไม่มีคำขอที่รออนุมัติ</div>';
      setClerkCenterView(currentClerkCenterView);
    }
    function renderLost() {
      if (!$("#lostGrid")) return;
      const entriesForView = (view) => {
        if (["approved", "rejected"].includes(view)) {
          return ["inventory", "lostposts", "claims"].flatMap((tab) =>
            lostSets[tab]
              .filter((item) => lostDecisionGroup(tab, item) === view)
              .map((item) => ({ item, tab }))
          );
        }
        const data = view === "claims"
          ? lostSets.claims.filter((item) => item.status !== "คืนของแล้ว")
          : lostSets[view].filter((item) => approvalGroup(item.status) === "approved");
        return data.map((item) => ({ item, tab: view }));
      };
      const historySearch = currentRole === "admin"
        ? ($("#historySearch")?.value || "").trim().toLowerCase()
        : "";
      const matchesSearch = ({ item }) =>
        !historySearch ||
        `${item.id} ${item.title} ${item.place} ${item.status} ${item.custody}`
          .toLowerCase()
          .includes(historySearch);
      const visibleEntries = entriesForView(currentLostTab).filter(matchesSearch);
      if (currentRole === "admin") {
        const allEntries = ["inventory", "lostposts", "claims"].flatMap((tab) =>
          lostSets[tab].map((item) => ({ item, tab }))
        ).filter(matchesSearch);
        const summary = $("#adminLostSummary");
        if (summary) {
          const counts = { pending: 0, approved: 0, rejected: 0, claims: 0 };
          allEntries.forEach(({ item, tab }) => {
            counts[lostDecisionGroup(tab, item)] += 1;
            if (tab === "claims" && item.status !== "คืนของแล้ว") counts.claims += 1;
          });
          summary.innerHTML = [
            [counts.pending, "รอตรวจสอบ", "รายการที่ยังไม่มีผลอนุมัติ"],
            [counts.approved, "อนุมัติแล้ว", "รวมของรับฝาก ประกาศ และคำขอ"],
            [counts.rejected, "ไม่อนุมัติ", "รายการที่ไม่ผ่านการตรวจสอบ"],
            [counts.claims, "คำขอรับของ", "คำขอที่ยังไม่คืนของ"],
          ].map(([value, label, hint], index) =>
            `<article class="metric ${index === 2 ? "warn" : ""}"><span>${label}</span><strong>${value}</strong><small>${hint}</small></article>`
          ).join("");
        }
        $$("#lostTabs [data-lost-count]").forEach((count) => {
          count.textContent = entriesForView(count.dataset.lostCount)
            .filter(matchesSearch).length;
        });
      }
      renderClerkCenter();
      const emptyLabel = currentLostTab === "approved"
        ? "ยังไม่มีรายการที่อนุมัติแล้ว"
        : currentLostTab === "rejected"
        ? "ยังไม่มีรายการที่ไม่อนุมัติ"
        : "ไม่มีรายการในหมวดนี้";
      $("#lostGrid").innerHTML = visibleEntries.length
        ? visibleEntries
            .map(({ item: i, tab }) => {
              const note = i.decisionReason
                ? `<div class="approval-note"><strong>${
                    i.status.includes("ไม่อนุมัติ")
                      ? "เหตุผลที่ไม่อนุมัติ"
                      : "บันทึกการอนุมัติ"
                  }:</strong> ${i.decisionReason}</div>`
                : "";
              const adminDelete =
                currentRole === "admin"
                  ? `<div class="admin-delete-row"><button class="small-btn delete" type="button" data-lost-action="delete" data-tab="${tab}" data-item-id="${i.id}">ลบรายการ</button></div>`
                  : "";
              const controls =
                tab === "claims"
                  ? `<div class="claim-controls"><button type="button" class="primary" data-lost-action="claim-detail" data-tab="claims" data-item-id="${i.id}">ดูรายละเอียดคำขอ</button></div>`
                  : `${note}<div class="lost-foot"><span class="custody">${i.custody}</span>${tab === "inventory" ? `<span class="badge progress">สถานะการคืน: ${escapeHtml(returnStatusForFoundItem(i))}</span>` : ""}<button class="small-btn" type="button" data-lost-action="detail" data-tab="${tab}" data-item-id="${i.id}">ดูรายละเอียด</button></div>`;
              const claimHint = tab === "claims" ? '<div class="approval-note"><strong>รับคำขออัตโนมัติ:</strong> ธุรการไม่ต้องกดอนุมัติ สามารถตรวจรายละเอียด นัดหมาย และยืนยันการส่งคืนได้</div>' : "";
              const sourceBadge = ["approved", "rejected"].includes(currentLostTab)
                ? `<span class="badge neutral lost-source-badge">${approvalTypeLabel(tab)}</span>`
                : "";
              const image = i.imageUrl
                ? `<div class="lost-image has-image"><img src="${escapeHtml(i.imageUrl)}" alt="รูป ${escapeHtml(i.title)}" loading="lazy" /></div>`
                : '<div class="lost-image"><svg class="icon"><use href="#i-box"/></svg></div>';
              return `<article class="lost-card" tabindex="0" data-lost-card="${
                i.id
              }">${image}<div class="lost-content">${sourceBadge}<span class="badge ${badgeClass(
                i.status
              )}">${i.status}</span><h3>${i.id} · ${i.title}</h3><p>${
                i.place
              }</p>${claimHint}${controls}${tab === "claims" ? "" : decisionButtons(tab, i)}${adminDelete}</div></article>`;
            })
            .join("")
        : `<div class="empty" style="grid-column:1/-1">${emptyLabel}</div>`;
    }
    function approveLostItem(tab, id) {
      const item = lostSets[tab].find((x) => x.id === id);
      if (!item) return;
      const isLostAnnouncement = tab === "lostposts";
      requestConfirmation(
        isLostAnnouncement ? "ยืนยันเผยแพร่ประกาศของหาย" : "ยืนยันการอนุมัติ",
        isLostAnnouncement
          ? `${item.id} · ${item.title} จะถูกเปลี่ยนเป็นประกาศที่อนุมัติเผยแพร่`
          : `ตรวจสอบข้อมูลของ ${item.id} · ${item.title} แล้วใช่หรือไม่?`,
        () => confirmApproveLostItem(tab, id),
        isLostAnnouncement ? "อนุมัติเผยแพร่" : "อนุมัติ"
      );
    }
    async function confirmApproveLostItem(tab, id) {
      const item = lostSets[tab].find((x) => x.id === id);
      if (!item) return;
      if (item.backendId) {
        try {
          if (tab === "inventory") {
            await approveFoundItem(item.backendId);
          } else if (tab === "lostposts") {
            await approveLostItemAnnouncement(item.backendId);
          }
        } catch (error) {
          if (await handleUnauthorizedResponse(error.status)) return;

          console.error(`Approve ${tab} item failed:`, error);
          toast(error.message || "ไม่สามารถอนุมัติรายการได้");
          return;
        }
      }
      const nextStatus = tab === "inventory" ? "อนุมัติรับฝาก" : "อนุมัติเผยแพร่";
      item.status = nextStatus;
      item.decisionReason = tab === "inventory" ? "ตรวจสอบสิ่งของจริงและข้อมูลรับฝากแล้ว" : "ตรวจสอบข้อมูลประกาศ รูป และข้อมูลส่วนตัวแล้ว";
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
      renderLost();
      renderClerkCenter();
      renderMetrics();
      renderQueue();
      renderNotifications();
      currentLostTab = tab;
      $$("#lostTabs .tab").forEach((tabButton) => {
        const active = tabButton.dataset.tab === tab;
        tabButton.classList.toggle("active", active);
        if (tabButton.hasAttribute("aria-selected")) {
          tabButton.setAttribute("aria-selected", String(active));
        }
      });
      navigate(currentRole === "admin" ? "history" : "lost");
      renderLost();
      if (tab === "lostposts") {
        showSuccess(
          `${id} · ${item.title} ถูกเปลี่ยนสถานะเป็น “${nextStatus}” แล้ว`,
          "เผยแพร่ประกาศของหายแล้ว"
        );
      } else {
        showSuccess(
          `${id} · ${item.title} ถูกเปลี่ยนสถานะเป็น “${nextStatus}” แล้ว`,
          "อนุมัติรายการของที่พบแล้ว"
        );
      }
    }
    function openReject(tab, id) {
      const item = lostSets[tab].find((x) => x.id === id);
      if (!item) return;
      $("#rejectSource").value = tab;
      $("#rejectItemId").value = id;
      $("#rejectReason").value = "";
      const reasonDetail = $("#rejectReasonDetail");
      if (reasonDetail) reasonDetail.value = "";
      const rejectNote = $("#rejectNote");
      if (rejectNote) rejectNote.value = "";
      $("#rejectModalTitle").textContent = `ไม่อนุมัติ ${id} · ${item.title}`;
      openModal("rejectModal");
    }
    async function confirmRejectLostItem(tab, id, decisionReason) {
      const item = lostSets[tab]?.find((record) => record.id === id);
      if (!item) return;
      if (["inventory", "lostposts"].includes(tab) && item.backendId) {
        try {
          if (tab === "lostposts") {
            await rejectLostItemAnnouncement(item.backendId, decisionReason);
          } else {
            await rejectFoundItem(item.backendId, decisionReason);
          }
        } catch (error) {
          if (await handleUnauthorizedResponse(error.status)) return;

          console.error(`Reject ${tab} item failed:`, error);
          toast(
            error.message ||
              (tab === "lostposts"
                ? "ไม่สามารถปฏิเสธประกาศของหายได้"
                : "ไม่สามารถปฏิเสธรายการได้"),
          );
          return;
        }
      }
      item.status =
        tab === "inventory" ? "ไม่อนุมัติรับฝาก" : "ไม่อนุมัติเผยแพร่";
      item.decisionReason = decisionReason;
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
      renderLost();
      renderClerkCenter();
      renderMetrics();
      renderQueue();
      showRejectionResult(item, tab);
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
          () => confirmClaimStatus(item, nextStatus)
        );
        return;
      }
      confirmClaimStatus(item, nextStatus);
    }
    function confirmClaimStatus(item, nextStatus) {
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
      renderClerkCenter();
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
        `ลบรายการ ${id} หรือไม่?`,
        () => {
          const [record] = lostSets[tab].splice(index, 1);
          storeDeletedRecord("lost", record, tab, record.title);
          toast(`ลบรายการ ${id} แล้ว`);
          renderLost();
          renderMetrics();
          renderQueue();
          renderHistory();
        }
      );
    }

    // -------------------------------------------------------------------------
    // 8) ระบบประวัติงานและภาพรวมประสิทธิภาพ Staff
    // -------------------------------------------------------------------------

    // เติมประเภทงานในตัวกรองประวัติจากข้อมูลจริงของ role ปัจจุบัน
    function populateMyHistoryTypes() {
      if (!$("#myHistoryType")) return;
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
      if (!$("#myHistoryList")) return;
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
      if (!$("#staffOverviewTable")) return;
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
      const jobTypeForRole = { "แม่บ้าน": "cleaning", "ช่าง": "repair" };
      const unassignedCount = allJobs.filter(
        (job) =>
          !job.assignee &&
          !isTerminalStatus(job.status) &&
          !String(job.status).includes("ยกเลิก") &&
          (role === "all" || job.type === jobTypeForRole[role])
      ).length;
      summary.innerHTML = [
        [unassignedCount, "งานที่ยังไม่มีผู้รับผิดชอบ", "คิวงานปัจจุบันตาม Role"],
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
      ]
        .map(
          (v, i) =>
            `<article class="metric ${i === 3 ? "warn" : ""}"><span>${
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
    function showStaffOverview(name, trigger) {
      selectedOverviewStaff = name;
      renderStaffOverviewDetail();
      openModal("staffOverviewModal", trigger);
    }
    function renderStaffOverviewDetail() {
      if (!$("#staffOverviewDetail")) return;
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
      if ($("#historyLostSection")) renderLost();
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
        `ลบ ${item.itemId} ถาวรหรือไม่? การกระทำนี้ย้อนกลับไม่ได้`,
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

    // -------------------------------------------------------------------------
    // 9) ระบบ Notification
    // -------------------------------------------------------------------------

    // โหลด notification ของบัญชีที่ login จาก Backend แล้วแปลงให้ตรงกับ UI
    async function loadStaffNotifications() {
      try {
        const notifications = await getStaffNotifications();
        const mockNotifications = notificationSets[currentRole].filter(
          (notification) => notification.isMock,
        );
        notificationSets[currentRole] = [...notifications.map((notification) => ({
          id: notification.id,
          requestId: notification.request_id,
          title: notification.title,
          text: notification.message,
          time: new Date(notification.created_at).toLocaleString("th-TH", {
            dateStyle: "short",
            timeStyle: "short",
          }),
          unread: !notification.is_read,
          backend: true,
        })), ...mockNotifications];
        renderNotifications();
      } catch (error) {
        if (await handleUnauthorizedResponse(error.status)) return;
        console.error("Loading staff notifications failed:", error);
        toast(error.message || "ไม่สามารถโหลดการแจ้งเตือนได้");
      }
    }

    // อัปเดต badge ทั้ง Desktop/Mobile และซ่อนเมื่อไม่มีรายการที่ยังไม่อ่าน
    function updateUnreadNotificationCount(unreadCount) {
      const visibleCount = unreadCount > 99 ? "99+" : String(unreadCount);
      [$("#notificationCount"), $("#mobileNotificationCount")].forEach(
        (badge) => {
          if (!badge) return;
          badge.textContent = visibleCount;
          badge.hidden = unreadCount === 0;
          badge.style.display = unreadCount > 0 ? "grid" : "none";
          badge.setAttribute("aria-label", `${unreadCount} การแจ้งเตือนที่ยังไม่ได้อ่าน`);
        },
      );

      $("#notificationButton")?.setAttribute(
        "aria-label",
        unreadCount > 0
          ? `เปิดการแจ้งเตือน มี ${unreadCount} รายการที่ยังไม่ได้อ่าน`
          : "เปิดการแจ้งเตือน",
      );
      $("#mobileNotification")?.setAttribute(
        "aria-label",
        unreadCount > 0
          ? `เปิดการแจ้งเตือน มี ${unreadCount} รายการที่ยังไม่ได้อ่าน`
          : "เปิดการแจ้งเตือน",
      );

      const markAllButton = $("#markAllRead");
      if (markAllButton) markAllButton.disabled = unreadCount === 0;
    }

    // รวม notification ของ role ปัจจุบันและคำร้องใหม่ก่อน render
    function renderNotifications() {
      const list = notificationSets[currentRole] || [];
      const approvals = currentRole === "clerk" ? pendingApprovalRequests() : [];
      const claims = currentRole === "clerk" ? activeClaimNotifications() : [];
      const unread = list.filter((n) => n.unread).length + approvals.length + claims.filter((n) => n.unread).length;
      $("#notificationTitle").textContent = currentRole === "clerk" ? "การแจ้งเตือนของธุรการ" : `การแจ้งเตือนของ${roleConfig[currentRole].label}`;
      updateUnreadNotificationCount(unread);
      if (!list.length && !approvals.length && !claims.length) {
        $("#notificationList").innerHTML =
          '<div class="notification-empty">ไม่มีการแจ้งเตือน</div>';
        return;
      }
      let clerkHtml = "";
      if (approvals.length) clerkHtml += `<div class="notification-group-label">คำร้องใหม่ · ${approvals.length}</div>` + approvals.map((item) => `<button type="button" class="notification-item unread" data-clerk-notification-target="approval" data-item-id="${item.approvalId}"><div class="notification-symbol"><svg class="icon"><use href="#i-box"/></svg></div><div><span class="approval-type ${item.tab}">${approvalTypeLabel(item.tab)}</span><strong>${item.approvalId} · ${escapeHtml(item.title)}</strong><p>${escapeHtml(item.text)}</p><small>กดเพื่อไปที่ศูนย์รับงาน</small></div></button>`).join("");
      if (claims.length) clerkHtml += `<div class="notification-group-label">คำขอรับของ · ${claims.length}</div>` + claims.map((item) => `<button type="button" class="notification-item ${item.unread ? "unread" : ""}" data-clerk-notification-target="claim" data-item-id="${item.id}"><div class="notification-symbol"><svg class="icon"><use href="#i-user"/></svg></div><div><span class="approval-type claims">คำขอรับของ</span><strong>${item.id} · ${escapeHtml(item.title)}</strong><p>${escapeHtml(item.place)}</p><small>กดเพื่อไปที่ศูนย์รับงาน</small></div></button>`).join("");
      const groups = [
        ["วันนี้", list.filter((_, index) => index < 2)],
        ["เมื่อวาน", list.filter((_, index) => index === 2)],
        ["ก่อนหน้านี้", list.filter((_, index) => index > 2)],
      ];
      $("#notificationList").innerHTML = clerkHtml + groups
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
        backend: false,
      });
      if (role === currentRole) renderNotifications();
    }
    async function markNotificationsRead() {
      const notifications = notificationSets[currentRole];
      const backendUnread = notifications.filter(
        (notification) => notification.unread && notification.backend,
      );
      try {
        await Promise.all(
          backendUnread.map((notification) =>
            markStaffNotificationRead(notification.id),
          ),
        );
        notifications.forEach((notification) => {
          notification.unread = false;
        });
      } catch (error) {
        if (await handleUnauthorizedResponse(error.status)) return;
        console.error("Marking notifications as read failed:", error);
        toast(error.message || "ไม่สามารถอัปเดตการแจ้งเตือนได้");
        return;
      }
      if (currentRole === "clerk") lostSets.claims.filter((item) => item.status !== "คืนของแล้ว").forEach((item) => readClaimNotifications.add(item.id));
      renderNotifications();
      toast("ทำเครื่องหมายว่าอ่านทั้งหมดแล้ว");
    }

    // -------------------------------------------------------------------------
    // 10) ระบบจัดการบัญชี Staff
    // -------------------------------------------------------------------------

    // แสดงตารางบัญชีและ action ที่ผู้ดูแลระบบสามารถดำเนินการได้
    function renderStaff() {
      if (!$("#staffTable")) return;
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
        `ลบบัญชี ${staff.name} หรือไม่?`,
        () => {
          const [record] = staffData.splice(i, 1);
          storeDeletedRecord("staff", record, "staffData", record.name);
          renderStaff();
          renderHistory();
          toast("ลบบัญชี Staff แล้ว");
        }
      );
    }

    // -------------------------------------------------------------------------
    // 11) ระบบ QR ประจำห้อง
    // -------------------------------------------------------------------------

    // ใช้ token ของสถานที่จริงเพื่อให้ฟอร์ม guest ระบุสถานที่จาก QR ได้
    function makeRoomUrl() {
      const base = $("#baseUrl").value.trim() ||
        new URL(`${import.meta.env.BASE_URL}user`, window.location.origin).toString();
      return buildGuestQrUrl(base, $("#qrToken").value, $("#service").value);
    }
    function generateQr(addToList = false) {
      if (!$("#qrCode")) return false;
      let url;
      try {
        url = makeRoomUrl();
      } catch (error) {
        toast(error.message || "ลิงก์ QR ใช้ไม่ได้");
        return false;
      }
      if (!window.QRCode) {
        toast("ยังโหลดตัวสร้าง QR ไม่สำเร็จ กรุณาลองใหม่เมื่อเชื่อมต่ออินเทอร์เน็ต");
        return false;
      }
      $("#qrRoomName").textContent = $("#room").value.trim();
      $("#qrUrlText").textContent = url;
      const box = $("#qrCode");
      box.innerHTML = "";
      new QRCode(box, {
        text: url,
        width: 168,
        height: 168,
        colorDark: "#17202b",
        colorLight: "#ffffff",
        correctLevel: QRCode.CorrectLevel.M,
      });
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
      return true;
    }

    // -------------------------------------------------------------------------
    // 12) Modal, Sidebar และกล่องยืนยันส่วนกลาง
    // -------------------------------------------------------------------------

    // เปิด modal และจดจำ element ต้นทางเพื่อคืน focus เมื่อปิด
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
      const menuToggle = $("#menuToggle");
      menuToggle.setAttribute("aria-expanded", "false");
      menuToggle.setAttribute("aria-label", "เปิดเมนู");
      menuToggle.querySelector("use").setAttribute("href", "#i-menu");
    }
    function updateMenuToggle(menuVisible) {
      const menuToggle = $("#menuToggle");
      menuToggle.setAttribute("aria-expanded", String(menuVisible));
      menuToggle.setAttribute("aria-label", menuVisible ? "ปิดเมนู" : "เปิดเมนู");
      menuToggle.querySelector("use").setAttribute(
        "href",
        menuVisible ? "#i-close" : "#i-menu"
      );
    }
    function toggleSidebar() {
      if (window.matchMedia("(min-width: 1024px)").matches) return;
      const open = !$("#sidebar").classList.contains("open");
      $("#sidebar").classList.toggle("open", open);
      $("#sidebarBackdrop").classList.toggle("open", open);
      updateMenuToggle(open);
    }
    function requestConfirmation(title, text, action, label = "ยืนยัน") {
      pendingConfirmAction = action;
      $("#confirmModalTitle").textContent = title;
      $("#confirmModalText").textContent = text;
      $("#confirmActionButton").textContent = label;
      openModal("confirmModal");
    }
    function showSuccess(message, title = "บันทึกสำเร็จ") {
      const successModal = $("#successModal");
      successModal?.classList.remove("rejection-result");
      successModal
        ?.querySelector(".success-check use")
        ?.setAttribute("href", "#i-check");
      const successTitle = $("#successModalTitle");
      if (successTitle) successTitle.textContent = title;
      $("#successModalText").textContent = message;
      openModal("successModal");
    }
    function showRejectionResult(item, tab) {
      const successModal = $("#successModal");
      successModal?.classList.add("rejection-result");
      successModal
        ?.querySelector(".success-check use")
        ?.setAttribute("href", "#i-close");
      $("#successModalTitle").textContent =
        tab === "lostposts"
          ? "ปฏิเสธประกาศของหายแล้ว"
          : "ไม่อนุมัติรายการรับฝากแล้ว";
      $("#successModalText").textContent =
        `${item.id} · ${item.title}\n` +
        `สถานะ: ${item.status}\n` +
        `เหตุผล: ${item.decisionReason}`;
      openModal("successModal");
    }

    // -------------------------------------------------------------------------
    // 13) รายละเอียดงาน การมอบหมาย และการเปลี่ยนสถานะงาน
    // -------------------------------------------------------------------------

    // แสดงรายชื่อเจ้าหน้าที่ที่เหมาะกับประเภทงานใน modal มอบหมาย
    function renderAssignStaff() {
      if (!$("#assignStaffList")) return;
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
        ["ผู้รับผิดชอบ", assignedCleanerLabel(job)],
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
        const backendNext = job.backendId
          ? job.type === "repair" ? nextRepairStatus(job) : nextCleaningStatus(job)
          : null;
        if (job.backendId && ["cleaning", "repair"].includes(job.type)) {
          if (backendNext) {
            buttons.push([
              "status",
              `เปลี่ยนเป็น ${backendNext.label}`,
              "primary-action",
            ]);
          }
          if (job.type === "repair" && job.backendStatus === "in_progress")
            buttons.push(["complete", "เสร็จสิ้น", ""]);
          if (job.type === "cleaning")
            buttons.push(["note", "เพิ่มหมายเหตุ", ""], ["upload", "เพิ่มรูป", ""]);
        } else {
          buttons.push(
            ["start", "เริ่มดำเนินการ", "primary-action"],
            ["status", "อัปเดตสถานะ", ""],
            ["note", "เพิ่มหมายเหตุ", ""],
            ["upload", "เพิ่มรูป", ""],
            ["complete", "เสร็จสิ้น", ""]
          );
        }
        if (isMine && currentRole !== "admin" && !job.backendId)
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
    async function openJobDetail(id, trigger = document.activeElement) {
      const job = allJobs.find((item) => item.id === id);
      if (!job) return;
      if (job.type === "repair" && job.backendId) {
        try {
          const detail = await getRepairRequestDetail(job.backendId);
          job.detail = detail.description;
          job.room = repairLocation(detail.location);
          job.reporterContact = detail.reporter_email;
          job.backendStatus = detail.status;
          job.status = repairStatusLabels[detail.status] || detail.status;
          job.requestImageUrl = detail.images?.find((image) => image.image_type === "after")?.url
            || detail.images?.[0]?.url || "";
        } catch (error) {
          if (await handleUnauthorizedResponse(error.status)) return;
          console.error("Loading repair request detail failed:", error);
          toast(error.message || "ไม่สามารถโหลดรายละเอียดงานซ่อมได้");
          return;
        }
      }
      selectedJobId = id;
      $("#jobDetailCode").textContent = `${id} · ${job.category}`;
      $("#jobDetailTitle").textContent = job.title;
      $("#jobDetailDescription").textContent = job.detail;
      $("#jobDetailRoom").textContent = job.room;
      $("#jobDetailReporter").textContent = job.reporter;
      $("#jobDetailContact").textContent =
        job.reporterContact || "ติดต่อผ่านระบบ CS Building Care";
      $("#jobDetailAssignee").textContent =
        assignedCleanerLabel(job);
      $("#jobDetailBadges").innerHTML = `<span class="badge ${
        job.priority === "เร่งด่วน" ? "danger" : "wait"
      }">${job.priority}</span><span class="badge ${badgeClass(job.status)}">${
        job.status
      }</span><span class="badge neutral">${job.time}</span>`;
      $("#jobDetailIcon use").setAttribute(
        "href",
        job.type === "repair" ? "#i-tools" : "#i-broom"
      );
      const detailImage = $("#jobDetailImage");
      const detailIcon = $("#jobDetailIcon");
      if (detailImage && (job.completionPhotoUrl || job.requestImageUrl)) {
        detailImage.src = job.completionPhotoUrl || job.requestImageUrl;
        detailImage.alt = `รูปหลังดำเนินการ ${job.title}`;
        detailImage.hidden = false;
        if (detailIcon) detailIcon.hidden = true;
      } else {
        if (detailImage) {
          detailImage.hidden = true;
          detailImage.removeAttribute("src");
        }
        if (detailIcon) detailIcon.hidden = false;
      }
      $("#jobTimeline").innerHTML = jobTimeline(job);
      $("#jobDetailNotes").textContent = job.note || "ยังไม่มีหมายเหตุ";
      renderJobQuickActions(job);
      openModal("jobDetailModal", trigger);

      // งานจริงที่รับแล้วสามารถโหลด timeline จาก Backend ได้
      if (job.backendId && job.assignee) {
        try {
          const result = job.type === "repair"
            ? await getRepairRequestHistory(job.backendId)
            : await getCleaningTaskHistory(job.backendId);
          const actionLabels = {
            created: "สร้างคำร้อง",
            assigned: "มอบหมายงาน",
            accepted: "รับงาน",
            status_changed: "อัปเดตสถานะ",
            returned: "คืนงาน",
            reassigned: "เปลี่ยนผู้รับผิดชอบ",
            completed: "ปิดงาน",
            cancelled: "ยกเลิกงาน",
            completion_note_added: "หมายเหตุปิดงาน",
          };
          const history = Array.isArray(result.history) ? result.history : [];
          job.timeline = history.map((entry) => {
            const statusChange = `${
              (job.type === "repair" ? repairStatusLabels : cleaningStatusLabels)[entry.old_status] ||
              entry.old_status ||
              "เริ่มต้น"
            } → ${
              (job.type === "repair" ? repairStatusLabels : cleaningStatusLabels)[entry.new_status] ||
              entry.new_status ||
              "ไม่ระบุ"
            }`;
            return {
              title: actionLabels[entry.action] || "อัปเดตงาน",
              detail:
                entry.action === "completion_note_added"
                  ? entry.note || "ไม่ได้ระบุหมายเหตุ"
                  : statusChange,
              time: new Date(entry.created_at).toLocaleString("th-TH"),
            };
          });

          const latestCompletionNote = history
            .filter(
              (entry) =>
                entry.action === "completion_note_added" && entry.note,
            )
            .at(-1);
          if (latestCompletionNote) {
            job.note = latestCompletionNote.note;
            $("#jobDetailNotes").textContent = latestCompletionNote.note;
          }
          $("#jobTimeline").innerHTML = jobTimeline(job);
        } catch (error) {
          if (await handleUnauthorizedResponse(error.status)) return;
          console.error("Loading staff task history failed:", error);
        }
      }
    }

    // Notification มี request_id และข้อความรูปแบบ "request_code: title"
    // จึงสร้างรายการงานจากข้อมูลจริงที่ Backend ส่งมาแล้วเปิด modal รายละเอียด
    function openCleaningRequestFromNotification(
      notification,
      trigger = document.activeElement,
    ) {
      if (!notification.requestId) return false;

      const separatorIndex = notification.text.indexOf(":");
      const requestCode =
        separatorIndex > 0
          ? notification.text.slice(0, separatorIndex).trim()
          : `CLEAN-${notification.requestId.slice(0, 8).toUpperCase()}`;
      const requestTitle =
        separatorIndex > 0
          ? notification.text.slice(separatorIndex + 1).trim()
          : notification.title;

      let job = allJobs.find(
        (item) =>
          item.backendId === notification.requestId || item.id === requestCode,
      );
      if (!job) {
        job = {
          backendId: notification.requestId,
          id: requestCode,
          type: "cleaning",
          category: "งานทำความสะอาด",
          title: requestTitle || notification.title,
          room: "ดูสถานที่จากรายละเอียดคำร้อง",
          reporter: "ผู้ใช้งานอาคาร",
          reporterContact: "ติดต่อผ่านระบบ CS Building Care",
          time: notification.time,
          status: "รอรับงาน",
          priority: "ปกติ",
          detail: notification.text,
          assignee: null,
          timeline: [],
        };
        allJobs.unshift(job);
      }

      navigate("jobs");
      renderJobs();
      renderMetrics();
      openJobDetail(job.id, trigger);
      return true;
    }
    function openStatusUpdate(id, trigger = document.activeElement) {
      const job = allJobs.find((item) => item.id === id);
      if (!job) return;
      const backendNext = job.backendId
        ? job.type === "repair" ? nextRepairStatus(job) : nextCleaningStatus(job)
        : null;
      if (job.backendId && !backendNext) {
        toast(job.type === "repair" && job.backendStatus === "in_progress"
          ? "งานกำลังดำเนินการแล้ว กรุณาใช้ปุ่มเสร็จสิ้นเพื่อปิดงาน"
          : "ไม่มีสถานะถัดไปที่เปลี่ยนได้");
        return;
      }
      const options = backendNext
        ? [backendNext.label]
        :
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
      resetCompletionPreview();
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
        const backendNext = job.backendId
          ? job.type === "repair" ? nextRepairStatus(job) : nextCleaningStatus(job)
          : null;
        const nextStatus = backendNext?.label || "กำลังดำเนินการ";
        requestConfirmation(
          "ยืนยันเริ่มดำเนินการ",
          `เปลี่ยนสถานะงาน ${job.id} เป็น “${nextStatus}” หรือไม่?`,
          () => applyJobStatus(job, nextStatus, "อัปเดตจากหน้ารายละเอียดงาน")
        );
        return;
      }
    }
    async function applyJobStatus(job, next, note) {
      const previous = job.status;
      const isBackendCleaning = job.type === "cleaning" && job.backendId;
      const isBackendRepair = job.type === "repair" && job.backendId;
      if (isBackendCleaning || isBackendRepair) {
        const transition = isBackendRepair ? nextRepairStatus(job) : nextCleaningStatus(job);
        if ((!transition || transition.label !== next) &&
            !(isBackendRepair && next === "เสร็จสิ้น" && job.backendStatus === "in_progress")) {
          toast("ไม่สามารถเปลี่ยนไปยังสถานะนี้ได้ กรุณาโหลดข้อมูลใหม่");
          return false;
        }
        try {
          const updatedTask = isBackendRepair
            ? next === "เสร็จสิ้น"
              ? await completeRepairRequest(job.backendId)
              : await updateRepairRequestStatus(job.backendId, transition.backendStatus)
            : await updateCleaningTaskStatus(job.backendId, transition.backendStatus);
          job.backendStatus = updatedTask.status;
          job.assignee =
            updatedTask.assigned_staff?.full_name || job.assignee;
          job.assigneeCode =
            updatedTask.assigned_staff?.staff_code || job.assigneeCode;
          job.assigneeId = updatedTask.assigned_staff?.id || job.assigneeId;
          next = (isBackendRepair ? repairStatusLabels : cleaningStatusLabels)[updatedTask.status] || next;
        } catch (error) {
          if (await handleUnauthorizedResponse(error.status)) return false;
          console.error("Updating staff task status failed:", error);
          toast(
            error.status === 409
              ? "ลำดับสถานะไม่ถูกต้อง กรุณาโหลดข้อมูลใหม่"
              : error.status === 403
                ? "เฉพาะผู้รับผิดชอบงานเท่านั้นที่อัปเดตสถานะได้"
                : error.message || "ไม่สามารถอัปเดตสถานะงานได้",
          );
          return false;
        }
      }
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
      if ((isBackendCleaning || isBackendRepair) && job.backendStatus !== "completed") {
        showSuccess(
          `เลขงาน: ${job.id}\nสถานะล่าสุด: ${job.status}\nผู้รับผิดชอบ: ${assignedCleanerLabel(job)}`,
          "อัปเดตสถานะงานสำเร็จ",
        );
      }
      return true;
    }

    // -------------------------------------------------------------------------
    // 14) Modal รายละเอียด Lost & Found และการนัดรับของ
    // -------------------------------------------------------------------------

    // โหลดรายละเอียดล่าสุดจาก Backend แล้วแสดงใน modal กลาง
    async function openLostDetail(tab, id, trigger = document.activeElement) {
      const item = lostSets[tab]?.find((record) => record.id === id);
      if (!item) return;
      if (item.backendId) {
        try {
          const detail =
            tab === "lostposts"
              ? await getLostItemDetail(item.backendId)
              : await getFoundItemDetail(item.backendId);
          item.category = detail.item_category;
          item.description = detail.description || "ไม่มีรายละเอียดเพิ่มเติม";
          item.place = detail.location_detail || "ไม่ระบุสถานที่พบ";
          item.custody = detail.custody_location || "ไม่ระบุจุดรับฝาก";
          item.reporterEmail = detail.reporter_email;
          item.eventDatetime = detail.event_datetime;
        } catch (error) {
          if (await handleUnauthorizedResponse(error.status)) return;
          console.error("Loading found item detail failed:", error);
          toast(error.message || "ไม่สามารถโหลดรายละเอียดได้");
          return;
        }
      }
      const isLostAnnouncement = tab === "lostposts";
      selectedJobId = "";
      $("#jobDetailCode").textContent = `${id} · ${isLostAnnouncement ? "ประกาศของหาย" : "ของที่พบ"}`;
      $("#jobDetailTitle").textContent = item.title;
      $("#jobDetailDescription").textContent = item.description || item.place;
      const roomLabel = $("#jobDetailRoomLabel");
      if (roomLabel)
        roomLabel.textContent = isLostAnnouncement ? "สถานที่คาดว่าหาย" : "สถานที่พบ";
      $("#jobDetailRoom").textContent = item.place;
      const reporterLabel = $("#jobDetailReporterLabel");
      if (reporterLabel)
        reporterLabel.textContent = isLostAnnouncement ? "ผู้แจ้งประกาศ" : "ผู้แจ้ง";
      $("#jobDetailReporter").textContent =
        item.reporter || (isLostAnnouncement ? "ผู้แจ้งของหาย" : "ผู้แจ้งรายการ");
      const contactLabel = $("#jobDetailContactLabel");
      if (contactLabel) contactLabel.textContent = "ช่องทางติดต่อ";
      $("#jobDetailContact").textContent =
        item.reporterEmail || "ติดต่อผ่านระบบ CS Building Care";
      const assigneeLabel = $("#jobDetailAssigneeLabel");
      if (assigneeLabel) assigneeLabel.textContent = "ผู้ตรวจสอบ";
      $("#jobDetailAssignee").textContent = item.assignee || "ธุรการส่วนกลาง";
      const returnStatusGroup = $("#jobDetailReturnStatusGroup");
      if (returnStatusGroup) returnStatusGroup.hidden = isLostAnnouncement;
      const returnStatus = returnStatusForFoundItem(item);
      if (!isLostAnnouncement && $("#jobDetailReturnStatus")) {
        $("#jobDetailReturnStatus").textContent = returnStatus;
      }
      $("#jobDetailBadges").innerHTML = `<span class="badge ${badgeClass(
        item.status
      )}">${item.status}</span>`;
      const detailImage = $("#jobDetailImage");
      const detailIcon = $("#jobDetailIcon");
      if (item.imageUrl && detailImage) {
        detailImage.src = item.imageUrl;
        detailImage.alt = `รูป ${item.title}`;
        detailImage.hidden = false;
        if (detailIcon) detailIcon.hidden = true;
        detailImage.onerror = () => {
          detailImage.hidden = true;
          if (detailIcon) detailIcon.hidden = false;
        };
      } else {
        if (detailImage) {
          detailImage.hidden = true;
          detailImage.removeAttribute("src");
          detailImage.onerror = null;
        }
        if (detailIcon) detailIcon.hidden = false;
      }
      detailIcon?.querySelector("use")?.setAttribute(
        "href",
        isLostAnnouncement ? "#i-search" : "#i-box",
      );
      const detailTimeline = isLostAnnouncement
        ? [
            ["ส่งประกาศ", item.custody || "บันทึกในระบบแล้ว"],
            ["ตรวจสอบข้อมูล", item.status],
            ["เผยแพร่ต่อผู้ใช้งาน", approvalGroup(item.status) === "approved" ? "เผยแพร่แล้ว" : "ยังไม่เผยแพร่",],
          ]
        : [
            ["สร้างรายการ", "บันทึกในระบบแล้ว"],
            ["ตรวจสอบข้อมูล", item.status],
            ["สถานะการคืนของ", returnStatus],
          ];
      $("#jobTimeline").innerHTML = detailTimeline.map((step) =>
          `<div class="timeline-item"><span class="timeline-dot"></span><div><strong>${step[0]}</strong><small>${step[1]}</small></div></div>`
        ).join("");
      $("#jobDetailNotes").textContent = item.decisionReason || "ยังไม่มีหมายเหตุ";
      const approved = approvalGroup(item.status) === "approved";
      const ownershipClaim = lostSets.claims.find(
        (claim) => claim.foundItemBackendId === item.backendId,
      );
      if (!approved) {
        $("#jobQuickActions").innerHTML =
          `<button type="button" class="quick-action primary-action" data-lost-detail-action="approve" data-tab="${tab}" data-item-id="${id}">${isLostAnnouncement ? "อนุมัติเผยแพร่" : "ตรวจสอบและอนุมัติ"}</button><button type="button" class="quick-action" data-lost-detail-action="reject" data-tab="${tab}" data-item-id="${id}">ไม่อนุมัติ</button>`;
      } else if (!isLostAnnouncement && ownershipClaim?.backendStatus === "completed") {
        $("#jobQuickActions").innerHTML =
          '<button type="button" class="quick-action primary-action" disabled>ส่งคืนเจ้าของแล้ว</button>';
      } else if (
        !isLostAnnouncement &&
        (ownershipClaim?.backendStatus === "approved" || ownershipClaim?.status === "นัดหมายแล้ว")
      ) {
        $("#jobQuickActions").innerHTML =
          `<button type="button" class="quick-action primary-action" data-lost-detail-action="return" data-tab="${tab}" data-item-id="${id}">ยืนยันส่งคืนแล้ว</button>`;
      } else {
        $("#jobQuickActions").innerHTML = "";
      }
      openModal("jobDetailModal", trigger);
    }

    function confirmFoundItemReturn(tab, id) {
      const item = lostSets[tab]?.find((record) => record.id === id);
      const claim = lostSets.claims.find(
        (record) => record.foundItemBackendId === item?.backendId,
      );
      if (!item || !claim) {
        toast("ยังไม่พบคำขอรับคืนสำหรับรายการนี้");
        return;
      }
      requestConfirmation(
        "ยืนยันการส่งคืนของ",
        `${id} · ยืนยันว่าได้ส่ง ${item.title} คืนให้ ${claim.requester || "เจ้าของ"} แล้วใช่หรือไม่?`,
        async () => {
          try {
            const previousReturnStatus = returnStatusForFoundItem(item);
            const result = await updateOwnershipReturnStatus(
              claim.backendId,
              "returned",
            );
            claim.backendStatus = result.status;
            claim.returnStatusCode = result.return_status;
            claim.status = ownershipStatusLabel(result.status);
            claim.returnStatus = foundItemReturnStatus(
              result.return_status,
              result.status,
            );
            claim.custody = `ส่งคืนโดย ${activeStaffName()} · ${nowThai()}`;
            item.status = "คืนของแล้ว";
            item.returnStatus = claim.returnStatus;
            item.decisionReason = `สถานะการคืน: ${previousReturnStatus} → ${claim.returnStatus}`;
          addAudit(
            "lost",
            "ยืนยันการส่งคืนของ",
            id,
            item.title,
            `${item.decisionReason} · ${claim.custody}`,
          );
          recordWorkHistory({
            itemId: id,
            title: item.title,
            category: "ของที่รับฝาก",
            action: "ยืนยันการส่งคืนของ",
            status: "คืนของแล้ว",
            detail: `${item.decisionReason} · ${claim.custody}`,
          });
          renderLost();
          renderClerkCenter();
          renderMetrics();
          renderNotifications();
            showSuccess(
              `${id} · ${item.title} เปลี่ยนสถานะจาก “${previousReturnStatus}” เป็น “${claim.returnStatus}” แล้ว`,
              "ส่งคืนเจ้าของสำเร็จ",
            );
          } catch (error) {
            if (await handleUnauthorizedResponse(error.status)) return;
            console.error("Updating return status failed:", error);
            toast(error.message || "ไม่สามารถอัปเดตสถานะการคืนของได้");
          }
        },
        "ยืนยันส่งคืนแล้ว",
      );
    }

    function openClaimDetail(id, trigger = document.activeElement) {
      const item = lostSets.claims.find((record) => record.id === id);
      if (!item) return;
      $("#claimDetailCode").textContent = `${id} · ${item.status}`;
      $("#claimDetailTitle").textContent = item.title;
      $("#claimRequester").textContent = item.requester || "ไม่ระบุชื่อผู้ขอ";
      $("#claimContact").textContent = item.contact || "ไม่ระบุช่องทางติดต่อ";
      $("#claimDate").textContent = item.requestDate || "ไม่ระบุเวลาส่งคำขอ";
      const pickupDateText = item.pickupDate
        ? new Date(`${item.pickupDate}T00:00:00`).toLocaleDateString("th-TH", {
            dateStyle: "long",
          })
        : "ยังไม่มีนัดหมาย";
      $("#claimPickupDate").textContent = pickupDateText;
      $("#claimPickupTime").textContent = item.pickupTime || "–";
      $("#claimPickupLocation").textContent =
        item.pickupLocation || "ยังไม่ระบุจุดรับของ";
      $("#claimPickupNote").textContent =
        item.pickupNote || "ไม่มีหมายเหตุ";
      $("#claimReturnStatus").textContent =
        item.returnStatus || foundItemReturnStatus(
          item.returnStatusCode,
          item.backendStatus,
        );
      $("#claimEvidence").textContent =
        item.evidence || item.place || "ยังไม่มีรายละเอียดหลักฐาน";
      $("#claimSecret").textContent =
        item.secret || "ยังไม่มีข้อมูลลับสำหรับตรวจสอบ";
      $("#claimTimeline").innerHTML = [
        ["ส่งคำขอ", $("#claimDate").textContent],
        ["ตรวจสอบล่าสุด", item.status],
        ["ผู้รับผิดชอบ", item.assignee || "ธุรการส่วนกลาง"],
      ].map((step) =>
        `<div class="timeline-item"><span class="timeline-dot"></span><div><strong>${step[0]}</strong><small>${step[1]}</small></div></div>`
        ).join("");
      const claimActions = [
        ["more", "ขอข้อมูลเพิ่มเติม", ""],
        ["verify", "ยืนยันความเป็นเจ้าของ", "primary-action"],
      ];
      if (item.backendStatus === "approved" || item.status === "นัดหมายแล้ว") {
        claimActions.push([
          "appointment",
          item.status === "นัดหมายแล้ว" ? "แก้ไขนัดหมายรับของ" : "นัดหมายรับของ",
          "",
        ]);
        claimActions.push([
          "returned",
          "ยืนยันส่งคืนแล้ว",
          "primary-action",
        ]);
      }
      $("#claimActions").innerHTML = claimActions.map((action) =>
        `<button type="button" class="quick-action ${action[2]}" data-claim-action="${action[0]}" data-claim-id="${id}">${action[1]}</button>`
      ).join("");
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
        verify: ["ยืนยันความเป็นเจ้าของ", "ผ่านการตรวจสอบ"],
        returned: ["ยืนยันการส่งคืนของ", "คืนของแล้ว"],
      };
      const actionConfig = map[action];
      if (!actionConfig) return;
      const [title, status] = actionConfig;
      closeModal("claimDetailModal", false);
      const confirmationText =
        action === "verify"
          ? `${id} · ${item.requester || "ผู้ยื่นคำขอ"} ให้หลักฐานตรงกับรายการ ${item.title} แล้วใช่หรือไม่?`
          : action === "returned"
            ? `${id} · ยืนยันว่าได้ส่ง ${item.title} คืนให้ ${item.requester || "ผู้ยื่นคำขอ"} แล้วใช่หรือไม่?`
          : `ยืนยันการดำเนินการกับคำขอ ${id} หรือไม่?`;
      const additionalInfoMessage = action === "more"
        ? window.prompt("ระบุข้อมูลที่ต้องการให้ผู้ยื่นคำขอส่งเพิ่มเติม")
        : null;
      if (action === "more" && !additionalInfoMessage?.trim()) return;
      requestConfirmation(title, confirmationText, async () => {
        try {
          const result = action === "returned"
            ? await updateOwnershipReturnStatus(item.backendId, "returned")
            : action === "verify"
              ? await approveOwnershipRequest(item.backendId)
              : await requestOwnershipAdditionalInfo(
                  item.backendId,
                  additionalInfoMessage.trim(),
                );
          item.status = result.status === "approved"
            ? "ผ่านการตรวจสอบ"
            : result.status === "additional_info_required"
              ? "ขอข้อมูลเพิ่มเติม"
              : status;
          item.backendStatus = result.status;
          item.returnStatusCode = result.return_status;
          item.returnStatus = foundItemReturnStatus(
            result.return_status,
            result.status,
          );
          if (action === "returned") {
            item.custody = `ส่งคืนโดย ${activeStaffName()} · ${nowThai()}`;
          }
          item.assignee = activeStaffName();
          addAudit("lost", title, id, item.title, `เปลี่ยนสถานะเป็น ${status}`);
          recordWorkHistory({
            itemId: id,
            title: item.title,
            category: "คำขอรับของ",
            action: title,
            status,
            detail: `ดำเนินการโดย ${activeStaffName()}`,
          });
          renderLost();
          renderNotifications();
          showSuccess(
            action === "verify"
              ? `${id} · ยืนยันความเป็นเจ้าของสำหรับ ${item.requester || "ผู้ยื่นคำขอ"} แล้ว สถานะเปลี่ยนเป็น “${status}”`
              : action === "returned"
                ? `${id} · บันทึกว่าส่ง ${item.title} คืนเจ้าของแล้ว`
                : `อัปเดตคำขอ ${id} เป็น “${status}” แล้ว`,
            action === "verify"
              ? "ยืนยันความเป็นเจ้าของแล้ว"
              : action === "returned"
                ? "บันทึกการส่งคืนแล้ว"
                : "อัปเดตคำขอแล้ว"
          );
        } catch (error) {
          if (await handleUnauthorizedResponse(error.status)) return;
          console.error("Updating ownership request failed:", error);
          toast(error.message || "ไม่สามารถอัปเดตคำขอรับของได้");
        }
      });
    }
    function openAppointment(id, trigger = document.activeElement) {
      const item = lostSets.claims.find((record) => record.id === id);
      if (!item) return;
      if (item.backendStatus !== "approved" && item.status !== "นัดหมายแล้ว") {
        toast("กรุณายืนยันความเป็นเจ้าของก่อนสร้างนัดหมายรับของ");
        return;
      }
      $("#appointmentItemId").value = id;
      $("#appointmentTitle").textContent = `นัดหมายรับของ · ${id}`;
      $("#appointmentDate").min = todayISO();
      $("#appointmentDate").value = todayISO();
      $("#appointmentTime").value = "10:00";
      $("#appointmentNote").value = "";
      openModal("appointmentModal", trigger);
    }

    // -------------------------------------------------------------------------
    // 15) Responsive navigation และ Quick actions
    // -------------------------------------------------------------------------

    // สร้าง action ทางลัดให้เหมาะกับ role และขนาดหน้าจอ
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
              ["add-staff", "เพิ่ม Staff"],
              ["qr", "สร้าง QR"],
            ];
      if (!$("#mobileQuickActions")) return;
      $("#mobileQuickActions").innerHTML = actions.map((item) =>
        `<button type="button" class="quick-action" data-quick-action="${item[0]}">${item[1]}</button>`
        ).join("");
    }
    function renderDashboardQuickActions() {
      if (!$("#dashboardQuickActions")) return;
      if (currentRole === "admin") return;
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
              "คำขอรับของคืน",
              "ฝากของ",
              "ของหาย",
              "นัดหมายรับของ",
              "ยืนยันคืนของแล้ว",
            ]
          : [];
      $("#dashboardQuickActions").innerHTML = actions.map((label, index) =>
          `<button type="button" class="quick-action ${index === 0 && currentRole !== "clerk" ? "primary-action" : ""
          }" data-dashboard-action="${index}">${label}</button>`
        ).join("");
    }

    // -------------------------------------------------------------------------
    // 17) Event binding: Navigation, Profile และ Dashboard
    // -------------------------------------------------------------------------

    $$(".nav-item").forEach((button) =>
      button.addEventListener("click", () => {
        closeSidebar();
        navigate(button.dataset.page);
      })
    );
    $$("[data-go]").forEach((button) =>
      button.addEventListener("click", () =>
        navigate(currentRole === "clerk" && button.dataset.go === "jobs" ? "clerk-center" : button.dataset.go)
      )
    );
    $$("[data-role-switch]").forEach((button) =>
      button.addEventListener("click", () => {
        localStorage.setItem("buildingCareRole", button.dataset.roleSwitch);
        window.location.reload();
      })
    );
    $("#menuToggle")?.addEventListener("click", toggleSidebar);
    $("#sidebarBackdrop")?.addEventListener("click", closeSidebar);
    function syncNavigationForViewport() {
      $("#sidebar").classList.remove("open");
      $("#sidebarBackdrop").classList.remove("open");
      $(".app").classList.remove("sidebar-collapsed");
      updateMenuToggle(false);
    }
    window.addEventListener("resize", syncNavigationForViewport);
    syncNavigationForViewport();
    $("#dashboardQuickActions")?.addEventListener("click", (event) => {
      const button = event.target.closest("[data-dashboard-action]");
      if (!button) return;
      const index = Number(button.dataset.dashboardAction);
      if (currentRole === "clerk") {
        if (index === 0) {
          navigate("clerk-center");
          setClerkCenterView("approvals");
          renderClerkCenter();
        } else if ([1, 4, 5].includes(index)) {
          navigate("clerk-center");
          setClerkCenterView("claims");
          renderClerkCenter();
          const firstClaim = lostSets.claims.find(
            (item) => item.status !== "คืนของแล้ว",
          );
          if (index === 4 && firstClaim) {
            openAppointment(firstClaim.id, button);
          } else if (index === 5 && firstClaim) {
            openClaimDetail(firstClaim.id, button);
          }
        } else {
          currentLostTab = index === 2 ? "inventory" : "lostposts";
          navigate("lost");
          $$("#lostTabs .tab").forEach((tab) =>
            tab.classList.toggle("active", tab.dataset.tab === currentLostTab)
          );
          renderLost();
          if (index === 2) openFoundForm(button);
        }
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
          localStorage.removeItem("buildingCareAccessToken");
          localStorage.removeItem("buildingCareStaff");

          sessionStorage.clear();

          router.push("/staff-login");
        },
        "ออกจากระบบ"
      );
    }
    $("#logoutBtn")?.addEventListener("click", confirmLogout);
    $("#profileLogout")?.addEventListener("click", confirmLogout);
    $("#profileButton")?.addEventListener("click", (event) =>
      openModal("profileModal", event.currentTarget)
    );
    $("#mobileProfile")?.addEventListener("click", (event) =>
      openModal("profileModal", event.currentTarget)
    );
    $("#changePassword")?.addEventListener("click", () =>
      toast("ส่งลิงก์เปลี่ยนรหัสผ่านไปยังอีเมลเจ้าหน้าที่แล้ว")
    );
    $("#notificationSettings")?.addEventListener("click", () =>
      toast("บันทึกการตั้งค่าการแจ้งเตือนแล้ว")
    );
    $$("[data-mobile-page]").forEach((button) =>
      button.addEventListener("click", () =>
        navigate(
          currentRole === "clerk" && button.dataset.mobilePage === "jobs"
            ? "clerk-center"
            : button.dataset.mobilePage
        )
      )
    );
    $("#mobileQuickAction")?.addEventListener("click", (event) =>
      openModal("quickActionModal", event.currentTarget)
    );
    $("#mobileQuickActions")?.addEventListener("click", (event) => {
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
        navigate(currentRole === "admin" ? "history" : "lost");
        currentLostTab = "inventory";
        renderLost();
        openFoundForm(button);
      } else if (action === "claims" || action === "appointments") {
        navigate(currentRole === "admin" ? "history" : "lost");
        currentLostTab = "claims";
        renderLost();
        if (action === "appointments" && lostSets.claims[0])
          openAppointment(lostSets.claims[0].id, button);
      } else if (action === "add-staff") openModal("staffModal", button);
      else if (action === "qr") {
        navigate("qr");
        openModal("qrFormModal", button);
      }
    });
    $("#myHistoryFrom")?.addEventListener("change", renderMyHistory);
    $("#myHistoryTo")?.addEventListener("change", renderMyHistory);
    $("#myHistoryType")?.addEventListener("change", renderMyHistory);
    $("#myHistorySearch")?.addEventListener("input", renderMyHistory);
    $("#resetMyHistoryFilters")?.addEventListener("click", () => {
      $("#myHistoryFrom").value = "";
      $("#myHistoryTo").value = "";
      $("#myHistoryType").value = "all";
      $("#myHistorySearch").value = "";
      renderMyHistory();
    });
    $("#overviewRoleFilter")?.addEventListener("change", renderStaffOverview);
    $("#overviewFrom")?.addEventListener("change", renderStaffOverview);
    $("#overviewTo")?.addEventListener("change", renderStaffOverview);
    $("#overviewSearch")?.addEventListener("input", renderStaffOverview);
    $("#resetOverviewFilters")?.addEventListener("click", () => {
      $("#overviewRoleFilter").value = "all";
      $("#overviewFrom").value = "";
      $("#overviewTo").value = "";
      $("#overviewSearch").value = "";
      selectedOverviewStaff = "";
      renderStaffOverview();
    });

    // -------------------------------------------------------------------------
    // 18) Event binding: คิวงานและการอัปเดตความคืบหน้า
    // -------------------------------------------------------------------------

    $("#jobSearch")?.addEventListener("input", renderJobs);
    $("#clerkCenterSearch")?.addEventListener("input", renderClerkCenter);
    $("#categoryFilter")?.addEventListener("change", renderJobs);
    $("#jobStatusFilter")?.addEventListener("change", renderJobs);
    $("#boardTabs")?.addEventListener("click", (event) => {
      const button = event.target.closest(".board-tab");
      if (!button) return;
      currentBoardView = button.dataset.view;
      $$("#boardTabs .board-tab").forEach((tab) =>
        tab.classList.toggle("active", tab === button)
      );
      renderJobs();
    });
    $("#jobList")?.addEventListener("click", (event) => {
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
    $("#jobList")?.addEventListener("keydown", (event) => {
      const card = event.target.closest("[data-job-card]");
      if (card && (event.key === "Enter" || event.key === " ")) {
        event.preventDefault();
        openJobDetail(card.dataset.jobCard, card);
      }
    });
    $("#jobQuickActions")?.addEventListener("click", (event) => {
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
      else if (lostAction.dataset.lostDetailAction === "return")
        confirmFoundItemReturn(lostAction.dataset.tab, lostAction.dataset.itemId);
      else {
        currentLostTab = "claims";
        renderLost();
        navigate(currentRole === "admin" ? "history" : "lost");
      }
    });
    $("#assignForm")?.addEventListener("submit", (event) => {
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
    $("#assignSearch")?.addEventListener("input", renderAssignStaff);
    $("#assignRole")?.addEventListener("change", () => {
      $("#assignStaff").value = "";
      renderAssignStaff();
    });
    $("#assignStaffList")?.addEventListener("click", (event) => {
      const button = event.target.closest("[data-assign-staff]");
      if (!button) return;
      $("#assignStaff").value = button.dataset.assignStaff;
      renderAssignStaff();
    });
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

    function resetCompletionPreview() {
      const preview = $("#completionPreview");
      if (!preview) return;
      const image = preview.querySelector("img");
      if (image?.src?.startsWith("blob:")) URL.revokeObjectURL(image.src);
      image?.removeAttribute("src");
      const fileName = preview.querySelector("span");
      if (fileName) fileName.textContent = "";
      preview.classList.remove("visible");
    }

    function previewCompletionFile(file) {
      if (!validImage(file)) {
        toast("รองรับ JPG, PNG หรือ WebP ไม่เกิน 5 MB");
        $("#completeImage").value = "";
        resetCompletionPreview();
        return false;
      }
      const preview = $("#completionPreview");
      if (!preview) return true;
      const image = preview.querySelector("img");
      if (image.src?.startsWith("blob:")) URL.revokeObjectURL(image.src);
      image.src = URL.createObjectURL(file);
      preview.querySelector("span").textContent = `${file.name} · ${(
        file.size / 1048576
      ).toFixed(1)} MB`;
      preview.classList.add("visible");
      return true;
    }
    $("#progressImage")?.addEventListener("change", (event) => {
      if (event.target.files[0]) previewProgressFile(event.target.files[0]);
    });
    $("#removeProgressImage")?.addEventListener("click", () => {
      $("#progressImage").value = "";
      resetUploadPreview();
    });
    $("#completeImage")?.addEventListener("change", (event) => {
      const file = event.target.files[0];
      if (file) previewCompletionFile(file);
      else resetCompletionPreview();
    });
    $("#removeCompletionImage")?.addEventListener("click", () => {
      $("#completeImage").value = "";
      resetCompletionPreview();
    });
    $("#completeNote")?.addEventListener("input", (event) => {
      event.currentTarget.setCustomValidity("");
    });
    ["dragenter", "dragover"].forEach((type) =>
      $("#uploadDropZone")?.addEventListener(type, (event) => {
        event.preventDefault();
        $("#uploadDropZone").classList.add("dragging");
      })
    );
    ["dragleave", "drop"].forEach((type) =>
      $("#uploadDropZone")?.addEventListener(type, (event) => {
        event.preventDefault();
        $("#uploadDropZone").classList.remove("dragging");
      })
    );
    $("#uploadDropZone")?.addEventListener("drop", (event) => {
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
    ["dragenter", "dragover"].forEach((type) =>
      $("#completionDropZone")?.addEventListener(type, (event) => {
        event.preventDefault();
        $("#completionDropZone").classList.add("dragging");
      })
    );
    ["dragleave", "drop"].forEach((type) =>
      $("#completionDropZone")?.addEventListener(type, (event) => {
        event.preventDefault();
        $("#completionDropZone").classList.remove("dragging");
      })
    );
    $("#completionDropZone")?.addEventListener("drop", (event) => {
      const file = event.dataTransfer.files[0];
      if (!previewCompletionFile(file)) return;
      const transfer = new DataTransfer();
      transfer.items.add(file);
      $("#completeImage").files = transfer.files;
    });
    $("#statusUpdateForm")?.addEventListener("submit", async (event) => {
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
      const updated = await applyJobStatus(job, next, note);
      if (updated && !(job.type === "cleaning" && job.backendId)) {
        toast("บันทึกสถานะเรียบร้อย");
      }
    });
    $("#noteForm")?.addEventListener("submit", (event) => {
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
    $("#uploadForm")?.addEventListener("submit", (event) => {
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
    $("#completeForm")?.addEventListener("submit", async (event) => {
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
      const completionNoteInput = $("#completeNote");
      const completionNote = completionNoteInput.value.trim();
      if (!completionNote) {
        completionNoteInput.setCustomValidity("กรุณากรอกหมายเหตุปิดงาน");
        completionNoteInput.reportValidity();
        completionNoteInput.focus();
        return;
      }
      if (completionNote.length > 2000) {
        completionNoteInput.setCustomValidity(
          "หมายเหตุปิดงานต้องไม่เกิน 2,000 ตัวอักษร"
        );
        completionNoteInput.reportValidity();
        completionNoteInput.focus();
        return;
      }
      completionNoteInput.setCustomValidity("");
      const summary = `${$("#completeResult").value.trim()} · ${completionNote}`;
      if (!(job.backendId && job.backendStatus === "completed")) {
        const updated = await applyJobStatus(job, "เสร็จสิ้น", summary);
        if (!updated) return;
      }

      // Backend อนุญาตให้เพิ่ม note และรูปได้หลังเปลี่ยนสถานะเป็น completed แล้ว
      if (job.backendId) {
        try {
          // บันทึกผลทันทีเพื่อไม่สร้างหมายเหตุซ้ำ หากรูปอัปโหลดไม่สำเร็จ
          if (!job.completionNoteId) {
            const noteResult = job.type === "repair"
              ? await addRepairCompletionNote(job.backendId, completionNote)
              : await addCleaningCompletionNote(job.backendId, completionNote);
            job.completionNoteId = noteResult.id;
            job.note = noteResult.note;
          }
          if (job.type === "cleaning" || file) {
            const photoResult = job.type === "repair"
              ? await uploadRepairCompletionPhotos(job.backendId, [file])
              : await uploadCleaningCompletionPhotos(job.backendId, [file]);
            job.completionPhotos = photoResult.photos;
            job.completionPhotoCount = photoResult.image_count;
          }
        } catch (error) {
          if (await handleUnauthorizedResponse(error.status)) return;
          console.error("Saving task completion details failed:", error);
          toast(error.message || "บันทึกรายละเอียดปิดงานไม่สำเร็จ กรุณาลองใหม่");
          return;
        }
      }
      if (job.completionPhotoUrl?.startsWith("blob:")) {
        URL.revokeObjectURL(job.completionPhotoUrl);
        job.completionPhotoUrl = "";
      }
      if (file) {
        job.completionPhotoUrl = URL.createObjectURL(file);
        job.completionPhotoName = file.name;
      }
      appendJobTimeline(job, "ปิดงาน", `เสร็จวันที่ ${$("#completeDate").value}`);
      renderJobs();
      closeModal("completeModal", false);
      showSuccess(`ปิดงาน ${job.id} เรียบร้อย งานถูกย้ายไปประวัติแล้ว`);
    });
    $("#historySearch")?.addEventListener("input", renderHistory);
    $("#myHistoryList")?.addEventListener("click", (event) => {
      const button = event.target.closest("[data-history-detail]");
      if (!button) return;
      const job = allJobs.find(
        (item) => item.id === button.dataset.historyDetail
      );
      if (job) openJobDetail(job.id, button);
      else toast(`แสดงรายละเอียด ${button.dataset.historyDetail} จากประวัติแล้ว`);
    });
    $("#staffOverviewTable")?.addEventListener("click", (event) => {
      const button = event.target.closest("[data-staff-overview]");
      if (button) showStaffOverview(button.dataset.staffOverview, button);
    });
    $("#staffTable")?.addEventListener("click", (event) => {
      const button = event.target.closest("[data-staff-action]");
      if (!button) return;
      const index = Number(button.dataset.staffIndex);
      if (button.dataset.staffAction === "toggle") toggleStaff(index);
      if (button.dataset.staffAction === "remove") removeStaff(index);
      if (button.dataset.staffAction === "edit") openEditStaff(index, button);
      if (button.dataset.staffAction === "detail") {
        navigate("staff-overview");
        showStaffOverview(staffData[index].name, button);
      }
    });
    $("#lostTabs")?.addEventListener("click", (event) => {
      const button = event.target.closest(".tab");
      if (!button) return;
      $$("#lostTabs .tab").forEach((tab) => {
        const active = tab === button;
        tab.classList.toggle("active", active);
        if (tab.hasAttribute("aria-selected")) {
          tab.setAttribute("aria-selected", String(active));
        }
      });
      currentLostTab = button.dataset.tab;
      renderLost();
    });
    $("#clerkCenterTabs")?.addEventListener("click", (event) => {
      const tab = event.target.closest("[data-clerk-center-view]");
      if (tab) setClerkCenterView(tab.dataset.clerkCenterView);
    });
    ["#pendingApprovalList", "#pendingLostAnnouncementList"].forEach(
      (selector) =>
        $(selector)?.addEventListener("click", (event) => {
          const button = event.target.closest("[data-center-action]");
          if (!button) return;
          const { centerAction: action, tab, itemId: id } = button.dataset;
          if (action === "approve") approveLostItem(tab, id);
          else if (action === "reject") openReject(tab, id);
          else openLostDetail(tab, id, button);
        })
    );
    $("#activeClaimList")?.addEventListener("click", (event) => {
      const button = event.target.closest("[data-center-action]");
      if (button?.dataset.centerAction === "claim-detail")
        openClaimDetail(button.dataset.itemId, button);
    });
    // ฟังคลิกที่ container เพื่อรองรับปุ่มในการ์ดที่ถูกสร้างใหม่หลัง render โดยไม่ต้องผูก event ซ้ำ
    $("#lostGrid")?.addEventListener("click", (event) => {
      const button = event.target.closest("[data-lost-action]");
      if (!button) return;
      event.stopPropagation();
      const action = button.dataset.lostAction,
        tab = button.dataset.tab || "claims",
        id = button.dataset.itemId;
      if (action === "approve") approveLostItem(tab, id);
      if (action === "reject") openReject(tab, id);
      if (action === "complete") completeLostFoundItem(tab, id);
      if (action === "delete") deleteLostRecord(tab, id);
      if (action === "appointment") openAppointment(id, button);
      if (action === "detail") openLostDetail(tab, id, button);
      if (action === "claim-detail") openClaimDetail(id, button);
    });
    // -------------------------------------------------------------------------
    // 19) Event binding: Notification, Staff, Lost & Found, QR และประกาศ
    // -------------------------------------------------------------------------

    // เปิด/ปิด notification panel และอัปเดตค่า accessibility ให้ตรงกัน
    function toggleNotificationPanel(trigger) {
      const panel = $("#notificationPanel"),
        open = !panel.classList.contains("open");
      panel.classList.toggle("open", open);
      $("#notificationButton").setAttribute("aria-expanded", String(open));
      if (open) panel.querySelector("button")?.focus();
    }
    $("#notificationButton")?.addEventListener("click", (event) => {
      event.stopPropagation();
      toggleNotificationPanel(event.currentTarget);
    });
    $("#mobileNotification")?.addEventListener("click", (event) => {
      event.stopPropagation();
      toggleNotificationPanel(event.currentTarget);
    });
    $("#notificationPanel")?.addEventListener("click", async (event) => {
      event.stopPropagation();
      const clerkTarget = event.target.closest("[data-clerk-notification-target]");
      if (clerkTarget) {
        if (clerkTarget.dataset.clerkNotificationTarget === "claim")
          readClaimNotifications.add(clerkTarget.dataset.itemId);
        currentClerkCenterView = clerkTarget.dataset.clerkNotificationTarget === "claim" ? "claims" : "approvals";
        $("#notificationPanel").classList.remove("open");
        navigate("clerk-center");
        renderClerkCenter();
        return;
      }
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
      if (item.unread && item.backend) {
        try {
          await markStaffNotificationRead(item.id);
          item.unread = false;
        } catch (error) {
          if (await handleUnauthorizedResponse(error.status)) return;
          console.error("Marking notification as read failed:", error);
          toast(error.message || "ไม่สามารถอัปเดตการแจ้งเตือนได้");
          return;
        }
      } else {
        item.unread = false;
      }
      renderNotifications();
      $("#notificationPanel").classList.remove("open");
      if (
        currentRole === "housekeeper" &&
        openCleaningRequestFromNotification(item, itemButton)
      ) {
        return;
      }
      if (currentRole === "technician" && item.requestId) {
        let job = allJobs.find((entry) => entry.backendId === item.requestId);
        if (!job) {
          await loadRepairRequests();
          job = allJobs.find((entry) => entry.backendId === item.requestId);
        }
        if (job) {
          navigate("jobs");
          openJobDetail(job.id, itemButton);
        } else {
          toast("ไม่พบงานซ่อมที่เชื่อมกับการแจ้งเตือนนี้");
        }
        return;
      }
      if (currentRole === "technician" && item.isMock) {
        const mockJob = allJobs.find((job) =>
          job.type === "repair" && item.text.startsWith(`${job.id}:`),
        );
        if (mockJob) {
          navigate("jobs");
          openJobDetail(mockJob.id, itemButton);
          return;
        }
      }
      const match = item.text.match(/(?:CL|RP)-\d+/);
      if (match) openJobDetail(match[0], itemButton);
      else if (currentRole === "clerk") navigate("clerk-center");
      else toast(item.title);
    });
    document.addEventListener("click", () => {
      $("#notificationPanel")?.classList.remove("open");
      $("#notificationButton")?.setAttribute("aria-expanded", "false");
    });
    $("#markAllRead")?.addEventListener("click", markNotificationsRead);
    $("#openStaffModal")?.addEventListener("click", (event) =>
      openModal("staffModal", event.currentTarget)
    );
    function openFoundForm(trigger) {
      const form = $("#foundForm");
      form?.reset();
      if ($("#custodyPoint")) $("#custodyPoint").value = "ประชาสัมพันธ์ชั้น 1";
      if ($("#foundDate")) $("#foundDate").value = todayISO();
      if ($("#foundTime")) $("#foundTime").value = currentTimeHM();
      openModal("foundModal", trigger);
    }
    $("#addFoundBtn")?.addEventListener("click", (event) =>
      openFoundForm(event.currentTarget)
    );
    $("#openAnnouncementModal")?.addEventListener("click", (event) =>
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
    $("#confirmActionButton")?.addEventListener("click", () => {
      const action = pendingConfirmAction;
      pendingConfirmAction = null;
      closeModal("confirmModal", false);
      if (typeof action === "function") action();
    });
    $("#staffForm")?.addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = event.currentTarget;
      if (!form.checkValidity()) {
        form.reportValidity();
        return;
      }
      const submitButton = $("#createStaffButton");
      submitButton.disabled = true;
      const payload = {
        full_name: $("#newName").value.trim(),
        staff_code: $("#newId").value.trim(),
        email: $("#newEmail").value.trim(),
        password: $("#newPassword").value,
        role: $("#newRole").value,
      };
      let account;
      try {
        account = await createStaffAccount(payload);
      } catch (error) {
        if (await handleUnauthorizedResponse(error.status)) return;
        console.error("Creating staff account failed:", error);
        toast(error.message || "ไม่สามารถสร้างบัญชีได้");
        submitButton.disabled = false;
        return;
      }
      const record = toDashboardStaff(account);
      record.zone = $("#newZone").value.trim() || "-";
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
      form.reset();
      submitButton.disabled = false;
      showSuccess("สร้างบัญชี Staff แล้ว");
    });
    $("#editStaffForm")?.addEventListener("submit", (event) => {
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
    $("#claimActions")?.addEventListener("click", (event) => {
      const button = event.target.closest("[data-claim-action]");
      if (button)
        updateClaimWithConfirmation(
          button.dataset.claimId,
          button.dataset.claimAction,
          button
        );
    });
    $("#foundForm")?.addEventListener("submit", (event) => {
      event.preventDefault();
      if (!event.currentTarget.checkValidity()) {
        event.currentTarget.reportValidity();
        return;
      }
      const photo = $("#foundPhoto")?.files?.[0];
      if (photo && photo.size > 5 * 1024 * 1024) {
        toast("รูปสิ่งของต้องมีขนาดไม่เกิน 5 MB");
        $("#foundPhoto").focus();
        return;
      }
      const nextFoundNumber = Math.max(81, ...lostSets.inventory.map((item) => Number(item.id.replace("FD-", "")) || 0)) + 1;
      const record = {
        id: `FD-${String(nextFoundNumber).padStart(3, "0")}`,
        title: $("#foundName").value.trim(),
        category: $("#foundCategory").value,
        place: `พบที่ ${$("#foundLocation").value.trim()}`,
        foundDate: $("#foundDate").value,
        foundTime: $("#foundTime").value,
        custody: $("#custodyPoint").value.trim(),
        finder: $("#foundFinder").value.trim(),
        finderContact: $("#foundContact").value.trim(),
        description: $("#foundDescription").value.trim(),
        privateDetail: $("#privateDetail").value.trim(),
        photoName: photo?.name || "",
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
        detail: `${record.category} · ${record.place} · พบวันที่ ${record.foundDate} ${record.foundTime} · จุดเก็บ ${record.custody}`,
      });
      currentLostTab = "inventory";
      renderLost();
      renderClerkCenter();
      renderNotifications();
      renderMetrics();
      closeModal("foundModal", false);
      event.currentTarget.reset();
      showSuccess("ส่งคำขอรับฝากแล้ว · รายการอยู่ในศูนย์รับงานเพื่อรออนุมัติ");
    });
    $("#rejectForm")?.addEventListener("submit", (event) => {
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
        detail =
          $("#rejectReasonDetail")?.value.trim() ||
          $("#rejectNote")?.value.trim() ||
          "";
      const decisionReason = detail ? `${reason} — ${detail}` : reason;
      closeModal("rejectModal", false);
      const isLostAnnouncement = tab === "lostposts";
      requestConfirmation(isLostAnnouncement ? "ยืนยันปฏิเสธประกาศของหาย" : "ยืนยันไม่อนุมัติรายการรับฝาก",
        `${id} · ${item.title}\nเหตุผล: ${decisionReason}\n\n${
          isLostAnnouncement ? "ประกาศนี้จะไม่ถูกเผยแพร่ให้ผู้ใช้งานเห็น" : "รายการนี้จะไม่ได้รับการอนุมัติเข้าสู่ระบบรับฝาก" }`, () => 
            confirmRejectLostItem(tab, id, decisionReason),
          isLostAnnouncement ? "ยืนยันปฏิเสธประกาศ" : "ยืนยันไม่อนุมัติ",
      );
    });
    $("#returnJobForm")?.addEventListener("submit", (event) => {
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
    $("#appointmentForm")?.addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = event.currentTarget;
      const appointmentTimeInput = $("#appointmentTime");
      appointmentTimeInput.setCustomValidity("");
      if (!form.checkValidity()) {
        form.reportValidity();
        return;
      }
      const item = lostSets.claims.find(
        (record) => record.id === $("#appointmentItemId").value
      );
      if (!item) return;
      const appointmentDate = $("#appointmentDate").value;
      const appointmentTime = $("#appointmentTime").value;
      const appointmentPlace = $("#appointmentPlace").value.trim();
      const note = $("#appointmentNote").value.trim();
      const pickupAt = new Date(`${appointmentDate}T${appointmentTime}`);
      if (Number.isNaN(pickupAt.getTime()) || pickupAt.getTime() <= Date.now()) {
        appointmentTimeInput.setCustomValidity(
          "กรุณาเลือกวันและเวลานัดหมายที่ยังมาไม่ถึง",
        );
        appointmentTimeInput.reportValidity();
        return;
      }
      const submitButton = form.querySelector('button[type="submit"]');
      if (submitButton) submitButton.disabled = true;
      try {
        const result = await scheduleOwnershipPickup(item.backendId, {
          date: appointmentDate,
          time: appointmentTime,
          location: appointmentPlace,
          note,
        });
        item.backendStatus = result.status || item.backendStatus;
        item.returnStatusCode = result.return_status || "ready_for_pickup";
        item.returnStatus = foundItemReturnStatus(
          item.returnStatusCode,
          item.backendStatus,
        );
        item.pickupDate =
          result.pickup_date || result.appointment?.pickup_date || appointmentDate;
        item.pickupTime =
          result.pickup_time || result.appointment?.pickup_time || appointmentTime;
        item.pickupLocation =
          result.pickup_location ||
          result.appointment?.pickup_location ||
          appointmentPlace;
        item.pickupNote = result.pickup_note || result.appointment?.note || note;
        item.status = "นัดหมายแล้ว";
        item.assignee = activeStaffName();
        item.appointment = `${appointmentDate} เวลา ${appointmentTime} · ${appointmentPlace}`;
        item.custody = `นัด ${item.appointment}`;
        if (note) {
          item.appointment += ` · ${note}`;
          item.custody += ` · ${note}`;
        }
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
        renderClerkCenter();
        renderMetrics();
        showSuccess(
          `${item.id} · นัดรับ ${item.title}\n${item.appointment}`,
          "สร้างนัดหมายรับของแล้ว",
        );
      } catch (error) {
        if (await handleUnauthorizedResponse(error.status)) return;
        console.error("Scheduling ownership pickup failed:", error);
        toast(error.message || "ไม่สามารถสร้างนัดหมายรับของได้");
      } finally {
        if (submitButton) submitButton.disabled = false;
      }
    });
    $("#openQrModal")?.addEventListener("click", (event) =>
      openModal("qrFormModal", event.currentTarget)
    );
    $("#qrForm")?.addEventListener("submit", (event) => {
      event.preventDefault();
      if (!event.currentTarget.checkValidity()) {
        event.currentTarget.reportValidity();
        return;
      }
      if (!generateQr(true)) return;
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
    $("#downloadQr")?.addEventListener("click", () => {
      const canvas = $("#qrCode canvas"),
        img = $("#qrCode img");
      let href = canvas ? canvas.toDataURL("image/png") : img?.src;
      if (!href) {
        toast("ยังไม่มี QR จริงให้ดาวน์โหลด กรุณาสร้าง QR ก่อน");
        return;
      }
      const link = document.createElement("a");
      link.href = href;
      link.download = `QR-${$("#room").value.trim()}.png`;
      link.click();
      toast("ดาวน์โหลด QR แล้ว");
    });
    $("#roomList")?.addEventListener("click", (event) => {
      const button = event.target.closest("[data-copy-room-url]");
      if (!button) return;
      navigator.clipboard?.writeText(
        decodeURIComponent(button.dataset.copyRoomUrl)
      );
      toast("คัดลอกลิงก์ห้องแล้ว");
    });
    $("#bulkQr")?.addEventListener("click", (event) =>
      openModal("bulkQrModal", event.currentTarget)
    );
    $("#bulkQrForm")?.addEventListener("submit", (event) => {
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
    $("#printQr")?.addEventListener("click", () => {
      toast("เปิดหน้าต่างพิมพ์ QR แล้ว");
      window.print();
    });
    $("#heroPrimary")?.addEventListener("click", () =>
      navigate(currentRole === "clerk" ? "clerk-center" : "jobs")
    );

    // -------------------------------------------------------------------------
    // 20) Initial data loading: เริ่มหลังจากผูก event ทุกระบบเรียบร้อยแล้ว
    // -------------------------------------------------------------------------

    // โหลดข้อมูลแต่ละระบบตามลำดับ เพื่อให้ข้อมูลที่ render ภายหลังครบถ้วน
    async function loadInitialDashboardData() {
      renderStaff();
      await loadStaffAccounts();
      await loadPendingFoundItems();
      await loadPendingLostItems();
      await loadApprovedLostFoundItems();
      await loadPendingOwnershipRequests();
      await loadRepairRequests();
      await loadStaffNotifications();
      setRole(allowedRoles.includes(currentRole) ? currentRole : "admin");
    }

    await loadInitialDashboardData();

    // QR library และ DOM พร้อมใช้งานแล้ว จึงสร้าง preview และปิด loading mask
    setTimeout(() => {
      generateQr(false);
      $(".loading-mask")?.remove();
    }, 320);
  }

  onMounted(initializeDashboard);

  return { activeRole };
}
