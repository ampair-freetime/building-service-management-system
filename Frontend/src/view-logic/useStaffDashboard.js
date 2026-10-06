import { onBeforeUnmount, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { enhanceFilterSelects } from "../services/filterSelectDropdown.js";
import { requestStatusPresentation, serviceProgress } from "../services/requestStatus.js";
import {
  createAdminLocation,
  fetchAdminLocations,
  generateAdminLocationQr,
  setAdminLocationActive,
} from "../services/adminLocations.js";
import { createStaffDashboardData } from "./staff-dashboard/data.js";
import { taskHistoryRows } from "./staff-dashboard/work-history.js";
import { jobMetrics } from "./staff-dashboard/job-metrics.js";
import {
  STAFF_ROLE_PAGES,
  canRoleOpenPage,
} from "../config/staff-role-pages.js";
import {
  rejectOwnershipRequest,
  getPersonalLostFoundHistory,
  getFoundItemDetail,
  getLostItemDetail,
  getPendingFoundItems,
  getPendingLostItems,
  getApprovedLostFoundItems,
  rejectFoundItem,
  rejectLostItemAnnouncement,
  approveFoundItem,
  approveLostItemAnnouncement,
  closeFoundItem,
  closeLostItemAnnouncement,
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
import { fetchStaffWorkOverview, fetchStaffCurrentWork } from "./staff-dashboard/staff-work-overview.js";
import {
  createStaffAccount,
  deleteStaffAccount,
  fetchStaffAccounts,
  forgetInvitationDelivery,
  rememberInvitationDelivery,
  resendStaffInvitation,
  toDashboardStaff,
  toUpdatedDashboardStaff,
  updateStaffProfile,
} from "./staff-dashboard/staff-accounts.js";
import {
  acceptCleaningTask,
  addCleaningCompletionNote,
  getCleaningTaskDetail,
  getCleaningTaskHistory,
  getCleaningTasks,
  getStaffNotifications,
  markStaffNotificationRead,
  returnCleaningTask,
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
  returnRepairRequest,
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
  const activeRole = ref(
    allowedRoles.includes(savedRole) ? savedRole : "clerk",
  );
  let cleanupFilterSelects = () => {};
  let cleanupDashboardEvents = () => {};

  async function initializeDashboard() {
    // โหลด dependency ภายนอกก่อนสร้างหน้าจอ หากโหลดไม่ได้จะใช้ QR fallback แทน
    try {
      await loadQrCodeLibrary();
    } catch (error) {
      console.warn(
        "QR Code library could not be loaded. QR fallback will be used.",
        error,
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
        localStorage.getItem("buildingCareStaff") || "null",
      );
      if (
        signedInStaff?.full_name &&
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
        roleConfig[signedInRole].staffId = signedInStaff.staff_code || "-";
        roleConfig[signedInRole].avatar =
          initials || roleConfig[signedInRole].avatar;
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
    let currentLostTab = currentRole === "clerk" ? "all" : "inventory";
    let appliedHistorySearch = "";
    let currentClerkCenterView = "approvals";
    const clerkApprovalLoadState = { found: "loading", lost: "loading", claims: "loading" };
    const readClaimNotifications = new Set();
    let currentBoardView = "unassigned";
    let currentPage = STAFF_ROLE_PAGES[currentRole]?.[0]?.id || "dashboard";
    let navigationReady = false;
    let restoringNavigation = false;
    let currentHistoryTab = "work";
    let selectedJobId = "";
    let overviewData = null;
    let overviewRequest = 0;
    let overviewSearchTimer = null;
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
        loadStaffWorkOverview();
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
          createdAt: item.created_at,
          imageUrl: item.images?.[0]?.url || "",
          assignee: null,
        }));
        const processedItems = lostSets.inventory.filter(
          (item) => approvalGroup(item.status) !== "pending",
        );
        lostSets.inventory = [...pendingFoundItems, ...processedItems];
        clerkApprovalLoadState.found = "ready";
        renderClerkCenter();
        renderMetrics();
        renderNotifications();
      } catch (error) {
        clerkApprovalLoadState.found = "error";
        renderClerkApprovalsOverview();
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
          createdAt: item.created_at,
          imageUrl: item.images?.[0]?.url || "",
          assignee: null,
        }));
        const processedItems = lostSets.lostposts.filter(
          (item) => approvalGroup(item.status) !== "pending",
        );
        lostSets.lostposts = [...pendingLostItems, ...processedItems];
        clerkApprovalLoadState.lost = "ready";
        renderClerkCenter();
        renderMetrics();
        renderNotifications();
      } catch (error) {
        clerkApprovalLoadState.lost = "error";
        renderClerkApprovalsOverview();
        if (await handleUnauthorizedResponse(error.status)) return;
        console.error("Loading pending lost-item reports failed:", error);
        toast(error.message || "ไม่สามารถโหลดประกาศของหายได้");
      }
    }

    let approvedLoadVersion = 0;
    // โหลดของพบและประกาศของหายที่ผ่านการอนุมัติแล้ว
    async function loadApprovedLostFoundItems() {
      if (currentRole !== "clerk" && currentRole !== "admin") return;
      const version = ++approvedLoadVersion;
      try {
        const { foundItems, lostItems } = await getApprovedLostFoundItems();
        if (version !== approvedLoadVersion) return;
        const deletedIds = new Set(deletedRecords
          .filter((entry) => entry.source === "lost")
          .map((entry) => entry.itemId));
        const mapApprovedItem = (item, tab) => ({
          publicListItem: true,
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
          reporterEmail: item.reporter_email || null,
          reviewerId: item.reviewed_by || null,
          reviewerName: item.reviewer_name || item.reviewer?.full_name || null,
          assignee: null,
        });
        const mergeApproved = (tab, items) => {
          const previous = new Map(lostSets[tab].map((item) => [item.backendId, item]));
          const approved = items
            .filter((item) => !deletedIds.has(item.item_code))
            .map((item) => ({ ...previous.get(item.id), ...mapApprovedItem(item, tab) }));
          const approvedIds = new Set(approved.map((item) => item.backendId));
          lostSets[tab] = [
            ...lostSets[tab].filter((item) => !item.publicListItem && !approvedIds.has(item.backendId)),
            ...approved,
          ];
        };
        mergeApproved("inventory", foundItems);
        mergeApproved("lostposts", lostItems);
        renderLost();
        renderMetrics();
      } catch (error) {
        if (version !== approvedLoadVersion) return;
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
          returnStatus: foundItemReturnStatus(
            claim.return_status,
            claim.status,
          ),
          requester: claim.claimant_name,
          contact: claim.claimant_email,
          requestDate: new Date(
            claim.created_at,
          ).toLocaleString("th-TH"),
          createdAt: claim.created_at,
          evidence: claim.proof_detail,
          secret: claim.private_verification_detail,
          custodyLocation: claim.custody_location,
          pickupDate: claim.pickup_date || (claim.pickup_datetime ? new Intl.DateTimeFormat("en-CA", {timeZone: "Asia/Bangkok", year: "numeric", month: "2-digit", day: "2-digit"}).format(new Date(claim.pickup_datetime)) : ""),
          pickupTime: claim.pickup_time || (claim.pickup_datetime ? new Intl.DateTimeFormat("en-GB", {timeZone: "Asia/Bangkok", hour: "2-digit", minute: "2-digit"}).format(new Date(claim.pickup_datetime)) : ""),
          pickupLocation:
            claim.pickup_location || claim.appointment?.pickup_location || "",
          pickupNote: claim.pickup_note || claim.appointment?.note || "",
          appointment: claim.pickup_date
            ? `${claim.pickup_date} เวลา ${claim.pickup_time || "–"}`
            : "ยังไม่มีนัดหมาย",
          assignee: null,
        }));

        clerkApprovalLoadState.claims = "ready";
        renderClerkCenter();
        renderMetrics();
        renderNotifications();
      } catch (error) {
        clerkApprovalLoadState.claims = "error";
        renderClerkApprovalsOverview();
        if (await handleUnauthorizedResponse(error.status)) return;

        console.error("Loading pending ownership requests failed:", error);

        if (error.status !== 404) {
          toast(error.message || "ไม่สามารถโหลดคำขอแสดงความเป็นเจ้าของได้");
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
    function signedInStaffId() {
      try {
        return JSON.parse(localStorage.getItem("buildingCareStaff") || "null")?.id || null;
      } catch {
        return null;
      }
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
        actorId: signedInStaffId(),
        itemId,
        title,
        category,
        action,
        status,
        detail,
        date,
        time,
        timestamp: Date.now(),
      });
      renderActivities();
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
      waiting: "รอรับงาน",
      assigned: "รับงานแล้ว",
      received: "รับเรื่องแล้ว",
      in_progress: "กำลังดำเนินการ",
      completed: "เสร็จสิ้น",
      cancelled: "ยกเลิก",
    };
    const nextCleaningStatuses = {
      assigned: "received",
      received: "in_progress",
      in_progress: "completed",
    };
    const serviceProgressStatuses = ["assigned", "received", "in_progress", "completed"];

    function nextCleaningStatus(job) {
      const backendStatus = nextCleaningStatuses[job.backendStatus];
      return backendStatus
        ? { backendStatus, label: cleaningStatusLabels[backendStatus] }
        : null;
    }
    const repairStatusLabels = {
      waiting: "รอรับงาน",
      assigned: "รับงานแล้ว",
      received: "รับเรื่องแล้ว",
      in_progress: "กำลังดำเนินการ",
      completed: "เสร็จสิ้น",
      cancelled: "ยกเลิก",
    };
    function nextRepairStatus(job) {
      const next = { assigned: "received", received: "in_progress", in_progress: "completed" }[
        job.backendStatus
      ];
      return next
        ? { backendStatus: next, label: repairStatusLabels[next] }
        : null;
    }
    function repairLocation(location) {
      return (
        [location?.area, location?.floor && `ชั้น ${location.floor}`]
          .filter(Boolean)
          .join(" · ") || "ไม่ระบุสถานที่"
      );
    }
    async function loadRepairRequests() {
      if (currentRole !== "technician") return;
      try {
        const result = await getRepairRequests();
        const staffId = JSON.parse(
          localStorage.getItem("buildingCareStaff") || "null",
        )?.id;
        const requests = Array.isArray(result.requests) ? result.requests : [];
        const ids = new Set(requests.map((request) => request.id));
        for (const request of requests) {
          let job = allJobs.find((item) => item.backendId === request.id);
          if (!job) {
            job = {
              type: "repair",
              category: "งานซ่อม",
              reporter: "ผู้ใช้งานอาคาร",
              timeline: [],
            };
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
              ? request.assigned_staff_id === staffId
                ? activeStaffName()
                : "ช่างผู้รับผิดชอบ"
              : null,
            time: new Date(request.created_at).toLocaleString("th-TH"),
          });
        }
        allJobs = allJobs.filter(
          (job) =>
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
    // โหลดงานทำความสะอาดจาก Backend ตอนเปิด Dashboard ไม่ต้องรอให้กดการแจ้งเตือนก่อน
    async function loadCleaningTasks() {
      if (currentRole !== "housekeeper") return;
      try {
        const result = await getCleaningTasks();
        const staffId = JSON.parse(
          localStorage.getItem("buildingCareStaff") || "null",
        )?.id;
        const tasks = Array.isArray(result.requests) ? result.requests : [];
        const ids = new Set(tasks.map((task) => task.id));
        for (const task of tasks) {
          let job = allJobs.find((item) => item.backendId === task.id);
          if (!job) {
            job = {
              type: "cleaning",
              category: "งานทำความสะอาด",
              reporter: "ผู้ใช้งานอาคาร",
              timeline: [],
            };
            allJobs.push(job);
          }
          Object.assign(job, {
            backendId: task.id,
            id: task.request_code,
            category: task.cleaning_category || "ทำความสะอาดทั่วไป",
            title: task.title,
            detail: task.description,
            room: repairLocation(task.location),
            priority: task.priority === "urgent" ? "เร่งด่วน" : "ปกติ",
            backendStatus: task.status,
            status: cleaningStatusLabels[task.status] || task.status,
            assigneeId: task.assigned_staff_id,
            assignee: task.assigned_staff_id
              ? task.assigned_staff_id === staffId
                ? activeStaffName()
                : "แม่บ้านผู้รับผิดชอบ"
              : null,
            time: new Date(task.created_at).toLocaleString("th-TH"),
          });
        }
        // ลบการ์ดงานทำความสะอาดที่ Backend ไม่ส่งมาแล้ว (เช่น คนอื่นรับไป)
        allJobs = allJobs.filter(
          (job) =>
            job.type !== "cleaning" || !job.backendId || ids.has(job.backendId),
        );
        renderJobs();
        renderMetrics();
        renderQueue();
      } catch (error) {
        if (await handleUnauthorizedResponse(error.status)) return;
        console.error("Loading cleaning tasks failed:", error);
        toast(error.message || "ไม่สามารถโหลดรายการงานทำความสะอาดได้");
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
            }</option>`,
        )
        .join("");
    }
    function renderProfileAvatar(element) {
      if (!element) return;
      element.innerHTML =
        '<svg class="icon profile-person-icon" aria-hidden="true"><use href="#i-user"></use></svg>';
      element.setAttribute("aria-hidden", "true");
    }
    function staffRoleColor(role) {
      return {
        admin: "#335e8a",
        แอดมิน: "#335e8a",
        housekeeper: "#24613a",
        แม่บ้าน: "#24613a",
        technician: "#b45309",
        ช่าง: "#b45309",
        clerk: "#9a6508",
        ธุรการ: "#9a6508",
      }[role] || "#335e8a";
    }
    function staffRoleAvatar(role, neutral = false) {
      const color = neutral ? "#526b83" : staffRoleColor(role);
      return `<div class="person-avatar role-person-avatar" style="--avatar-role:${color}" aria-hidden="true"><svg class="icon profile-person-icon"><use href="#i-user"></use></svg></div>`;
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
      renderProfileAvatar(avatar);

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
        jobsTitle.textContent = ["housekeeper", "technician"].includes(role)
          ? "ศูนย์รับงาน" : c.jobTitle || "ศูนย์รับงานรวม";
      }

      const jobsSubtitle = $("#jobsSubtitle");
      if (jobsSubtitle) {
        jobsSubtitle.textContent = c.jobSubtitle || "";
      }

      const heroPrimary = $("#heroPrimary");
      if (heroPrimary) heroPrimary.textContent = c.primary;

      const headerAvatar = $("#headerAvatar");
      renderProfileAvatar(headerAvatar);

      const headerName = $("#headerName");
      if (headerName) {
        headerName.textContent = currentUserName[role].split(" ")[0];
      }

      const headerRole = $("#headerRole");
      if (headerRole) headerRole.textContent = c.label;

      const compactHeaderAvatar = $("#compactHeaderAvatar");
      renderProfileAvatar(compactHeaderAvatar);

      const compactHeaderName = $("#compactHeaderName");
      if (compactHeaderName) {
        compactHeaderName.textContent = currentUserName[role].split(" ")[0];
      }

      const compactHeaderRole = $("#compactHeaderRole");
      if (compactHeaderRole) compactHeaderRole.textContent = c.label;

      const profileAvatar = $("#profileAvatar");
      renderProfileAvatar(profileAvatar);

      const profileName = $("#profileName");
      if (profileName) profileName.textContent = currentUserName[role];

      let signedInProfile = null;
      try {
        signedInProfile = JSON.parse(
          localStorage.getItem("buildingCareStaff") || "null",
        );
      } catch (error) {
        console.warn("Stored staff profile is invalid:", error);
      }

      const profileEmail = $("#profileEmail");
      if (profileEmail)
        profileEmail.textContent =
          signedInProfile?.role === role && signedInProfile?.email
            ? signedInProfile.email
            : "-";

      const profileRole = $("#profileRole");
      if (profileRole) profileRole.textContent = c.label;

      const jobsNavLabel = $("#jobsNavLabel");
      if (jobsNavLabel) {
        jobsNavLabel.textContent =
          role === "housekeeper"
            ? "ศูนย์รับงาน"
            : role === "technician"
              ? "ศูนย์รับงาน"
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
        n.classList.toggle("role-hidden", !roleAllows(n, role)),
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
    function modalSlug(id) {
      return id
        .replace(/Modal$/, "")
        .replace(/([a-z0-9])([A-Z])/g, "$1-$2")
        .toLowerCase();
    }

    function modalIdFromSlug(slug) {
      return $$(".modal").find((modal) => modalSlug(modal.id) === slug)?.id;
    }

    function dashboardBasePath() {
      return currentRole === "admin" ? "/admin-dashboard" : "/staff-dashboard";
    }

    function readDashboardRoute() {
      const match = window.location.pathname.match(
        /\/(?:admin-dashboard|staff-dashboard)(?:\/([^/]+))?(?:\/([^/]+))?\/?$/,
      );
      return {
        page: match?.[1] ? decodeURIComponent(match[1]) : "",
        dialog: match?.[2] ? decodeURIComponent(match[2]) : "",
      };
    }

    function updateDashboardRoute(modalId = "", mode = "push") {
      if (!navigationReady || restoringNavigation) return;
      const dialog = modalId ? `/${modalSlug(modalId)}` : "";
      const path = `${dashboardBasePath()}/${currentPage}${dialog}`;
      const query = { ...router.currentRoute.value.query };
      const target = router.resolve({ path, query }).fullPath;
      const current = `${window.location.pathname}${window.location.search}`;
      if (target === current) return;
      void router[mode]({ path, query });
    }

    function navigate(page, historyMode = "push") {
      const destinationPage = page === "my-jobs" ? "jobs" : page;
      if (!canRoleOpenPage(currentRole, page)) {
        toast("บทบาทนี้ไม่มีสิทธิ์เข้าถึงเมนูดังกล่าว");
        return;
      }
      const target = $(`.nav-item[data-page="${page}"]`);
      if (target && target.classList.contains("role-hidden")) {
        toast("บทบาทนี้ไม่มีสิทธิ์เข้าถึงเมนูดังกล่าว");
        return;
      }
      const destination = $(`#page-${destinationPage}`);
      if (!destination) {
        toast("ไม่พบหน้าที่เลือก");
        return;
      }
      currentPage = page;
      if (["housekeeper", "technician"].includes(currentRole) && destinationPage === "jobs") {
        currentBoardView = page === "my-jobs" ? "mine" : "unassigned";
      }
      $("#notificationPanel")?.classList.remove("open", "mobile-notification-page");
      $("#notificationButton")?.setAttribute("aria-expanded", "false");
      $$("#mobileNotification, #mobileNotificationAdmin").forEach((button) => {
        button.classList.remove("active");
        button.removeAttribute("aria-current");
      });
      $$(".page").forEach((p) => p.classList.remove("active"));
      destination.classList.add("active");
      $$(".nav-item").forEach((n) =>
        n.classList.toggle("active", n.dataset.page === page),
      );
      $$("[data-mobile-page]").forEach((n) =>
        n.classList.toggle("active", n.dataset.mobilePage === page),
      );
      // ให้หัวข้อหลักของหน้าตรงกับชื่อเมนู Sidebar ที่ผู้ใช้เลือก
      if (target) {
        const labelSource = target.cloneNode(true);
        labelSource
          .querySelectorAll(".nav-icon")
          .forEach((icon) => icon.remove());
        const pageHeading = destination.querySelector("h2");
        if (pageHeading)
          pageHeading.textContent = labelSource.textContent.trim();
      }
      if (destinationPage === "jobs") renderJobs();
      if (page === "clerk-center") renderClerkCenter();

      if (page === "my-history") {
        currentHistoryTab = "work";
        $$("#myHistoryTabs [data-history-tab]").forEach(button => {
          const active = button.dataset.historyTab === currentHistoryTab;
          button.classList.toggle("active", active);
          button.setAttribute("aria-selected", String(active));
        });
        const historyType = $("#myHistoryType");
        if (historyType) { historyType.value = "all"; historyType.closest("select").hidden = false; }
        renderMyHistory();
        void loadMyTaskHistory();
      }
      if (page === "notifications") renderNotifications();
      if (page === "staff-overview") loadStaffWorkOverview();
      if (page === "history") {
        renderHistory();
        window.dispatchEvent(new Event("clerk-approvals:refresh"));
      }
      closeSidebar();
      window.scrollTo({
        top: 0,
        behavior: matchMedia("(prefers-reduced-motion: reduce)").matches
          ? "auto"
          : "smooth",
      });
      if (historyMode !== "none") updateDashboardRoute("", historyMode);
    }
    function renderMetrics() {
      if (!$("#metricGrid")) return;
      const jobs = roleJobs();
      const today = new Intl.DateTimeFormat("en-CA", {
        timeZone: "Asia/Bangkok", year: "numeric", month: "2-digit", day: "2-digit",
      }).format(new Date());
      const { unassigned, mine, urgent, completed } = jobMetrics(jobs, workHistory, activeStaffName(), today);
      let values;
      if (currentRole === "clerk")
        values = [
          [
            "ของที่พบใหม่",
            String(
              lostSets.inventory.filter((x) => x.status.includes("รอ")).length,
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
              lostSets.claims.filter((x) => x.status === "คืนของแล้ว").length,
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
          ["งานเสร็จวันนี้", String(jobs.filter((job) => job.status === "เสร็จสิ้น").length), "ปิดงานแล้ว"],
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
          ["งานเสร็จวันนี้", String(completed), "ปิดงานแล้ว"],
        ];
      else
        values = [
          ["งานทำความสะอาดใหม่", String(unassigned), "คิวงานใหม่"],
          ["งานของฉัน", String(mine), "กำลังรับผิดชอบ"],
          ["งานเร่งด่วน", String(urgent), "ควรรับก่อน"],
          ["งานเสร็จวันนี้", String(completed), "ปิดงานแล้ว"],
        ];
      $("#metricGrid").innerHTML = values
        .map(
          (v, i) =>
            `<article class="metric ${
              v[0].includes("เร่ง") ? "urgent" : v[0].includes("เกิน") ? "warn" : ""
            }"><span>${v[0]}</span><strong>${v[1]}</strong><small>${
              v[2]
            }</small></article>`,
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
              (b.priority === "เร่งด่วน" ? -1 : 1),
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
                }</span></article>`,
            )
            .join("")
        : '<div class="empty">ไม่มีรายการรอรับในขณะนี้</div>';
    }
    function renderActivities() {
      if (!$("#activityList")) return;
      if (!["housekeeper", "technician"].includes(currentRole)) return;
      const staffId = signedInStaffId();
      const staffName = activeStaffName();
      const staffActions = new Set(["accepted", "status_changed", "completed", "returned", "completion_note_added"]);
      const recent = workHistory
        .filter((record) => record.staff === staffName)
        .filter((record) => record.sourceAction
          ? staffActions.has(record.sourceAction)
          : !record.actorId || record.actorId === staffId)
        .sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0))
        .slice(0, 5);
      $("#activityList").innerHTML = recent.length
        ? recent.map((record) => {
          const when = Number.isFinite(record.timestamp)
            ? new Intl.DateTimeFormat("th-TH", { dateStyle: "short", timeStyle: "short" }).format(record.timestamp)
            : `${record.date || ""} ${record.time || ""}`;
          return `<div class="activity-item"><div class="activity-dot"></div><div><strong>${escapeHtml(record.action)} · ${escapeHtml(record.itemId || "")}</strong><p>${escapeHtml(record.title || "งาน")} · ${escapeHtml(record.status || "")} · ${escapeHtml(when)}</p></div></div>`;
        }).join("")
        : '<div class="empty">ยังไม่มีกิจกรรมที่คุณดำเนินการ</div>';
    }

    // -------------------------------------------------------------------------
    // 6) ระบบคิวงานแม่บ้านและช่าง
    // -------------------------------------------------------------------------

    // ตรวจว่างานตรงกับ tab และตัวกรองที่ผู้ใช้เลือกหรือไม่
    function jobMatchesView(job) {
      if (currentRole === "admin" && currentBoardView === "mine")
        return job.assignee === activeStaffName();
      if (currentBoardView === "unassigned") return !job.assignee && !isTerminalStatus(job.status) && job.backendStatus !== "cancelled" && job.status !== "ยกเลิก";
      if (currentBoardView === "mine")
        return job.assignee === activeStaffName();
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
        .map(
          (s) => `<option ${job.status === s ? "selected" : ""}>${s}</option>`,
        )
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
            .includes(query),
      );
      $("#jobList").innerHTML = data.length
        ? data
            .map((j) => {
              const isMine = j.assignee === activeStaffName(),
                isUnassigned = !j.assignee,
                canEdit = isMine || currentRole === "admin";
              let actions;
              if (isTerminalStatus(j.status)) actions = "";
              else if (isUnassigned && currentRole !== "admin")
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
                  j.assignee,
                )}</div>`;
              const icon = j.type === "repair" ? "#i-tools" : "#i-broom";
              const photo = `<div class="job-photo"><svg class="icon"><use href="${icon}"/></svg></div>`;
              return `<article class="job-card ${
                isMine ? "owned" : ""
              }" tabindex="0" data-job-card="${
                j.id
              }">${photo}<div><div class="job-meta"><span class="badge ${
                j.priority === "เร่งด่วน" ? "danger" : "normal"
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
              }</span><span class="assignee ${isUnassigned ? "is-unassigned" : ""}"><span class="assignee-dot"></span>${escapeHtml(
                assignedCleanerLabel(j),
              )}</span></div></div><div class="job-actions">${actions}<button class="small-btn" type="button" data-job-action="detail" data-job-id="${
                j.id
              }">ดูรายละเอียด</button></div></article>`;
            })
            .join("")
        : '<div class="empty">ยังไม่มีงาน</div>';
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
          closeModal("jobDetailModal", false);
          $("#jobSearch").value = "";
          $("#categoryFilter").value = "all";
          $("#jobStatusFilter").value = "all";
          navigate("my-jobs");
          showSuccess(
            `เลขงาน: ${acceptedJob.id}\nสถานะ: ${acceptedJob.status}\nผู้รับผิดชอบ: ${assignedCleanerLabel(acceptedJob)}`,
            job.type === "repair"
              ? "รับงานซ่อมสำเร็จ"
              : "รับงานทำความสะอาดสำเร็จ",
          );
        },
        "ยืนยันรับงาน",
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
          const acceptedTask =
            job.type === "repair"
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
          else await loadCleaningTasks();
          return false;
        }
      } else {
        job.assignee = activeStaffName();
        job.status = "รับงานแล้ว";
      }
      job.returnReason = "";
      currentBoardView = "mine";
      $$("#boardTabs .board-tab").forEach((t) =>
        t.classList.toggle("active", t.dataset.view === "mine"),
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
        $("#jobDetailAssignee").classList.toggle("is-unassigned", !job.assignee);
        $("#jobTimeline").innerHTML = jobTimeline(job);
        renderJobQuickActions(job);
      }
      addNotification(
        currentRole,
        `รับงาน ${id} สำเร็จ`,
        `คุณเป็นผู้รับผิดชอบงาน “${job.title}” แล้ว`,
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
        `เปลี่ยนจาก “${previous}” เป็น “${job.status}”`,
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
    function openReturnJob(id, historyMode = "push") {
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
      openModal("returnJobModal", document.activeElement, historyMode);
    }
    function addAudit(
      source,
      action,
      itemId,
      title,
      detail,
      actor = activeStaffName(),
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
        "ย้ายรายการไปยังถังเก็บแบบ Soft Delete",
      );
    }
    function deleteJob(id) {
      if (currentRole !== "admin") {
        toast("เฉพาะ Admin เท่านั้นที่ลบงานได้");
        return;
      }
      const index = allJobs.findIndex((j) => j.id === id);
      if (index < 0) return;
      requestConfirmation("ยืนยันลบงาน", `ลบงาน ${id} หรือไม่?`, () => {
        const [record] = allJobs.splice(index, 1);
        storeDeletedRecord("jobs", record, "allJobs", record.title);
        toast(`ลบงาน ${id} แล้ว`);
        renderJobs();
        renderMetrics();
        renderQueue();
        renderStaffOverview();
        renderHistory();
      });
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
          (s) => `<option ${item.status === s ? "selected" : ""}>${s}</option>`,
        )
        .join("");
    }
    function decisionButtons(tab, item) {
      if (currentRole === "admin" || tab === "claims") return "";
      const decision = approvalGroup(item.status);
      if (decision === "rejected") return "";
      if (decision === "approved") {
        return `<div class="decision-strip completed"><button class="approve-btn" type="button" data-lost-action="complete" data-tab="${tab}" data-item-id="${item.id}">ปิดรายการ</button></div>`;
      }
      return `<div class="decision-strip"><button class="approve-btn" type="button" data-lost-action="approve" data-tab="${tab}" data-item-id="${item.id}">อนุมัติ</button><button class="reject-btn" type="button" data-lost-action="reject" data-tab="${tab}" data-item-id="${item.id}">ไม่อนุมัติ</button></div>`;
    }
    function approvalGroup(status = "") {
      if (status.includes("ไม่อนุมัติ") || status.includes("ไม่ผ่าน"))
        return "rejected";
      if (status.includes("รออนุมัติ")) return "pending";
      return "approved";
    }
    function lostDecisionGroup(tab, item) {
      if (tab !== "claims") return approvalGroup(item.status);
      if (item.backendStatus === "rejected" || item.status.includes("ไม่ผ่าน"))
        return "rejected";
      if (
        ["approved", "completed"].includes(item.backendStatus) ||
        ["ผ่านการตรวจสอบ", "นัดหมายแล้ว", "คืนของแล้ว"].includes(item.status)
      )
        return "approved";
      return "pending";
    }
    function completeLostFoundItem(tab, id) {
      const item = lostSets[tab]?.find((record) => record.id === id);
      if (!item) return;
      requestConfirmation(
        "ยืนยันปิดรายการ",
        `${id} · ยืนยันว่าดำเนินการ “${item.title}” สำเร็จแล้วใช่หรือไม่?`,
        async () => {
          // ปิดที่ backend ก่อน หน้า guest จะได้เลิกแสดงรายการนี้ด้วย ไม่ใช่แค่ซ่อนในเครื่อง staff
          if (item.backendId) {
            try {
              if (tab === "inventory") await closeFoundItem(item.backendId);
              else if (tab === "lostposts")
                await closeLostItemAnnouncement(item.backendId);
            } catch (error) {
              if (await handleUnauthorizedResponse(error.status)) return;
              console.error(`Close ${tab} item failed:`, error);
              toast(error.message || "ไม่สามารถปิดรายการได้");
              return;
            }
          }
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
          showSuccess(
            `${id} · ${item.title} ถูกปิดเป็นรายการสำเร็จแล้ว`,
            "ปิดรายการแล้ว",
          );
        },
        "สำเร็จแล้ว",
      );
    }
    function ownershipStatusLabel(status = "") {
      return (
        {
          pending: "รอตรวจสอบ",
          additional_info_required: "ขอข้อมูลเพิ่มเติม",
          approved: "ผ่านการตรวจสอบ",
          rejected: "ไม่ผ่านการตรวจสอบ",
          completed: "คืนของแล้ว",
        }[status] ||
        status ||
        "ไม่ทราบสถานะ"
      );
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
        return (
          claim.returnStatus ||
          foundItemReturnStatus(claim.returnStatusCode, claim.backendStatus)
        );
      }
      if (item.status === "คืนของแล้ว") return "ส่งคืนเจ้าของแล้ว";
      return "ยังไม่มีคำขอรับคืน";
    }
    function approvalTypeLabel(tab) {
      return tab === "inventory"
        ? "ของที่รับฝาก"
        : tab === "lostposts"
          ? "ประกาศตามหา"
          : "คำขอรับของ";
    }
    function findLostItem(tab, id) {
      return lostSets[tab]?.find((item) => item.id === id);
    }
    function pendingApprovalRequests() {
      return ["inventory", "lostposts"].flatMap((tab) =>
        lostSets[tab]
          .filter((item) => approvalGroup(item.status) === "pending")
          .map((item) => ({
            approvalId: item.id,
            tab,
            title: item.title,
            text: item.place,
          })),
      );
    }
    function activeClaimNotifications() {
      return lostSets.claims
        .filter((item) => !["คืนของแล้ว", "ไม่ผ่านการตรวจสอบ"].includes(item.status))
        .map((item) => ({
          ...item,
          unread: !readClaimNotifications.has(item.id),
        }));
    }
    function matchesClerkCenterSearch(...values) {
      const keyword = ($("#clerkCenterSearch")?.value || "")
        .trim()
        .toLocaleLowerCase("th");
      if (!keyword) return true;
      return values
        .filter((value) => value !== null && value !== undefined)
        .some((value) =>
          String(value).toLocaleLowerCase("th").includes(keyword),
        );
    }
    function setClerkCenterView(view) {
      const availableViews = ["approvals", "lost-announcements", "claims"];
      currentClerkCenterView = availableViews.includes(view)
        ? view
        : "approvals";
      $$("#clerkCenterTabs [data-clerk-center-view]").forEach((tab) =>
        tab.classList.toggle(
          "active",
          tab.dataset.clerkCenterView === currentClerkCenterView,
        ),
      );
      $$("[data-clerk-center-panel]").forEach((panel) =>
        panel.classList.toggle(
          "active",
          panel.dataset.clerkCenterPanel === currentClerkCenterView,
        ),
      );
    }
    function renderClerkApprovalsOverview() {
      if (currentRole !== "clerk") return;
      const metrics = $("#clerkApprovalMetrics");
      const preview = $("#clerkApprovalPreview");
      const shortcuts = $("#clerkApprovalShortcuts");
      if (!metrics || !preview || !shortcuts) return;
      const states = Object.values(clerkApprovalLoadState);
      if (states.includes("loading")) {
        metrics.innerHTML = '<div class="empty clerk-overview-state" role="status">กำลังโหลดภาพรวมงานอนุมัติ…</div>';
        preview.innerHTML = '<div class="empty" role="status">กำลังโหลดรายการรอพิจารณา…</div>';
        shortcuts.innerHTML = "";
        return;
      }
      if (states.includes("error")) {
        metrics.innerHTML = '<div class="empty clerk-overview-state" role="alert">ไม่สามารถโหลดภาพรวมงานอนุมัติได้ <button class="small-btn" type="button" data-clerk-overview-retry>ลองใหม่</button></div>';
        preview.innerHTML = '<div class="empty">ข้อมูลรายการยังไม่ครบ กรุณาลองใหม่</div>';
        shortcuts.innerHTML = "";
        return;
      }
      const found = lostSets.inventory.filter((item) => approvalGroup(item.status) === "pending");
      const lost = lostSets.lostposts.filter((item) => approvalGroup(item.status) === "pending");
      const claims = lostSets.claims.filter((item) => !["คืนของแล้ว", "ไม่ผ่านการตรวจสอบ"].includes(item.status));
      metrics.innerHTML = [
        [found.length + lost.length, "รออนุมัติทั้งหมด", "ของที่พบและประกาศของหาย"],
        [found.length, "ของที่พบ", "รออนุมัติรับฝาก"],
        [lost.length, "ประกาศของหาย", "รออนุมัติเผยแพร่"],
        [claims.length, "คำขอรับของ", "รอดำเนินการ"],
      ].map(([count, label, hint]) =>
        `<article class="metric"><span>${label}</span><strong>${count}</strong><small>${hint}</small></article>`
      ).join("");
      const pending = [
        ...found.map((item) => ({ item, tab: "inventory", type: "ของที่พบ" })),
        ...lost.map((item) => ({ item, tab: "lostposts", type: "ประกาศของหาย" })),
      ].sort((a, b) => String(a.item.createdAt || "").localeCompare(String(b.item.createdAt || "")));
      preview.innerHTML = pending.length
        ? pending.slice(0, 5).map(({ item, tab, type }) =>
          `<article class="clerk-approval-preview-item"><div><span class="badge wait">${type}</span><strong>${escapeHtml(item.id)} · ${escapeHtml(item.title)}</strong><small>${escapeHtml(item.place || "ไม่ระบุสถานที่")}</small></div><button class="small-btn" type="button" data-clerk-overview-detail="${escapeHtml(item.id)}" data-tab="${tab}">ดูรายละเอียด</button></article>`
        ).join("")
        : '<div class="empty">ไม่มีรายการรออนุมัติในขณะนี้</div>';
      shortcuts.innerHTML = [
        ["approvals", "ของที่พบรออนุมัติ", found.length],
        ["lost-announcements", "ประกาศของหายรออนุมัติ", lost.length],
        ["claims", "คำขอรับของ", claims.length],
      ].map(([view, label, count]) =>
        `<button class="clerk-approval-shortcut" type="button" data-clerk-overview-view="${view}"><span>${label}</span><strong>${count} รายการ →</strong></button>`
      ).join("");
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
      const approvals = filteredRequests.filter(
        (item) => item.tab === "inventory",
      );
      const lostAnnouncements = filteredRequests.filter(
        (item) => item.tab === "lostposts",
      );
      const claims = lostSets.claims.filter(
        (item) =>
          !["คืนของแล้ว", "ไม่ผ่านการตรวจสอบ"].includes(item.status) &&
          matchesClerkCenterSearch(
            item.id,
            item.title,
            item.place,
            item.requester,
            item.contact,
            item.status,
            item.returnStatus,
            item.evidence,
            item.custody,
          ),
      );
      ["#pendingApprovalCount", "#pendingApprovalTabCount"].forEach(
        (id) => ($(id).textContent = approvals.length),
      );
      [
        "#pendingLostAnnouncementCount",
        "#pendingLostAnnouncementTabCount",
      ].forEach((id) => ($(id).textContent = lostAnnouncements.length));
      ["#activeClaimCount", "#activeClaimTabCount"].forEach(
        (id) => ($(id).textContent = claims.length),
      );
      pendingList.innerHTML = approvals.length
        ? approvals
            .map((item) => {
              const record = findLostItem(item.tab, item.approvalId);
              return `<article class="clerk-request-card"><div class="clerk-request-top"><div><span class="approval-type ${item.tab}">${approvalTypeLabel(item.tab)}</span><h4>${item.approvalId} · ${escapeHtml(item.title)}</h4></div><span class="badge wait">รออนุมัติ</span></div><p>${escapeHtml(item.text)}</p><div class="clerk-request-meta"><span>${escapeHtml(record?.custody || "รอการตรวจสอบ")}</span></div><div class="clerk-request-actions"><button class="small-btn" type="button" data-center-action="detail" data-tab="${item.tab}" data-item-id="${item.approvalId}">ดูรายละเอียด</button><button class="approve-btn" type="button" data-center-action="approve" data-tab="${item.tab}" data-item-id="${item.approvalId}">อนุมัติ</button><button class="reject-btn" type="button" data-center-action="reject" data-tab="${item.tab}" data-item-id="${item.approvalId}">ไม่อนุมัติ</button></div></article>`;
            })
            .join("")
        : '<div class="empty">ไม่มีคำขอที่รออนุมัติ</div>';
      lostAnnouncementList.innerHTML = lostAnnouncements.length
        ? lostAnnouncements
            .map((item) => {
              const record = findLostItem(item.tab, item.approvalId);
              return `<article class="clerk-request-card"><div class="clerk-request-top"><div><span class="approval-type lostposts">ประกาศตามหา</span><h4>${item.approvalId} · ${escapeHtml(item.title)}</h4></div><span class="badge wait">รออนุมัติเผยแพร่</span></div><p>${escapeHtml(item.text)}</p><div class="clerk-request-meta"><span>${escapeHtml(record?.custody || "รอการตรวจสอบ")}</span></div><div class="clerk-request-actions"><button class="small-btn" type="button" data-center-action="detail" data-tab="lostposts" data-item-id="${item.approvalId}">ดูรายละเอียด</button><button class="approve-btn" type="button" data-center-action="approve" data-tab="lostposts" data-item-id="${item.approvalId}">อนุมัติเผยแพร่</button><button class="reject-btn" type="button" data-center-action="reject" data-tab="lostposts" data-item-id="${item.approvalId}">ไม่อนุมัติ</button></div></article>`;
            })
            .join("")
        : '<div class="empty">ไม่มีคำขอที่รออนุมัติ</div>';
      claimList.innerHTML = claims.length
        ? claims
            .map(
              (item) =>
                `<article class="clerk-request-card"><div class="clerk-request-top"><div><span class="approval-type claims">คำขอแสดงความเป็นเจ้าของ</span><h4>${item.id} · ${escapeHtml(item.title)}</h4></div><span class="badge ${badgeClass(item.status)}">${escapeHtml(item.status)}</span></div><p>${escapeHtml(item.place)}</p><div class="clerk-request-meta"><span>ผู้ขอ: ${escapeHtml(item.requester || "ไม่ระบุชื่อ")}</span><span>ส่งคำขอ: ${escapeHtml(item.requestDate || "ไม่ระบุเวลา")}</span><span>สถานะการคืน: ${escapeHtml(item.returnStatus || "ไม่ทราบสถานะ")}</span><span>${escapeHtml(item.custody || "คำขอใหม่")}</span></div><div class="clerk-request-actions"><button class="small-btn" type="button" data-center-action="claim-detail" data-item-id="${item.id}">ดูรายละเอียดคำขอ</button></div></article>`,
            )
            .join("")
        : '<div class="empty">ไม่มีคำขอที่รออนุมัติ</div>';
      setClerkCenterView(currentClerkCenterView);
      renderClerkApprovalsOverview();
    }
    function renderLost() {
      if (!$("#lostGrid")) return;
      const entriesForView = (view) => {
        if (view === "all") return ["inventory", "lostposts", "claims"].flatMap(entriesForView);
        if (["approved", "rejected"].includes(view)) {
          return ["inventory", "lostposts", "claims"].flatMap((tab) =>
            lostSets[tab]
              .filter((item) => lostDecisionGroup(tab, item) === view)
              .map((item) => ({ item, tab })),
          );
        }
        const data =
          view === "claims"
            ? lostSets.claims.filter((item) => !["คืนของแล้ว", "ไม่ผ่านการตรวจสอบ"].includes(item.status))
            : lostSets[view].filter(
                (item) => approvalGroup(item.status) === "approved",
              );
        return data.map((item) => ({ item, tab: view }));
      };
      const historySearch = currentRole === "admin" ? appliedHistorySearch : "";
      const matchesSearch = ({ item }) =>
        !historySearch ||
        `${item.id} ${item.title} ${item.place} ${item.status} ${item.custody}`
          .toLowerCase()
          .includes(historySearch);
      const visibleEntries =
        entriesForView(currentLostTab).filter(matchesSearch);
      if (currentRole === "admin") {
        $$("#lostTabs [data-lost-count]").forEach((count) => {
          count.textContent = entriesForView(count.dataset.lostCount).filter(
            matchesSearch,
          ).length;
        });
      }
      renderClerkCenter();
      const emptyLabel =
        currentLostTab === "approved"
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
              const controls =
                tab === "claims"
                  ? `<div class="claim-controls"><button type="button" class="primary" data-lost-action="claim-detail" data-tab="claims" data-item-id="${i.id}">ดูรายละเอียดคำขอ</button></div>`
                  : `${note}<div class="lost-foot"><span class="custody">${i.custody}</span>${tab === "inventory" ? `<span class="badge progress">สถานะการคืน: ${escapeHtml(returnStatusForFoundItem(i))}</span>` : ""}<button class="small-btn" type="button" data-lost-action="detail" data-tab="${tab}" data-item-id="${i.id}">ดูรายละเอียด</button></div>`;
              const claimHint =
                tab === "claims"
                  ? '<div class="approval-note"><strong>รับคำขออัตโนมัติ:</strong> ธุรการไม่ต้องกดอนุมัติ สามารถตรวจรายละเอียด นัดหมาย และยืนยันการส่งคืนได้</div>'
                  : "";
              const sourceBadge = ["all", "approved", "rejected"].includes(
                currentLostTab,
              )
                ? `<span class="badge neutral lost-source-badge">${approvalTypeLabel(tab)}</span>`
                : "";
              const image = i.imageUrl
                ? `<div class="lost-image has-image"><img src="${escapeHtml(i.imageUrl)}" alt="รูป ${escapeHtml(i.title)}" loading="lazy" /></div>`
                : '<div class="lost-image"><svg class="icon"><use href="#i-box"/></svg></div>';
              return `<article class="lost-card" tabindex="0" data-lost-card="${
                i.id
              }">${image}<div class="lost-content">${sourceBadge}<span class="badge ${badgeClass(
                i.status,
              )}">${i.status}</span><h3>${i.id} · ${i.title}</h3><p>${
                i.place
              }</p>${claimHint}${controls}${decisionButtons(tab, i)}</div></article>`;
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
        isLostAnnouncement ? "อนุมัติเผยแพร่" : "อนุมัติ",
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
      const nextStatus =
        tab === "inventory" ? "อนุมัติรับฝาก" : "อนุมัติเผยแพร่";
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
        `เปลี่ยนสถานะเป็น “${nextStatus}”`,
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
        false,
      );
      if (currentRole === "admin")
        addNotification(
          "admin",
          `${id} อนุมัติแล้ว`,
          `Admin อนุมัติรายการ ${item.title}`,
          false,
        );
      renderLost();
      renderClerkCenter();
      renderMetrics();
      renderQueue();
      renderNotifications();
      currentLostTab = tab;
      if (item.backendId) await loadApprovedLostFoundItems();
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
          "เผยแพร่ประกาศของหายแล้ว",
        );
      } else {
        showSuccess(
          `${id} · ${item.title} ถูกเปลี่ยนสถานะเป็น “${nextStatus}” แล้ว`,
          "อนุมัติรายการของที่พบแล้ว",
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
          () => confirmClaimStatus(item, nextStatus),
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
        `เปลี่ยนจาก “${previous}” เป็น “${item.status}”`,
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
        false,
      );
    }
    function deleteLostRecord(tab, id) {
      if (currentRole !== "admin") {
        toast("เฉพาะ Admin เท่านั้นที่ลบรายการได้");
        return;
      }
      const index = lostSets[tab].findIndex((x) => x.id === id);
      if (index < 0) return;
      requestConfirmation("ยืนยันลบรายการ", `ลบรายการ ${id} หรือไม่?`, () => {
        const [record] = lostSets[tab].splice(index, 1);
        storeDeletedRecord("lost", record, tab, record.title);
        toast(`ลบรายการ ${id} แล้ว`);
        renderLost();
        renderMetrics();
        renderQueue();
        renderHistory();
      });
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
          : ["all", "เสร็จสิ้น", "ยังไม่เสร็จ"];
      select.innerHTML = base
        .map(
          (x) =>
            `<option value="${x}">${x === "all" ? currentRole === "clerk" ? "ทุกกิจกรรม" : "ทุกงาน" : x}</option>`,
        )
        .join("");
    }
    function inDateRange(date, from, to) {
      return (!from || date >= from) && (!to || date <= to);
    }
    async function loadMyTaskHistory() {
      if (currentRole === "clerk") {
        try {
          const records = await getPersonalLostFoundHistory();
          const ids = new Set(records.map(record => record.item_code));
          for (let index = workHistory.length - 1; index >= 0; index--) {
            if (workHistory[index].source === "clerk-server" ||
                (workHistory[index].actorId === signedInStaffId() && ids.has(workHistory[index].itemId))) {
              workHistory.splice(index, 1);
            }
          }
          workHistory.push(...records.map(record => {
            const parts = new Intl.DateTimeFormat("en-CA", {
              timeZone: "Asia/Bangkok", year: "numeric", month: "2-digit", day: "2-digit",
              hour: "2-digit", minute: "2-digit", hourCycle: "h23",
            }).formatToParts(new Date(record.created_at));
            const value = type => parts.find(part => part.type === type)?.value;
            return {uid: record.uid, source: "clerk-server", actorId: signedInStaffId(),
              staff: activeStaffName(), role: roleConfig[currentRole].label,
              itemId: record.item_code, backendId: record.item_id,
              tab: record.report_type === "found" ? "inventory" : "lostposts",
              title: record.title, category: record.report_type === "found" ? "ของที่รับฝาก" : "ประกาศตามหา",
              action: record.status === "approved" ? "อนุมัติ" : record.status === "rejected" ? "ไม่อนุมัติ" : "ปิดงาน",
              status: record.status === "approved" ? "อนุมัติแล้ว" : record.status === "rejected" ? "ไม่อนุมัติ" : "ปิดรายการแล้ว",
              detail: record.note || "ตรวจสอบและอนุมัติรายการแล้ว",
              date: `${value("year")}-${value("month")}-${value("day")}`,
              time: `${value("hour")}:${value("minute")}`, timestamp: new Date(record.created_at).getTime()};
          }));
          renderMyHistory();
        } catch (error) {
          if (await handleUnauthorizedResponse(error.status)) return;
          toast(error.message || "โหลดประวัติงานธุรการไม่สำเร็จ");
        }
        return;
      }
      if (!["housekeeper", "technician"].includes(currentRole)) return;
      const staffId = JSON.parse(localStorage.getItem("buildingCareStaff") || "null")?.id;
      if (!staffId) return;
      const jobs = roleJobs().filter((job) => job.backendId && job.assigneeId === staffId);
      const results = await Promise.allSettled(jobs.map(async (job) => {
        const result = job.type === "repair"
          ? await getRepairRequestHistory(job.backendId)
          : await getCleaningTaskHistory(job.backendId);
        try {
          const detail = job.type === "repair" ? await getRepairRequestDetail(job.backendId) : await getCleaningTaskDetail(job.backendId);
          job.historyPhotos = (detail.images || [])
            .filter(image => image.image_type === "after")
            .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
            .slice(0, 1);
        } catch (error) {
          job.historyPhotos = [];
          console.warn("Loading history photos failed:", error);
        }
        const rows = taskHistoryRows(job, result.history || [], {
          staff: activeStaffName(), role: roleConfig[currentRole].label,
          statusLabels: job.type === "repair" ? repairStatusLabels : cleaningStatusLabels,
        });
        for (let index = workHistory.length - 1; index >= 0; index--) {
          if (workHistory[index].itemId === job.id) workHistory.splice(index, 1);
        }
        workHistory.push(...rows);
      }));
      for (const result of results) {
        if (result.status === "rejected") {
          if (await handleUnauthorizedResponse(result.reason.status)) return;
          console.error("Loading personal work history failed:", result.reason);
          toast("โหลดประวัติบางงานไม่สำเร็จ กรุณาเปิดหน้าประวัติอีกครั้ง");
          break;
        }
      }
      renderMyHistory();
      renderActivities();
      renderStaffOverview();
      renderMetrics();
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
      const own = workHistory.filter((x) => x.actorId ? x.actorId === signedInStaffId() : x.staff === staff),
        rows = own
          .filter(
            (x) =>
              inDateRange(x.date, from, to) &&
              (type === "all" || x.action === type) &&
              `${x.itemId} ${x.title} ${x.category} ${x.action} ${x.status} ${x.detail}`
                .toLowerCase()
                .includes(q),
          )
          .sort((a, b) =>
            `${b.date} ${b.time}`.localeCompare(`${a.date} ${a.time}`),
          );
      if (["housekeeper", "technician"].includes(currentRole)) {
        renderGroupedMyHistory(own, {from, to, type, q}, list, summary);
        return;
      }
      const closed = new Set(own.filter(
          (x) => ["ปิดงาน", "ปิดคำขอ"].includes(x.action),
        ).map((x) => x.itemId)).size,
        returned = own.filter((x) => x.action === "คืนงาน").length,
        decisions = own.filter((x) =>
          ["อนุมัติ", "ไม่อนุมัติ"].includes(x.action),
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
            }</span><strong>${v[0]}</strong><small>${v[2]}</small></article>`,
        )
        .join("");
      list.innerHTML = rows.length
        ? rows
            .map(
              (x) =>
                `<article class="work-history-card"><div class="work-history-date">${new Intl.DateTimeFormat(
                  "th-TH",
                  { dateStyle: "medium" },
                ).format(new Date(`${x.date}T00:00:00`))}<small>${
                  x.time
                } น.</small></div><div class="work-history-main"><div><span class="badge ${badgeClass(
                  x.action,
                )}">${x.action}</span> <span class="badge neutral">${
                  x.category
                }</span></div><h3>${x.itemId} · ${x.title}</h3><p>${escapeHtml(
                  x.detail,
                )}</p><div class="work-history-meta"><span class="badge ${badgeClass(
                  x.status,
                )}">${x.status}</span><span class="custody">บันทึกโดย ${
                  x.staff
                }</span></div></div><button class="small-btn" type="button" data-history-detail="${
                  x.itemId
                }">ดูรายละเอียด</button></article>`,
            )
            .join("")
        : '<div class="empty">ไม่พบประวัติงานในช่วงวันที่หรือตัวกรองที่เลือก</div>';
    }
    function renderGroupedMyHistory(own, filters, list, summary) {
      const groups = new Map();
      for (const entry of own) {
        if (!groups.has(entry.itemId)) groups.set(entry.itemId, []);
        groups.get(entry.itemId).push(entry);
      }
      const jobs = [...groups].map(([id, events]) => {
        events.sort((a,b) => `${a.date} ${a.time}`.localeCompare(`${b.date} ${b.time}`));
        const latest = events.at(-1);
        const job = allJobs.find(job => job.id === id);
        const completed = events.findLast(event => event.action === "ปิดงาน");
        const returned = events.findLast(event => event.action === "คืนงาน");
        const note = events.findLast(event => event.action === "เพิ่มหมายเหตุ");
        return {id, events, latest, job, completed, returned, note, status: job?.status || latest.status};
      });
      const counts = [
        [jobs.length, "งานทั้งหมด", "หนึ่งรายการต่อหนึ่งงาน"],
        [jobs.filter(job => job.status === "เสร็จสิ้น").length, "เสร็จสิ้น", "งานที่ปิดแล้ว"],
        [jobs.filter(job => job.returned).length, "คืนเข้ากองกลาง", "งานที่เคยคืนพร้อมเหตุผล"],
      ];
      summary.innerHTML = counts.map(([count,label,description]) => `<article class="metric"><span>${label}</span><strong>${count}</strong><small>${description}</small></article>`).join("");
      const dateLabel = event => event ? `${new Date(`${event.date}T00:00:00`).toLocaleDateString("th-TH")} ${event.time} น.` : "–";
      const rows = jobs.filter(({events,status,returned,latest,job}) =>
        events.some(event => inDateRange(event.date, filters.from, filters.to)) &&
        (filters.type === "all" || (filters.type === "เสร็จสิ้น" && status === "เสร็จสิ้น") || (filters.type === "คืนเข้ากองกลาง" && returned) || (filters.type === "ยังไม่เสร็จ" && !isTerminalStatus(status))) &&
        `${latest.itemId} ${latest.title} ${job?.room || ""} ${events.map(event => event.detail).join(" ")}`.toLowerCase().includes(filters.q)
      ).sort((a,b) => `${b.latest.date} ${b.latest.time}`.localeCompare(`${a.latest.date} ${a.latest.time}`));
      const mainRows = rows.filter(row => row.latest.action !== "คืนงาน" && filters.type !== "คืนเข้ากองกลาง");
      const mainMarkup = mainRows.length ? mainRows.map(({id,events,latest,job,status,completed,returned,note}) => `<article class="grouped-history-card">
        <header><div><span class="badge neutral">${escapeHtml(latest.category)}</span><h3>${escapeHtml(id)} · ${escapeHtml(latest.title)}</h3></div><span class="badge ${badgeClass(status)}">${escapeHtml(status)}</span></header>
        <div class="detail-meta"><div><small>สถานที่</small><strong>${escapeHtml(job?.room || "–")}</strong></div><div><small>วันที่รับงาน</small><strong>${dateLabel(events.find(event => event.action === "รับงาน"))}</strong></div><div><small>วันที่เสร็จ</small><strong>${dateLabel(completed)}</strong></div></div>
        ${note ? `<p class="history-note"><strong>หมายเหตุปิดงาน</strong><br>${escapeHtml(note.detail)}</p>` : ""}
        ${job?.historyPhotos?.length ? `<div class="history-photos">${job.historyPhotos.map(photo => `<img src="${escapeHtml(photo.url)}" alt="รูปหลังดำเนินการ ${escapeHtml(latest.title)}" loading="lazy" />`).join("")}</div>` : ""}
        <details><summary>ดูลำดับเหตุการณ์</summary><div class="timeline">${events.filter(event => event.action !== "คืนงาน").map(event => `<div class="timeline-item"><span class="timeline-dot"></span><div><strong>${escapeHtml(event.action)}</strong><small>${dateLabel(event)} · ${escapeHtml(event.staff)}</small><p>${escapeHtml(event.detail)}</p></div></div>`).join("")}</div></details>
      </article>`).join("") : '<div class="empty">ไม่พบประวัติงานที่ตรงกับตัวกรอง</div>';
      const returns = own.filter(event => event.action === "คืนงาน" &&
        inDateRange(event.date, filters.from, filters.to) &&
        ["all", "คืนเข้ากองกลาง"].includes(filters.type) &&
        `${event.itemId} ${event.title} ${event.detail}`.toLowerCase().includes(filters.q)
      ).sort((a,b) => `${b.date} ${b.time}`.localeCompare(`${a.date} ${a.time}`));
      const returnMarkup = returns.length ? returns.map(event => `<article class="grouped-history-card"><header><div><span class="badge wait">คืนเข้ากองกลาง</span><h3>${escapeHtml(event.itemId)} · ${escapeHtml(event.title)}</h3></div></header><p>คืนเมื่อ ${dateLabel(event)} · ${escapeHtml(event.staff)}</p><p class="history-note"><strong>เหตุผลในการคืนงาน</strong><br>${escapeHtml(event.detail)}</p></article>`).join("") : '<div class="empty">ไม่มีประวัติคืนงานที่ตรงกับตัวกรอง</div>';
      list.innerHTML = currentHistoryTab === "returns"
        ? `<section class="history-group"><h3>ประวัติคืนเข้ากองกลาง</h3>${returnMarkup}</section>`
        : `<section class="history-group"><h3>ประวัติการทำงาน</h3>${mainMarkup}</section>`;
    }
    function activeWorkCountForStaff(staff) {
      const jobs = allJobs.filter(
        (j) => j.assignee === staff.name && !isTerminalStatus(j.status),
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
                !["คืนของแล้ว", "ไม่ผ่านการตรวจสอบ"].includes(i.status),
            ).length
          : 0;
      return jobs + lost;
    }
    function latestHistoryFor(staffName, from = "", to = "") {
      return workHistory
        .filter((x) => x.staff === staffName && inDateRange(x.date, from, to))
        .sort((a, b) =>
          `${b.date} ${b.time}`.localeCompare(`${a.date} ${a.time}`),
        )[0];
    }
    function staffOverviewStats(staff, from = "", to = "") {
      const rows = workHistory.filter(
        (x) => x.staff === staff.name && inDateRange(x.date, from, to),
      );
      const closedItems = new Set(
        rows
          .filter(
            (x) =>
              ["ปิดงาน", "ปิดคำขอ"].includes(x.action) ||
              isTerminalStatus(x.status),
          )
          .map((x) => x.itemId),
      );
      const returnedItems = new Set(
        rows.filter((x) => x.action === "คืนงาน").map((x) => x.itemId),
      );
      return {
        active: activeWorkCountForStaff(staff),
        closed: closedItems.size,
        returned: returnedItems.size,
        latest: latestHistoryFor(staff.name, from, to),
      };
    }
    async function loadStaffWorkOverview() {
      if (currentRole !== "admin") return;
      const request = ++overviewRequest;
      const summary = $("#staffOverviewSummary");
      const table = $("#staffOverviewTable");
      if (summary) summary.innerHTML = '<div class="history-empty overview-state" role="status">กำลังโหลดสถิติงาน…</div>';
      if (table) table.innerHTML = '<div class="history-empty overview-state" role="status">กำลังโหลดรายชื่อเจ้าหน้าที่…</div>';
      try {
        const result = await fetchStaffWorkOverview({
          role: $("#overviewRoleFilter")?.value || "all",
          search: $("#overviewSearch")?.value || "",
        });
        if (request !== overviewRequest) return;
        overviewData = result;
        renderStaffOverview();
      } catch (error) {
        if (request !== overviewRequest) return;
        overviewData = null;
        if (await handleUnauthorizedResponse(error.status)) return;
        console.error("Loading staff work overview failed:", error);
        if (summary) summary.innerHTML = '<div class="history-empty overview-state" role="alert">ไม่สามารถโหลดสถิติงานได้ <button type="button" class="overview-retry" data-overview-retry="summary">ลองใหม่</button></div>';
        if (table) table.innerHTML = '<div class="history-empty staff-overview-empty overview-state">ยังไม่สามารถแสดงข้อมูลเจ้าหน้าที่ได้</div>';
      }
    }
    function renderStaffOverview() {
      const table = $("#staffOverviewTable");
      const summary = $("#staffOverviewSummary");
      if (!table || !summary || !overviewData) return;
      const { staff, summary: counts } = overviewData;
      summary.innerHTML = [
        [counts.unassigned, "งานที่ยังไม่มีผู้รับผิดชอบ", "คิวงานแม่บ้านและช่าง"],
        [counts.current_assigned, "กำลังรับผิดชอบ", "งานที่ยังไม่เสร็จของทีมที่แสดง"],
        [counts.closed, "ปิดแล้ว", "จำนวนงานที่เจ้าหน้าที่ปิด"],
        [counts.returned, "คืนเข้ากองกลาง", "จำนวนงานที่เจ้าหน้าที่คืน"],
      ].map(([value, label, description], index) =>
        `<article class="metric ${index === 3 ? "warn" : ""}"><span>${label}</span><strong>${value}</strong><small>${description}</small></article>`
      ).join("");
      table.innerHTML = staff.length
        ? staff.map((person) => {
          const role = person.role === "housekeeper" ? "แม่บ้าน" : "ช่าง";
          return `<article class="staff-overview-card">
            <header class="staff-overview-card-head">
              <div class="overview-staff-name">
                ${staffRoleAvatar(person.role, true)}
                <div><strong>${escapeHtml(person.full_name)}</strong><small>${escapeHtml(person.email)}</small></div>
              </div>
              <span class="badge overview-role-badge" style="--badge-role:${staffRoleColor(person.role)}">${role}</span>
            </header>
            <div class="staff-overview-card-stats">
              <div><span>กำลังรับผิดชอบ</span><strong>${person.counts.current_assigned}</strong></div>
              <div><span>ปิดแล้ว</span><strong>${person.counts.closed}</strong></div>
              <div><span>คืนเข้ากองกลาง</span><strong>${person.counts.returned}</strong></div>
            </div>
            <footer class="staff-overview-card-foot">
              <button class="small-btn" type="button" data-staff-overview="${person.id}">ดูสถิติรายบุคคล</button>
            </footer>
          </article>`;
        }).join("")
        : `<div class="history-empty staff-overview-empty overview-state" role="status">${$("#overviewRoleFilter")?.value !== "all" || $("#overviewSearch")?.value.trim() ? "ไม่พบเจ้าหน้าที่ที่ตรงกับตัวกรอง" : "ยังไม่มีเจ้าหน้าที่แม่บ้านหรือช่างในระบบ"}</div>`;
    }
    function overviewWorkItemMarkup(item, owner = "") {
      const statuses = item.request_type === "cleaning" ? cleaningStatusLabels : repairStatusLabels;
      const type = item.request_type === "cleaning" ? "งานทำความสะอาด" : "งานซ่อม";
      return `<article class="overview-detail-item"><div><strong>${escapeHtml(item.request_code)}</strong></div><div><strong>${escapeHtml(item.title)}</strong><p>${type}${owner ? ` · ${escapeHtml(owner)}` : ""}</p></div><span class="badge neutral">${escapeHtml(statuses[item.status] || item.status)}</span></article>`;
    }
    async function showStaffOverview(staffId, trigger) {
      const person = overviewData?.staff.find((item) => item.id === staffId);
      if (!person) return;
      selectedOverviewStaff = staffId;
      $("#overviewDetailTitle").textContent = `สถิติรายบุคคล · ${person.full_name}`;
      $("#overviewDetailEmail").textContent = person.email;
      $("#overviewPersonStats").innerHTML = [
        ["กำลังรับผิดชอบ", person.counts.current_assigned],
        ["ปิดแล้ว", person.counts.closed],
        ["คืนเข้ากองกลาง", person.counts.returned],
      ].map(([label, value]) => `<div><span>${label}</span><strong>${value}</strong></div>`).join("");
      $("#overviewDetailCount").textContent = "กำลังโหลด…";
      $("#staffOverviewDetail").innerHTML = '<div class="empty overview-state" role="status">กำลังโหลดงานปัจจุบัน…</div>';
      $("#staffOverviewReturned").innerHTML = '<div class="empty" role="status">กำลังโหลดประวัติคืนงาน…</div>';
      openModal("staffOverviewModal", trigger);
      try {
        const result = await fetchStaffCurrentWork(staffId);
        if (selectedOverviewStaff !== staffId || !$("#staffOverviewModal")?.classList.contains("open")) return;
        $("#overviewDetailCount").textContent = `${result.current_work_count} รายการ`;
        $("#staffOverviewReturned").innerHTML = result.returned_work?.length
          ? result.returned_work.map((item) => `<article class="overview-detail-item"><div><strong>${escapeHtml(item.request_code)}</strong><p>${escapeHtml(item.title)}</p><p>คืนโดย ${escapeHtml(item.returned_by)} · ${escapeHtml(new Date(item.returned_at).toLocaleString("th-TH", {timeZone: "Asia/Bangkok"}))}</p><p style="white-space:pre-wrap;overflow-wrap:anywhere">เหตุผล: ${escapeHtml(item.reason || "ไม่ได้ระบุเหตุผล")}</p></div><span class="badge neutral">ปัจจุบัน: ${escapeHtml((item.request_type === "cleaning" ? cleaningStatusLabels : repairStatusLabels)[item.status] || item.status)}</span></article>`).join("")
          : '<div class="empty">ไม่มีประวัติคืนงานเข้ากองกลาง</div>';
        $("#staffOverviewDetail").innerHTML = result.current_work.length
          ? result.current_work.map((item) => overviewWorkItemMarkup(item)).join("")
          : '<div class="empty">ไม่มีงานที่กำลังรับผิดชอบ</div>';
      } catch (error) {
        if (selectedOverviewStaff !== staffId) return;
        if (await handleUnauthorizedResponse(error.status)) return;
        $("#overviewDetailCount").textContent = "ไม่สามารถโหลดได้";
        $("#staffOverviewReturned").innerHTML = '<div class="empty" role="alert">ไม่สามารถโหลดประวัติคืนงานได้ กรุณากดลองใหม่ด้านบน</div>';
        $("#staffOverviewDetail").innerHTML = '<div class="empty overview-state" role="alert">ไม่สามารถโหลดงานปัจจุบันได้ <button type="button" class="overview-retry" data-overview-retry="staff-work">ลองใหม่</button></div>';
      }
    }
    function renderHistory() {
      if ($("#historyLostSection")) renderLost();
    }
    function restoreDeleted(uid) {
      const index = deletedRecords.findIndex((x) => x.uid === uid);
      if (index < 0) return;
      const item = deletedRecords[index];
      if (item.collectionKey === "allJobs") allJobs.unshift(item.record);
      else if (item.collectionKey === "staffData")
        staffData.unshift(item.record);
      else if (lostSets[item.collectionKey])
        lostSets[item.collectionKey].unshift(item.record);
      deletedRecords.splice(index, 1);
      addAudit(
        item.source,
        "กู้คืน",
        item.itemId,
        item.title,
        "กู้คืนรายการจาก Soft Delete",
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
            "นำข้อมูลออกจากรายการ Soft Delete",
          );
          toast(`ลบ ${item.itemId} ถาวรแล้ว`);
          renderHistory();
        },
      );
    }

    // -------------------------------------------------------------------------
    // 9) ระบบ Notification
    // -------------------------------------------------------------------------

    // โหลด notification ของบัญชีที่ login จาก Backend แล้วแปลงให้ตรงกับ UI
    async function loadStaffNotifications() {
      try {
        const notifications = await getStaffNotifications();
        notificationSets[currentRole] = notifications.map((notification) => ({
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
          }));
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
      [$("#notificationCount"), $("#mobileNotificationCount"), $("#mobileAdminNotificationCount")].forEach(
        (badge) => {
          if (!badge) return;
          badge.textContent = visibleCount;
          badge.hidden = unreadCount === 0;
          badge.style.display = unreadCount > 0 ? "grid" : "none";
          badge.setAttribute(
            "aria-label",
            `${unreadCount} การแจ้งเตือนที่ยังไม่ได้อ่าน`,
          );
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

      $("#mobileNotificationAdmin")?.setAttribute(
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
      const notificationPage = $("#page-notifications");
      notificationPage?.classList.toggle(
        "housekeeper-notifications",
        currentRole === "housekeeper",
      );
      notificationPage?.classList.toggle(
        "technician-notifications",
        currentRole === "technician",
      );
      notificationPage?.classList.toggle(
        "clerk-notifications",
        currentRole === "clerk",
      );
      const approvals = currentRole === "clerk" ? pendingApprovalRequests() : [];
      const claims = currentRole === "clerk" ? activeClaimNotifications() : [];
      const unread =
        list.filter((n) => n.unread).length +
        approvals.length +
        claims.filter((n) => n.unread).length;
      $("#notificationTitle").textContent = "ศูนย์การแจ้งเตือน";
      $("#notificationSummaryTitle").textContent =
        currentRole === "clerk"
          ? "การแจ้งเตือนของธุรการ"
          : `การแจ้งเตือนของ${roleConfig[currentRole].label}`;
      updateUnreadNotificationCount(unread);
      if (!list.length && !approvals.length && !claims.length) {
        $("#notificationList").innerHTML =
          '<div class="notification-empty">ไม่มีการแจ้งเตือน</div>';
        return;
      }
      let clerkHtml = "";
      if (approvals.length)
        clerkHtml +=
          `<div class="notification-group-label">คำร้องใหม่ · ${approvals.length}</div>` +
          approvals
            .map(
              (item) =>
                `<button type="button" class="notification-item unread" data-clerk-notification-target="approval" data-item-id="${item.approvalId}"><div class="notification-symbol"><svg class="icon"><use href="#i-box"/></svg></div><div><span class="approval-type ${item.tab}">${approvalTypeLabel(item.tab)}</span><strong>${item.approvalId} · ${escapeHtml(item.title)}</strong><p>${escapeHtml(item.text)}</p><small>กดเพื่อไปที่ศูนย์รับงาน</small></div></button>`,
            )
            .join("");
      if (claims.length)
        clerkHtml +=
          `<div class="notification-group-label">คำขอรับของ · ${claims.length}</div>` +
          claims
            .map(
              (item) =>
                `<button type="button" class="notification-item ${item.unread ? "unread" : ""}" data-clerk-notification-target="claim" data-item-id="${item.id}"><div class="notification-symbol"><svg class="icon"><use href="#i-user"/></svg></div><div><span class="approval-type claims">คำขอรับของ</span><strong>${item.id} · ${escapeHtml(item.title)}</strong><p>${escapeHtml(item.place)}</p><small>กดเพื่อไปที่ศูนย์รับงาน</small></div></button>`,
            )
            .join("");
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
                  }"><div class="notification-symbol"><svg class="icon"><use href="${
                    currentRole === "technician"
                      ? "#i-tools"
                      : currentRole === "housekeeper"
                        ? "#i-broom"
                        : "#i-bell"
                  }"/></svg></div><div class="notification-item-content"><div class="notification-item-heading"><span class="notification-kind">${
                    currentRole === "technician"
                      ? "งานซ่อม"
                      : currentRole === "housekeeper"
                        ? "งานทำความสะอาด"
                        : "อัปเดต"
                  }</span><time>${escapeHtml(n.time)}</time></div><strong>${escapeHtml(
                    n.title
                  )}</strong><p>${escapeHtml(
                    n.text
                  )}</p><div class="notification-actions"><span class="notification-open-action">เปิดรายละเอียด</span><span class="notification-hide-action" data-hide-notification="${
                    n.id
                  }">ซ่อน</span></div></div></button>`
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
      if (currentRole === "clerk")
        lostSets.claims
          .filter((item) => !["คืนของแล้ว", "ไม่ผ่านการตรวจสอบ"].includes(item.status))
          .forEach((item) => readClaimNotifications.add(item.id));
      renderNotifications();
      toast("ทำเครื่องหมายว่าอ่านทั้งหมดแล้ว");
    }

    // -------------------------------------------------------------------------
    // 10) ระบบจัดการบัญชี Staff
    // -------------------------------------------------------------------------

    // แสดงตารางบัญชีและ action ที่ผู้ดูแลระบบสามารถดำเนินการได้
    function renderStaff() {
      if (!$("#staffTable")) return;
      const roleLabels = {
        admin: "แอดมิน",
        clerk: "ธุรการ",
        housekeeper: "แม่บ้าน",
        technician: "ช่าง",
      };
      const selectedRole = $("#staffRoleFilter")?.value || "all";
      const query = ($("#staffAccountSearch")?.value || "")
        .trim()
        .toLowerCase();
      const visibleStaff = staffData
        .map((staff, index) => ({ staff, index }))
        .filter(({ staff }) => {
          const matchesRole =
            selectedRole === "all" || staff.role === roleLabels[selectedRole];
          const searchable = `${staff.name} ${staff.role}`.toLowerCase();
          return matchesRole && searchable.includes(query);
        });
      $("#staffTable").innerHTML = visibleStaff.length
        ? visibleStaff.map(({ staff: s, index: i }) => {
          const invitationDelivery = s.isActivated ? { label: "เปิดใช้งานแล้ว", className: "done" } : {
            sent: { label: "ส่งสำเร็จ", className: "done" },
            failed: { label: "ส่งไม่สำเร็จ", className: "danger" },
            pending: { label: "กำลังส่ง", className: "neutral" },
            unknown: { label: "ไม่มีข้อมูล", className: "neutral" },
          }[s.invitationDeliveryStatus] || {
            label: "ไม่มีข้อมูล",
            className: "neutral",
          };
          return `<article class="staff-account-card">
            <header class="staff-account-card-head">
              <div class="person"><div class="person-avatar" style="background:${
            staffRoleColor(s.role)
          }18;color:${staffRoleColor(s.role)}">${s.name.slice(
            0,
            2
          ) ? escapeHtml(s.name.slice(0, 2)) : "-"}</div><div><strong>${escapeHtml(s.name)}</strong><small>${
            escapeHtml(s.email)
            
          }</small></div></div>
          
              <span class="badge ${
            s.status === "ใช้งาน" ? "done" : "wait"
          }">${
            s.status
          }</span>
            </header>
            <div class="staff-account-meta">
              <div><span>Role</span><strong>${escapeHtml(s.role)}</strong></div>
              <div><span>สถานะการส่งคำเชิญ</span><strong class="invitation-delivery-status ${invitationDelivery.className}">${invitationDelivery.label}</strong></div>
            </div>
            <button class="small-btn resend-invitation-button" type="button" data-staff-action="resend-invitation" data-staff-index="${i}">ส่งคำเชิญซ้ำ</button>
            <footer class="staff-account-actions"><button class="small-btn" type="button" data-staff-action="detail" data-staff-index="${i}">ดูรายละเอียด</button><button class="small-btn" type="button" data-staff-action="edit" data-staff-index="${i}">แก้ไขข้อมูล</button><button class="small-btn" type="button" data-staff-action="toggle" data-staff-index="${i}">${
              s.status === "ใช้งาน" ? "ปิดบัญชี" : "เปิดใช้"
            }</button><button class="small-btn delete" type="button" data-staff-action="remove" data-staff-index="${i}">ลบ</button></footer>
          </article>`;
            })
            .join("")
        : '<div class="history-empty staff-account-empty">ไม่พบบัญชี Staff ที่ตรงกับตัวกรอง</div>';
      $("#staffTotal").textContent = staffData.length;
      $("#staffActiveTotal").textContent = `ใช้งาน ${
        staffData.filter((staff) => staff.status === "ใช้งาน").length
      } บัญชี`;
      $("#housekeeperTotal").textContent = staffData.filter(
        (staff) => staff.role === "แม่บ้าน",
      ).length;
      $("#technicianTotal").textContent = staffData.filter(
        (staff) => staff.role === "ช่าง",
      ).length;
      $("#clerkTotal").textContent = staffData.filter(
        (staff) => staff.role === "ธุรการ",
      ).length;
      $("#adminTotal").textContent = staffData.filter(
        (staff) => staff.role === "แอดมิน"
      ).length;
    }
    function openEditStaff(index, trigger = document.activeElement) {
      const staff = staffData[index];
      if (!staff || currentRole !== "admin") return;
      $("#editStaffIndex").value = staff.id;
      $("#editStaffName").value = staff.name;
      $("#editStaffEmail").value = staff.email;
      $("#editStaffRole").textContent = staff.role;
      $("#editStaffError").hidden = true;
      $("#editStaffButton").disabled = false;
      openModal("editStaffModal", trigger);
    }
    async function performStaffProfileUpdate(staff, changes) {
      const button = $("#editStaffButton");
      if (currentRole !== "admin" || button.disabled) return;
      // The confirmation dialog closes the edit modal; restore the retained form.
      if (!$("#editStaffModal").classList.contains("open")) openModal("editStaffModal");
      const errorMessage = $("#editStaffError");
      errorMessage.hidden = true;
      button.disabled = true;
      button.textContent = "กำลังบันทึก…";
      try {
        const account = await updateStaffProfile(staff.id, changes);
        const index = staffData.findIndex((item) => item.id === staff.id);
        if (index !== -1) staffData[index] = toUpdatedDashboardStaff(staff, account);
        const emailChanged = staff.email !== account.email;
        let signedIn;
        try {
          signedIn = JSON.parse(localStorage.getItem("buildingCareStaff") || "null");
        } catch {
          // A browser cache problem must not turn a successful API save into an error.
        }
        if (signedIn?.id === account.id) {
          try {
            localStorage.setItem("buildingCareStaff", JSON.stringify(account));
          } catch {
            // The saved profile can still be displayed when storage is unavailable.
          }
          currentUserName[currentRole] = account.full_name;
          roleConfig[currentRole].name = account.full_name;
          const headerName = $("#headerName");
          if (headerName) headerName.textContent = account.full_name.split(" ")[0];
          const profileName = $("#profileName");
          if (profileName) profileName.textContent = account.full_name;
          const profileEmail = $("#profileEmail");
          if (profileEmail) profileEmail.textContent = account.email;
        }
        addAudit("staff", "แก้ไข Staff", account.id, account.full_name,
          `แก้ไข ${Object.keys(changes).join(", ")}`);
        closeModal("editStaffModal", false);
        renderStaff();
        loadStaffWorkOverview();
        showSuccess(emailChanged
          ? "บันทึกอีเมลใหม่แล้ว กดส่งคำเชิญซ้ำเพื่อส่งลิงก์ตั้งรหัสผ่านไปยังอีเมลใหม่"
          : "บันทึกข้อมูล Staff แล้ว");
      } catch (error) {
        if (await handleUnauthorizedResponse(error.status)) return;
        errorMessage.textContent = error.status === 409
          ? "อีเมลนี้ถูกใช้แล้ว กรุณาใช้อีเมลอื่น"
          : error.status === 422
            ? "กรุณาตรวจสอบชื่อและอีเมลให้ถูกต้อง"
            : error.status === 403
              ? "เฉพาะ Admin เท่านั้นที่แก้ข้อมูล Staff ได้"
              : error.status === 404
                ? "ไม่พบบัญชี Staff นี้ กรุณาโหลดรายการใหม่"
                : "บันทึกไม่สำเร็จ กรุณาลองใหม่";
        errorMessage.hidden = false;
      } finally {
        button.disabled = false;
        button.textContent = "บันทึกข้อมูล";
      }
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
            `เปลี่ยนสถานะบัญชีเป็น ${staff.status}`,
          );
          renderStaff();
          toast("อัปเดตสถานะบัญชีแล้ว");
        },
      );
    }
    async function performResendStaffInvitation(index, button) {
      const staff = staffData[index];
      if (!staff || currentRole !== "admin") return;
      button.disabled = true;
      button.textContent = "กำลังส่ง…";
      try {
        const result = await resendStaffInvitation(staff.id);
        const delivered = result.email_sent === true;
        staff.invitationDeliveryStatus = delivered ? "sent" : "failed";
        staff.invitationStatusSource = "browser";
        rememberInvitationDelivery(staff, staff.invitationDeliveryStatus);
        addAudit(
          "staff",
          "ส่งคำเชิญซ้ำ",
          staff.id,
          staff.name,
          delivered ? "ส่งอีเมลสำเร็จ" : "ส่งอีเมลไม่สำเร็จ",
        );
        renderStaff();
        showSuccess(
          delivered
            ? `ส่งคำเชิญใหม่ไปยัง ${staff.email} แล้ว`
            : `ระบบสร้างคำเชิญใหม่แล้ว แต่ส่งไปยัง ${staff.email} ไม่สำเร็จ`,
          delivered ? "ส่งคำเชิญสำเร็จ" : "ส่งคำเชิญไม่สำเร็จ",
          delivered ? "success" : "error",
        );
      } catch (error) {
        if (await handleUnauthorizedResponse(error.status)) return;
        console.error("Resending staff invitation failed:", error);
        showSuccess(
          error.message === "Account has already been activated"
            ? "บัญชีนี้เปิดใช้งานแล้ว ใช้อีเมลปัจจุบันกับรหัสผ่านเดิมได้ หากลืมรหัสผ่านให้กดลืมรหัสผ่านที่หน้าเข้าสู่ระบบ"
            : error.status === 404
            ? "Backend ยังไม่รองรับการส่งคำเชิญซ้ำ"
            : error.message || "ไม่สามารถส่งคำเชิญซ้ำได้",
          "ส่งคำเชิญไม่สำเร็จ",
          "error",
        );
        if (document.contains(button)) {
          button.disabled = false;
          button.textContent = "ส่งคำเชิญซ้ำ";
        }
      }
    }
    function resendInvitation(index, button) {
      const staff = staffData[index];
      if (!staff || currentRole !== "admin") return;
      if (staff.isActivated) {
        showSuccess("บัญชีเปิดใช้งานแล้ว", "บัญชีเปิดใช้งานแล้ว");
        return;
      }
      requestConfirmation(
        "ยืนยันส่งคำเชิญซ้ำ",
        `ส่งคำเชิญและข้อมูลเข้าสู่ระบบชุดใหม่ไปยัง ${staff.email} หรือไม่?`,
        () => performResendStaffInvitation(index, button),
        "ส่งคำเชิญ",
      );
    }
    const deletingStaffIds = new Set();
    function removeStaff(i) {
      if (currentRole !== "admin") return;
      const staff = staffData[i];
      if (!staff || deletingStaffIds.has(staff.id)) return;
      requestConfirmation(
        "ยืนยันการลบบัญชีพนักงาน",
        `คุณต้องการลบบัญชี ${staff.name} (${staff.email}) หรือไม่? บัญชีนี้จะเข้าสู่ระบบไม่ได้อีก และจะหายไปจากรายการพนักงาน`,
        async () => {
          if (deletingStaffIds.has(staff.id)) return;
          deletingStaffIds.add(staff.id);
          try {
            await deleteStaffAccount(staff.id);
            const index = staffData.findIndex((item) => item.id === staff.id);
            if (index !== -1) staffData.splice(index, 1);
            forgetInvitationDelivery(staff.id);
            addAudit("staff", "ลบ", staff.id, staff.name, "ปิดบัญชี Staff แล้ว");
            renderStaff();
            renderHistory();
            loadStaffWorkOverview();
            showSuccess(
              `ลบบัญชี ${staff.name} (${staff.email}) เรียบร้อยแล้ว`,
              "ลบบัญชีสำเร็จ",
            );
          } catch (error) {
            if (await handleUnauthorizedResponse(error.status)) return;
            const assignments = error.unfinishedAssignments || [];
            const codes = assignments.map((item) => item.request_code).filter(Boolean);
            const message = codes.length
              ? `กรุณาโอนงานที่ยังไม่เสร็จก่อนลบบัญชี: ${codes.join(", ")}`
              : error.status === 404
                ? "ไม่พบบัญชีนี้ในระบบ กรุณาโหลดรายการพนักงานใหม่"
                : error.message === "You cannot delete your own account"
                ? "ไม่สามารถลบบัญชีของตัวเองได้"
                : error.message === "You cannot delete the last active administrator"
                  ? "ไม่สามารถลบบัญชีแอดมินที่ใช้งานอยู่คนสุดท้ายได้"
                  : error instanceof TypeError
                    ? "เชื่อมต่อระบบไม่ได้ กรุณาลองใหม่อีกครั้ง"
                    : error.message || "ไม่สามารถลบบัญชีเจ้าหน้าที่ได้";
            showSuccess(
              message,
              "ลบบัญชีไม่สำเร็จ",
              "error",
            );
          } finally {
            deletingStaffIds.delete(staff.id);
          }
        },
        "ลบบัญชี",
      );
    }

    // -------------------------------------------------------------------------
    // 11) ระบบจัดการสถานที่
    // -------------------------------------------------------------------------

    let selectedQrLocation = null;
    let qrLocations = [];

    // แปลงข้อมูลสถานที่จาก API เป็นรูปแบบที่หน้า Dashboard ใช้
    function toDashboardQrLocation(location) {
      return {
        id: String(location.id),
        name: location.area,
        floor: location.floor || "",
        token: location.qr_token,
        url: location.qr_url,
        createdAt: location.created_at,
        isActive: location.is_active,
      };
    }

    // โหลดรายการสถานที่ล่าสุดจาก Backend
    async function loadQrLocations() {
      if (currentRole !== "admin") return;
      try {
        const locations = await fetchAdminLocations();
        qrLocations = locations.map(toDashboardQrLocation);
        renderQrLocations();
      } catch (error) {
        if (await handleUnauthorizedResponse(error.status)) return;
        console.error("Loading QR locations failed:", error);
        toast(error.message || "ไม่สามารถโหลดรายการสถานที่ได้");
      }
    }

    function changeQrLocationStatus(location) {
      const nextActive = !location.isActive;
      const actionText = nextActive ? "เปิดใช้งาน" : "ปิดใช้งาน";
      requestConfirmation(
        `ยืนยัน${actionText}สถานที่`,
        `ต้องการ${actionText} ${location.name} และ QR Code ของสถานที่นี้หรือไม่?`,
        async () => {
          try {
            // บันทึกสถานะใหม่แล้วโหลดรายการทั้งหมดอีกครั้ง
            await setAdminLocationActive(location.id, nextActive);
            if (!nextActive && selectedQrLocation?.id === location.id)
              selectedQrLocation = null;
            await loadQrLocations();
            addAudit(
              "qr",
              `${actionText}สถานที่`,
              `LOCATION-${location.id}`,
              location.name,
              `${actionText}สถานที่ชั้น ${location.floor || "ไม่ระบุ"} และ QR Code`,
            );
            toast(`${actionText}สถานที่ ${location.name} แล้ว`);
          } catch (error) {
            if (await handleUnauthorizedResponse(error.status)) return;
            console.error("Updating QR location status failed:", error);
            toast(error.message || "ไม่สามารถเปลี่ยนสถานะสถานที่ได้");
          }
        },
        actionText,
      );
    }

    function renderQrFloorOptions() {
      const select = $("#qrFloorFilter");
      if (!select) return;
      const selected = select.value || "all";
      const floors = [
        ...new Set(
          qrLocations.map((location) => location.floor).filter(Boolean),
        ),
      ].sort((a, b) =>
        String(a).localeCompare(String(b), "th", { numeric: true }),
      );
      select.innerHTML = [
        '<option value="all">ทุกชั้น</option>',
        ...floors.map(
          (floor) =>
            `<option value="${escapeHtml(floor)}">ชั้น ${escapeHtml(floor)}</option>`,
        ),
      ].join("");
      select.value = floors.includes(selected) ? selected : "all";
    }

    function renderQrLocations() {
      const list = $("#roomList");
      if (!list) return;
      renderQrFloorOptions();
      const selectedFloor = $("#qrFloorFilter")?.value || "all";
      const query = ($("#qrLocationSearch")?.value || "").trim().toLowerCase();
      const visibleLocations = qrLocations.filter((location) => {
        const matchesFloor =
          selectedFloor === "all" || location.floor === selectedFloor;
        const searchable =
          `${location.name} ${location.floor || ""}`.toLowerCase();
        return matchesFloor && searchable.includes(query);
      });
      const count = $("#qrLocationCount");
      if (count) count.textContent = String(visibleLocations.length);
      if (!visibleLocations.length) {
        list.innerHTML = `
          <div class="qr-location-empty">
            <strong>${qrLocations.length ? "ไม่พบสถานที่" : "ยังไม่มีสถานที่"}</strong>
            <span>${
              qrLocations.length
                ? "ลองเปลี่ยนชั้นหรือคำค้นหา"
                : "กด “เพิ่มสถานที่ใหม่” เพื่อสร้าง QR Code รายการแรก"
            }</span>
          </div>`;
        return;
      }
      list.innerHTML = visibleLocations
        .map(
          (location) => `
            <article class="qr-location-item">
              <div class="qr-location-symbol" data-qr-preview="${escapeHtml(location.id)}" aria-label="QR Code ของ ${escapeHtml(location.name)}">QR</div>
              <div class="qr-location-copy">
                <div class="qr-location-title">
                  <strong>${escapeHtml(location.name)}</strong>
                  <span class="qr-status-badge ${location.isActive ? "is-active" : "is-inactive"}">
                    ${location.isActive ? "ใช้งาน" : "ปิดใช้งาน"}
                  </span>
                </div>
                <small>${location.floor ? `ชั้น ${escapeHtml(location.floor)} · ` : ""}${
                  location.url ? "พร้อมใช้งาน QR" : "ยังไม่ได้สร้าง QR"
                }</small>
              </div>
              <div class="qr-location-actions">
                <button
                  class="secondary"
                  type="button"
                  data-view-qr-location="${escapeHtml(location.id)}"
                  ${location.isActive ? "" : "disabled"}
                >${location.url ? "ดูรายละเอียด" : "สร้าง QR"}</button>
                <button
                  class="${location.isActive ? "danger" : "secondary"} qr-location-status-button"
                  type="button"
                  data-toggle-qr-location="${escapeHtml(location.id)}"
                  aria-label="${location.isActive ? "ปิด" : "เปิด"}ใช้งานสถานที่ ${escapeHtml(location.name)}"
                >${location.isActive ? "ปิดใช้งาน" : "เปิดใช้งาน"}</button>
              </div>
            </article>`,
        )
        .join("");
      // สร้างภาพ QR ขนาดย่อบนการ์ดของแต่ละพื้นที่
      list.querySelectorAll("[data-qr-preview]").forEach((box) => {
        const location = qrLocations.find(
          (item) => item.id === box.dataset.qrPreview,
        );
        if (!location?.url || !window.QRCode) return;
        box.innerHTML = "";
        new QRCode(box, {
          text: location.url,
          width: 54,
          height: 54,
          colorDark: location.isActive ? "#17202b" : "#94a3b8",
          colorLight: "#ffffff",
          correctLevel: QRCode.CorrectLevel.M,
        });
      });
    }
    function showQrLocation(location) {
      if (!location || !$("#qrCode")) return false;
      if (!location.isActive) {
        toast("สถานที่นี้ปิดใช้งานอยู่ กรุณาเปิดใช้งานก่อนดูรายละเอียด QR");
        return false;
      }
      if (!location.url) {
        toast("สถานที่นี้ยังไม่มี QR Code");
        return false;
      }
      if (!window.QRCode) {
        toast(
          "ยังโหลดตัวสร้าง QR ไม่สำเร็จ กรุณาลองใหม่เมื่อเชื่อมต่ออินเทอร์เน็ต",
        );
        return false;
      }
      selectedQrLocation = location;
      $("#qrRoomName").textContent = location.name;
      $("#qrRoomFloor").textContent = location.floor
        ? `ชั้น ${location.floor}`
        : "ไม่ระบุชั้น";
      const box = $("#qrCode");
      box.innerHTML = "";
      new QRCode(box, {
        text: location.url,
        width: 168,
        height: 168,
        colorDark: "#17202b",
        colorLight: "#ffffff",
        correctLevel: QRCode.CorrectLevel.M,
      });
      return true;
    }

    // -------------------------------------------------------------------------
    // 12) Modal, Sidebar และกล่องยืนยันส่วนกลาง
    // -------------------------------------------------------------------------

    // เปิด modal และจดจำ element ต้นทางเพื่อคืน focus เมื่อปิด
    function openModal(
      id,
      trigger = document.activeElement,
      historyMode = "push",
    ) {
      const modal = $(`#${id}`);
      if (!modal) return;
      $$(".modal.open").forEach((item) => closeModal(item.id, false));
      lastModalTrigger = trigger instanceof HTMLElement ? trigger : null;
      modal.classList.add("open");
      modal.removeAttribute("aria-hidden");
      document.body.classList.add("modal-open");
      if (historyMode !== "none") {
        // Replace the previous dialog so closing success cannot reopen its form.
        const mode = historyMode === "push" && readDashboardRoute().dialog
          ? "replace"
          : historyMode;
        updateDashboardRoute(id, mode);
      }
      requestAnimationFrame(() =>
        modal
          .querySelector(
            'input:not([type="hidden"]),select,textarea,button:not([disabled])',
          )
          ?.focus(),
      );
    }
    function closeModal(
      id,
      restoreFocus = true,
      updateHistory = restoreFocus,
    ) {
      const modal = $(`#${id}`);
      if (!modal) return;
      modal.classList.remove("open");
      modal.setAttribute("aria-hidden", "true");
      if (!$(".modal.open")) document.body.classList.remove("modal-open");
      if (
        restoreFocus &&
        lastModalTrigger &&
        document.contains(lastModalTrigger)
      )
        lastModalTrigger.focus();
      if (
        updateHistory &&
        !restoringNavigation &&
        readDashboardRoute().dialog === modalSlug(id)
      ) {
        router.back();
      }
    }
    function syncDashboardFromRoute() {
      const routeState = readDashboardRoute();
      const page = canRoleOpenPage(currentRole, routeState.page)
        ? routeState.page
        : STAFF_ROLE_PAGES[currentRole][0].id;

      restoringNavigation = true;
      $$(".modal.open").forEach((modal) =>
        closeModal(modal.id, false, false),
      );
      navigate(page, "none");
      let modalId = modalIdFromSlug(routeState.dialog);
      // A consumed confirmation cannot be restored from browser history.
      if (modalId === "confirmModal" && !pendingConfirmAction) modalId = "";
      if (modalId) openModal(modalId, document.activeElement, "none");
      restoringNavigation = false;

      return modalId || "";
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
      menuToggle.setAttribute(
        "aria-label",
        menuVisible ? "ปิดเมนู" : "เปิดเมนู",
      );
      menuToggle
        .querySelector("use")
        .setAttribute("href", menuVisible ? "#i-close" : "#i-menu");
    }
    function toggleSidebar() {
      if (window.matchMedia("(min-width: 981px)").matches) return;
      const open = !$("#sidebar").classList.contains("open");
      $("#sidebar").classList.toggle("open", open);
      $("#sidebarBackdrop").classList.toggle("open", open);
      updateMenuToggle(open);
    }
    function requestConfirmation(title, text, action, label = "ยืนยัน", historyMode = "push") {
      pendingConfirmAction = action;
      $("#confirmModalTitle").textContent = title;
      $("#confirmModalText").textContent = text;
      $("#confirmActionButton").textContent = label;
      $("#confirmActionButton").classList.toggle("confirm-accept", ["ยืนยันรับงาน", "ยืนยันคืนงาน"].includes(label) ||
        (currentRole === "clerk" && !/ลบ|ไม่อนุมัติ|ปฏิเสธ/.test(`${title} ${label}`)));
      openModal("confirmModal", document.activeElement, historyMode);
    }
    function showSuccess(message, title = "บันทึกสำเร็จ", variant = "success") {
      const successModal = $("#successModal");
      successModal?.classList.toggle("rejection-result", variant === "error");
      successModal
        ?.querySelector(".success-check use")
        ?.setAttribute("href", variant === "error" ? "#i-close" : "#i-check");
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
          `${staff.name} ${staff.zone}`.toLowerCase().includes(query),
      );
      $("#assignStaffList").innerHTML = options.length
        ? options
            .map((staff) => {
              const stats = staffOverviewStats(staff);
              return `<button type="button" class="staff-choice ${
                $("#assignStaff").value === staff.name ? "selected" : ""
              }" data-assign-staff="${escapeHtml(
                staff.name,
              )}"><span><strong>${escapeHtml(
                staff.name,
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
        ["สถานะปัจจุบัน", job.backendId && ["cleaning", "repair"].includes(job.type)
          ? requestStatusPresentation({ request_type: job.type, status: job.backendStatus }, job.id).label
          : job.status],
      ];
      return steps
        .map(
          (step) =>
            `<div class="timeline-item"><span class="timeline-dot"></span><div><strong>${escapeHtml(
              step[0],
            )}</strong><small>${escapeHtml(step[1])}</small></div></div>`,
        )
        .join("");
    }
    function renderJobDetailProgress(job) {
      const container = $("#jobDetailProgress");
      const list = $("#jobDetailProgressSteps");
      if (!container || !list) return;
      const supported = ["waiting", "assigned", "received", "in_progress", "completed"];
      const show = job.backendId && ["cleaning", "repair"].includes(job.type) && supported.includes(job.backendStatus);
      container.hidden = !show;
      const timeline = $("#jobTimeline");
      if (timeline) timeline.hidden = show;
      if (!show) {
        list.replaceChildren();
        return;
      }
      const request = { request_type: job.type, status: job.backendStatus };
      const presentation = requestStatusPresentation(request, job.id);
      const progress = serviceProgress(request, job.id);
      $("#jobDetailProgressText").textContent = presentation.description;
      list.innerHTML = progress.steps.map((step, index) => {
        const state = index < progress.currentIndex ? "complete" : index === progress.currentIndex ? "current" : "upcoming";
        const marker = index < progress.currentIndex ? "✓" : String(index + 1);
        return `<li class="${state}"${index === progress.currentIndex ? ' aria-current="step"' : ""}><span class="job-detail-progress-marker" aria-hidden="true">${marker}</span><span>${escapeHtml(step.label)}</span></li>`;
      }).join("");
    }
    function renderJobQuickActions(job) {
      const isMine = job.assignee === activeStaffName(),
        canEdit = isMine || currentRole === "admin",
        buttons = [];
      if (!job.assignee && !isTerminalStatus(job.status) && currentRole !== "admin")
        buttons.push(["accept", "รับงาน", "primary-action"]);
      if (!job.assignee && !isTerminalStatus(job.status) && currentRole === "admin")
        buttons.push(["assign", "มอบหมายงาน", "primary-action"]);
      if (canEdit && !isTerminalStatus(job.status)) {
        const backendNext = job.backendId
          ? job.type === "repair"
            ? nextRepairStatus(job)
            : nextCleaningStatus(job)
          : null;
        if (job.backendId && ["cleaning", "repair"].includes(job.type)) {
          if (backendNext) {
            buttons.push([
              "status",
              "อัปเดตสถานะ",
              "primary-action",
            ]);
          }
        } else {
          buttons.push(
            ["start", "เริ่มดำเนินการ", "primary-action"],
            ["status", "อัปเดตสถานะ", ""],
            ["complete", "เสร็จสิ้น", ""],
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
                `<button type="button" class="quick-action ${item[2]}" data-detail-action="${item[0]}">${item[1]}</button>`,
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
          job.updatedAt = new Date(detail.updated_at).toLocaleString("th-TH");
          job.requestImageUrl =
            detail.images?.find((image) => image.image_type === "after")?.url ||
            detail.images?.[0]?.url ||
            "";
        } catch (error) {
          if (await handleUnauthorizedResponse(error.status)) return;
          console.error("Loading repair request detail failed:", error);
          toast(error.message || "ไม่สามารถโหลดรายละเอียดงานซ่อมได้");
          return;
        }
      }
      if (job.type === "cleaning" && job.backendId && currentRole === "housekeeper") {
        try {
          const detail = await getCleaningTaskDetail(job.backendId);
          job.detail = detail.description;
          job.room = repairLocation(detail.location);
          job.reporterContact = detail.reporter_email;
          job.backendStatus = detail.status;
          job.status = cleaningStatusLabels[detail.status] || detail.status;
          job.updatedAt = new Date(detail.updated_at).toLocaleString("th-TH");
          job.requestImageUrl = detail.images?.[0]?.url || job.requestImageUrl || "";
        } catch (error) {
          if (await handleUnauthorizedResponse(error.status)) return;
          console.error("Loading cleaning task detail failed:", error);
          toast(
            error.status === 404
              ? "งานนี้ถูกรับไปแล้วหรือไม่อยู่ในรายการของคุณ"
              : error.message || "ไม่สามารถโหลดรายละเอียดงานทำความสะอาดได้",
          );
          if (error.status === 404) await loadCleaningTasks();
          return;
        }
      }
      selectedJobId = id;
      $("#jobDetailModal")?.classList.remove("lost-post-detail");
      $("#jobDetailCode").textContent = `${id} · ${job.category}`;
      $("#jobDetailTitle").textContent = job.title;
      $("#jobDetailDescription").textContent = job.detail || "ผู้แจ้งไม่ได้ระบุรายละเอียดเพิ่มเติม";
      $("#jobDetailRoom").textContent = job.room;
      $("#jobDetailReporter").textContent = job.reporter;
      $("#jobDetailContact").textContent =
        job.reporterContact || "ติดต่อผ่านระบบ CS Building Care";
      $("#jobDetailAssignee").textContent =
        assignedCleanerLabel(job);
      $("#jobDetailAssignee").classList.toggle("is-unassigned", !job.assignee);
      [
        ["#jobDetailRoomLabel", "สถานที่"],
        ["#jobDetailReporterLabel", "ผู้แจ้ง"],
        ["#jobDetailContactLabel", "ติดต่อ"],
        ["#jobDetailAssigneeLabel", "ผู้รับผิดชอบ"],
      ].forEach(([selector, label]) => {
        const element = $(selector);
        if (element) element.textContent = label;
      });
      const returnStatusGroup = $("#jobDetailReturnStatusGroup");
      if (returnStatusGroup) returnStatusGroup.hidden = true;
      const servicePresentation = job.backendId && ["cleaning", "repair"].includes(job.type)
        ? requestStatusPresentation({ request_type: job.type, status: job.backendStatus }, job.id)
        : null;
      $("#jobDetailBadges").innerHTML = `<span class="badge ${
        job.priority === "เร่งด่วน" ? "danger" : "normal"
      }">${job.priority}</span><span class="badge ${badgeClass(job.status)}">${
        escapeHtml(servicePresentation?.label || job.status)
      }</span><span class="badge neutral">${escapeHtml(job.updatedAt || job.time)}</span>`;
      renderJobDetailProgress(job);
      $("#jobDetailIcon use").setAttribute(
        "href",
        job.type === "repair" ? "#i-tools" : "#i-broom",
      );
      const detailImage = $("#jobDetailImage");
      const detailIcon = $("#jobDetailIcon");
      if (detailImage) {
        detailImage.onerror = () => {
          detailImage.hidden = true;
          if (detailIcon) detailIcon.removeAttribute("hidden");
        };
      }
      if (detailImage && (job.completionPhotoUrl || job.requestImageUrl)) {
        detailImage.src = job.completionPhotoUrl || job.requestImageUrl;
        detailImage.alt = `${job.completionPhotoUrl ? "รูปหลังดำเนินการ" : "รูปประกอบคำร้อง"} ${job.title}`;
        detailImage.hidden = false;
        if (detailIcon) detailIcon.setAttribute("hidden", "");
      } else {
        if (detailImage) {
          detailImage.hidden = true;
          detailImage.removeAttribute("src");
        }
        if (detailIcon) detailIcon.removeAttribute("hidden");
      }
      $("#jobTimeline").innerHTML = jobTimeline(job);
      $("#jobDetailNotes").textContent = job.note || "ยังไม่มีหมายเหตุ";
      renderJobQuickActions(job);
      openModal("jobDetailModal", trigger);

      // งานจริงที่รับแล้วสามารถโหลด timeline จาก Backend ได้
      if (job.backendId && job.assignee) {
        try {
          const result =
            job.type === "repair"
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
              (job.type === "repair"
                ? repairStatusLabels
                : cleaningStatusLabels)[entry.old_status] ||
              entry.old_status ||
              "เริ่มต้น"
            } → ${
              (job.type === "repair"
                ? repairStatusLabels
                : cleaningStatusLabels)[entry.new_status] ||
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
              (entry) => entry.action === "completion_note_added" && entry.note,
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

    // หางานจาก request_id ของการแจ้งเตือน ถ้ายังไม่มีในรายการให้โหลดจาก Backend ใหม่
    async function openCleaningRequestFromNotification(
      notification,
      trigger = document.activeElement,
    ) {
      if (!notification.requestId) return false;
      let job = allJobs.find((item) => item.backendId === notification.requestId);
      if (!job) {
        await loadCleaningTasks();
        job = allJobs.find((item) => item.backendId === notification.requestId);
      }
      if (!job) {
        toast("งานนี้ถูกรับไปแล้วหรือไม่อยู่ในรายการของคุณ");
        return true;
      }
      openJobDetail(job.id, trigger);
      return true;
    }
    function updateStatusFields() {
      const needsReason = ["พักงาน", "รอข้อมูลเพิ่มเติม", "ขอข้อมูลเพิ่มเติม", "ยกเลิก"].includes($("#newJobStatus")?.value);
      const note = $("#statusNote");
      if (note) {
        note.closest(".field").hidden = !needsReason;
        note.required = needsReason;
        if (!needsReason) note.value = "";
      }
      const image = $("#statusImage");
      if (image) {
        image.closest(".field").hidden = true;
        image.value = "";
      }
    }
    $("#newJobStatus")?.addEventListener("change", updateStatusFields);
    function openStatusUpdate(id, trigger = document.activeElement) {
      const job = allJobs.find((item) => item.id === id);
      if (!job) return;
      if (isTerminalStatus(job.status)) {
        toast("งานนี้สิ้นสุดแล้ว ดูรายละเอียดได้อย่างเดียว");
        return;
      }
      const backendNext = job.backendId
        ? job.type === "repair"
          ? nextRepairStatus(job)
          : nextCleaningStatus(job)
        : null;
      const canReturnToPool =
        ["housekeeper", "technician"].includes(currentRole) &&
        job.assignee === activeStaffName() &&
        !["completed", "cancelled"].includes(job.backendStatus);
      if (job.backendId && !backendNext && !canReturnToPool) {
        toast("ไม่มีสถานะถัดไปที่เปลี่ยนได้");
        return;
      }
      const serviceOptions = ["cleaning", "repair"].includes(job.type) && job.backendId
        ? serviceProgressStatuses
            .slice(serviceProgressStatuses.indexOf(job.backendStatus) + 1)
            .map((status) => (job.type === "repair" ? repairStatusLabels : cleaningStatusLabels)[status])
        : null;
      const options = serviceOptions || (backendNext
        ? [backendNext.label]
        : currentRole === "technician"
          ? ["กำลังดำเนินการ", "รอข้อมูลเพิ่มเติม", "เสร็จสิ้น"]
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
                ? ["กำลังดำเนินการ", "รอข้อมูลเพิ่มเติม", "เสร็จสิ้น"]
                : [
                    "กำลังดำเนินการ",
                    "พักงาน",
                    "รอข้อมูลเพิ่มเติม",
                    "เสร็จสิ้น",
                  ]);
      if (canReturnToPool) options.push("คืนเข้าคิวกลาง");
      $("#statusJobId").value = id;
      $("#newJobStatus").innerHTML = options
        .map((value) => `<option>${value}</option>`)
        .join("");
      const statusNote = $("#statusNote");
      if (statusNote) statusNote.value = "";
      updateStatusFields();
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
    function openCompleteModal(id, trigger = document.activeElement, historyMode = "push") {
      $("#completeJobId").value = id;
      $("#completeResult").value = "";
      $("#completeNote").value = "";
      $("#completeImage").value = "";
      resetCompletionPreview();
      $("#completeDate").value = todayISO();
      openModal("completeModal", trigger, historyMode);
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
          ? job.type === "repair"
            ? nextRepairStatus(job)
            : nextCleaningStatus(job)
          : null;
        const nextStatus = backendNext?.label || "กำลังดำเนินการ";
        requestConfirmation(
          "ยืนยันเริ่มดำเนินการ",
          `เปลี่ยนสถานะงาน ${job.id} เป็น “${nextStatus}” หรือไม่?`,
          async () => {
            const updated = await applyJobStatus(job, nextStatus, "อัปเดตจากหน้ารายละเอียดงาน");
            if (updated) updateDashboardRoute("", "replace");
          },
        );
        return;
      }
    }
    async function applyJobStatus(job, next, note) {
      const previous = job.status;
      const isBackendCleaning = job.type === "cleaning" && job.backendId;
      const isBackendRepair = job.type === "repair" && job.backendId;
      if (isBackendCleaning || isBackendRepair) {
        const transition = isBackendRepair
          ? nextRepairStatus(job)
          : nextCleaningStatus(job);
        const isBackendService = isBackendCleaning || isBackendRepair;
        const targetServiceStatus = isBackendService
          ? serviceProgressStatuses.find((status) =>
              (isBackendRepair ? repairStatusLabels : cleaningStatusLabels)[status] === next)
          : null;
        const currentServiceIndex = serviceProgressStatuses.indexOf(job.backendStatus);
        const targetServiceIndex = serviceProgressStatuses.indexOf(targetServiceStatus);
        if (
          !(isBackendService && targetServiceIndex > currentServiceIndex) &&
          (!transition || transition.label !== next) &&
          !(
            isBackendRepair &&
            next === "เสร็จสิ้น" &&
            job.backendStatus === "in_progress"
          )
        ) {
          toast("ไม่สามารถเปลี่ยนไปยังสถานะนี้ได้ กรุณาโหลดข้อมูลใหม่");
          return false;
        }
        try {
          let updatedTask;
          for (const status of serviceProgressStatuses.slice(currentServiceIndex + 1, targetServiceIndex + 1)) {
            updatedTask = isBackendRepair
              ? status === "completed"
                ? await completeRepairRequest(job.backendId)
                : await updateRepairRequestStatus(job.backendId, status)
              : await updateCleaningTaskStatus(job.backendId, status);
            job.backendStatus = updatedTask.status;
          }
          job.backendStatus = updatedTask.status;
          job.assignee = updatedTask.assigned_staff?.full_name || job.assignee;
          job.assigneeCode =
            updatedTask.assigned_staff?.staff_code || job.assigneeCode;
          job.assigneeId = updatedTask.assigned_staff?.id || job.assigneeId;
          next =
            (isBackendRepair ? repairStatusLabels : cleaningStatusLabels)[
              updatedTask.status
            ] || next;
        } catch (error) {
          if (await handleUnauthorizedResponse(error.status)) return false;
          console.error("Updating staff task status failed:", error);
          if (isBackendCleaning) await loadCleaningTasks();
          if (isBackendRepair) await loadRepairRequests();
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
        `${previous} → ${next}${note ? ` · ${note}` : ""}`,
      );
      addAudit(
        "jobs",
        next === "เสร็จสิ้น" ? "ปิดงาน" : "อัปเดตสถานะ",
        job.id,
        job.title,
        `เปลี่ยนจาก “${previous}” เป็น “${next}”`,
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
      if (job.backendStatus !== "completed") toast("บันทึกสถานะเรียบร้อย");
      return true;
    }

    // -------------------------------------------------------------------------
    // 14) Modal รายละเอียด Lost & Found และการนัดรับของ
    // -------------------------------------------------------------------------

    // โหลดรายละเอียดล่าสุดจาก Backend แล้วแสดงใน modal กลาง
    async function openLostDetail(tab, id, trigger = document.activeElement) {
      const item = lostSets[tab]?.find((record) => record.id === id);
      if (!item) return;
      if (item.backendId && currentRole === "clerk") {
        try {
          const detail =
            tab === "lostposts"
              ? await getLostItemDetail(item.backendId)
              : await getFoundItemDetail(item.backendId);
          item.privateVerificationDetail = detail.private_verification_detail || "";
          item.category = detail.item_category;
          item.description = detail.description || "ไม่มีรายละเอียดเพิ่มเติม";
          item.place = detail.location_detail || "ไม่ระบุสถานที่พบ";
          item.custody = detail.custody_location || "ไม่ระบุจุดรับฝาก";
          item.reporterEmail = detail.reporter_email;
          item.eventDatetime = detail.event_datetime;
          // ขอ signed URL ใหม่ทุกครั้งที่เปิด เพราะ URL จากรายการอาจหมดอายุแล้ว
          if (detail.images?.length) item.imageUrl = detail.images[0].url;
        } catch (error) {
          if (await handleUnauthorizedResponse(error.status)) return;
          console.error("Loading found item detail failed:", error);
          toast(error.message || "ไม่สามารถโหลดรายละเอียดได้");
          return;
        }
      }
      const privateGroup = $("#jobDetailPrivateGroup");
      if (privateGroup) privateGroup.hidden = !item.privateVerificationDetail;
      const privateText = $("#jobDetailPrivate");
      if (privateText) privateText.textContent = item.privateVerificationDetail || "";
      const notesGroup = $("#jobDetailNotesGroup");
      if (notesGroup) notesGroup.hidden = !item.decisionReason;
      const isLostAnnouncement = tab === "lostposts";
      selectedJobId = "";
      $("#jobDetailModal")?.classList.add("lost-post-detail");
      $("#jobDetailProgress")?.setAttribute("hidden", "");
      $("#jobTimeline")?.removeAttribute("hidden");
      $("#jobDetailCode").textContent = `${id} · ${isLostAnnouncement ? "ประกาศของหาย" : "ของที่พบ"}`;
      $("#jobDetailTitle").textContent = item.title;
      $("#jobDetailDescription").textContent = item.description || item.place;
      const roomLabel = $("#jobDetailRoomLabel");
      if (roomLabel)
        roomLabel.textContent = isLostAnnouncement
          ? "สถานที่คาดว่าหาย"
          : "สถานที่พบ";
      $("#jobDetailRoom").textContent = item.place;
      const reporterLabel = $("#jobDetailReporterLabel");
      if (reporterLabel)
        reporterLabel.textContent = isLostAnnouncement ? "ผู้แจ้งประกาศ" : "ผู้แจ้ง";
      const reporterEmail = item.reporterEmail || "";
      $("#jobDetailReporter").textContent = reporterEmail || "อีเมลของผู้แจ้ง";
      const contactLabel = $("#jobDetailContactLabel");
      if (contactLabel) contactLabel.textContent = "ช่องทางติดต่อ";
      $("#jobDetailContact").textContent = reporterEmail || "อีเมลของผู้แจ้ง";
      const assigneeLabel = $("#jobDetailAssigneeLabel");
      if (assigneeLabel) assigneeLabel.textContent = "ผู้ตรวจสอบ";
      $("#jobDetailAssignee").classList.remove("is-unassigned");
      const reviewerName = item.reviewerName ||
        staffData.find((staff) => staff.id === item.reviewerId)?.name ||
        item.decidedBy || item.assignee;
      $("#jobDetailAssignee").textContent = reviewerName ||
        (approvalGroup(item.status) === "pending" ? "ยังไม่ตรวจสอบ" : "ธุรการ");
      const returnStatusGroup = $("#jobDetailReturnStatusGroup");
      if (returnStatusGroup) returnStatusGroup.hidden = isLostAnnouncement;
      const returnStatus = returnStatusForFoundItem(item);
      if (!isLostAnnouncement && $("#jobDetailReturnStatus")) {
        $("#jobDetailReturnStatus").textContent = returnStatus;
      }
      $("#jobDetailBadges").innerHTML = `<span class="badge ${badgeClass(
        item.status,
      )}">${item.status}</span>`;
      const detailImage = $("#jobDetailImage");
      const detailIcon = $("#jobDetailIcon");
      if (item.imageUrl && detailImage) {
        detailImage.src = item.imageUrl;
        detailImage.alt = `รูป ${item.title}`;
        detailImage.hidden = false;
        if (detailIcon) detailIcon.setAttribute("hidden", "");
        detailImage.onerror = () => {
          detailImage.hidden = true;
          if (detailIcon) detailIcon.removeAttribute("hidden");
        };
      } else {
        if (detailImage) {
          detailImage.hidden = true;
          detailImage.removeAttribute("src");
          detailImage.onerror = null;
        }
        if (detailIcon) detailIcon.removeAttribute("hidden");
      }
      detailIcon
        ?.querySelector("use")
        ?.setAttribute("href", isLostAnnouncement ? "#i-search" : "#i-box");
      const detailTimeline = isLostAnnouncement
        ? [
            ["ส่งประกาศ", item.custody || "บันทึกในระบบแล้ว"],
            ["ตรวจสอบข้อมูล", item.status],
            [
              "เผยแพร่ต่อผู้ใช้งาน",
              approvalGroup(item.status) === "approved"
                ? "เผยแพร่แล้ว"
                : "ยังไม่เผยแพร่",
            ],
          ]
        : [
            ["สร้างรายการ", "บันทึกในระบบแล้ว"],
            ["ตรวจสอบข้อมูล", item.status],
            ["สถานะการคืนของ", returnStatus],
          ];
      $("#jobTimeline").innerHTML = detailTimeline
        .map(
          (step) =>
            `<div class="timeline-item"><span class="timeline-dot"></span><div><strong>${step[0]}</strong><small>${step[1]}</small></div></div>`,
        )
        .join("");
      $("#jobDetailNotes").textContent =
        item.decisionReason || "ยังไม่มีหมายเหตุ";
      const approved = approvalGroup(item.status) === "approved";
      const ownershipClaim = lostSets.claims.find(
        (claim) => claim.foundItemBackendId === item.backendId,
      );
      if (currentRole === "admin") {
        $("#jobQuickActions").innerHTML = "";
      } else if (!approved) {
        $("#jobQuickActions").innerHTML =
          `<button type="button" class="quick-action primary-action" data-lost-detail-action="approve" data-tab="${tab}" data-item-id="${id}">${isLostAnnouncement ? "อนุมัติเผยแพร่" : "ตรวจสอบและอนุมัติ"}</button><button type="button" class="quick-action" data-lost-detail-action="reject" data-tab="${tab}" data-item-id="${id}">ไม่อนุมัติ</button>`;
      } else if (
        !isLostAnnouncement &&
        ownershipClaim?.backendStatus === "completed"
      ) {
        $("#jobQuickActions").innerHTML =
          '<button type="button" class="quick-action primary-action" disabled>ส่งคืนเจ้าของแล้ว</button>';
      } else if (
        !isLostAnnouncement &&
        (ownershipClaim?.backendStatus === "approved" ||
          ownershipClaim?.status === "นัดหมายแล้ว")
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
            item.publicListItem = false;
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
            await loadApprovedLostFoundItems();
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
      $("#claimPickupNote").textContent = item.pickupNote || "ไม่มีหมายเหตุ";
      $("#claimReturnStatus").textContent =
        item.returnStatus ||
        foundItemReturnStatus(item.returnStatusCode, item.backendStatus);
      $("#claimEvidence").textContent =
        item.evidence || item.place || "ยังไม่มีรายละเอียดหลักฐาน";
      $("#claimSecret").textContent =
        item.secret || "ยังไม่มีข้อมูลลับสำหรับตรวจสอบ";
      $("#claimTimeline").innerHTML = [
        ["ส่งคำขอ", $("#claimDate").textContent],
        ["ตรวจสอบล่าสุด", item.status],
        ["ผู้รับผิดชอบ", item.assignee || "ธุรการส่วนกลาง"],
      ]
        .map(
          (step) =>
            `<div class="timeline-item"><span class="timeline-dot"></span><div><strong>${step[0]}</strong><small>${step[1]}</small></div></div>`,
        )
        .join("");
      const verified = ["approved", "scheduled"].includes(item.backendStatus);
      const returned = item.returnStatusCode === "returned";
      const appointmentGroup = $("#claimAppointmentGroup");
      if (appointmentGroup) appointmentGroup.hidden = !item.pickupDate;
      const nextStep = $("#claimNextStep");
      if (nextStep) nextStep.textContent = returned ? "ส่งคืนเจ้าของแล้ว" : verified
        ? "ยืนยันเจ้าของแล้ว นัดวัน เวลา และจุดรับของกับผู้ขอ ก่อนบันทึกนัดหมาย"
        : "เทียบหลักฐานที่ผู้ขอระบุกับข้อมูลลับของสิ่งของ แล้วจึงยืนยันความเป็นเจ้าของ";
      const claimActions = verified || returned || item.backendStatus === "rejected" ? [] : [
        ["reject", "ปฏิเสธคำขอ", "claim-reject-action"],
        ["more", "ขอข้อมูลเพิ่มเติม", ""],
        ["verify", "ยืนยันความเป็นเจ้าของ", "primary-action"],
      ];
      if (verified && !returned) {
        claimActions.push([
          "appointment",
          item.status === "นัดหมายแล้ว"
            ? "แก้ไขนัดหมายรับของ"
            : "นัดหมายรับของ",
          "",
        ]);
        claimActions.push(["returned", "ยืนยันส่งคืนแล้ว", "primary-action"]);
      }
      $("#claimActions").innerHTML = claimActions
        .map(
          (action) =>
            `<button type="button" class="quick-action ${action[2]}" data-claim-action="${action[0]}" data-claim-id="${id}">${action[1]}</button>`,
        )
        .join("");
      openModal("claimDetailModal", trigger);
    }
    function updateClaimWithConfirmation(id, action, trigger, additionalInfoMessage = "") {
      const item = lostSets.claims.find((record) => record.id === id);
      if (!item) return;
      if (["more", "reject"].includes(action) && !additionalInfoMessage.trim()) {
        closeModal("claimDetailModal", false);
        $("#claimMoreId").value = id;
        $("#claimMoreAction").value = action;
        $("#claimMoreTitle").textContent = action === "reject" ? "ปฏิเสธคำขอรับคืน" : "ขอข้อมูลเพิ่มเติม";
        $("#claimMoreLabel").textContent = action === "reject" ? "เหตุผลที่ปฏิเสธ (จำเป็น)" : "ข้อมูลที่ต้องการให้ส่งเพิ่ม";
        $("#claimMoreMessage").value = "";
        openModal("claimMoreModal", trigger);
        return;
      }
      if (action === "appointment") {
        closeModal("claimDetailModal", false);
        openAppointment(id, trigger);
        return;
      }
      const map = {
        reject: ["ปฏิเสธคำขอรับคืน", "ไม่ผ่านการตรวจสอบ"],
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
      requestConfirmation(title, confirmationText, async () => {
        try {
          const result =
            action === "reject"
              ? await rejectOwnershipRequest(item.backendId, additionalInfoMessage.trim())
              : action === "returned"
              ? await updateOwnershipReturnStatus(item.backendId, "returned")
              : action === "verify"
                ? await approveOwnershipRequest(item.backendId)
                : await requestOwnershipAdditionalInfo(
                    item.backendId,
                    additionalInfoMessage.trim(),
                  );
          item.status =
            result.status === "approved"
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
            await loadApprovedLostFoundItems();
          }
          if (action === "verify" && result.status === "approved") {
            // backend ปฏิเสธคำขออื่นของของชิ้นเดียวกันให้แล้ว ทำตามในหน้าจอโดยไม่ต้องโหลดใหม่
            // (โหลดใหม่ไม่ได้ เพราะ API คืนเฉพาะคำขอ pending คำขอที่เพิ่งอนุมัติจะหายไป)
            lostSets.claims
              .filter(
                (claim) =>
                  claim !== item &&
                  claim.foundItemBackendId === item.foundItemBackendId &&
                  ["pending", "additional_info_required"].includes(claim.backendStatus),
              )
              .forEach((claim) => {
                claim.backendStatus = "rejected";
                claim.status = "ไม่ผ่านการตรวจสอบ";
              });
            // ของถูกเอาออกจากหน้า guest แล้ว จึงไม่อยู่ในรายการรับฝากที่ดึงจาก public API อีก
            await loadApprovedLostFoundItems();
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
          if (action === "verify") {
            openAppointment(id, trigger);
            toast("ยืนยันเจ้าของแล้ว กรุณาระบุนัดหมายรับของ");
            return;
          }
          if (action === "reject") {
            showSuccess(result.email_sent
              ? "ปฏิเสธคำขอแล้ว และส่งเหตุผลให้ผู้ขอทางอีเมลแล้ว"
              : "ปฏิเสธคำขอแล้ว แต่ส่งอีเมลไม่สำเร็จ กรุณาติดต่อผู้ขอเพื่อแจ้งเหตุผล", "ปฏิเสธคำขอแล้ว");
            return;
          }
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
                : "อัปเดตคำขอแล้ว",
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
      $("#appointmentDate").value = item.pickupDate || todayISO();
      $("#appointmentTime").value = item.pickupTime || "";
      $("#appointmentPlace").value = item.pickupLocation || item.custodyLocation || "ประชาสัมพันธ์ ชั้น 1";
      $("#appointmentNote").value = item.pickupNote || "";
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
      $("#mobileQuickActions").innerHTML = actions
        .map(
          (item) =>
            `<button type="button" class="quick-action" data-quick-action="${item[0]}">${item[1]}</button>`,
        )
        .join("");
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
      $("#dashboardQuickActions").innerHTML = actions
        .map(
          (label, index) =>
            `<button type="button" class="quick-action ${
              index === 0 && currentRole !== "clerk" ? "primary-action" : ""
            }" data-dashboard-action="${index}">${label}</button>`,
        )
        .join("");
    }

    // -------------------------------------------------------------------------
    // 17) Event binding: Navigation, Profile และ Dashboard
    // -------------------------------------------------------------------------

    $$(".nav-item").forEach((button) =>
      button.addEventListener("click", () => {
        if (["housekeeper", "technician"].includes(currentRole)) {
          if (button.dataset.page === "my-jobs") {
            currentBoardView = "mine";
          } else if (button.dataset.page === "jobs") {
            currentBoardView = "unassigned";
          }
          $$("#boardTabs .board-tab").forEach((tab) =>
            tab.classList.toggle(
              "active",
              tab.dataset.view === currentBoardView,
            ),
          );
        }
        closeSidebar();
        navigate(button.dataset.page);
        if (["jobs", "my-jobs"].includes(button.dataset.page)) renderJobs();
      }),
    );
    $$("[data-go]").forEach((button) =>
      button.addEventListener("click", () =>
        navigate(
          currentRole === "clerk" && button.dataset.go === "jobs"
            ? "clerk-center"
            : button.dataset.go,
        ),
      ),
    );
    $$("[data-role-switch]").forEach((button) =>
      button.addEventListener("click", () => {
        localStorage.setItem("buildingCareRole", button.dataset.roleSwitch);
        window.location.reload();
      }),
    );
    $("#menuToggle")?.addEventListener("click", toggleSidebar);
    $("#mobileNotificationButton")?.addEventListener("click", () =>
      navigate("notifications"),
    );
    $(".sidebar-close")?.addEventListener("click", closeSidebar);
    $("#sidebarBackdrop")?.addEventListener("click", closeSidebar);
    function syncNavigationForViewport() {
      $("#sidebar").classList.remove("open");
      $("#sidebarBackdrop").classList.remove("open");
      $(".app").classList.remove("sidebar-collapsed");
      updateMenuToggle(false);
    }
    window.addEventListener("resize", syncNavigationForViewport);
    const handleBrowserNavigation = () => syncDashboardFromRoute();
    window.addEventListener("popstate", handleBrowserNavigation);
    cleanupDashboardEvents = () => {
      window.removeEventListener("resize", syncNavigationForViewport);
      window.removeEventListener("popstate", handleBrowserNavigation);
    };
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
            (item) => !["คืนของแล้ว", "ไม่ผ่านการตรวจสอบ"].includes(item.status),
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
            tab.classList.toggle("active", tab.dataset.tab === currentLostTab),
          );
          renderLost();
          if (index === 2) openFoundForm(button);
        }
        return;
      }
      currentBoardView = index === 0 ? "unassigned" : "mine";
      $$("#boardTabs .board-tab").forEach((tab) =>
        tab.classList.toggle("active", tab.dataset.view === currentBoardView),
      );
      navigate(index === 0 ? "jobs" : "my-jobs");
      renderJobs();
      const candidate = roleJobs().find((job) =>
        index === 0 ? !job.assignee : job.assignee === activeStaffName(),
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
        "ออกจากระบบ",
      );
    }
    $("#logoutBtn")?.addEventListener("click", confirmLogout);
    $("#profileLogout")?.addEventListener("click", confirmLogout);
    $("#profileButton")?.addEventListener("click", (event) =>
      openModal("profileModal", event.currentTarget),
    );
    $("#mobileProfile")?.addEventListener("click", (event) =>
      openModal("profileModal", event.currentTarget),
    );
    $("#changePassword")?.addEventListener("click", () =>
      toast("ส่งลิงก์เปลี่ยนรหัสผ่านไปยังอีเมลเจ้าหน้าที่แล้ว"),
    );
    $("#notificationSettings")?.addEventListener("click", () =>
      toast("บันทึกการตั้งค่าการแจ้งเตือนแล้ว")
    );
    $(".bottom-nav")?.addEventListener("click", (event) => {
      const button = event.target.closest("[data-mobile-page]");
      if (!button) return;
      navigate(
        currentRole === "clerk" && button.dataset.mobilePage === "jobs"
          ? "clerk-center"
          : button.dataset.mobilePage
      );
    });
    $("#mobileQuickAction")?.addEventListener("click", (event) =>
      openModal("quickActionModal", event.currentTarget),
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
        navigate("my-jobs");
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
    $("#myHistoryTabs")?.addEventListener("click", event => {
      const button = event.target.closest("[data-history-tab]");
      if (!button) return;
      currentHistoryTab = button.dataset.historyTab;
      $$("#myHistoryTabs [data-history-tab]").forEach(tab => {
        const active = tab === button;
        tab.classList.toggle("active", active);
        tab.setAttribute("aria-selected", String(active));
      });
      const type = $("#myHistoryType");
      if (type) { type.value = "all"; type.hidden = currentHistoryTab === "returns"; }
      renderMyHistory();
    });
    $("#myHistoryFrom")?.addEventListener("change", renderMyHistory);
    $("#myHistoryTo")?.addEventListener("change", renderMyHistory);
    $("#myHistoryType")?.addEventListener("change", renderMyHistory);
    $("#myHistorySearch")?.addEventListener("input", renderMyHistory);
    $("#resetMyHistoryFilters")?.addEventListener("click", () => {
      $("#myHistoryFrom").value = "";
      $("#myHistoryTo").value = "";
      $("#myHistoryType").value = "all";
      $("#myHistoryType").dispatchEvent(new Event("change", { bubbles: true }));
      $("#myHistorySearch").value = "";
      renderMyHistory();
    });
    $("#overviewRoleFilter")?.addEventListener("change", loadStaffWorkOverview);
    $("#overviewSearch")?.addEventListener("input", () => {
      clearTimeout(overviewSearchTimer);
      overviewSearchTimer = setTimeout(loadStaffWorkOverview, 300);
    });
    $("#resetOverviewFilters")?.addEventListener("click", () => {
      clearTimeout(overviewSearchTimer);
      $("#overviewRoleFilter").value = "all";
      $("#overviewSearch").value = "";
      loadStaffWorkOverview();
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
        tab.classList.toggle("active", tab === button),
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
        confirmFoundItemReturn(
          lostAction.dataset.tab,
          lostAction.dataset.itemId,
        );
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
        `${previous ? `${previous} → ` : ""}${job.assignee}`,
      );
      addAudit(
        "jobs",
        "มอบหมายงาน",
        job.id,
        job.title,
        `มอบหมายให้ ${job.assignee}`,
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
      }),
    );
    ["dragleave", "drop"].forEach((type) =>
      $("#uploadDropZone")?.addEventListener(type, (event) => {
        event.preventDefault();
        $("#uploadDropZone").classList.remove("dragging");
      }),
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
      }),
    );
    ["dragleave", "drop"].forEach((type) =>
      $("#completionDropZone")?.addEventListener(type, (event) => {
        event.preventDefault();
        $("#completionDropZone").classList.remove("dragging");
      }),
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
        note = $("#statusNote")?.value.trim() || "";
      if (["คืนเข้าคิวกลาง", "คืนเข้ากองกลาง"].includes(next)) {
        closeModal("statusUpdateModal", false, false);
        openReturnJob(job.id, "replace");
        return;
      }
      if (next === "เสร็จสิ้น") {
        closeModal("statusUpdateModal", false, false);
        openCompleteModal(job.id, document.activeElement, "replace");
        $("#completeResult").value = note;
        return;
      }
      const updated = await applyJobStatus(job, next, note);
      if (updated) {
        closeModal("statusUpdateModal", false, false);
        updateDashboardRoute("", "replace");
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
        $("#uploadDescription").value.trim(),
      );
      addAudit(
        "jobs",
        "เพิ่มรูป",
        job.id,
        job.title,
        $("#uploadDescription").value.trim(),
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
          "หมายเหตุปิดงานต้องไม่เกิน 2,000 ตัวอักษร",
        );
        completionNoteInput.reportValidity();
        completionNoteInput.focus();
        return;
      }
      completionNoteInput.setCustomValidity("");
      const summary = [$("#completeResult").value.trim(), completionNote].filter(Boolean).join(" · ");
      if (!(job.backendId && job.backendStatus === "completed")) {
        const updated = await applyJobStatus(job, "เสร็จสิ้น", summary);
        if (!updated) return;
      }

      // Backend อนุญาตให้เพิ่ม note และรูปได้หลังเปลี่ยนสถานะเป็น completed แล้ว
      if (job.backendId) {
        try {
          // บันทึกผลทันทีเพื่อไม่สร้างหมายเหตุซ้ำ หากรูปอัปโหลดไม่สำเร็จ
          if (completionNote && !job.completionNoteId) {
            const noteResult =
              job.type === "repair"
                ? await addRepairCompletionNote(job.backendId, completionNote)
                : await addCleaningCompletionNote(
                    job.backendId,
                    completionNote,
                  );
            job.completionNoteId = noteResult.id;
            job.note = noteResult.note;
          }
          if (file) {
            const photoResult =
              job.type === "repair"
                ? await uploadRepairCompletionPhotos(job.backendId, [file])
                : await uploadCleaningCompletionPhotos(job.backendId, [file]);
            job.completionPhotos = photoResult.photos;
            job.completionPhotoCount = photoResult.image_count;
          }
        } catch (error) {
          if (await handleUnauthorizedResponse(error.status)) return;
          console.error("Saving task completion details failed:", error);
          toast(
            error.message || "บันทึกรายละเอียดปิดงานไม่สำเร็จ กรุณาลองใหม่",
          );
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
      appendJobTimeline(
        job,
        "ปิดงาน",
        `เสร็จวันที่ ${$("#completeDate").value}`,
      );
      renderJobs();
      closeModal("completeModal", false, false);
      updateDashboardRoute("", "replace");
      toast(`ปิดงาน ${job.id} เรียบร้อย`);
    });
    $("#historySearchForm")?.addEventListener("submit", (event) => {
      event.preventDefault();
      appliedHistorySearch = ($("#historySearch")?.value || "").trim().toLowerCase();
      renderHistory();
    });
    $("#myHistoryList")?.addEventListener("click", (event) => {
      const button = event.target.closest("[data-history-detail]");
      if (!button) return;
      const job = allJobs.find(
        (item) => item.id === button.dataset.historyDetail,
      );
      if (job) openJobDetail(job.id, button);
      else {
        const record = workHistory.find(item => item.itemId === button.dataset.historyDetail);
        if (record?.tab) {
          if (!lostSets[record.tab].some(item => item.id === record.itemId)) {
            lostSets[record.tab].push({id: record.itemId, backendId: record.backendId,
              title: record.title, status: record.status});
          }
          openLostDetail(record.tab, record.itemId, button);
        }
      }
    });
    $("#staffOverviewSummary")?.addEventListener("click", (event) => {
      if (event.target.closest('[data-overview-retry="summary"]')) loadStaffWorkOverview();
    });
    $("#staffOverviewDetail")?.addEventListener("click", (event) => {
      const button = event.target.closest('[data-overview-retry="staff-work"]');
      if (button && selectedOverviewStaff) showStaffOverview(selectedOverviewStaff, button);
    });
    $("#staffOverviewTable")?.addEventListener("click", (event) => {
      const button = event.target.closest("[data-staff-overview]");
      if (button) showStaffOverview(button.dataset.staffOverview, button);
    });
    $("#staffRoleFilter")?.addEventListener("change", renderStaff);
    $("#staffAccountSearch")?.addEventListener("input", renderStaff);
    $("#resetStaffAccountFilters")?.addEventListener("click", () => {
      $("#staffRoleFilter").value = "all";
      $("#staffRoleFilter").dispatchEvent(
        new Event("change", { bubbles: true }),
      );
      $("#staffAccountSearch").value = "";
      renderStaff();
    });
    let selectedAccountDetailId = null;
    async function showStaffAccountDetail(index, trigger) {
      const staff = staffData[index];
      if (!staff) return;
      selectedAccountDetailId = staff.id;
      $("#staffAccountDetailTitle").textContent = `รายละเอียดบัญชี · ${staff.name}`;
      const invitation = {sent: "ส่งสำเร็จ", failed: "ส่งไม่สำเร็จ", pending: "รอส่ง"}[staff.invitationDeliveryStatus] || "ไม่มีข้อมูล";
      $("#staffAccountDetailInfo").innerHTML = [
        ["ชื่อ", staff.name], ["อีเมล", staff.email], ["บทบาท", staff.role],
        ["สถานะบัญชี", staff.status], ["สถานะคำเชิญ", invitation],
      ].map(([label, value]) => `<div><small>${label}</small><strong>${escapeHtml(value || "–")}</strong></div>`).join("");
      const work = $("#staffAccountDetailWork");
      const isWorker = ["แม่บ้าน", "ช่าง"].includes(staff.role);
      work.innerHTML = isWorker && staff.status === "ใช้งาน" ? '<p role="status">กำลังโหลดสถิติงาน…</p>' : "";
      openModal("staffAccountDetailModal", trigger);
      if (!isWorker || staff.status !== "ใช้งาน") return;
      try {
        const data = await fetchStaffWorkOverview();
        if (selectedAccountDetailId !== staff.id || !$("#staffAccountDetailModal").classList.contains("open")) return;
        const person = data.staff.find(person => person.id === staff.id);
        if (!person) { work.innerHTML = '<p>ไม่มีข้อมูลสถิติงานของบัญชีนี้</p>'; return; }
        work.innerHTML = `<h4 class="overview-work-heading" style="margin-top:24px;margin-bottom:14px">ข้อมูลการทำงาน</h4><div class="staff-overview-card-stats overview-person-stats">${[
          ["กำลังรับผิดชอบ", person.counts.current_assigned], ["ปิดแล้ว", person.counts.closed], ["คืนเข้ากองกลาง", person.counts.returned],
        ].map(([label, count]) => `<div><span>${label}</span><strong>${count}</strong></div>`).join("")}</div><button type="button" class="small-btn" data-account-work-history="${staff.id}">ดูประวัติงาน</button>`;
      } catch (error) {
        if (selectedAccountDetailId !== staff.id) return;
        if (await handleUnauthorizedResponse(error.status)) return;
        work.innerHTML = '<p role="alert">โหลดสถิติงานไม่สำเร็จ <button type="button" class="small-btn" data-account-detail-retry>ลองใหม่</button></p>';
      }
    }
    $("#staffAccountDetailWork")?.addEventListener("click", async (event) => {
      const retry = event.target.closest("[data-account-detail-retry]");
      if (retry) { showStaffAccountDetail(staffData.findIndex(staff => staff.id === selectedAccountDetailId), retry); return; }
      const button = event.target.closest("[data-account-work-history]");
      if (!button) return;
      button.disabled = true;
      try {
        overviewData = await fetchStaffWorkOverview();
      } catch (error) {
        if (!(await handleUnauthorizedResponse(error.status))) toast("โหลดประวัติงานไม่สำเร็จ กรุณาลองใหม่");
        button.disabled = false;
        return;
      }
      button.disabled = false;
      if (!$("#staffAccountDetailModal").classList.contains("open") || selectedAccountDetailId !== button.dataset.accountWorkHistory) return;
      if (!overviewData?.staff.some(person => person.id === button.dataset.accountWorkHistory)) return;
      closeModal("staffAccountDetailModal", false);
      showStaffOverview(button.dataset.accountWorkHistory, $("#staffTable")?.querySelector(`[data-staff-action="detail"][data-staff-index="${staffData.findIndex(staff => staff.id === button.dataset.accountWorkHistory)}"]`));
    });
    $("#staffTable")?.addEventListener("click", (event) => {
      const button = event.target.closest("[data-staff-action]");
      if (!button) return;
      const index = Number(button.dataset.staffIndex);
      if (button.dataset.staffAction === "edit") openEditStaff(index, button);
      if (button.dataset.staffAction === "toggle") toggleStaff(index);
      if (button.dataset.staffAction === "remove") removeStaff(index);
      if (button.dataset.staffAction === "resend-invitation")
        resendInvitation(index, button);
      if (button.dataset.staffAction === "detail") {
        showStaffAccountDetail(index, button);
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
    $("#staffLostRefreshButton")?.addEventListener("click", async (event) => {
      const button = event.currentTarget;
      button.disabled = true;
      try {
        await loadApprovedLostFoundItems();
      } finally {
        button.disabled = false;
      }
    });
    $("#page-dashboard")?.addEventListener("click", (event) => {
      if (currentRole !== "clerk") return;
      const retry = event.target.closest("[data-clerk-overview-retry]");
      if (retry) {
        clerkApprovalLoadState.found = "loading";
        clerkApprovalLoadState.lost = "loading";
        clerkApprovalLoadState.claims = "loading";
        renderClerkApprovalsOverview();
        Promise.all([loadPendingFoundItems(), loadPendingLostItems(), loadPendingOwnershipRequests()]);
        return;
      }
      const detail = event.target.closest("[data-clerk-overview-detail]");
      if (detail) {
        openLostDetail(detail.dataset.tab, detail.dataset.clerkOverviewDetail, detail);
        return;
      }
      const link = event.target.closest("[data-clerk-overview-view]");
      if (link) {
        navigate("clerk-center");
        setClerkCenterView(link.dataset.clerkOverviewView);
      }
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
        }),
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
      if (currentRole === "admin" && !["detail", "claim-detail"].includes(action)) return;
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

    // Phones and tablets show notifications as a bottom navigation page.
    function openMobileNotifications(button) {
      const panel = $("#notificationPanel");
      if (!panel) return;
      panel.classList.add("open", "mobile-notification-page");
      $("#notificationButton")?.setAttribute("aria-expanded", "false");
      $$(".bottom-nav button").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      button.setAttribute("aria-current", "page");
      closeSidebar();
      panel.scrollTop = 0;
      window.scrollTo(0, 0);
    }
    function toggleNotificationPanel() {
      const panel = $("#notificationPanel");
      if (!panel) return;
      const open = !panel.classList.contains("open");
      panel.classList.toggle("open", open);
      $("#notificationButton")?.setAttribute("aria-expanded", String(open));
      if (open) panel.querySelector("button")?.focus();
    }
    $("#notificationButton")?.addEventListener("click", (event) => {
      event.stopPropagation();
      toggleNotificationPanel();
    });
    $(".bottom-nav")?.addEventListener("click", (event) => {
      const button = event.target.closest("[data-mobile-notification]");
      if (!button) return;
      event.stopPropagation();
      if (window.matchMedia("(max-width: 1024px)").matches)
        openMobileNotifications(button);
      else toggleNotificationPanel();
    });
    $("#notificationList")?.addEventListener("click", async (event) => {
      event.stopPropagation();
      if (event.target.closest("[data-close-notifications]")) {
        event.currentTarget.classList.remove("open");
        $("#notificationButton")?.setAttribute("aria-expanded", "false");
        return;
      }
      if (event.target === event.currentTarget) {
        event.currentTarget.classList.remove("open");
        $("#notificationButton")?.setAttribute("aria-expanded", "false");
        return;
      }
      const clerkTarget = event.target.closest("[data-clerk-notification-target]");
      if (clerkTarget) {
        if (clerkTarget.dataset.clerkNotificationTarget === "claim")
          readClaimNotifications.add(clerkTarget.dataset.itemId);
        currentClerkCenterView =
          clerkTarget.dataset.clerkNotificationTarget === "claim"
            ? "claims"
            : "approvals";
        navigate("clerk-center");
        renderClerkCenter();
        return;
      }
      const hide = event.target.closest("[data-hide-notification]");
      if (hide) {
        const list = notificationSets[currentRole],
          index = list.findIndex(
            (item) => item.id === hide.dataset.hideNotification,
          );
        if (index >= 0) list.splice(index, 1);
        renderNotifications();
        toast("ซ่อนการแจ้งเตือนแล้ว");
        return;
      }
      const itemButton = event.target.closest("[data-notification-id]");
      if (!itemButton) return;
      const item = notificationSets[currentRole].find(
        (entry) => entry.id === itemButton.dataset.notificationId,
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
      if (
        currentRole === "housekeeper" &&
        (await openCleaningRequestFromNotification(item, itemButton))
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
          openJobDetail(job.id, itemButton);
        } else {
          toast("ไม่พบงานซ่อมที่เชื่อมกับการแจ้งเตือนนี้");
        }
        return;
      }
      const match = item.text.match(/(?:CL|RP)-\d+/);
      if (match) openJobDetail(match[0], itemButton);
      else if (currentRole === "clerk") navigate("clerk-center");
      else toast(item.title);
    });
    document.addEventListener("click", () => {
      if ($("#notificationPanel")?.classList.contains("mobile-notification-page")) return;
      $("#notificationPanel")?.classList.remove("open");
      $("#notificationButton")?.setAttribute("aria-expanded", "false");
    });
    $("#markAllRead")?.addEventListener("click", markNotificationsRead);
    $("#openStaffModal")?.addEventListener("click", (event) => {
      const form = $("#staffForm");
      form?.reset();
      clearStaffFormValidation(form);
      openModal("staffModal", event.currentTarget);
    });
    function openFoundForm(trigger) {
      const form = $("#foundForm");
      form?.reset();
      if ($("#custodyPoint")) $("#custodyPoint").value = "ประชาสัมพันธ์ชั้น 1";
      if ($("#foundDate")) $("#foundDate").value = todayISO();
      if ($("#foundTime")) $("#foundTime").value = currentTimeHM();
      openModal("foundModal", trigger);
    }
    $("#addFoundBtn")?.addEventListener("click", (event) =>
      openFoundForm(event.currentTarget),
    );
    $("#openAnnouncementModal")?.addEventListener("click", (event) =>
      openAnnouncementEditor(null, event.currentTarget),
    );
    $$("[data-close]").forEach((button) =>
      button.addEventListener("click", () => closeModal(button.dataset.close)),
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
          'button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])',
        ).filter(
          (element) => modal.contains(element) && element.offsetParent !== null,
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
      updateDashboardRoute("", "replace");
      if (typeof action === "function") action();
    });
    const staffForm = $("#staffForm");
    const staffFormFields = staffForm
      ? [...staffForm.querySelectorAll("input, select")]
      : [];

    function setStaffFieldError(field, message) {
      if (!field) return false;
      field.setCustomValidity(message);
      if (message) field.setAttribute("aria-invalid", "true");
      else field.removeAttribute("aria-invalid");

      const errorId = field.getAttribute("aria-describedby");
      const errorMessage = errorId ? document.getElementById(errorId) : null;
      if (errorMessage) errorMessage.textContent = message;

      if (field.tagName === "SELECT") {
        const visibleTrigger = field
          .closest(".filter-select-dropdown")
          ?.querySelector(".filter-select-trigger");
        if (visibleTrigger) {
          visibleTrigger.setAttribute("aria-describedby", errorId || "");
          if (message) visibleTrigger.setAttribute("aria-invalid", "true");
          else visibleTrigger.removeAttribute("aria-invalid");
        }
      }
      return !message;
    }

    function validateStaffField(field) {
      const value = field.value.trim();
      const firstName = $("#newFirstName")?.value.trim() || "";
      const lastName = $("#newLastName")?.value.trim() || "";
      const fullName = `${firstName} ${lastName}`.trim();
      let message = "";

      if (field.id === "newFirstName") {
        if (!value) message = "กรุณากรอกชื่อ";
        else if (value.length < 2) message = "ชื่อต้องมีอย่างน้อย 2 ตัวอักษร";
      } else if (field.id === "newLastName") {
        if (!value) message = "กรุณากรอกนามสกุล";
        else if (value.length < 2) {
          message = "นามสกุลต้องมีอย่างน้อย 2 ตัวอักษร";
        } else if (fullName.length > 150) {
          message = "ชื่อและนามสกุลรวมกันต้องไม่เกิน 150 ตัวอักษร";
        }
      } else if (field.id === "newEmail") {
        if (!value) message = "กรุณากรอกอีเมล";
        else if (field.validity.typeMismatch) message = "กรุณากรอกอีเมลให้ถูกต้อง";
      } else if (field.id === "newRole" && !value) {
        message = "กรุณาเลือก Role";
      }

      return setStaffFieldError(field, message);
    }

    function validateStaffForm(form) {
      if (!form) return false;
      const results = staffFormFields.map(validateStaffField);
      const isValid = results.every(Boolean);
      if (!isValid) {
        const firstInvalid = staffFormFields.find(
          (field) => field.getAttribute("aria-invalid") === "true",
        );
        if (firstInvalid?.id === "newRole") {
          firstInvalid
            .closest(".filter-select-dropdown")
            ?.querySelector(".filter-select-trigger")
            ?.focus();
        } else {
          firstInvalid?.focus();
        }
      }
      return isValid;
    }

    function clearStaffFormValidation(form) {
      form?.querySelectorAll("input, select").forEach((field) => {
        field.setCustomValidity("");
        field.removeAttribute("aria-invalid");
        const errorId = field.getAttribute("aria-describedby");
        const errorMessage = errorId ? document.getElementById(errorId) : null;
        if (errorMessage) errorMessage.textContent = "";
        field
          .closest(".filter-select-dropdown")
          ?.querySelector(".filter-select-trigger")
          ?.removeAttribute("aria-invalid");
      });
    }

    staffFormFields.forEach((field) => {
      const handleStaffFieldChange = () => {
        validateStaffField(field);
        const lastNameField = $("#newLastName");
        if (field.id === "newFirstName" && lastNameField?.value.trim()) {
          validateStaffField(lastNameField);
        }
      };
      field.addEventListener("input", handleStaffFieldChange);
      field.addEventListener("change", handleStaffFieldChange);
      field.addEventListener("blur", () => validateStaffField(field));
    });
    staffForm?.addEventListener("reset", () => clearStaffFormValidation(staffForm));

    staffForm?.addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = event.currentTarget;
      const firstNameInput = $("#newFirstName");
      const lastNameInput = $("#newLastName");
      const firstName = firstNameInput.value.trim();
      const lastName = lastNameInput.value.trim();
      const fullName = `${firstName} ${lastName}`.trim();

      if (!validateStaffForm(form)) return;
      const submitButton = $("#createStaffButton");
      submitButton.disabled = true;
      const payload = {
        full_name: fullName,
        email: $("#newEmail").value.trim(),
        role: $("#newRole").value,
      };
      let account;
      try {
        account = await createStaffAccount(payload);
      } catch (error) {
        if (await handleUnauthorizedResponse(error.status)) return;
        console.error("Creating staff account failed:", error);
        if (error.status === 409) {
          const emailInput = $("#newEmail");
          setStaffFieldError(emailInput, "อีเมลนี้ถูกใช้งานแล้ว");
          emailInput.focus();
        } else {
          toast(error.message || "ไม่สามารถสร้างบัญชีได้");
        }
        submitButton.disabled = false;
        return;
      }
      const record = toDashboardStaff(account);
      rememberInvitationDelivery(record, record.invitationDeliveryStatus);
      record.invitationStatusSource = "browser";
      staffData.push(record);
      loadStaffWorkOverview();
      addAudit(
        "staff",
        "สร้างบัญชี",
        record.id,
        record.name,
        `สร้างบัญชี Role ${record.role}`,
      );
      await loadStaffAccounts();
      closeModal("staffModal", false);
      form.reset();
      submitButton.disabled = false;
      showSuccess(
        account.email_sent
          ? `สร้างบัญชี Staff และส่งคำเชิญไปยัง ${record.email} แล้ว`
          : `สร้างบัญชี Staff แล้ว แต่ส่งคำเชิญไปยัง ${record.email} ไม่สำเร็จ กรุณาตรวจสอบระบบอีเมล`,
        account.email_sent ? "ส่งคำเชิญสำเร็จ" : "ส่งคำเชิญไม่สำเร็จ",
        account.email_sent ? "success" : "error",
      );
    });
    $("#editStaffForm")?.addEventListener("submit", (event) => {
      event.preventDefault();
      if (!event.currentTarget.checkValidity()) {
        event.currentTarget.reportValidity();
        return;
      }
      const staff = staffData.find((item) => item.id === $("#editStaffIndex").value);
      if (!staff || currentRole !== "admin" || $("#editStaffButton").disabled) return;
      const name = $("#editStaffName").value.trim().replace(/\s+/g, " ");
      const email = $("#editStaffEmail").value.trim().toLowerCase();
      const changes = {};
      if (name !== staff.name) changes.full_name = name;
      if (email !== staff.email) changes.email = email;
      if (changes.email) {
        requestConfirmation("ยืนยันเปลี่ยนอีเมล Staff",
          `ตรวจสอบว่า ${email} เป็นอีเมลของ Staff คนนี้แล้วหรือไม่? ลิงก์คำเชิญเดิมจะใช้ไม่ได้ และต้องใช้อีเมลใหม่เพื่อเข้าสู่ระบบ`,
          () => performStaffProfileUpdate(staff, changes), "ยืนยันและบันทึก");
      } else {
        performStaffProfileUpdate(staff, changes);
      }
    });
    $("#claimActions")?.addEventListener("click", (event) => {
      const button = event.target.closest("[data-claim-action]");
      if (button)
        updateClaimWithConfirmation(
          button.dataset.claimId,
          button.dataset.claimAction,
          button,
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
      const nextFoundNumber =
        Math.max(
          81,
          ...lostSets.inventory.map(
            (item) => Number(item.id.replace("FD-", "")) || 0,
          ),
        ) + 1;
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
        "บันทึกรายการใหม่และรออนุมัติรับฝาก",
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
      requestConfirmation(
        isLostAnnouncement
          ? "ยืนยันปฏิเสธประกาศของหาย"
          : "ยืนยันไม่อนุมัติรายการรับฝาก",
        `${id} · ${item.title}\nเหตุผล: ${decisionReason}\n\n${
          isLostAnnouncement
            ? "ประกาศนี้จะไม่ถูกเผยแพร่ให้ผู้ใช้งานเห็น"
            : "รายการนี้จะไม่ได้รับการอนุมัติเข้าสู่ระบบรับฝาก"
        }`,
        () => confirmRejectLostItem(tab, id, decisionReason),
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
      closeModal("returnJobModal", false, false);
      requestConfirmation(
        "ยืนยันคืนงานเข้าคิวกลาง",
        `ยืนยันคืนงาน ${id} เพราะ “${reason}” หรือไม่?`,
        async () => {
          const job = allJobs.find((item) => item.id === id);
          if (!job || job.assignee !== activeStaffName()) {
            toast("งานนี้ไม่อยู่ในความรับผิดชอบของคุณแล้ว");
            renderJobs();
            return;
          }
          const fullReason = note ? `${reason} — ${note}` : reason;
          // งานจริงต้องให้ Backend ปลดผู้รับผิดชอบและบันทึกประวัติก่อน แล้วค่อยเปลี่ยน UI
          if (job.backendId && ["cleaning", "repair"].includes(job.type)) {
            try {
              const returned =
                job.type === "repair"
                  ? await returnRepairRequest(job.backendId, { reason, note })
                  : await returnCleaningTask(job.backendId, { reason, note });
              job.backendStatus = returned.status;
              job.assigneeId = null;
              job.assigneeCode = "";
            } catch (error) {
              if (await handleUnauthorizedResponse(error.status)) return;
              console.error("Returning staff task failed:", error);
              toast(
                [403, 409].includes(error.status)
                  ? "งานนี้ไม่อยู่ในความรับผิดชอบของคุณแล้ว หรือปิดงานไปแล้ว"
                  : error.message || "ไม่สามารถคืนงานได้",
              );
              if (job.type === "repair") await loadRepairRequests();
              else await loadCleaningTasks();
              return;
            }
          }
          job.returnReason = fullReason;
          job.returnedBy = activeStaffName();
          job.returnedAt = nowThai();
          appendJobTimeline(
            job,
            "คืนงานเข้าคิวกลาง",
            `${activeStaffName()} · ${fullReason}`,
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
          addNotification(
            currentRole,
            `มีงาน ${id} กลับเข้าคิวร่วม`,
            fullReason,
          );
          addNotification(
            "admin",
            `${id} ถูกคืนเข้าคิวกลาง`,
            `${activeStaffName()} · ${fullReason}`,
          );
          currentBoardView = "unassigned";
          renderJobs();
          renderMetrics();
          renderQueue();
          renderStaffOverview();
          updateDashboardRoute("", "replace");
          toast("คืนงานเข้าคิวกลางเรียบร้อย");
        },
        "ยืนยันคืนงาน",
        "replace",
      );
    });
    $("#claimMoreForm")?.addEventListener("submit", event => {
      event.preventDefault();
      const message = $("#claimMoreMessage").value.trim();
      if (!message) return;
      const id = $("#claimMoreId").value;
      closeModal("claimMoreModal", false);
      updateClaimWithConfirmation(id, $("#claimMoreAction").value || "more", event.submitter, message);
    });
    ["#appointmentDate", "#appointmentTime"].forEach(selector => {
      $(selector)?.addEventListener("change", () => $("#appointmentTime").setCustomValidity(""));
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
        (record) => record.id === $("#appointmentItemId").value,
      );
      if (!item) return;
      const appointmentDate = $("#appointmentDate").value;
      const appointmentTime = $("#appointmentTime").value;
      const appointmentPlace = $("#appointmentPlace").value.trim();
      const note = $("#appointmentNote").value.trim();
      const pickupAt = new Date(`${appointmentDate}T${appointmentTime}`);
      const weekday = new Date(`${appointmentDate}T12:00:00+07:00`).getUTCDay();
      if ([0, 6].includes(weekday) || appointmentTime < "08:30" || appointmentTime > "16:30") {
        toast("นัดรับได้เฉพาะจันทร์–ศุกร์ เวลา 08:30–16:30 น.");
        return;
      }
      if (
        Number.isNaN(pickupAt.getTime()) ||
        pickupAt.getTime() <= Date.now()
      ) {
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
          result.pickup_date ||
          result.appointment?.pickup_date ||
          appointmentDate;
        item.pickupTime =
          result.pickup_time ||
          result.appointment?.pickup_time ||
          appointmentTime;
        item.pickupLocation =
          result.pickup_location ||
          result.appointment?.pickup_location ||
          appointmentPlace;
        item.pickupNote =
          result.pickup_note || result.appointment?.note || note;
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
          `${item.id} · นัดรับ ${item.title}\n${item.appointment}\n${result.email_sent ? "ส่งอีเมลนัดหมายให้ผู้ขอแล้ว" : "บันทึกนัดหมายแล้ว แต่ส่งอีเมลไม่สำเร็จ กรุณาติดต่อผู้ขอหรือบันทึกนัดหมายอีกครั้งเพื่อส่งใหม่"}`,
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
      openModal("qrFormModal", event.currentTarget),
    );
    $("#qrFloorFilter")?.addEventListener("change", renderQrLocations);
    $("#qrLocationSearch")?.addEventListener("input", renderQrLocations);
    $("#resetQrLocationFilters")?.addEventListener("click", () => {
      $("#qrFloorFilter").value = "all";
      $("#qrFloorFilter").dispatchEvent(new Event("change", { bubbles: true }));
      $("#qrLocationSearch").value = "";
      renderQrLocations();
    });
    $("#qrForm")?.addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = event.currentTarget;
      if (!form.checkValidity()) {
        form.reportValidity();
        return;
      }
      const submitButton = form.querySelector('button[type="submit"]');
      const area = $("#qrLocationName").value.trim();
      const floor = $("#qrLocationFloor").value.trim();
      if (submitButton) submitButton.disabled = true;
      try {
        // สร้างสถานที่ก่อนเพื่อรับ ID จาก Backend
        const created = await createAdminLocation({
          floor: floor || null,
          area,
        });
        // ขอ token และ qr_url จาก Backend
        const generated = await generateAdminLocationQr(created.id);
        const location = toDashboardQrLocation(generated);
        await loadQrLocations();
        addAudit(
          "qr",
          "เพิ่มสถานที่และสร้าง QR",
          `LOCATION-${location.id}`,
          location.name,
          `สร้าง QR สำหรับชั้น ${location.floor || "ไม่ระบุ"} · ${location.name}`,
        );
        closeModal("qrFormModal", false);
        form.reset();
        if (showQrLocation(location)) {
          openModal("qrDetailModal", $("#openQrModal"));
        }
      } catch (error) {
        if (await handleUnauthorizedResponse(error.status)) return;
        console.error("Creating QR location failed:", error);
        toast(error.message || "ไม่สามารถเพิ่มสถานที่และสร้าง QR Code ได้");
        await loadQrLocations();
      } finally {
        if (submitButton) submitButton.disabled = false;
      }
    });
    // สร้างรูปป้าย QR พร้อมชื่อบริการสำหรับดาวน์โหลดและพิมพ์
    function createQrPosterDataUrl() {
      const qrImage = $("#qrCode canvas") || $("#qrCode img");
      if (!qrImage || !selectedQrLocation) return null;
      const poster = document.createElement("canvas");
      const context = poster.getContext("2d");
      poster.width = 640;
      poster.height = 780;
      context.fillStyle = "#ffffff";
      context.fillRect(0, 0, poster.width, poster.height);
      context.fillStyle = "#17202b";
      context.textAlign = "center";
      context.font = "700 32px system-ui, sans-serif";
      context.fillText("บริการแจ้งซ่อมและทำความสะอาด", 320, 70);
      context.drawImage(qrImage, 90, 120, 460, 460);
      context.font = "700 30px system-ui, sans-serif";
      context.fillText(selectedQrLocation.name, 320, 640);
      context.fillStyle = "#64748b";
      context.font = "24px system-ui, sans-serif";
      context.fillText(
        selectedQrLocation.floor
          ? `ชั้น ${selectedQrLocation.floor}`
          : "ไม่ระบุชั้น",
        320,
        690,
      );
      return poster.toDataURL("image/png");
    }
    $("#downloadQr")?.addEventListener("click", () => {
      const href = createQrPosterDataUrl();
      if (!href || !selectedQrLocation) {
        toast("กรุณาเลือกสถานที่ก่อนดาวน์โหลด QR Code");
        return;
      }
      const link = document.createElement("a");
      link.href = href;
      link.download = `QR-${selectedQrLocation.name.replace(/[^\p{L}\p{N}_-]+/gu, "-")}.png`;
      link.click();
      toast("ดาวน์โหลด QR Code แล้ว");
    });
    $("#printQr")?.addEventListener("click", () => {
      const imageUrl = createQrPosterDataUrl();
      if (!imageUrl || !selectedQrLocation) {
        toast("กรุณาเลือกสถานที่ก่อนพิมพ์ QR Code");
        return;
      }
      // เปิดหน้าสำหรับพิมพ์เฉพาะ QR และข้อมูลพื้นที่
      const printWindow = window.open("", "_blank", "width=640,height=720");
      if (!printWindow) {
        toast("เบราว์เซอร์ปิดกั้นหน้าต่างพิมพ์ กรุณาอนุญาต Pop-up");
        return;
      }
      printWindow.onload = () => {
        printWindow.focus();
        printWindow.print();
      };
      printWindow.document.write(`<!doctype html>
        <html lang="th"><head><meta charset="utf-8"><title>QR ${escapeHtml(selectedQrLocation.name)}</title>
        <style>body{display:grid;place-items:center;min-height:95vh;margin:0}img{display:block;width:min(90vw,640px);height:auto}@page{margin:12mm}</style>
        </head><body><img src="${imageUrl}" alt="บริการแจ้งซ่อมและทำความสะอาด"></body></html>`);
      printWindow.document.close();
    });
    $("#roomList")?.addEventListener("click", async (event) => {
      const statusButton = event.target.closest("[data-toggle-qr-location]");
      if (statusButton) {
        const location = qrLocations.find(
          (item) => item.id === statusButton.dataset.toggleQrLocation,
        );
        if (location) changeQrLocationStatus(location);
        return;
      }
      const button = event.target.closest("[data-view-qr-location]");
      if (!button) return;
      let location = qrLocations.find(
        (item) => item.id === button.dataset.viewQrLocation,
      );
      if (!location?.isActive) {
        toast("สถานที่นี้ปิดใช้งานอยู่ กรุณาเปิดใช้งานก่อนดูรายละเอียด QR");
        return;
      }
      if (location && !location.url) {
        button.disabled = true;
        try {
          const generated = await generateAdminLocationQr(location.id);
          location = toDashboardQrLocation(generated);
          await loadQrLocations();
        } catch (error) {
          if (await handleUnauthorizedResponse(error.status)) return;
          console.error("Generating QR location failed:", error);
          toast(error.message || "ไม่สามารถสร้าง QR Code ได้");
          return;
        } finally {
          button.disabled = false;
        }
      }
      if (!showQrLocation(location)) return;
      openModal("qrDetailModal", button);
    });
    $("#heroPrimary")?.addEventListener("click", () =>
      navigate(currentRole === "clerk" ? "clerk-center" : "jobs"),
    );

    // -------------------------------------------------------------------------
    // 20) Initial data loading: เริ่มหลังจากผูก event ทุกระบบเรียบร้อยแล้ว
    // -------------------------------------------------------------------------

    // โหลดข้อมูลแต่ละระบบตามลำดับ เพื่อให้ข้อมูลที่ render ภายหลังครบถ้วน
    async function loadInitialDashboardData() {
      renderStaff();
      await loadStaffAccounts();
      await loadQrLocations();
      await loadPendingFoundItems();
      await loadPendingLostItems();
      await loadApprovedLostFoundItems();
      await loadPendingOwnershipRequests();
      await loadRepairRequests();
      await loadCleaningTasks();
      await loadMyTaskHistory();
      await loadStaffNotifications();
      setRole(allowedRoles.includes(currentRole) ? currentRole : "admin");
    }

    await loadInitialDashboardData();
    const initialModalId = syncDashboardFromRoute();
    navigationReady = true;
    updateDashboardRoute(initialModalId, "replace");
    cleanupFilterSelects = enhanceFilterSelects();

    // DOM พร้อมใช้งานแล้ว จึงแสดงรายการสถานที่และปิด loading mask
    setTimeout(() => {
      renderQrLocations();
      $(".loading-mask")?.remove();
    }, 320);
  }

  onMounted(initializeDashboard);
  onBeforeUnmount(() => {
    cleanupFilterSelects();
    cleanupDashboardEvents();
  });

  return { activeRole };
}
