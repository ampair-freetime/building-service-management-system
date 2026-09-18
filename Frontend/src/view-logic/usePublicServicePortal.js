import { installServiceFormValidation } from "../services/serviceFormValidation.js";
import {
  requestProgress,
  requestStatusPresentation,
  serviceTypeForRequest,
} from "../services/requestStatus.js";
import { onMounted, onUnmounted, ref } from "vue";
import {
  createFoundItem,
  createFoundItemClaim,
  createLostItem,
  getLostFoundItem,
  searchLostFoundItems,
  trackLostFoundItem,
  trackServiceRequest,
} from "../services/api";

export function usePublicServicePortal() {
  const validationCleanups = [];
  const sidebarOpen = ref(false);
  const closeSidebar = () => { sidebarOpen.value = false; };
  const toggleSidebar = () => { sidebarOpen.value = !sidebarOpen.value; };
  const compactSidebar = window.matchMedia("(min-width: 681px) and (max-width: 980px)");
  onMounted(() => compactSidebar.addEventListener("change", closeSidebar));
  onUnmounted(() => compactSidebar.removeEventListener("change", closeSidebar));
  // รอ Vue สร้าง DOM ก่อนผูก event เพราะหน้านี้ควบคุมองค์ประกอบผ่าน querySelector
  onMounted(() => {
    document.title = "CS Building Care";

    const pages = document.querySelectorAll(".page");
    const navItems = document.querySelectorAll(".nav-item");
    const sidebar = document.getElementById("sidebar");
    const bottomButtons = document.querySelectorAll(".bottom-nav > button");
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    let currentPage = "dashboard";
    let activePostFilter = "all";
    let lastModalTrigger = null;
    let toastTimer = 0;
    let detailAction = "close";
    let detailRequestId = 0;
    let selectedClaimItem = "";
    let selectedClaimItemCode = "";
    // เก็บเฉพาะคำร้องที่ผู้ใช้ส่งจริงในรอบการเปิดหน้านี้ ไม่มีข้อมูลตัวอย่างปะปน
    const trackedRequests = new Map();


    function syncBottomNavigation(modalId = "") {
      bottomButtons.forEach((button) => {
        const matchesPage = button.dataset.bottomPage === currentPage;
        const matchesModal = modalId && button.dataset.openModal === modalId;
        button.classList.toggle("active", Boolean(matchesPage || matchesModal));
      });
    }

    function scrollToForm(selector) {
      const form = document.querySelector(selector);
      if (!form) return;

      window.setTimeout(
        () => {
          form.scrollIntoView({
            behavior: prefersReducedMotion ? "auto" : "smooth",
            block: "start",
          });

          const firstField = form.querySelector(
            'input:not([type="hidden"]):not([disabled]), select:not([disabled]), textarea:not([disabled])',
          );
          firstField?.focus({ preventScroll: true });
        },
        prefersReducedMotion ? 0 : 120,
      );
    }

    function navigate(pageId) {
      const destination = document.getElementById(pageId);
      if (!destination || !destination.classList.contains("page")) return;
      currentPage = pageId;
      pages.forEach((page) =>
        page.classList.toggle("active", page.id === pageId),
      );
      navItems.forEach((item) =>
        item.classList.toggle("active", item.dataset.page === pageId),
      );
      syncBottomNavigation();
      closeSidebar();
      window.scrollTo({
        top: 0,
        behavior: prefersReducedMotion ? "auto" : "smooth",
      });

      if (pageId === "lost") {
        openLostView("browse", false);
        void filterPosts();
      }

    }

    navItems.forEach((item) =>
      item.addEventListener("click", () => navigate(item.dataset.page)),
    );
    document.querySelectorAll("[data-go]").forEach((button) =>
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        navigate(button.dataset.go);
        if (button.dataset.lostTab && button.dataset.lostTab !== "browse") {
          openLostView(button.dataset.lostTab);
        }
      }),
    );
    document.querySelectorAll("[data-card-go]").forEach((card) => {
      const openCard = () => {
        navigate(card.dataset.cardGo);
        if (card.dataset.cardGo === "lost") openLostView("browse");
      };
      card.addEventListener("click", (event) => {
        if (!event.target.closest("button")) openCard();
      });
      card.addEventListener("keydown", (event) => {
        if (
          (event.key === "Enter" || event.key === " ") &&
          !event.target.closest("button")
        ) {
          event.preventDefault();
          openCard();
        }
      });
    });

    function openLostView(viewName, moveToForm = true) {
      document
        .querySelectorAll(".lost-view")
        .forEach((view) =>
          view.classList.toggle("active", view.id === `lost-view-${viewName}`),
        );
      document
        .querySelectorAll(".lost-tab")
        .forEach((tab) =>
          tab.classList.toggle("active", tab.dataset.lostView === viewName),
        );
      document
        .querySelectorAll("[data-open-lost-view]")
        .forEach((button) =>
          button.classList.toggle(
            "active",
            button.dataset.openLostView === viewName,
          ),
        );
      if (viewName === "report-found") {
        const now = new Date();
        const offsetDate = new Date(
          now.getTime() - now.getTimezoneOffset() * 60000,
        );
        const dateInput = document.getElementById("publicFoundDate");
        const timeInput = document.getElementById("publicFoundTime");
        if (dateInput && !dateInput.value)
          dateInput.value = offsetDate.toISOString().slice(0, 10);
        if (timeInput && !timeInput.value)
          timeInput.value = offsetDate.toISOString().slice(11, 16);
      }

      if (moveToForm) {
        const lostViewForms = {
          // ปุ่มดูประกาศทั้งหมดเลื่อนไปยังส่วนรายการประกาศโดยตรง
          browse: "#lostSearchResults",
          "report-lost": "#lostItemForm",
          "report-found": "#publicFoundForm",
        };
        if (lostViewForms[viewName]) scrollToForm(lostViewForms[viewName]);
      }
    }

    document
      .querySelectorAll("[data-lost-view]")
      .forEach((tab) =>
        // แถบแท็บใช้สลับเนื้อหาเท่านั้น จึงไม่เลื่อนหน้าจอไปยังฟอร์ม
        tab.addEventListener("click", () =>
          openLostView(tab.dataset.lostView, false),
        ),
      );
    document
      .querySelectorAll("[data-open-lost-view]")
      .forEach((button) =>
        button.addEventListener("click", () => {
          const viewName = button.dataset.openLostView;
          if (viewName === "browse") {
            void filterPosts();
          } else {
            openLostView(viewName, false);
          }

          window.requestAnimationFrame(() => {
            document.querySelector(".lost-tabs")?.scrollIntoView({
              behavior: prefersReducedMotion ? "auto" : "smooth",
              block: "start",
            });
          });
        }),
      );

    function showToast(message) {
      const toast = document.getElementById("toastMessage");
      window.clearTimeout(toastTimer);
      toast.textContent = message;
      toast.classList.add("show");
      toastTimer = window.setTimeout(
        () => toast.classList.remove("show"),
        2400,
      );
    }

    function closeUiModal(id, restoreFocus = true) {
      const modal = document.getElementById(id);
      if (!modal || !modal.classList.contains("open")) return;
      modal.classList.remove("open");
      modal.setAttribute("aria-hidden", "true");
      if (!document.querySelector(".ui-modal.open")) {
        document.body.classList.remove("modal-open");
        syncBottomNavigation();
      }
      // คืน focus ให้ปุ่มที่เปิด modal เพื่อให้ใช้งานต่อด้วยคีย์บอร์ดได้ โดยตรวจว่าปุ่มยังอยู่ใน DOM
      if (
        restoreFocus &&
        lastModalTrigger instanceof HTMLElement &&
        document.contains(lastModalTrigger)
      ) {
        lastModalTrigger.focus();
      }
    }

    function openUiModal(id, trigger = document.activeElement) {
      const modal = document.getElementById(id);
      if (!modal) return;
      document
        .querySelectorAll(".ui-modal.open")
        .forEach((openModal) => closeUiModal(openModal.id, false));
      lastModalTrigger = trigger instanceof HTMLElement ? trigger : null;
      modal.classList.add("open");
      modal.removeAttribute("aria-hidden");
      document.body.classList.add("modal-open");
      syncBottomNavigation(id);
      // เลื่อน focus หลังเปลี่ยนสถานะ modal เพื่อให้ช่องเป้าหมายพร้อมแสดงผล
      window.requestAnimationFrame(() => {
        const focusTarget = modal.querySelector(
          'input:not([type="hidden"]), select, textarea, button:not([disabled])',
        );
        focusTarget?.focus();
      });
    }

    document.querySelectorAll("[data-open-modal]").forEach((button) =>
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        openUiModal(button.dataset.openModal, button);
      }),
    );
    document
      .querySelectorAll("[data-modal-close]")
      .forEach((button) =>
        button.addEventListener("click", () =>
          closeUiModal(button.dataset.modalClose),
        ),
      );
    document.querySelectorAll(".ui-modal").forEach((modal) =>
      modal.addEventListener("click", (event) => {
        if (event.target === modal) closeUiModal(modal.id);
      }),
    );
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        const openModal = document.querySelector(".ui-modal.open");
        if (openModal) closeUiModal(openModal.id);
        else if (sidebar.classList.contains("open")) closeSidebar();
      }
    });
    // นับลำดับการค้นหา เพื่อป้องกันผลเก่าทับผลล่าสุด
    let searchRequestId = 0;

    // ค้นหาประกาศตามคำค้นและประเภท แล้วแสดงผลจาก API
    async function filterPosts() {
      const requestId = ++searchRequestId;
      const query = document.getElementById("lostSearch").value.trim();
      const summary = document.getElementById("resultSummary");
      const empty = document.getElementById("noSearchResults");
      const grid = document.getElementById("postGrid");

      openLostView("browse", false);
      summary.textContent = "กำลังค้นหา...";
      empty.hidden = true;
      grid.setAttribute("aria-busy", "true");
      grid.classList.add("is-loading");

      try {
        const result = await searchLostFoundItems({
          type: activePostFilter,
          search: query,
        });

        // ป้องกันผลจากการค้นหาเก่าทับการค้นหาครั้งล่าสุด
        if (requestId !== searchRequestId) return;

        renderSearchPosts(result.items);
        summary.textContent = `แสดง ${result.items.length} จาก ${result.total} รายการ`;
        empty.hidden = result.items.length !== 0;
        grid.removeAttribute("aria-busy");
        grid.classList.remove("is-loading");
      } catch (error) {
        if (requestId !== searchRequestId) return;
        summary.textContent = error.message;
        grid.removeAttribute("aria-busy");
        grid.classList.remove("is-loading");
      }
    }

    function renderSearchPosts(items) {
      // แสดงผลรายการค้นหาใน grid โดยสร้าง article.post-card สำหรับแต่ละ item
      const grid = document.getElementById("postGrid");
      // ล้างผลเก่าก่อนแสดงผลใหม่
      grid.replaceChildren();
      const cards = items.map((item) => {
        const card = document.createElement("article");
        card.className = "post-card";
        // เก็บรหัสและประเภทจาก API ไว้ใช้เปิดรายละเอียดและส่งคำขอรับคืน
        card.dataset.itemCode = item.item_code;
        card.dataset.kind = item.report_type;

        const imageContainer = document.createElement("div");
        imageContainer.className = "post-image";
        const firstImage = item.images?.[0];

        if (firstImage?.url) {
          const image = document.createElement("img");
          image.src = firstImage.url;
          image.alt = `รูป${item.item_name}`;
          image.loading = "lazy";
          imageContainer.append(image);
        } else {
          // ใช้ไอคอนเป็นภาพวางเมื่อประกาศไม่ได้แนบรูป
          const icon = document.createElementNS(
            "http://www.w3.org/2000/svg",
            "svg",
          );
          icon.classList.add("icon");
          icon.setAttribute("aria-hidden", "true");
          const use = document.createElementNS(
            "http://www.w3.org/2000/svg",
            "use",
          );
          use.setAttribute(
            "href",
            item.report_type === "found" ? "#i-box" : "#i-search",
          );
          icon.append(use);
          imageContainer.append(icon);
        }

        const body = document.createElement("div");
        body.className = "post-body";

        const meta = document.createElement("div");
        meta.className = "post-meta";

        const type = document.createElement("span");
        type.className = `post-type ${item.report_type}`;
        type.textContent =
          item.report_type === "found" ? "พบของแล้ว" : "กำลังตามหา";

        const date = document.createElement("span");
        date.className = "post-date";
        date.textContent = formatItemDate(item.event_datetime);
        meta.append(type, date);

        const title = document.createElement("h4");
        title.textContent = item.item_name;

        const description = document.createElement("p");
        description.textContent =
          item.description || item.location_detail || "ไม่มีรายละเอียด";

        const detailButton = document.createElement("button");
        detailButton.type = "button";
        detailButton.className = "post-detail-button";
        detailButton.textContent = "ดูรายละเอียด";

        body.append(meta, title, description, detailButton);
        card.append(imageContainer, body);
        bindPostCard(card);
        return card;
      });

      grid.replaceChildren(...cards);
    }

    document.querySelectorAll(".filter-chip").forEach((chip) =>
      chip.addEventListener("click", () => {
        activePostFilter = chip.dataset.filter;
        document
          .querySelectorAll(".filter-chip")
          .forEach((item) => item.classList.toggle("active", item === chip));
        filterPosts();
      }),
    );
    document
      .getElementById("lostSearchForm")
      .addEventListener("submit", (event) => {
        event.preventDefault();
        const searchButton = document.getElementById("lostSearchButton");
        searchButton.classList.add("pressed");
        window.setTimeout(() => {
          searchButton.classList.remove("pressed");
          filterPosts();
          window.requestAnimationFrame(() => {
            document.getElementById("lostSearchResults").scrollIntoView({
              behavior: prefersReducedMotion ? "auto" : "smooth",
              block: "start",
            });
          });
        }, 120);
      });

    // โหลดประกาศจริงทันทีเพื่อแทนที่การ์ดตัวอย่างที่ไม่มี item_code จากฐานข้อมูล
    filterPosts();

    function setDetailContent(data, action = "close") {
      document.getElementById("detailModalTitle").textContent =
        data.dialogTitle || "รายละเอียด";
      document.getElementById("detailTitle").textContent =
        data.title || "รายการ";
      document.getElementById("detailDescription").textContent =
        data.detail || "ไม่มีรายละเอียดเพิ่มเติม";
      document.getElementById("detailDate").textContent = data.date || "–";
      document.getElementById("detailLocation").textContent =
        data.location || "–";
      const detailHero = document.querySelector("#detailModal .detail-hero");
      const detailImage = document.getElementById("detailImage");
      const detailIcon = document.getElementById("detailIcon");
      const use = detailIcon.querySelector("use");
      use.setAttribute("href", data.icon || "#i-box");

      // แสดงรูปจริงแบบเต็มกรอบในรายละเอียด และใช้ไอคอนแทนเมื่อไม่มีรูปหรือโหลดรูปไม่ได้
      const showImagePlaceholder = () => {
        detailImage.hidden = true;
        detailImage.removeAttribute("src");
        detailIcon.removeAttribute("hidden");
        detailHero.classList.remove("has-image");
      };
      if (data.imageUrl) {
        detailImage.alt = `รูป${data.title || "ประกาศ"}`;
        detailImage.onerror = showImagePlaceholder;
        detailImage.src = data.imageUrl;
        detailImage.hidden = false;
        detailIcon.setAttribute("hidden", "");
        detailHero.classList.add("has-image");
      } else {
        showImagePlaceholder();
      }
      const continueButton = document.getElementById("detailContinueButton");
      detailAction = action;
      continueButton.textContent =
        action === "claim"
          ? "นี่อาจเป็นของฉัน"
          : action === "contact"
            ? "ติดต่อเจ้าหน้าที่"
            : "รับทราบ";
    }

    function setItemDetailState(state, message = "") {
      document.getElementById("detailLoadingState").hidden =
        state !== "loading";
      document.getElementById("detailNotFoundState").hidden =
        state !== "not-found";
      document.getElementById("detailErrorState").hidden = state !== "error";
      document.getElementById("detailContent").hidden = state !== "content";
      if (message)
        document.getElementById("detailErrorMessage").textContent = message;
    }

    function itemStatusLabel(status) {
      return (
        {
          pending: "รอเจ้าหน้าที่ตรวจสอบ",
          approved: "เผยแพร่แล้ว",
          claimed: "มีผู้ขอรับคืน",
          closed: "ปิดประกาศแล้ว",
          rejected: "ไม่อนุมัติ",
        }[status] ||
        status ||
        "–"
      );
    }

    function formatItemDate(value) {
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return "–";
      return new Intl.DateTimeFormat("th-TH", {
        dateStyle: "medium",
        timeStyle: "short",
      }).format(date);
    }

    function openDetailFromData(element, trigger = element) {
      setDetailContent(
        {
          title: element.dataset.title,
          detail: element.dataset.detail,
          date: element.dataset.date,
          location: element.dataset.location,
          status: element.dataset.status,
          code: element.dataset.code,
          icon:
            element.dataset.category === "repair"
              ? "#i-tools"
              : element.dataset.category === "clean"
                ? "#i-broom"
                : "#i-box",
        },
        "close",
      );
      openUiModal("detailModal", trigger);
    }

    document
      .querySelectorAll("[data-request-detail], [data-history-detail]")
      .forEach((item) =>
        item.addEventListener("click", () => openDetailFromData(item)),
      );
    async function openLostFoundDetail(card, trigger = card) {
      const requestId = ++detailRequestId;
      selectedClaimItemCode = "";
      selectedClaimItem =
        card.querySelector("h4")?.textContent.trim() || "รายการ";
      const isFound = card.dataset.kind === "found";
      const itemCode = card.dataset.itemCode || card.dataset.code || "";

      openUiModal("detailModal", trigger);

      // การ์ดตัวอย่างยังไม่มี item_code จึงแสดงข้อมูลเดิมจากหน้าเว็บได้ตามปกติ
      if (!itemCode) {
        setDetailContent(
          {
            dialogTitle: "รายละเอียดประกาศ",
            title: selectedClaimItem,
            detail: card.querySelector(".post-body p")?.textContent.trim(),
            date: card.querySelector(".post-date")?.textContent.trim(),
            location: card.dataset.search?.split(" ").slice(-3).join(" "),
            status: card.querySelector(".post-type")?.textContent.trim(),
            icon: isFound ? "#i-box" : "#i-search",
          },
          isFound ? "claim" : "contact",
        );
        setItemDetailState("content");
        return;
      }

      setItemDetailState("loading");

      try {
        const item = await getLostFoundItem(itemCode, card.dataset.kind);
        if (requestId !== detailRequestId) return;

        if (!item) {
          setItemDetailState("not-found");
          return;
        }

        selectedClaimItem = item.item_name;
        selectedClaimItemCode =
          item.report_type === "found" ? item.item_code : "";
        setDetailContent(
          {
            dialogTitle: "รายละเอียดประกาศ",
            title: item.item_name,
            detail: item.description,
            date: formatItemDate(item.event_datetime),
            location: item.location_detail,
            status: itemStatusLabel(item.status),
            code: item.item_code,
            icon: item.report_type === "found" ? "#i-box" : "#i-search",
            imageUrl: item.images?.[0]?.url,
          },
          item.report_type === "found" ? "claim" : "contact",
        );
        setItemDetailState("content");
      } catch (error) {
        if (requestId !== detailRequestId) return;
        setItemDetailState(
          "error",
          error.message || "ไม่สามารถโหลดรายละเอียดรายการได้",
        );
      }
    }

    function bindPostCard(card) {
      card
        .querySelector(".post-detail-button")
        ?.addEventListener("click", (event) => {
          event.stopPropagation();
          openLostFoundDetail(card, event.currentTarget);
        });
      card.tabIndex = 0;
      card.addEventListener("click", (event) => {
        if (!event.target.closest("button")) openLostFoundDetail(card);
      });
      card.addEventListener("keydown", (event) => {
        if (
          event.target === card &&
          (event.key === "Enter" || event.key === " ")
        ) {
          event.preventDefault();
          openLostFoundDetail(card);
        }
      });
    }

    document.querySelectorAll(".post-card").forEach(bindPostCard);

    function openClaim(itemName, trigger) {
      if (!selectedClaimItemCode) {
        showToast("กรุณาเลือกประกาศพบของจากผลค้นหาอีกครั้ง");
        return;
      }
      const claimItemName = document.getElementById("claimItemName");
      const claimModal = document.getElementById("claimModal");
      if (!claimItemName || !claimModal) {
        showToast("ระบบคำขอรับคืนอยู่ระหว่างจัดเตรียม");
        return;
      }
      selectedClaimItem = itemName;
      claimItemName.textContent = itemName;
      openUiModal("claimModal", trigger);
      window.requestAnimationFrame(() =>
        document.getElementById("claimName")?.focus(),
      );
    }

    document
      .getElementById("detailContinueButton")
      .addEventListener("click", (event) => {
        if (detailAction === "claim")
          openClaim(
            selectedClaimItem ||
              document.getElementById("detailTitle").textContent,
            event.currentTarget,
          );
        else if (detailAction === "contact") {
          closeUiModal("detailModal", false);
          showToast("ส่งข้อมูลติดต่อให้เจ้าหน้าที่แล้ว");
        } else closeUiModal("detailModal");
      });

    function showConfirmationDetails(details = {}) {
      document.getElementById("successLocation").textContent = details.location || "";
      document.getElementById("successProblem").textContent = details.problem || "";
      document.getElementById("successRequestDetails").hidden = !(details.location || details.problem);
    }

    function showSuccess(type, recipientEmail = "", requestId = "", details = {}) {
      showConfirmationDetails(details);
      const trackingCode =
        requestId || `BC-${Math.floor(1000 + Math.random() * 9000)}`;
      const serviceType = serviceTypeForRequest(
        { requestType: type },
        trackingCode,
      );

      trackedRequests.set(trackingCode, {
        summary: type,
        status: details.status || "waiting",
        serviceType,
        requestType:
          serviceType === "cleaning"
            ? "แจ้งทำความสะอาด"
            : serviceType === "repair"
              ? "แจ้งซ่อม"
              : "คำร้องที่ส่งผ่านระบบ",
        itemName: details.problem || "ไม่ระบุรายละเอียด",
        updatedAt: "เพิ่งส่งคำร้อง",
        email: recipientEmail.trim().toLowerCase(),
        demo: Boolean(details.demo),
      });
      document.getElementById("successType").textContent = type;
      document.getElementById("successInstruction").textContent =
        "เก็บรหัสคำร้องนี้ไว้เพื่อติดตามสถานะ";
      document.getElementById("successCode").textContent = trackingCode;
      document.getElementById("successCode").hidden = false;
      document.getElementById("successEmail").textContent = recipientEmail
        ? `ติดตามด้วย ${trackingCode} + ${recipientEmail}`
        : "เก็บรหัสนี้ไว้ใช้ติดตามสถานะร่วมกับอีเมล";
      document.getElementById("successEmail").hidden = false;
      document.getElementById("viewStatusButton").hidden = false;
      document.getElementById("backHomeButton").textContent = "กลับหน้าหลัก";
      // ทุกประเภทคำร้องใช้ฟอร์มติดตามเดียวกันในหน้าภาพรวม
      document.getElementById("trackingCode").value = trackingCode;
      if (recipientEmail)
        document.getElementById("trackingEmail").value = recipientEmail;
      validateTrackingField(document.getElementById("trackingCode"));
      if (recipientEmail)
        validateTrackingField(document.getElementById("trackingEmail"));
      openUiModal("successModal", document.activeElement);
    }

    function showLostFoundConfirmation(type, message) {
      showConfirmationDetails();
      document.getElementById("successType").textContent = type;
      document.getElementById("successInstruction").textContent =
        "กรุณาติดต่อเจ้าหน้าที่ธุรการด้วยตนเอง";
      document.getElementById("successCode").hidden = true;
      document.getElementById("successEmail").textContent = message;
      document.getElementById("successEmail").hidden = false;
      document.getElementById("viewStatusButton").hidden = true;
      document.getElementById("backHomeButton").textContent = "รับทราบ";
      openUiModal("successModal", document.activeElement);
    }

    // blob URL ของพรีวิวใช้หน่วยความจำในเบราว์เซอร์ ต้องคืนด้วย revokeObjectURL เมื่อเลิกใช้
    function clearImagePreviews(form) {
      form.querySelectorAll(".image-preview").forEach((preview) => {
        const image = preview.querySelector("img");
        if (image.src.startsWith("blob:")) URL.revokeObjectURL(image.src);
        image.removeAttribute("src");
        preview.querySelector("span").textContent = "";
        preview.classList.remove("visible");
      });
    }

    function createDemoRequestCode(prefix) {
      const today = new Date();
      const date = [today.getFullYear(), String(today.getMonth() + 1).padStart(2, "0"), String(today.getDate()).padStart(2, "0")].join("");
      const suffix = crypto.randomUUID().replaceAll("-", "").slice(0, 8).toUpperCase();
      return `${prefix}-${date}-${suffix}`;
    }

    const cleaningForm = document.querySelector("#clean form");
    const confirmCleaningRequest = (event) => {
      const { demo, request_code, recipientEmail, location, problem, status } = event.detail;
      showSuccess(
        "แจ้งทำความสะอาดเรียบร้อยแล้ว",
        recipientEmail,
        demo ? createDemoRequestCode("CLEAN") : request_code,
        { location, problem, status, demo },
      );
    };
    cleaningForm?.addEventListener("cleaning-request-confirmed", confirmCleaningRequest);
    validationCleanups.push(() => cleaningForm?.removeEventListener("cleaning-request-confirmed", confirmCleaningRequest));

    const repairForm = document.querySelector("#repair form");
    const confirmRepairRequest = (event) => {
      const { demo, request_code, recipientEmail, location, problem, status } = event.detail;
      showSuccess(
        "แจ้งซ่อมเรียบร้อยแล้ว",
        recipientEmail,
        demo ? createDemoRequestCode("REPAIR") : request_code,
        { location, problem, status, demo },
      );
    };
    repairForm?.addEventListener("repair-request-confirmed", confirmRepairRequest);
    validationCleanups.push(() => repairForm?.removeEventListener("repair-request-confirmed", confirmRepairRequest));

    document.querySelectorAll("[data-service-validation]").forEach(form => {
      validationCleanups.push(installServiceFormValidation(form));
    });

    const lostItemForm = document.getElementById("lostItemForm");
    const lostItemValidationRules = {
      item_category: (value) => (value ? "" : "กรุณาเลือกประเภทสิ่งของ"),
      item_name: (value) => {
        const trimmed = value.trim();
        if (!trimmed) return "กรุณาระบุชื่อสิ่งของ";
        if (trimmed.length < 2) return "ชื่อสิ่งของต้องมีอย่างน้อย 2 ตัวอักษร";
        return "";
      },
      event_datetime: (value) => {
        if (!value) return "กรุณาระบุวันที่และเวลาที่คาดว่าทำหาย";
        if (new Date(value).getTime() > Date.now()) {
          return "วันที่และเวลาที่ทำหายต้องไม่เป็นเวลาในอนาคต";
        }
        return "";
      },
      location_detail: (value) => {
        const trimmed = value.trim();
        if (!trimmed) return "กรุณาระบุสถานที่คาดว่าทำหาย";
        if (trimmed.length < 2) return "สถานที่ต้องมีอย่างน้อย 2 ตัวอักษร";
        return "";
      },
      description: (value) => {
        const trimmed = value.trim();
        if (!trimmed) return "กรุณาระบุลักษณะเฉพาะของสิ่งของ";
        if (trimmed.length < 10) return "รายละเอียดต้องมีอย่างน้อย 10 ตัวอักษร";
        return "";
      },
      reporter_email: (value, field) => {
        if (!value.trim()) return "กรุณาระบุอีเมลสำหรับติดตามสถานะ";
        if (field.validity.typeMismatch) return "กรุณาระบุอีเมลให้ถูกต้อง";
        return "";
      },
    };

    function validateLostItemField(field) {
      const message =
        lostItemValidationRules[field.name]?.(field.value, field) || "";
      field.setCustomValidity(message);
      field.setAttribute("aria-invalid", String(Boolean(message)));
      document.getElementById(`${field.id}Error`).textContent = message;
      return !message;
    }

    function validateLostItemForm(form) {
      const fields = Array.from(
        form.querySelectorAll("select, input, textarea"),
      );
      // ใช้ map ตรวจทุกช่องก่อน every เพื่อแสดง error ครบ ไม่หยุดตรวจเมื่อเจอช่องแรกที่ผิด
      const isValid = fields
        .filter((field) => lostItemValidationRules[field.name])
        .map(validateLostItemField)
        .every(Boolean);

      if (isValid) {
        fields.forEach((field) => {
          if (field.type !== "file") field.value = field.value.trim();
        });
      }
      return isValid;
    }

    lostItemForm
      .querySelectorAll("select, input, textarea")
      .forEach((field) => {
        if (!lostItemValidationRules[field.name]) return;
        const eventName = field.tagName === "SELECT" ? "change" : "input";
        field.addEventListener(eventName, () => validateLostItemField(field));
        field.addEventListener("blur", () => validateLostItemField(field));
      });

    lostItemForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = event.currentTarget;
      // ป้องกัน submit ซ้ำระหว่างคำขอเดิมยังรอคำตอบ
      if (form.querySelector('button[type="submit"]').disabled) return;

      if (!validateLostItemForm(form) || !form.checkValidity()) {
        return;
      }

      const formData = new FormData(form);
      const submitButton = form.querySelector('button[type="submit"]');
      // รองรับชื่อช่องเดิมระหว่างหน้าเว็บอัปเดต แต่ส่งให้ Backend ด้วยชื่อ reporter_email เสมอ
      const emailValue =
        formData.get("reporter_email") ?? formData.get("recipient_email");
      const reporterEmail =
        typeof emailValue === "string" ? emailValue.trim() : "";
      if (!reporterEmail) {
        showToast("กรุณาระบุอีเมลสำหรับติดตามสถานะ แล้วลองส่งอีกครั้ง");
        form.querySelector('input[type="email"]')?.focus();
        return;
      }

      submitButton.disabled = true;
      submitButton.textContent = "กำลังส่งประกาศ...";

      try {
        // datetime-local ไม่มีเขตเวลา: แปลงเวลาท้องถิ่นเป็น ISO UTC ก่อนส่งให้ Backend
        formData.set(
          "event_datetime",
          new Date(formData.get("event_datetime")).toISOString(),
        );
        formData.set("reporter_email", reporterEmail);
        formData.delete("recipient_email");
        // ช่องไฟล์ที่ไม่ได้เลือกอาจอยู่ใน FormData เป็น File ชื่อว่าง ต้องลบเพื่อไม่ให้ Backend รับเป็นรูปว่าง
        const image = formData.get("image");
        if (!image || !image.name) formData.delete("image");
        const item = await createLostItem(formData);

        clearImagePreviews(form);
        form.reset();
        showSuccess("แจ้งของหายเรียบร้อยแล้ว", reporterEmail, item.item_code);
      } catch (error) {
        showToast(error.message || "ไม่สามารถส่งรายการของหายได้");
        // คืนปุ่มทุกกรณี; ล้างฟอร์มเฉพาะเมื่อสำเร็จ เพื่อให้ข้อมูลยังอยู่เมื่อส่งไม่ผ่าน
      } finally {
        submitButton.disabled = false;
        submitButton.textContent = "เผยแพร่ประกาศตามหา";
      }
    });

    const foundItemForm = document.getElementById("publicFoundForm");
    const foundItemValidationRules = {
      item_category: (value) => (value ? "" : "กรุณาเลือกประเภทสิ่งของ"),
      item_name: (value) => validateRequiredText(value, "ชื่อสิ่งของ"),
      found_date: (value) => {
        if (!value) return "กรุณาระบุวันที่พบสิ่งของ";
        if (new Date(`${value}T23:59:59`).getTime() > Date.now()) {
          return "วันที่พบสิ่งของต้องไม่เป็นวันในอนาคต";
        }
        return "";
      },
      found_time: (value, field) => {
        if (!value) return "กรุณาระบุเวลาที่พบสิ่งของ";
        const foundDate = field.form.elements.found_date.value;
        if (
          foundDate &&
          new Date(`${foundDate}T${value}`).getTime() > Date.now()
        ) {
          return "เวลาที่พบสิ่งของต้องไม่เป็นเวลาในอนาคต";
        }
        return "";
      },
      location_detail: (value) =>
        validateRequiredText(value, "สถานที่พบสิ่งของ"),
      custody_location: (value) =>
        validateRequiredText(value, "จุดรับฝากสิ่งของ"),
      description: (value) =>
        validateRequiredText(value, "รายละเอียดสิ่งของ", 10),
      private_detail: (value) =>
        validateRequiredText(value, "รายละเอียดลับ", 10),
      recipient_email: (value, field) => {
        if (!value.trim()) return "กรุณาระบุอีเมลสำหรับติดตามสถานะ";
        if (field.validity.typeMismatch) return "กรุณาระบุอีเมลให้ถูกต้อง";
        return "";
      },
    };

    function validateRequiredText(value, label, minimumLength = 2) {
      const trimmed = value.trim();
      if (!trimmed) return `กรุณาระบุ${label}`;
      if (trimmed.length < minimumLength) {
        return `${label}ต้องมีอย่างน้อย ${minimumLength} ตัวอักษร`;
      }
      return "";
    }

    function validateFoundItemField(field) {
      const message =
        foundItemValidationRules[field.name]?.(field.value, field) || "";
      field.setCustomValidity(message);
      field.setAttribute("aria-invalid", String(Boolean(message)));
      document.getElementById(`${field.id}Error`).textContent = message;
      return !message;
    }

    function validateFoundItemForm(form) {
      const fields = Array.from(
        form.querySelectorAll("select, input, textarea"),
      );
      const isValid = fields
        .filter((field) => foundItemValidationRules[field.name])
        .map(validateFoundItemField)
        .every(Boolean);

      if (isValid) {
        fields.forEach((field) => {
          if (field.type !== "file") field.value = field.value.trim();
        });
      }
      return isValid;
    }

    foundItemForm
      .querySelectorAll("select, input, textarea")
      .forEach((field) => {
        if (!foundItemValidationRules[field.name]) return;
        const eventName = field.tagName === "SELECT" ? "change" : "input";
        field.addEventListener(eventName, () => validateFoundItemField(field));
        field.addEventListener("blur", () => validateFoundItemField(field));
      });

    foundItemForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = event.currentTarget;
      const submitButton = form.querySelector('button[type="submit"]');
      if (submitButton.disabled) return;

      if (!validateFoundItemForm(form) || !form.checkValidity()) {
        return;
      }

      const formData = new FormData(form);
      const emailValue = formData.get("recipient_email");
      const reporterEmail =
        typeof emailValue === "string" ? emailValue.trim() : "";
      if (!reporterEmail) {
        showToast("กรุณาระบุอีเมลสำหรับติดตามสถานะ แล้วลองส่งอีกครั้ง");
        form.querySelector('input[type="email"]')?.focus();
        return;
      }

      submitButton.disabled = true;
      submitButton.textContent = "กำลังส่งรายการ...";

      try {
        const foundDate = formData.get("found_date");
        const foundTime = formData.get("found_time");
        formData.set(
          "event_datetime",
          new Date(`${foundDate}T${foundTime}`).toISOString(),
        );
        formData.set("reporter_email", reporterEmail);
        formData.set(
          "private_verification_detail",
          formData.get("private_detail"),
        );
        formData.delete("found_date");
        formData.delete("found_time");
        formData.delete("recipient_email");
        formData.delete("private_detail");
        const image = formData.get("image");
        if (!image || !image.name) formData.delete("image");

        const item = await createFoundItem(formData);
        clearImagePreviews(form);
        form.reset();
        showSuccess("แจ้งพบของเรียบร้อยแล้ว", reporterEmail, item.item_code);
      } catch (error) {
        showToast(error.message || "ไม่สามารถส่งรายการพบของได้");
      } finally {
        submitButton.disabled = false;
        submitButton.textContent = "ส่งให้เจ้าหน้าที่ตรวจสอบ";
      }
    });

    document.querySelectorAll(".image-input").forEach((input) => {
      const container = input.closest(".upload-field");
      const preview = container.querySelector(".image-preview");
      const image = preview.querySelector("img");
      const fileName = preview.querySelector(".image-file-name");
      const removeButton = preview.querySelector(".remove-image");
      const fileError = document.getElementById(input.dataset.errorId);
      const allowedTypes = ["image/jpeg", "image/png", "image/webp"];
      const maxSize = Number(input.dataset.maxSize) || 5 * 1024 * 1024;
      const maxSizeMB = maxSize / (1024 * 1024);

      const setFileError = (message = "") => {
        // เมื่อมีข้อความ ฟอร์มจะไม่ผ่าน checkValidity()
        input.setCustomValidity(message);
        input.setAttribute("aria-invalid", String(Boolean(message)));
        if (fileError) fileError.textContent = message;
      };
      function clearPreview() {
        // คืนหน่วยความจำของรูปเดิมก่อนล้างหรือเปลี่ยนพรีวิว
        if (image.src.startsWith("blob:")) URL.revokeObjectURL(image.src);
        image.removeAttribute("src");
        fileName.textContent = "";
        preview.classList.remove("visible");
      }

      input.addEventListener("change", () => {
        const file = input.files[0];
        clearPreview();
        setFileError();
        if (!file) return;

        let message = "";
        if (!allowedTypes.includes(file.type)) {
          message = "รองรับเฉพาะไฟล์ JPG, PNG หรือ WebP";
        } else if (file.size === 0) {
          message = "ไฟล์รูปภาพว่างเปล่า กรุณาเลือกไฟล์ใหม่";
        } else if (file.size > maxSize) {
          message = `รูปภาพต้องมีขนาดไม่เกิน ${maxSizeMB} MB`;
        }

        if (message) {
          input.value = "";
          setFileError(message);
          showToast(message);
          return;
        }
        // สร้างพรีวิวเฉพาะไฟล์ที่ผ่านการตรวจแล้ว
        image.src = URL.createObjectURL(file);
        fileName.textContent = file.name;
        preview.classList.add("visible");
      });
      removeButton.addEventListener("click", () => {
        input.value = "";
        clearPreview();
        setFileError();
        input.focus();
      });
    });

    function validateTrackingField(field) {
      let message = "";
      if (field.id === "trackingCode" && !field.value.trim()) {
        message = "กรุณากรอกรหัสคำร้อง";
      }
      if (field.id === "trackingEmail") {
        if (!field.value.trim()) {
          message = "กรุณากรอกอีเมลที่ใช้แจ้งคำร้อง";
        } else if (field.validity.typeMismatch) {
          message = "กรุณากรอกอีเมลให้ถูกต้อง";
        }
      }

      field.setCustomValidity(message);
      field.setAttribute("aria-invalid", String(Boolean(message)));
      document.getElementById(`${field.id}Error`).textContent = message;
      return !message;
    }

    const trackingFields = [
      document.getElementById("trackingCode"),
      document.getElementById("trackingEmail"),
    ];
    trackingFields.forEach((field) => {
      field.addEventListener("input", () => validateTrackingField(field));
      field.addEventListener("blur", () => validateTrackingField(field));
    });

    function renderTrackingProgress(item, code, ids) {
      if (!ids.progress || !ids.progressSteps) return;
      const container = document.getElementById(ids.progress);
      const list = document.getElementById(ids.progressSteps);
      const progress = requestProgress(item, code);

      list.replaceChildren();
      if (!progress) {
        container.hidden = true;
        return;
      }

      progress.steps.forEach((step, index) => {
        const itemElement = document.createElement("li");
        itemElement.className =
          index < progress.currentIndex
            ? "complete"
            : index === progress.currentIndex
              ? "current"
              : "upcoming";
        if (step.status === "rejected") {
          itemElement.classList.add("rejected");
        }
        if (index === progress.currentIndex) {
          itemElement.setAttribute("aria-current", "step");
        }

        const marker = document.createElement("span");
        marker.className = "tracking-progress-marker";
        marker.setAttribute("aria-hidden", "true");
        marker.textContent = index < progress.currentIndex ? "✓" : String(index + 1);

        const label = document.createElement("span");
        label.className = "tracking-progress-label";
        label.textContent = step.label;

        itemElement.append(marker, label);
        list.append(itemElement);
      });
      container.hidden = false;
    }

    function renderTrackingResult(item, code, ids, { refreshed = false } = {}) {
      const result = document.getElementById(ids.result);
      const statusBadge = document.getElementById(ids.status);

      // แสดงรหัสที่ผู้ใช้กรอก
      document.getElementById(ids.code).textContent = code;

      if (!item) {
        // API ตอบ 404 เมื่อรหัสไม่พบหรืออีเมลไม่ตรง
        document.getElementById(ids.text).textContent =
          "ไม่พบคำร้อง กรุณาตรวจสอบรหัสและอีเมลอีกครั้ง";

        statusBadge.textContent = "ไม่พบข้อมูล";
        statusBadge.className = "status not-found";

        if (ids.details) {
          document.getElementById(ids.details).hidden = true;
        }
        if (ids.progress) {
          document.getElementById(ids.progress).hidden = true;
        }

        result.classList.add("show");
        showToast("ไม่พบคำร้อง");
        return;
      }

      // ใช้ label และสีชุดเดียวกันกับทุกประเภทคำร้อง โดยบริการอาคารมีขั้นตอนเพิ่มด้านล่าง
      const presentation = requestStatusPresentation(item, code);

      document.getElementById(ids.text).textContent =
        presentation.description ||
        item.summary ||
        `สถานะล่าสุด: ${presentation.label}`;

      statusBadge.textContent = presentation.label;
      statusBadge.className = `status ${presentation.className}`;

      if (ids.details) {
        document.getElementById(ids.details).hidden = false;

        document.getElementById(ids.requestType).textContent =
          item.requestType ||
          (item.request_type === "cleaning"
            ? "แจ้งทำความสะอาด"
            : item.request_type === "repair"
              ? "แจ้งซ่อม"
              : item.report_type === "found"
                ? "แจ้งพบของ"
                : "แจ้งของหาย");

        document.getElementById(ids.itemName).textContent =
          item.itemName || item.item_name || item.title || item.problem || "–";

        document.getElementById(ids.updatedAt).textContent =
          item.updatedAt || formatItemDate(item.updated_at);
      }

      renderTrackingProgress(item, code, ids);

      result.classList.add("show");
      showToast(refreshed ? "รีเฟรชสถานะแล้ว" : "พบข้อมูลคำร้อง");
    }

    const trackingForm = document.getElementById("trackingForm");
    const trackingSubmitButton = trackingForm.querySelector('button[type="submit"]');
    const refreshTrackingButton = document.getElementById("refreshTrackingStatus");
    const trackingResult = document.getElementById("trackingResult");
    const trackingIds = {
      result: "trackingResult",
      code: "trackingResultCode",
      text: "trackingResultText",
      status: "trackingResultStatus",
      details: "trackingDetails",
      requestType: "trackingRequestType",
      itemName: "trackingItemName",
      updatedAt: "trackingUpdatedAt",
      progress: "trackingProgress",
      progressSteps: "trackingProgressSteps",
    };
    let isTrackingRequestPending = false;

    async function loadTrackingStatus({ refreshed = false } = {}) {
      if (isTrackingRequestPending) return;

      const isValid = trackingFields.map(validateTrackingField).every(Boolean);
      if (!isValid) {
        trackingFields.find((field) => !field.checkValidity())?.focus();
        return;
      }

      const code = document
        .getElementById("trackingCode")
        .value.trim()
        .toUpperCase();
      const email = document
        .getElementById("trackingEmail")
        .value.trim()
        .toLowerCase();

      isTrackingRequestPending = true;
      trackingResult.setAttribute("aria-busy", "true");
      trackingSubmitButton.disabled = true;
      refreshTrackingButton.disabled = true;
      trackingSubmitButton.textContent = refreshed
        ? "ตรวจสอบสถานะ"
        : "กำลังตรวจสอบ…";
      refreshTrackingButton.textContent = refreshed
        ? "กำลังรีเฟรช…"
        : "รีเฟรชสถานะ";

      try {
        const isLostFoundCode =
          code.startsWith("LOST-") || code.startsWith("FOUND-");
        const isServiceCode =
          code.startsWith("CLN-") ||
          code.startsWith("CLEAN-") ||
          code.startsWith("REPAIR-");
        const localItem = trackedRequests.get(code);
        if (!isLostFoundCode && (!isServiceCode || localItem?.demo)) {
          // เปิดโอกาสให้ browser วาด loading state ก่อนอัปเดตข้อมูลในหน่วยความจำ
          await new Promise((resolve) => window.setTimeout(resolve, 0));
        }
        const item = isLostFoundCode
          ? await trackLostFoundItem(code, email)
          : isServiceCode && !localItem?.demo
            ? await trackServiceRequest(code, email)
            : localItem && (!localItem.email || localItem.email === email)
              ? localItem
              : null;
        renderTrackingResult(item, code, trackingIds, { refreshed });
        document.getElementById("trackingRefreshTime").textContent =
          `ตรวจสอบล่าสุด ${new Intl.DateTimeFormat("th-TH", {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
          }).format(new Date())}`;
      } catch (error) {
        // แสดงกรอบผลลัพธ์แม้เกิดปัญหาการเชื่อมต่อ และให้ผู้ใช้กดรีเฟรชซ้ำได้
        document.getElementById(trackingIds.code).textContent = code;
        document.getElementById(trackingIds.text).textContent =
          error.message || "ไม่สามารถตรวจสอบสถานะได้";

        const statusBadge = document.getElementById(trackingIds.status);
        statusBadge.textContent = "เกิดข้อผิดพลาด";
        statusBadge.className = "status not-found";

        document.getElementById(trackingIds.details).hidden = true;
        document.getElementById(trackingIds.progress).hidden = true;
        trackingResult.classList.add("show");
        showToast("ไม่สามารถรีเฟรชสถานะได้ กรุณาลองอีกครั้ง");
      } finally {
        isTrackingRequestPending = false;
        trackingResult.removeAttribute("aria-busy");
        trackingSubmitButton.disabled = false;
        refreshTrackingButton.disabled = false;
        trackingSubmitButton.textContent = "ตรวจสอบสถานะ";
        refreshTrackingButton.textContent = "รีเฟรชสถานะ";
      }
    }

    trackingForm.addEventListener("submit", (event) => {
      event.preventDefault();
      void loadTrackingStatus();
    });
    refreshTrackingButton.addEventListener("click", () => {
      void loadTrackingStatus({ refreshed: true });
    });
    document.querySelectorAll("[data-scroll-track]").forEach((button) =>
      button.addEventListener("click", () => {
        navigate("dashboard");
        bottomButtons.forEach((item) =>
          item.classList.toggle("active", item === button),
        );
        window.setTimeout(
          () => {
            document.getElementById("trackingSection").scrollIntoView({
              behavior: prefersReducedMotion ? "auto" : "smooth",
              block: "center",
            });
            document.getElementById("trackingCode").focus();
          },
          prefersReducedMotion ? 0 : 120,
        );
      }),
    );

    document.querySelectorAll("[data-service-choice]").forEach((button) =>
      button.addEventListener("click", () => {
        const destination = button.dataset.serviceChoice;
        closeUiModal("serviceChooserModal", false);
        navigate(destination);
        if (destination === "lost") openLostView("browse");
      }),
    );

    const claimForm = document.getElementById("claimForm");
    const claimValidationRules = {
      claimant_name: (value) => {
        const trimmed = value.trim();
        if (!trimmed) return "กรุณาระบุชื่อผู้ขอรับคืน";
        if (trimmed.length < 2) return "ชื่อต้องมีอย่างน้อย 2 ตัวอักษร";
        return "";
      },
      claimant_email: (value, field) => {
        if (!value.trim()) return "กรุณาระบุอีเมลสำหรับติดต่อ";
        if (field.validity.typeMismatch) return "กรุณาระบุอีเมลให้ถูกต้อง";
        return "";
      },
      proof_detail: (value) => {
        const trimmed = value.trim();
        if (!trimmed) return "กรุณาระบุรายละเอียดเพื่อยืนยันความเป็นเจ้าของ";
        if (trimmed.length < 10) return "รายละเอียดต้องมีอย่างน้อย 10 ตัวอักษร";
        if (/password|รหัสผ่าน|เลขบัตร/i.test(trimmed)) {
          return "ห้ามใส่รหัสผ่านหรือเลขบัตรในรายละเอียด";
        }
        return "";
      },
    };

    function validateClaimField(field) {
      const message =
        claimValidationRules[field.name]?.(field.value, field) || "";
      field.setCustomValidity(message);
      field.setAttribute("aria-invalid", String(Boolean(message)));
      document.getElementById(`${field.id}Error`).textContent = message;
      return !message;
    }

    function validateClaimForm() {
      return Array.from(claimForm.querySelectorAll("input, textarea"))
        .filter((field) => claimValidationRules[field.name])
        .map(validateClaimField)
        .every(Boolean);
    }

    claimForm?.querySelectorAll("input, textarea").forEach((field) => {
      field.addEventListener("input", () => validateClaimField(field));
      field.addEventListener("blur", () => validateClaimField(field));
    });

    claimForm?.addEventListener("submit", async (event) => {
      event.preventDefault();

      if (!validateClaimForm()) {
        showToast("กรุณากรอกข้อมูลยืนยันให้ครบ");
        return;
      }

      if (!selectedClaimItemCode) {
        showToast("ไม่พบรหัสรายการที่ต้องการขอรับคืน");
        return;
      }

      const submitButton = claimForm.querySelector('button[type="submit"]');
      const formData = new FormData(claimForm);
      const payload = {
        claimant_name: String(formData.get("claimant_name") || "").trim(),
        claimant_email: String(formData.get("claimant_email") || "")
          .trim()
          .toLowerCase(),
        proof_detail: String(formData.get("proof_detail") || "").trim(),
      };

      submitButton.disabled = true;
      submitButton.textContent = "กำลังส่ง...";

      try {
        const claim = await createFoundItemClaim(
          selectedClaimItemCode,
          payload,
        );

        claimForm.reset();
        closeUiModal("claimModal", false);

        // Backend ใช้ UUID เป็นรหัส claim จึงต้องแสดงค่าที่ตอบกลับแทนการสุ่มรหัสใน frontend
        document.getElementById("successType").textContent =
          `ส่งคำขอรับคืน ${selectedClaimItem} แล้ว`;
        document.getElementById("successInstruction").textContent =
          claim.message;
        document.getElementById("successCode").textContent = claim.id;
        document.getElementById("successCode").hidden = false;
        document.getElementById("successEmail").textContent =
          `รหัสประกาศ ${claim.found_item_code} · สถานะ ${claim.status}`;
        document.getElementById("successEmail").hidden = false;

        // ฟอร์มติดตามรวมรับรหัสคำร้องหลัก แต่ยังไม่รับ UUID ของคำขอรับคืน
        document.getElementById("viewStatusButton").hidden = true;
        document.getElementById("backHomeButton").textContent = "รับทราบ";
        openUiModal("successModal", document.activeElement);
      } catch (error) {
        showToast(error.message || "ไม่สามารถส่งคำขอรับคืนได้");
      } finally {
        submitButton.disabled = false;
        submitButton.textContent = "ส่งคำขอรับคืน";
      }
    });

    const viewStatusButton = document.getElementById("viewStatusButton");
    viewStatusButton?.addEventListener("click", () => {
      closeUiModal("successModal", false);
      navigate("dashboard");

      window.setTimeout(
        () => {
          document.getElementById("trackingSection").scrollIntoView({
            behavior: prefersReducedMotion ? "auto" : "smooth",
            block: "center",
          });
          // รหัสและอีเมลถูกกรอกไว้ตั้งแต่ได้รับผลสำเร็จ เหลือเพียงกดตรวจสอบสถานะ
          document.getElementById("trackingCode").focus({
            preventScroll: true,
          });
        },
        80,
      );
    });

    document.getElementById("backHomeButton")?.addEventListener("click", () => {
      closeUiModal("successModal", false);
      navigate("dashboard");
    });

    const syncNetworkState = () =>
      document.body.classList.toggle("offline", !navigator.onLine);
    window.addEventListener("online", () => {
      syncNetworkState();
      showToast("กลับมาออนไลน์แล้ว");
    });
    window.addEventListener("offline", syncNetworkState);
    syncNetworkState();
    // syncUnreadBadges();
    document
      .querySelectorAll(".ui-modal")
      .forEach((modal) => modal.setAttribute("aria-hidden", "true"));
    window.setTimeout(
      () => document.querySelector(".loading-mask")?.remove(),
      320,
    );
  });

  onUnmounted(() => {
    validationCleanups.forEach(cleanup => cleanup());
    document.body.classList.remove("modal-open", "offline");
  });
  return { sidebarOpen, closeSidebar, toggleSidebar };
}
