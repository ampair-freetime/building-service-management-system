import { onMounted, ref } from "vue";
import { createStaffDashboardData } from "./staff-dashboard/data.js";
import { canRoleOpenPage } from "../config/staff-role-pages.js";
import {
  badgeClass,
  currentTimeHM,
  escapeHtml,
  isTerminalStatus,
  loadQrCodeLibrary,
  nowThai,
  sourceLabel,
  todayISO,
  validImage,
} from "./staff-dashboard/utils.js";

export function useStaffDashboard() {
  const allowedRoles = ["housekeeper", "technician", "clerk", "admin"];
  const savedRole = localStorage.getItem("buildingCareRole");
  const activeRole = ref(allowedRoles.includes(savedRole) ? savedRole : "admin");

  onMounted(async () => {
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
      currentHistoryView,
      notificationSets,
      announcements,
      categories,
    } = createStaffDashboardData();
    let currentRole = activeRole.value;
    let currentLostTab = "inventory";
    let currentClerkCenterView = "approvals";
    const readClaimNotifications = new Set();
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
      const jobsTitle = $("#jobsTitle");
      const jobsSubtitle = $("#jobsSubtitle");
      if (jobsTitle) jobsTitle.textContent = c.jobTitle || "ศูนย์รับงานรวม";
      if (jobsSubtitle) jobsSubtitle.textContent = c.jobSubtitle || "";
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
      const active = $(".nav-item.active");
      if (active && !roleAllows(active, role)) navigate("dashboard");
      populateCategoryFilter();
      populateMyHistoryTypes();
      renderMetrics();
      renderQueue();
      renderActivities();
      renderJobs();
      renderNotifications();
      renderClerkCenter();
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
        "clerk-center": "ศูนย์รับงาน",
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
      if (page === "clerk-center") renderClerkCenter();
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
      if (tab === "claims") return "";
      const approved = approvalGroup(item.status) === "approved";
      return `<div class="decision-strip"><button class="approve-btn" type="button" data-lost-action="approve" data-tab="${tab}" data-item-id="${item.id}">${approved ? "อนุมัติอยู่แล้ว" : "อนุมัติ"}</button><button class="reject-btn" type="button" data-lost-action="reject" data-tab="${tab}" data-item-id="${item.id}">ไม่อนุมัติ</button></div>`;
    }
    function approvalGroup(status = "") {
      if (status.includes("ไม่อนุมัติ") || status.includes("ไม่ผ่าน")) return "rejected";
      if (status.includes("รออนุมัติ")) return "pending";
      return "approved";
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
    function setClerkCenterView(view) {
      currentClerkCenterView = view === "claims" ? "claims" : "approvals";
      $$("#clerkCenterTabs [data-clerk-center-view]").forEach((tab) => tab.classList.toggle("active", tab.dataset.clerkCenterView === currentClerkCenterView));
      $$('[data-clerk-center-panel]').forEach((panel) => panel.classList.toggle("active", panel.dataset.clerkCenterPanel === currentClerkCenterView));
    }
    function renderClerkCenter() {
      const pendingList = $("#pendingApprovalList"), claimList = $("#activeClaimList");
      if (!pendingList || !claimList) return;
      const approvals = pendingApprovalRequests();
      const claims = lostSets.claims.filter((item) => item.status !== "คืนของแล้ว");
      ["#pendingApprovalCount", "#pendingApprovalTabCount"].forEach((id) => $(id).textContent = approvals.length);
      ["#activeClaimCount", "#activeClaimTabCount"].forEach((id) => $(id).textContent = claims.length);
      pendingList.innerHTML = approvals.length ? approvals.map((item) => {
        const record = findLostItem(item.tab, item.approvalId);
        return `<article class="clerk-request-card"><div class="clerk-request-top"><div><span class="approval-type ${item.tab}">${approvalTypeLabel(item.tab)}</span><h4>${item.approvalId} · ${escapeHtml(item.title)}</h4></div><span class="badge wait">รออนุมัติ</span></div><p>${escapeHtml(item.text)}</p><div class="clerk-request-meta"><span>${escapeHtml(record?.custody || "รอการตรวจสอบ")}</span></div><div class="clerk-request-actions"><button class="small-btn" type="button" data-center-action="detail" data-tab="${item.tab}" data-item-id="${item.approvalId}">ดูรายละเอียด</button><button class="approve-btn" type="button" data-center-action="approve" data-tab="${item.tab}" data-item-id="${item.approvalId}">อนุมัติ</button><button class="reject-btn" type="button" data-center-action="reject" data-tab="${item.tab}" data-item-id="${item.approvalId}">ไม่อนุมัติ</button></div></article>`;
      }).join("") : '<div class="empty">ไม่มีคำขอที่รออนุมัติ</div>';
      claimList.innerHTML = claims.length ? claims.map((item) => `<article class="clerk-request-card"><div class="clerk-request-top"><div><span class="approval-type claims">คำขอรับของ</span><h4>${item.id} · ${escapeHtml(item.title)}</h4></div><span class="badge ${badgeClass(item.status)}">${item.status}</span></div><p>${escapeHtml(item.place)}</p><div class="clerk-request-meta"><span>${escapeHtml(item.custody || "คำขอใหม่")}</span></div><div class="clerk-request-actions"><button class="small-btn" type="button" data-center-action="claim-detail" data-item-id="${item.id}">ดูรายละเอียดคำขอ</button></div></article>`).join("") : '<div class="empty">ไม่มีคำขอรับของที่กำลังดำเนินการ</div>';
      setClerkCenterView(currentClerkCenterView);
    }
    function renderLost() {
      if (!$("#lostGrid")) return;
      const data = currentLostTab === "claims"
        ? lostSets.claims.filter((item) => item.status !== "คืนของแล้ว")
        : lostSets[currentLostTab].filter((item) => approvalGroup(item.status) === "approved");
      renderClerkCenter();
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
              const claimHint = currentLostTab === "claims" ? '<div class="approval-note"><strong>รับคำขออัตโนมัติ:</strong> ธุรการไม่ต้องกดอนุมัติ สามารถตรวจรายละเอียด นัดหมาย และยืนยันการส่งคืนได้</div>' : "";
              return `<article class="lost-card" tabindex="0" data-lost-card="${
                i.id
              }"><div class="lost-image"><svg class="icon"><use href="#i-box"/></svg></div><div class="lost-content"><span class="badge ${badgeClass(
                i.status
              )}">${i.status}</span><h3>${i.id} · ${i.title}</h3><p>${
                i.place
              }</p>${claimHint}${controls}${currentLostTab === "claims" ? "" : decisionButtons(currentLostTab, i)}${adminDelete}</div></article>`;
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
      renderClerkCenter();
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
      if (!$("#historyTable")) return;
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
      const list = notificationSets[currentRole] || [];
      const approvals = currentRole === "clerk" ? pendingApprovalRequests() : [];
      const claims = currentRole === "clerk" ? activeClaimNotifications() : [];
      const unread = list.filter((n) => n.unread).length + approvals.length + claims.filter((n) => n.unread).length;
      $("#notificationTitle").textContent = currentRole === "clerk" ? "การแจ้งเตือนของธุรการ" : `การแจ้งเตือนของ${roleConfig[currentRole].label}`;
      [$("#notificationCount"), $("#mobileNotificationCount")].forEach(
        (badge) => {
          badge.textContent = unread;
          badge.style.display = unread ? "grid" : "none";
        }
      );
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
      });
      if (role === currentRole) renderNotifications();
    }
    function markNotificationsRead() {
      notificationSets[currentRole].forEach((n) => (n.unread = false));
      if (currentRole === "clerk") lostSets.claims.filter((item) => item.status !== "คืนของแล้ว").forEach((item) => readClaimNotifications.add(item.id));
      renderNotifications();
      toast("ทำเครื่องหมายว่าอ่านทั้งหมดแล้ว");
    }
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
      if (!$("#qrCode")) return;
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
      if (!$("#announcementList")) return;
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
      button.addEventListener("click", () =>
        navigate(currentRole === "clerk" && button.dataset.go === "jobs" ? "clerk-center" : button.dataset.go)
      )
    );
    $$("[data-role-switch]").forEach((button) =>
      button.addEventListener("click", () => {
        // Demo only: reload so the next Role receives its own isolated page tree.
        localStorage.setItem("buildingCareRole", button.dataset.roleSwitch);
        window.location.reload();
      })
    );
    $("#menuToggle")?.addEventListener("click", toggleSidebar);
    $("#sidebarBackdrop")?.addEventListener("click", closeSidebar);
    $("#sidebarCollapse")?.addEventListener("click", () => {
      $(".app").classList.toggle("sidebar-collapsed");
      $("#sidebarCollapse use").setAttribute(
        "href",
        $(".app").classList.contains("sidebar-collapsed")
          ? "#i-menu"
          : "#i-chevron"
      );
    });
    $("#dashboardQuickActions")?.addEventListener("click", (event) => {
      const button = event.target.closest("[data-dashboard-action]");
      if (!button) return;
      const index = Number(button.dataset.dashboardAction);
      if (currentRole === "clerk") {
        navigate("clerk-center");
        setClerkCenterView(index === 4 ? "claims" : "approvals");
        renderClerkCenter();
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
    $("#jobSearch")?.addEventListener("input", renderJobs);
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
      else {
        currentLostTab = "claims";
        renderLost();
        navigate("lost");
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
    $("#progressImage")?.addEventListener("change", (event) => {
      if (event.target.files[0]) previewProgressFile(event.target.files[0]);
    });
    $("#removeProgressImage")?.addEventListener("click", () => {
      $("#progressImage").value = "";
      resetUploadPreview();
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
    $("#statusUpdateForm")?.addEventListener("submit", (event) => {
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
    $("#completeForm")?.addEventListener("submit", (event) => {
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
    $("#historySearch")?.addEventListener("input", renderHistory);
    $("#historySourceFilter")?.addEventListener("change", renderHistory);
    $("#historyActionFilter")?.addEventListener("change", renderHistory);
    $("#historyTabs")?.addEventListener("click", (event) => {
      const button = event.target.closest(".board-tab");
      if (!button) return;
      currentHistoryView = button.dataset.historyView;
      $$("#historyTabs .board-tab").forEach((tab) =>
        tab.classList.toggle("active", tab === button)
      );
      renderHistory();
    });
    $("#myHistoryList")?.addEventListener("click", (event) => {
      const button = event.target.closest("[data-history-detail]");
      if (!button) return;
      const job = allJobs.find(
        (item) => item.id === button.dataset.historyDetail
      );
      if (job) openJobDetail(job.id, button);
      else toast(`แสดงรายละเอียด ${button.dataset.historyDetail} จากประวัติแล้ว`);
    });
    $("#historyTable")?.addEventListener("click", (event) => {
      const button = event.target.closest("[data-history-action]");
      if (!button) return;
      if (button.dataset.historyAction === "restore")
        restoreDeleted(button.dataset.historyUid);
      else permanentDelete(button.dataset.historyUid);
    });
    $("#staffOverviewTable")?.addEventListener("click", (event) => {
      const button = event.target.closest("[data-staff-overview]");
      if (button) showStaffOverview(button.dataset.staffOverview);
    });
    $("#staffTable")?.addEventListener("click", (event) => {
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
    $("#lostTabs")?.addEventListener("click", (event) => {
      const button = event.target.closest(".tab");
      if (!button) return;
      $$(".tab").forEach((tab) => tab.classList.toggle("active", tab === button));
      currentLostTab = button.dataset.tab;
      renderLost();
    });
    $("#clerkCenterTabs")?.addEventListener("click", (event) => {
      const tab = event.target.closest("[data-clerk-center-view]");
      if (tab) setClerkCenterView(tab.dataset.clerkCenterView);
    });
    $("#pendingApprovalList")?.addEventListener("click", (event) => {
      const button = event.target.closest("[data-center-action]");
      if (!button) return;
      const { centerAction: action, tab, itemId: id } = button.dataset;
      if (action === "approve") approveLostItem(tab, id);
      else if (action === "reject") openReject(tab, id);
      else openLostDetail(tab, id, button);
    });
    $("#activeClaimList")?.addEventListener("click", (event) => {
      const button = event.target.closest("[data-center-action]");
      if (button?.dataset.centerAction === "claim-detail")
        openClaimDetail(button.dataset.itemId, button);
    });
    $("#lostGrid")?.addEventListener("click", (event) => {
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
    $("#notificationButton")?.addEventListener("click", (event) => {
      event.stopPropagation();
      toggleNotificationPanel(event.currentTarget);
    });
    $("#mobileNotification")?.addEventListener("click", (event) => {
      event.stopPropagation();
      toggleNotificationPanel(event.currentTarget);
    });
    $("#notificationPanel")?.addEventListener("click", (event) => {
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
      item.unread = false;
      renderNotifications();
      $("#notificationPanel").classList.remove("open");
      const match = item.text.match(/(?:CL|RP)-\d+/);
      if (match) openJobDetail(match[0], itemButton);
      else if (currentRole === "clerk") navigate("clerk-center");
      else toast(item.title);
    });
    document.addEventListener("click", () => {
      $("#notificationPanel").classList.remove("open");
      $("#notificationButton").setAttribute("aria-expanded", "false");
    });
    $("#markAllRead")?.addEventListener("click", markNotificationsRead);
    $("#openStaffModal")?.addEventListener("click", (event) =>
      openModal("staffModal", event.currentTarget)
    );
    $("#addFoundBtn")?.addEventListener("click", (event) =>
      openModal("foundModal", event.currentTarget)
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
    $("#staffForm")?.addEventListener("submit", (event) => {
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
    $("#appointmentForm")?.addEventListener("submit", (event) => {
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
    $("#openQrModal")?.addEventListener("click", (event) =>
      openModal("qrFormModal", event.currentTarget)
    );
    $("#qrForm")?.addEventListener("submit", (event) => {
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
    $("#downloadQr")?.addEventListener("click", () => {
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
    $("#announcementForm")?.addEventListener("submit", (event) => {
      event.preventDefault();
      saveAnnouncement("เผยแพร่");
    });
    $("#saveAnnouncementDraft")?.addEventListener("click", () =>
      saveAnnouncement("Draft")
    );
    $("#announcementList")?.addEventListener("click", (event) => {
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
    $("#heroPrimary")?.addEventListener("click", () =>
      navigate(currentRole === "clerk" ? "clerk-center" : "jobs")
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

  return { activeRole };
}
