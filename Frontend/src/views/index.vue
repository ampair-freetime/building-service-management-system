<script setup>
import { onMounted, onUnmounted } from "vue";

onMounted(() => {
  document.title = "CMU Building Care";

  const pages = document.querySelectorAll(".page");
  const navItems = document.querySelectorAll(".nav-item");
  const sidebar = document.getElementById("sidebar");
  const sidebarBackdrop = document.getElementById("sidebarBackdrop");
  const bottomButtons = document.querySelectorAll(".bottom-nav > button");
  const prefersReducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
  ).matches;
  let currentPage = "dashboard";
  let activePostFilter = "all";
  let lastModalTrigger = null;
  let toastTimer = 0;
  let detailAction = "close";
  let selectedClaimItem = "";

  function closeSidebar() {
    sidebar.classList.remove("open");
    sidebarBackdrop.classList.remove("open");
    document
      .getElementById("menuButton")
      .setAttribute("aria-expanded", "false");
  }

  function toggleSidebar(forceOpen) {
    const shouldOpen =
      typeof forceOpen === "boolean"
        ? forceOpen
        : !sidebar.classList.contains("open");
    sidebar.classList.toggle("open", shouldOpen);
    sidebarBackdrop.classList.toggle("open", shouldOpen);
    document
      .getElementById("menuButton")
      .setAttribute("aria-expanded", String(shouldOpen));
  }

  function syncBottomNavigation(modalId = "") {
    bottomButtons.forEach((button) => {
      const matchesPage = button.dataset.bottomPage === currentPage;
      const matchesModal = modalId && button.dataset.openModal === modalId;
      button.classList.toggle("active", Boolean(matchesPage || matchesModal));
    });
  }

  function navigate(pageId) {
    const destination = document.getElementById(pageId);
    if (!destination || !destination.classList.contains("page")) return;
    currentPage = pageId;
    pages.forEach((page) =>
      page.classList.toggle("active", page.id === pageId)
    );
    navItems.forEach((item) =>
      item.classList.toggle("active", item.dataset.page === pageId)
    );
    syncBottomNavigation();
    closeSidebar();
    window.scrollTo({
      top: 0,
      behavior: prefersReducedMotion ? "auto" : "smooth",
    });
  }

  navItems.forEach((item) =>
    item.addEventListener("click", () => navigate(item.dataset.page))
  );
  document.querySelectorAll("[data-go]").forEach((button) =>
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      navigate(button.dataset.go);
      if (button.dataset.lostTab) openLostView(button.dataset.lostTab);
    })
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
  document
    .getElementById("menuButton")
    .addEventListener("click", () => toggleSidebar());
  sidebarBackdrop.addEventListener("click", closeSidebar);

  function openLostView(viewName) {
    document
      .querySelectorAll(".lost-view")
      .forEach((view) =>
        view.classList.toggle("active", view.id === `lost-view-${viewName}`)
      );
    document
      .querySelectorAll(".lost-tab")
      .forEach((tab) =>
        tab.classList.toggle("active", tab.dataset.lostView === viewName)
      );
  }

  document
    .querySelectorAll("[data-lost-view]")
    .forEach((tab) =>
      tab.addEventListener("click", () => openLostView(tab.dataset.lostView))
    );
  document
    .querySelectorAll("[data-open-lost-view]")
    .forEach((button) =>
      button.addEventListener("click", () =>
        openLostView(button.dataset.openLostView)
      )
    );

  function showToast(message) {
    const toast = document.getElementById("toastMessage");
    window.clearTimeout(toastTimer);
    toast.textContent = message;
    toast.classList.add("show");
    toastTimer = window.setTimeout(() => toast.classList.remove("show"), 2400);
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
    window.requestAnimationFrame(() => {
      const focusTarget = modal.querySelector(
        'input:not([type="hidden"]), select, textarea, button:not([disabled])'
      );
      focusTarget?.focus();
    });
  }

  document.querySelectorAll("[data-open-modal]").forEach((button) =>
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      openUiModal(button.dataset.openModal, button);
    })
  );
  document
    .querySelectorAll("[data-modal-close]")
    .forEach((button) =>
      button.addEventListener("click", () =>
        closeUiModal(button.dataset.modalClose)
      )
    );
  document.querySelectorAll(".ui-modal").forEach((modal) =>
    modal.addEventListener("click", (event) => {
      if (event.target === modal) closeUiModal(modal.id);
    })
  );
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      const openModal = document.querySelector(".ui-modal.open");
      if (openModal) closeUiModal(openModal.id);
      else if (sidebar.classList.contains("open")) closeSidebar();
    }
  });

  function filterPosts() {
    const searchInput = document.getElementById("lostSearch");
    const query = searchInput.value.trim().toLowerCase();
    let visible = 0;
    document.querySelectorAll(".post-card").forEach((card) => {
      const matchesType =
        activePostFilter === "all" || card.dataset.kind === activePostFilter;
      const matchesQuery =
        !query || card.dataset.search.toLowerCase().includes(query);
      const show = matchesType && matchesQuery;
      card.style.display = show ? "" : "none";
      if (show) visible += 1;
    });
    document.getElementById("resultSummary").textContent = query
      ? `พบ ${visible} รายการที่ตรงกับ “${query}”`
      : `แสดง ${visible} รายการล่าสุด`;
    openLostView("browse");
  }

  document.querySelectorAll(".filter-chip").forEach((chip) =>
    chip.addEventListener("click", () => {
      activePostFilter = chip.dataset.filter;
      document
        .querySelectorAll(".filter-chip")
        .forEach((item) => item.classList.toggle("active", item === chip));
      filterPosts();
    })
  );
  document
    .getElementById("lostSearchButton")
    .addEventListener("click", filterPosts);
  document.getElementById("lostSearch").addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      filterPosts();
    }
  });

  function setDetailContent(data, action = "close") {
    document.getElementById("detailModalTitle").textContent =
      data.dialogTitle || "รายละเอียด";
    document.getElementById("detailTitle").textContent = data.title || "รายการ";
    document.getElementById("detailDescription").textContent =
      data.detail || "ไม่มีรายละเอียดเพิ่มเติม";
    document.getElementById("detailDate").textContent = data.date || "–";
    document.getElementById("detailLocation").textContent =
      data.location || "–";
    document.getElementById("detailStatus").textContent =
      data.status || "รอรับเรื่อง";
    document.getElementById("detailCode").textContent =
      data.code || `BC-${Math.floor(1000 + Math.random() * 9000)}`;
    const use = document.querySelector("#detailIcon use");
    use.setAttribute("href", data.icon || "#i-box");
    const continueButton = document.getElementById("detailContinueButton");
    detailAction = action;
    continueButton.textContent =
      action === "claim"
        ? "นี่อาจเป็นของฉัน"
        : action === "contact"
        ? "ติดต่อเจ้าหน้าที่"
        : "รับทราบ";
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
      "close"
    );
    openUiModal("detailModal", trigger);
  }

  document
    .querySelectorAll("[data-request-detail], [data-history-detail]")
    .forEach((item) =>
      item.addEventListener("click", () => openDetailFromData(item))
    );
  document.querySelectorAll(".post-detail-button").forEach((button) =>
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      const card = button.closest(".post-card");
      selectedClaimItem = card.querySelector("h4").textContent.trim();
      const isFound = card.dataset.kind === "found";
      setDetailContent(
        {
          dialogTitle: "รายละเอียดประกาศ",
          title: selectedClaimItem,
          detail: card.querySelector(".post-body p").textContent.trim(),
          date: card.querySelector(".post-date").textContent.trim(),
          location: card.dataset.search.split(" ").slice(-3).join(" "),
          status: card.querySelector(".post-type").textContent.trim(),
          icon: isFound ? "#i-box" : "#i-search",
        },
        isFound ? "claim" : "contact"
      );
      openUiModal("detailModal", button);
    })
  );

  function openClaim(itemName, trigger) {
    selectedClaimItem = itemName;
    document.getElementById("claimItemName").textContent = itemName;
    openUiModal("claimModal", trigger);
  }

  document.querySelectorAll(".claim-button").forEach((button) =>
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      openClaim(
        button.closest(".post-card").querySelector("h4").textContent.trim(),
        button
      );
    })
  );
  document
    .getElementById("detailContinueButton")
    .addEventListener("click", (event) => {
      if (detailAction === "claim")
        openClaim(
          selectedClaimItem ||
            document.getElementById("detailTitle").textContent,
          event.currentTarget
        );
      else if (detailAction === "contact") {
        closeUiModal("detailModal", false);
        showToast("ส่งข้อมูลติดต่อให้เจ้าหน้าที่แล้ว");
      } else closeUiModal("detailModal");
    });

  function showSuccess(type, recipientEmail = "") {
    const requestId = `BC-${Math.floor(1000 + Math.random() * 9000)}`;
    document.getElementById("successType").textContent = type;
    document.getElementById("successCode").textContent = requestId;
    document.getElementById("successEmail").textContent = recipientEmail
      ? `ติดตามด้วย ${requestId} + ${recipientEmail}`
      : "เก็บรหัสนี้ไว้ใช้ติดตามสถานะร่วมกับอีเมล";
    document.getElementById("trackingCode").value = requestId;
    if (recipientEmail)
      document.getElementById("trackingEmail").value = recipientEmail;
    openUiModal("successModal", document.activeElement);
  }

  function clearImagePreviews(form) {
    form.querySelectorAll(".image-preview").forEach((preview) => {
      const image = preview.querySelector("img");
      if (image.src.startsWith("blob:")) URL.revokeObjectURL(image.src);
      image.removeAttribute("src");
      preview.querySelector("span").textContent = "";
      preview.classList.remove("visible");
    });
  }

  function submitDemo(event, type) {
    event.preventDefault();
    const form = event.currentTarget;
    if (!form.checkValidity()) {
      form.reportValidity();
      showToast("กรุณากรอกข้อมูลที่จำเป็นให้ครบ");
      return;
    }
    const recipientEmail =
      form.querySelector('[name="recipient_email"]')?.value.trim() || "";
    clearImagePreviews(form);
    form.reset();
    showSuccess(`${type}เรียบร้อยแล้ว`, recipientEmail);
  }

  document
    .querySelectorAll("[data-submit-type]")
    .forEach((form) =>
      form.addEventListener("submit", (event) =>
        submitDemo(event, form.dataset.submitType)
      )
    );

  document.querySelectorAll(".image-input").forEach((input) => {
    const container = input.closest(".upload-field");
    const preview = container.querySelector(".image-preview");
    const image = preview.querySelector("img");
    const fileName = preview.querySelector("span");
    const removeButton = preview.querySelector(".remove-image");
    input.addEventListener("change", () => {
      const file = input.files[0];
      if (!file) return;
      if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
        input.value = "";
        showToast("รองรับเฉพาะไฟล์ JPG, PNG หรือ WebP");
        return;
      }
      if (file.size > Number(input.dataset.maxSize)) {
        input.value = "";
        showToast("รูปภาพต้องมีขนาดไม่เกิน 5 MB");
        return;
      }
      if (image.src.startsWith("blob:")) URL.revokeObjectURL(image.src);
      image.src = URL.createObjectURL(file);
      fileName.textContent = file.name;
      preview.classList.add("visible");
    });
    removeButton.addEventListener("click", () => {
      if (image.src.startsWith("blob:")) URL.revokeObjectURL(image.src);
      input.value = "";
      image.removeAttribute("src");
      fileName.textContent = "";
      preview.classList.remove("visible");
      input.focus();
    });
  });

  document
    .getElementById("trackingForm")
    .addEventListener("submit", (event) => {
      event.preventDefault();
      const form = event.currentTarget;
      if (!form.checkValidity()) {
        form.reportValidity();
        return;
      }
      const code = document
        .getElementById("trackingCode")
        .value.trim()
        .toUpperCase();
      const email = document.getElementById("trackingEmail").value.trim();
      document.getElementById("trackingResultCode").textContent = code;
      document.getElementById(
        "trackingResultText"
      ).textContent = `ตรวจสอบด้วย ${email} · ตัวอย่างสถานะสำหรับเดโม`;
      document.getElementById("trackingResult").classList.add("show");
      showToast("พบข้อมูลคำร้อง");
    });
  document.querySelectorAll("[data-scroll-track]").forEach((button) =>
    button.addEventListener("click", () => {
      navigate("dashboard");
      window.setTimeout(
        () => {
          document
            .getElementById("trackingSection")
            .scrollIntoView({
              behavior: prefersReducedMotion ? "auto" : "smooth",
              block: "center",
            });
          document.getElementById("trackingCode").focus();
        },
        prefersReducedMotion ? 0 : 120
      );
    })
  );

  document.querySelectorAll("[data-service-choice]").forEach((button) =>
    button.addEventListener("click", () => {
      const destination = button.dataset.serviceChoice;
      closeUiModal("serviceChooserModal", false);
      navigate(destination);
      if (destination === "lost") openLostView("browse");
    })
  );

  document.getElementById("claimForm").addEventListener("submit", (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    if (!form.checkValidity()) {
      form.reportValidity();
      showToast("กรุณากรอกข้อมูลยืนยันให้ครบ");
      return;
    }
    const recipientEmail = document.getElementById("claimContact").value.trim();
    form.reset();
    showSuccess(`ส่งคำขอรับคืน ${selectedClaimItem} แล้ว`, recipientEmail);
  });
  document
    .getElementById("viewStatusButton")
    .addEventListener("click", (event) => {
      closeUiModal("successModal", false);
      navigate("dashboard");
      window.setTimeout(
        () =>
          document
            .getElementById("trackingSection")
            .scrollIntoView({
              behavior: prefersReducedMotion ? "auto" : "smooth",
              block: "center",
            }),
        80
      );
    });
  document.getElementById("backHomeButton").addEventListener("click", () => {
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
    320
  );
});

onUnmounted(() => {
  document.body.classList.remove("modal-open", "offline");
});
</script>

<template>
  <div class="user-page">
    <svg class="svg-sprite" aria-hidden="true" focusable="false">
      <symbol id="i-menu" viewBox="0 0 24 24">
        <path d="M4 7h16M4 12h16M4 17h16" />
      </symbol>
      <symbol id="i-user" viewBox="0 0 24 24">
        <circle cx="12" cy="8" r="4" />
        <path d="M4 21a8 8 0 0 1 16 0" />
      </symbol>
      <symbol id="i-pin" viewBox="0 0 24 24">
        <path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" />
        <circle cx="12" cy="10" r="2.5" />
      </symbol>
      <symbol id="i-qr" viewBox="0 0 24 24">
        <path
          d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h2v2h-2zM18 14h2v6h-4v-2h-2"
        />
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
        <path d="m3 7 9-4 9 4-9 4-9-4Z" />
        <path d="m3 7 9 4 9-4v10l-9 4-9-4V7Zm9 4v10" />
      </symbol>
      <symbol id="i-search" viewBox="0 0 24 24">
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-4-4" />
      </symbol>
      <symbol id="i-home" viewBox="0 0 24 24">
        <path d="m3 11 9-8 9 8v9h-6v-6H9v6H3z" />
      </symbol>
      <symbol id="i-history" viewBox="0 0 24 24">
        <path d="M3 12a9 9 0 1 0 3-6.7L3 8" />
        <path d="M3 3v5h5M12 7v5l3 2" />
      </symbol>
      <symbol id="i-plus" viewBox="0 0 24 24">
        <path d="M12 5v14M5 12h14" />
      </symbol>
      <symbol id="i-megaphone" viewBox="0 0 24 24">
        <path
          d="M3 11v2a2 2 0 0 0 2 2h3l9 4V5L8 9H5a2 2 0 0 0-2 2ZM8 15l1 5h3"
        />
        <path d="M21 9v6" />
      </symbol>
      <symbol id="i-chevron" viewBox="0 0 24 24">
        <path d="m9 18 6-6-6-6" />
      </symbol>
      <symbol id="i-upload" viewBox="0 0 24 24">
        <path d="M12 16V4m0 0L7 9m5-5 5 5M4 16v4h16v-4" />
      </symbol>
      <symbol id="i-close" viewBox="0 0 24 24">
        <path d="m6 6 12 12M18 6 6 18" />
      </symbol>
      <symbol id="i-camera" viewBox="0 0 24 24">
        <path d="M4 7h3l2-3h6l2 3h3v13H4z" />
        <circle cx="12" cy="13" r="4" />
      </symbol>
      <symbol id="i-check" viewBox="0 0 24 24">
        <path d="m5 12 4 4L19 6" />
      </symbol>
      <symbol id="i-edit" viewBox="0 0 24 24">
        <path d="m4 20 4.5-1 10-10a2.1 2.1 0 0 0-3-3l-10 10L4 20Z" />
        <path d="m14 7 3 3" />
      </symbol>
      <symbol id="i-logout" viewBox="0 0 24 24">
        <path d="M10 5H5v14h5M14 8l4 4-4 4M8 12h10" />
      </symbol>
    </svg>
    <div class="loading-mask" role="status" aria-label="กำลังโหลด">
      <div class="loading-card">
        <span class="skeleton"></span><span class="skeleton"></span
        ><span class="skeleton"></span>
      </div>
    </div>
    <div class="app-shell">
      <aside class="sidebar" id="sidebar">
        <div class="brand">
          <div class="brand-mark">BC</div>
          <div><strong>Building Care</strong><span>ศูนย์บริการอาคาร</span></div>
        </div>
        <p class="nav-label">เมนูบริการ</p>
        <nav class="nav-list" aria-label="เมนูหลัก">
          <button type="button" class="nav-item active" data-page="dashboard">
            <span class="nav-dot"></span>ภาพรวม
          </button>
          <button type="button" class="nav-item" data-page="lost">
            <span class="nav-dot"></span>ของหาย–ของได้คืน
          </button>
          <button type="button" class="nav-item" data-page="repair">
            <span class="nav-dot"></span>แจ้งซ่อม
          </button>
          <button type="button" class="nav-item" data-page="clean">
            <span class="nav-dot"></span>แจ้งทำความสะอาด
          </button>
        </nav>
        <div class="sidebar-note">
          <strong>ไม่ต้องเข้าสู่ระบบ</strong
          >ผู้ใช้งานสามารถส่งเรื่องได้โดยไม่ต้องมีบัญชี
          และติดตามสถานะด้วยรหัสคำร้อง + อีเมล
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
        <div class="topbar">
          <button
            type="button"
            class="mobile-menu"
            id="menuButton"
            aria-label="เปิดเมนู"
          >
            <svg class="icon"><use href="#i-menu" /></svg>
          </button>
          <div></div>
          <div class="date-chip">
            อาคาร วิทยาศาสตร์คอมพิวเตอร์ (CS) · เปิดบริการ 08:00–18:00
          </div>
        </div>

        <section class="page active" id="dashboard">
          <header class="mobile-hero">
            <div class="eyebrow">Building Care</div>
            <p class="greeting">บริการอาคาร วิทยาศาสตร์คอมพิวเตอร์ (CS)</p>
            <h1 class="greeting-name">แจ้งเรื่องได้ทันที</h1>
            <p class="hero-subtitle">
              Building Service Management System · ไม่ต้องเข้าสู่ระบบ
            </p>
            <svg
              class="building-illustration"
              viewBox="0 0 220 170"
              aria-hidden="true"
            >
              <path
                d="M12 154h196M28 154V76h46v78M74 154V42h72v112M146 154V66h48v88M94 42V25h32v17M40 93h10m10 0h7M40 111h10m10 0h7M40 129h10m10 0h7M91 62h12m18 0h12M91 84h12m18 0h12M91 106h12m18 0h12M91 128h12m18 0h12M160 85h10m10 0h6M160 105h10m10 0h6M160 125h10m10 0h6M104 154v-22h14v22"
                fill="none"
                stroke="currentColor"
                stroke-width="5"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </header>

          <section class="location-card" aria-label="ตำแหน่งปัจจุบัน">
            <div class="location-icon">
              <svg class="icon"><use href="#i-pin" /></svg>
            </div>
            <div class="location-copy">
              <small>ตำแหน่งปัจจุบัน</small
              ><strong>อาคาร วิทยาศาสตร์คอมพิวเตอร์ (CS)</strong>
            </div>
          </section>

          <section class="dashboard-section">
            <div class="section-head">
              <h2>เมนูบริการ</h2>
              <span class="eyebrow">เลือกได้ทันที</span>
            </div>
            <div class="service-grid">
              <article
                class="service-card repair"
                tabindex="0"
                data-card-go="repair"
              >
                <div class="service-icon">
                  <svg class="icon icon-lg"><use href="#i-tools" /></svg>
                </div>
                <h3>แจ้งซ่อม</h3>
                <p>รายงานจุดชำรุด</p>
                <div class="service-footer">
                  <span class="count">2 งานกำลังดำเนินการ</span
                  ><button type="button" class="service-open" data-go="repair">
                    เริ่มแจ้ง
                  </button>
                </div>
              </article>
              <article
                class="service-card clean"
                tabindex="0"
                data-card-go="clean"
              >
                <div class="service-icon">
                  <svg class="icon icon-lg"><use href="#i-broom" /></svg>
                </div>
                <h3>แจ้งทำความสะอาด</h3>
                <p>แจ้งพื้นที่ที่ต้องดูแล</p>
                <div class="service-footer">
                  <span class="count">1 งานใหม่</span
                  ><button type="button" class="service-open" data-go="clean">
                    เริ่มแจ้ง
                  </button>
                </div>
              </article>
              <article
                class="service-card lost"
                tabindex="0"
                data-card-go="lost"
              >
                <div class="service-icon">
                  <svg class="icon icon-lg"><use href="#i-box" /></svg>
                </div>
                <h3>ของหาย–ของได้คืน</h3>
                <p>ค้นหาและแจ้งพบของ</p>
                <div class="lost-card-actions">
                  <button
                    type="button"
                    class="service-open"
                    data-go="lost"
                    data-lost-tab="browse"
                  >
                    ค้นหาของ
                  </button>
                  <button
                    type="button"
                    class="service-open"
                    data-go="lost"
                    data-lost-tab="report-lost"
                  >
                    แจ้งของหาย
                  </button>
                  <button
                    type="button"
                    class="service-open"
                    data-go="lost"
                    data-lost-tab="report-found"
                  >
                    แจ้งพบของ
                  </button>
                </div>
              </article>
            </div>
          </section>

          <section class="dashboard-section" id="trackingSection">
            <div class="section-head">
              <div>
                <h2>ติดตามสถานะงาน</h2>
                <p style="margin: 4px 0 0; font-size: 12px">
                  ใช้รหัสคำร้องและอีเมลเดียวกับที่กรอกตอนแจ้งเรื่อง
                </p>
              </div>
              <span class="eyebrow">ไม่ต้องล็อกอิน</span>
            </div>
            <form class="tracking-box" id="trackingForm">
              <div class="field">
                <label for="trackingCode">รหัสคำร้อง</label
                ><input
                  id="trackingCode"
                  type="text"
                  required
                  placeholder="เช่น BC-4821"
                  autocomplete="off"
                />
              </div>
              <div class="field">
                <label for="trackingEmail">อีเมล</label
                ><input
                  id="trackingEmail"
                  type="email"
                  required
                  placeholder="name@example.com"
                  autocomplete="email"
                />
              </div>
              <button type="submit" class="primary-btn">ตรวจสอบสถานะ</button>
            </form>
            <div class="tracking-result" id="trackingResult">
              <div class="tracking-result-head">
                <div>
                  <small>รหัสคำร้อง</small
                  ><strong id="trackingResultCode">BC-4821</strong>
                  <p id="trackingResultText" style="margin: 5px 0 0">
                    ช่างรับงานแล้วและกำลังตรวจสอบ
                  </p>
                </div>
                <span class="status progress" id="trackingResultStatus"
                  >กำลังดำเนินการ</span
                >
              </div>
            </div>
          </section>

          <section class="dashboard-section">
            <div class="section-head">
              <h2>สถิติเดือนนี้</h2>
              <span class="eyebrow">กรกฎาคม 2569</span>
            </div>
            <div class="stat-grid">
              <article class="stat-card repair">
                <span>แจ้งซ่อม</span><strong>18</strong><small>รายการ</small>
              </article>
              <article class="stat-card clean">
                <span>ทำความสะอาด</span><strong>24</strong><small>รายการ</small>
              </article>
              <article class="stat-card lost">
                <span>ของหาย</span><strong>7</strong><small>รายการ</small>
              </article>
              <article class="stat-card rate">
                <span>สำเร็จ</span><strong>86%</strong><small>ตรงเวลา</small>
              </article>
            </div>
          </section>
        </section>

        <section class="page" id="lost" data-theme="lost">
          <header class="page-header">
            <div>
              <div class="eyebrow">Lost &amp; found</div>
              <h2>ของหายและของที่พบ</h2>
            </div>
            <p>
              ค้นหาประกาศที่มีอยู่ก่อน หากยังไม่พบจึงสร้างประกาศใหม่
              เพื่อช่วยลดรายการซ้ำและเพิ่มโอกาสได้ของคืน
            </p>
          </header>
          <div class="lost-hub">
            <section class="lost-search-panel">
              <div class="eyebrow">ค้นหาก่อนแจ้ง</div>
              <h3>มีใครพบของของคุณแล้วหรือยัง?</h3>
              <p>ค้นหาจากชื่อสิ่งของ สี สถานที่ หรือรายละเอียดที่จำได้</p>
              <div class="search-row">
                <input
                  type="text"
                  id="lostSearch"
                  placeholder="เช่น กระเป๋าสีดำ, บัตรนักศึกษา, อาคาร 3"
                /><button type="button" id="lostSearchButton">
                  ค้นหาประกาศ
                </button>
              </div>
            </section>

            <div class="lost-actions-grid">
              <button
                type="button"
                class="lost-action-card"
                data-open-lost-view="report-lost"
              >
                <span class="action-symbol"
                  ><svg class="icon"><use href="#i-search" /></svg></span
                ><strong>แจ้งของหาย</strong
                ><span>ระบุสิ่งของ จุดที่หาย และลักษณะเฉพาะ</span>
              </button>
              <button
                type="button"
                class="lost-action-card"
                data-open-lost-view="report-found"
              >
                <span class="action-symbol"
                  ><svg class="icon"><use href="#i-box" /></svg></span
                ><strong>แจ้งพบของ</strong><span>ระบุสิ่งของและจุดรับฝาก</span>
              </button>
              <button
                type="button"
                class="lost-action-card"
                data-open-lost-view="browse"
              >
                <span class="action-symbol"
                  ><svg class="icon"><use href="#i-history" /></svg></span
                ><strong>ดูประกาศทั้งหมด</strong
                ><span>ดูรายการตามหาและรายการที่พบแล้ว</span>
              </button>
            </div>

            <div
              class="lost-tabs"
              role="tablist"
              aria-label="เมนูของหายและของที่พบ"
            >
              <button
                type="button"
                class="lost-tab active"
                data-lost-view="browse"
              >
                ประกาศทั้งหมด
              </button>
              <button
                type="button"
                class="lost-tab"
                data-lost-view="report-lost"
              >
                แจ้งของหาย
              </button>
              <button
                type="button"
                class="lost-tab"
                data-lost-view="report-found"
              >
                แจ้งพบของ
              </button>
            </div>

            <div class="lost-view active" id="lost-view-browse">
              <section class="lost-board">
                <div class="board-head">
                  <div>
                    <h3>ประกาศล่าสุด</h3>
                    <p id="resultSummary">
                      แสดงรายการที่กำลังตามหาและของที่พบแล้ว
                    </p>
                  </div>
                </div>
                <div class="filter-row">
                  <button
                    type="button"
                    class="filter-chip active"
                    data-filter="all"
                  >
                    ทั้งหมด</button
                  ><button type="button" class="filter-chip" data-filter="lost">
                    กำลังตามหา</button
                  ><button
                    type="button"
                    class="filter-chip"
                    data-filter="found"
                  >
                    พบของแล้ว
                  </button>
                </div>
                <div class="post-grid" id="postGrid">
                  <article
                    class="post-card"
                    data-kind="lost"
                    data-search="กระเป๋าผ้าสีดำ อาคาร csb ชั้น 3 พวงกุญแจแมว"
                  >
                    <div class="post-image">
                      <svg class="icon"><use href="#i-search" /></svg>
                    </div>
                    <div class="post-body">
                      <div class="post-meta">
                        <span class="post-type lost">กำลังตามหา</span
                        ><span class="post-date">29 ก.ค. 2569</span>
                      </div>
                      <h4>กระเป๋าผ้าสีดำ</h4>
                      <p>หายบริเวณอาคาร CSB ชั้น 3 มีพวงกุญแจรูปแมว</p>
                      <button type="button" class="post-detail-button">
                        ดูรายละเอียด
                      </button>
                    </div>
                  </article>
                  <article
                    class="post-card"
                    data-kind="found"
                    data-search="บัตรนักศึกษา โรงอาหารกลาง เคาน์เตอร์ประชาสัมพันธ์"
                  >
                    <div class="post-image">
                      <svg class="icon"><use href="#i-box" /></svg>
                    </div>
                    <div class="post-body">
                      <div class="post-meta">
                        <span class="post-type found">พบของแล้ว</span
                        ><span class="post-date">29 ก.ค. 2569</span>
                      </div>
                      <h4>บัตรนักศึกษา</h4>
                      <p>พบที่โรงอาหารกลาง ฝากไว้ที่เคาน์เตอร์ประชาสัมพันธ์</p>
                      <button type="button" class="claim-button">
                        นี่อาจเป็นของฉัน
                      </button>
                    </div>
                  </article>
                  <article
                    class="post-card"
                    data-kind="found"
                    data-search="กุญแจ พวงกุญแจสีแดง อาคาร 2 บันได"
                  >
                    <div class="post-image">
                      <svg class="icon"><use href="#i-box" /></svg>
                    </div>
                    <div class="post-body">
                      <div class="post-meta">
                        <span class="post-type found">พบของแล้ว</span
                        ><span class="post-date">28 ก.ค. 2569</span>
                      </div>
                      <h4>กุญแจพร้อมพวงกุญแจ</h4>
                      <p>พบบริเวณบันไดอาคาร 2 พวงกุญแจสีแดง</p>
                      <button type="button" class="claim-button">
                        นี่อาจเป็นของฉัน
                      </button>
                    </div>
                  </article>
                  <article
                    class="post-card"
                    data-kind="lost"
                    data-search="ร่มพับสีดำ ห้อง b201"
                  >
                    <div class="post-image">
                      <svg class="icon"><use href="#i-search" /></svg>
                    </div>
                    <div class="post-body">
                      <div class="post-meta">
                        <span class="post-type lost">กำลังตามหา</span
                        ><span class="post-date">28 ก.ค. 2569</span>
                      </div>
                      <h4>ร่มพับสีดำ</h4>
                      <p>พบเห็นครั้งสุดท้ายหน้าห้อง B201</p>
                      <button type="button" class="post-detail-button">
                        ดูรายละเอียด
                      </button>
                    </div>
                  </article>
                  <article
                    class="post-card"
                    data-kind="found"
                    data-search="หูฟังไร้สาย สีขาว ห้องสมุด ชั้น 2"
                  >
                    <div class="post-image">
                      <svg class="icon"><use href="#i-box" /></svg>
                    </div>
                    <div class="post-body">
                      <div class="post-meta">
                        <span class="post-type found">พบของแล้ว</span
                        ><span class="post-date">27 ก.ค. 2569</span>
                      </div>
                      <h4>หูฟังไร้สายสีขาว</h4>
                      <p>พบบริเวณโต๊ะอ่านหนังสือ ห้องสมุดชั้น 2</p>
                      <button type="button" class="claim-button">
                        นี่อาจเป็นของฉัน
                      </button>
                    </div>
                  </article>
                  <article
                    class="post-card"
                    data-kind="lost"
                    data-search="กระบอกน้ำ สีเขียว ห้อง c104"
                  >
                    <div class="post-image">
                      <svg class="icon"><use href="#i-search" /></svg>
                    </div>
                    <div class="post-body">
                      <div class="post-meta">
                        <span class="post-type lost">กำลังตามหา</span
                        ><span class="post-date">27 ก.ค. 2569</span>
                      </div>
                      <h4>กระบอกน้ำสีเขียว</h4>
                      <p>คาดว่าลืมไว้ในห้อง C104 ช่วงบ่าย</p>
                      <button type="button" class="post-detail-button">
                        ดูรายละเอียด
                      </button>
                    </div>
                  </article>
                </div>
              </section>
            </div>

            <div class="lost-view" id="lost-view-report-lost">
              <div class="two-form-layout">
                <form class="form-panel" data-submit-type="แจ้งของหาย">
                  <h3>แจ้งของหาย</h3>
                  <div class="field">
                    <label>ประเภทสิ่งของ</label
                    ><select required>
                      <option value="">เลือกประเภท</option>
                      <option>กระเป๋า</option>
                      <option>บัตรหรือเอกสาร</option>
                      <option>อุปกรณ์อิเล็กทรอนิกส์</option>
                      <option>กุญแจ</option>
                      <option>อื่น ๆ</option>
                    </select>
                  </div>
                  <div class="field">
                    <label>ชื่อสิ่งของ</label
                    ><input
                      type="text"
                      required
                      placeholder="เช่น กระเป๋าผ้าสีดำ"
                    />
                  </div>
                  <div class="field">
                    <label>วันที่และเวลาที่คาดว่าทำหาย</label
                    ><input type="datetime-local" required />
                  </div>
                  <div class="field">
                    <label>สถานที่คาดว่าทำหาย</label
                    ><input
                      type="text"
                      required
                      placeholder="อาคาร / ชั้น / ห้อง"
                    />
                  </div>
                  <div class="field">
                    <label>ลักษณะเฉพาะ</label
                    ><textarea
                      required
                      placeholder="สี ยี่ห้อ รอยตำหนิ หรือพวงกุญแจที่ติดอยู่"
                    ></textarea>
                  </div>
                  <div class="field">
                    <label>รูปภาพสิ่งของ (ถ้ามี)</label>
                    <div class="upload-field">
                      <label class="upload-trigger"
                        ><input
                          type="file"
                          class="image-input"
                          accept="image/jpeg,image/png,image/webp"
                          data-max-size="5242880"
                        /><span class="upload-icon">＋</span
                        ><span class="upload-copy"
                          ><strong>เลือกรูปภาพ</strong
                          ><small>JPG, PNG หรือ WebP ไม่เกิน 5 MB</small></span
                        ></label
                      >
                      <div class="image-preview">
                        <img
                          src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs="
                          alt="ตัวอย่างรูปที่แนบ"
                        /><span></span
                        ><button type="button" class="remove-image">ลบ</button>
                      </div>
                    </div>
                  </div>
                  <div class="field">
                    <label>อีเมลสำหรับติดตามสถานะ</label
                    ><input
                      type="email"
                      name="recipient_email"
                      required
                      placeholder="name@example.com"
                      autocomplete="email"
                    />
                  </div>
                  <button type="submit" class="submit-btn">
                    เผยแพร่ประกาศตามหา
                  </button>
                </form>
                <div class="list-panel">
                  <h3>ก่อนเผยแพร่</h3>
                  <div class="privacy-note">
                    อย่าใส่ข้อมูลสำคัญทั้งหมดในประกาศสาธารณะ
                    ควรเก็บรายละเอียดบางอย่างไว้ใช้ตรวจสอบผู้ที่อ้างว่าเป็นเจ้าของ
                  </div>
                  <div class="ticket-list">
                    <div class="ticket">
                      <div>
                        <strong>ค้นหาประกาศก่อน</strong
                        ><small>อาจมีคนประกาศพบสิ่งของไว้แล้ว</small>
                      </div>
                      <span class="status">แนะนำ</span>
                    </div>
                    <div class="ticket">
                      <div>
                        <strong>ระบุลักษณะให้ชัด</strong
                        ><small>สี ยี่ห้อ จุดสังเกต และบริเวณที่หาย</small>
                      </div>
                      <span class="status">สำคัญ</span>
                    </div>
                    <div class="ticket">
                      <div>
                        <strong>เก็บรหัสติดตาม</strong
                        ><small>ใช้ตรวจสอบสถานะหรือปิดประกาศภายหลัง</small>
                      </div>
                      <span class="status">จำเป็น</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="lost-view" id="lost-view-report-found">
              <div class="two-form-layout">
                <form class="form-panel" data-submit-type="แจ้งพบของ">
                  <h3>แจ้งพบของ</h3>
                  <div class="field">
                    <label>ประเภทสิ่งของ</label
                    ><select required>
                      <option value="">เลือกประเภท</option>
                      <option>กระเป๋า</option>
                      <option>บัตรหรือเอกสาร</option>
                      <option>อุปกรณ์อิเล็กทรอนิกส์</option>
                      <option>กุญแจ</option>
                      <option>อื่น ๆ</option>
                    </select>
                  </div>
                  <div class="field">
                    <label>ชื่อสิ่งของ</label
                    ><input
                      type="text"
                      required
                      placeholder="เช่น กุญแจพร้อมพวงกุญแจสีแดง"
                    />
                  </div>
                  <div class="field">
                    <label>วันที่และเวลาที่พบ</label
                    ><input type="datetime-local" required />
                  </div>
                  <div class="field">
                    <label>สถานที่พบ</label
                    ><input
                      type="text"
                      required
                      placeholder="อาคาร / ชั้น / ห้อง"
                    />
                  </div>
                  <div class="field">
                    <label>นำของไปฝากไว้ที่ใด</label
                    ><input
                      type="text"
                      required
                      placeholder="เช่น ห้องประชาสัมพันธ์ชั้น 1"
                    />
                  </div>
                  <div class="field">
                    <label>รายละเอียดทั่วไป</label
                    ><textarea
                      placeholder="อธิบายเฉพาะข้อมูลที่เปิดเผยต่อสาธารณะได้"
                    ></textarea>
                  </div>
                  <div class="field">
                    <label>รูปภาพของที่พบ</label>
                    <div class="upload-field">
                      <label class="upload-trigger"
                        ><input
                          type="file"
                          class="image-input"
                          accept="image/jpeg,image/png,image/webp"
                          data-max-size="5242880"
                        /><span class="upload-icon">＋</span
                        ><span class="upload-copy"
                          ><strong>เลือกรูปภาพ</strong
                          ><small>JPG, PNG หรือ WebP ไม่เกิน 5 MB</small></span
                        ></label
                      >
                      <div class="image-preview">
                        <img
                          src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs="
                          alt="ตัวอย่างรูปที่แนบ"
                        /><span></span
                        ><button type="button" class="remove-image">ลบ</button>
                      </div>
                    </div>
                  </div>
                  <div class="field">
                    <label>รายละเอียดลับสำหรับยืนยันเจ้าของ</label
                    ><textarea
                      required
                      placeholder="เช่น ของภายใน ตำหนิ หรือข้อมูลที่ไม่ควรแสดงสาธารณะ"
                    ></textarea>
                  </div>
                  <div class="field">
                    <label>อีเมลสำหรับติดตามสถานะ</label
                    ><input
                      type="email"
                      name="recipient_email"
                      required
                      placeholder="name@example.com"
                      autocomplete="email"
                    />
                  </div>
                  <button type="submit" class="submit-btn">
                    เผยแพร่ประกาศพบของ
                  </button>
                </form>
                <div class="list-panel">
                  <h3>การปกป้องเจ้าของสิ่งของ</h3>
                  <div class="privacy-note">
                    เลขบัตร ชื่อเต็ม จำนวนเงิน
                    หรือรายละเอียดสำคัญไม่ควรแสดงต่อสาธารณะ
                    ให้เจ้าหน้าที่ใช้ข้อมูลเหล่านี้ตรวจสอบก่อนคืนของ
                  </div>
                  <div class="ticket-list">
                    <div class="ticket">
                      <div>
                        <strong>ฝากไว้ในจุดที่ปลอดภัย</strong
                        ><small
                          >ระบุห้องหรือเคาน์เตอร์ที่ผู้ใช้ติดต่อรับได้</small
                        >
                      </div>
                      <span class="status">แนะนำ</span>
                    </div>
                    <div class="ticket">
                      <div>
                        <strong>อย่าเปิดเผยข้อมูลทั้งหมด</strong
                        ><small
                          >เก็บรายละเอียดบางอย่างไว้ยืนยันเจ้าของจริง</small
                        >
                      </div>
                      <span class="status">สำคัญ</span>
                    </div>
                    <div class="ticket">
                      <div>
                        <strong>ให้ Staff ตรวจคำขอรับ</strong
                        ><small>ลดความเสี่ยงจากการแอบอ้างเป็นเจ้าของ</small>
                      </div>
                      <span class="status">ปลอดภัย</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section class="page" id="repair" data-theme="repair">
          <header class="page-header">
            <div>
              <div class="eyebrow">Repair request</div>
              <h2>แจ้งซ่อม</h2>
            </div>
            <p>
              แจ้งอุปกรณ์หรือพื้นที่ชำรุด
              พร้อมระดับความเร่งด่วนเพื่อให้ทีมช่างจัดลำดับงานได้เหมาะสม
            </p>
          </header>
          <div class="work-layout single-form-layout">
            <form class="form-panel" data-submit-type="แจ้งซ่อม">
              <h3>รายละเอียดปัญหา</h3>
              <div class="field">
                <label>ประเภทอุปกรณ์</label
                ><select required>
                  <option value="">เลือกประเภท</option>
                  <option>ไฟฟ้า</option>
                  <option>ประปา</option>
                  <option>เครื่องปรับอากาศ</option>
                  <option>อุปกรณ์ห้องเรียน</option>
                </select>
              </div>
              <div class="field">
                <label>สถานที่</label
                ><input
                  type="text"
                  required
                  placeholder="อาคาร / ชั้น / ห้อง"
                />
              </div>
              <div class="field">
                <label>ความเร่งด่วน</label
                ><select required>
                  <option>ทั่วไป</option>
                  <option>เร่งด่วน</option>
                  <option>กระทบความปลอดภัย</option>
                </select>
              </div>
              <div class="field">
                <label>อธิบายปัญหา</label
                ><textarea
                  required
                  placeholder="เกิดอะไรขึ้น และมีผลต่อการใช้งานอย่างไร"
                ></textarea>
              </div>
              <div class="field">
                <label>รูปภาพจุดชำรุด</label>
                <div class="upload-field">
                  <label class="upload-trigger"
                    ><input
                      type="file"
                      class="image-input"
                      accept="image/jpeg,image/png,image/webp"
                      data-max-size="5242880"
                    /><span class="upload-icon">＋</span
                    ><span class="upload-copy"
                      ><strong>เลือกรูปภาพ</strong
                      ><small>JPG, PNG หรือ WebP ไม่เกิน 5 MB</small></span
                    ></label
                  >
                  <div class="image-preview">
                    <img
                      src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs="
                      alt="ตัวอย่างรูปที่แนบ"
                    /><span></span
                    ><button type="button" class="remove-image">ลบ</button>
                  </div>
                </div>
              </div>
              <div class="field">
                <label>อีเมลสำหรับติดตามสถานะ</label
                ><input
                  type="email"
                  name="recipient_email"
                  required
                  placeholder="name@example.com"
                  autocomplete="email"
                />
              </div>
              <button type="submit" class="submit-btn">ส่งคำขอซ่อม</button>
            </form>
          </div>
        </section>

        <section class="page" id="clean" data-theme="clean">
          <header class="page-header">
            <div>
              <div class="eyebrow">Cleaning request</div>
              <h2>แจ้งทำความสะอาด</h2>
            </div>
            <p>
              ระบุพื้นที่และลักษณะงาน
              เพื่อให้เจ้าหน้าที่เตรียมอุปกรณ์และเข้าดำเนินการได้ตรงจุด
            </p>
          </header>
          <div class="work-layout single-form-layout">
            <form class="form-panel" data-submit-type="แจ้งทำความสะอาด">
              <h3>ขอทำความสะอาดพื้นที่</h3>
              <div class="field">
                <label>ประเภทพื้นที่</label
                ><select required>
                  <option value="">เลือกพื้นที่</option>
                  <option>ห้องเรียน</option>
                  <option>ห้องน้ำ</option>
                  <option>โถงทางเดิน</option>
                  <option>พื้นที่ส่วนกลาง</option>
                </select>
              </div>
              <div class="field">
                <label>สถานที่</label
                ><input
                  type="text"
                  required
                  placeholder="อาคาร / ชั้น / ห้อง"
                />
              </div>
              <div class="field">
                <label>ประเภทงาน</label
                ><select required>
                  <option>ทำความสะอาดทั่วไป</option>
                  <option>คราบหกเลอะ</option>
                  <option>ขยะสะสม</option>
                  <option>เหตุเร่งด่วน</option>
                </select>
              </div>
              <div class="field">
                <label>รายละเอียด</label
                ><textarea
                  required
                  placeholder="บอกตำแหน่งและลักษณะพื้นที่ที่ต้องการให้ดูแล"
                ></textarea>
              </div>
              <div class="field">
                <label>รูปภาพพื้นที่</label>
                <div class="upload-field">
                  <label class="upload-trigger"
                    ><input
                      type="file"
                      class="image-input"
                      accept="image/jpeg,image/png,image/webp"
                      data-max-size="5242880"
                    /><span class="upload-icon">＋</span
                    ><span class="upload-copy"
                      ><strong>เลือกรูปภาพ</strong
                      ><small>JPG, PNG หรือ WebP ไม่เกิน 5 MB</small></span
                    ></label
                  >
                  <div class="image-preview">
                    <img
                      src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs="
                      alt="ตัวอย่างรูปที่แนบ"
                    /><span></span
                    ><button type="button" class="remove-image">ลบ</button>
                  </div>
                </div>
              </div>
              <div class="field">
                <label>อีเมลสำหรับติดตามสถานะ</label
                ><input
                  type="email"
                  name="recipient_email"
                  required
                  placeholder="name@example.com"
                  autocomplete="email"
                />
              </div>
              <button type="submit" class="submit-btn">
                ส่งคำขอทำความสะอาด
              </button>
            </form>
          </div>
        </section>
      </main>
      <nav class="bottom-nav" aria-label="เมนูด้านล่าง">
        <button
          type="button"
          class="active"
          data-go="dashboard"
          data-bottom-page="dashboard"
        >
          <span class="nav-glyph"
            ><svg class="icon"><use href="#i-home" /></svg></span
          ><span>หน้าหลัก</span>
        </button>
        <button type="button" data-go="repair" data-bottom-page="repair">
          <span class="nav-glyph"
            ><svg class="icon"><use href="#i-tools" /></svg></span
          ><span>แจ้งซ่อม</span>
        </button>
        <button type="button" data-go="clean" data-bottom-page="clean">
          <span class="nav-glyph"
            ><svg class="icon"><use href="#i-broom" /></svg></span
          ><span>แจ้งทำความสะอาด</span>
        </button>
        <button
          type="button"
          data-go="lost"
          data-lost-tab="report-lost"
          data-bottom-page="lost"
        >
          <span class="nav-glyph"
            ><svg class="icon"><use href="#i-box" /></svg></span
          ><span>แจ้งของหาย</span>
        </button>
        <button type="button" data-scroll-track>
          <span class="nav-glyph"
            ><svg class="icon"><use href="#i-history" /></svg></span
          ><span>ติดตามสถานะงาน</span>
        </button>
      </nav>

      <div
        class="ui-modal"
        id="serviceChooserModal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="serviceChooserTitle"
      >
        <section class="ui-modal-card compact">
          <header class="ui-modal-head">
            <div>
              <h2 id="serviceChooserTitle">เลือกบริการ</h2>
              <p class="modal-copy">ต้องการแจ้งเรื่องใด</p>
            </div>
            <button
              type="button"
              class="modal-close"
              data-modal-close="serviceChooserModal"
              aria-label="ปิด"
            >
              <svg class="icon"><use href="#i-close" /></svg>
            </button>
          </header>
          <div class="service-choice-grid">
            <button
              type="button"
              class="service-choice"
              data-service-choice="repair"
            >
              <svg class="icon"><use href="#i-tools" /></svg
              ><span>แจ้งซ่อม</span></button
            ><button
              type="button"
              class="service-choice"
              data-service-choice="clean"
            >
              <svg class="icon"><use href="#i-broom" /></svg
              ><span>แจ้งทำความสะอาด</span></button
            ><button
              type="button"
              class="service-choice"
              data-service-choice="lost"
            >
              <svg class="icon"><use href="#i-box" /></svg
              ><span>ของหาย–ของได้คืน</span>
            </button>
          </div>
        </section>
      </div>

      <div
        class="ui-modal"
        id="detailModal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="detailModalTitle"
      >
        <section class="ui-modal-card">
          <header class="ui-modal-head">
            <h2 id="detailModalTitle">รายละเอียด</h2>
            <button
              type="button"
              class="modal-close"
              data-modal-close="detailModal"
              aria-label="ปิด"
            >
              <svg class="icon"><use href="#i-close" /></svg>
            </button>
          </header>
          <div class="detail-hero">
            <svg class="icon" id="detailIcon"><use href="#i-box" /></svg>
          </div>
          <h3 id="detailTitle">รายการ</h3>
          <p id="detailDescription"></p>
          <div class="detail-meta">
            <div><small>วันที่</small><strong id="detailDate">–</strong></div>
            <div>
              <small>สถานที่</small><strong id="detailLocation">–</strong>
            </div>
            <div><small>สถานะ</small><strong id="detailStatus">–</strong></div>
            <div><small>หมายเลข</small><strong id="detailCode">–</strong></div>
          </div>
          <div class="modal-actions">
            <button
              type="button"
              class="secondary"
              data-modal-close="detailModal"
            >
              ปิด</button
            ><button
              type="button"
              class="primary-btn"
              id="detailContinueButton"
            >
              ดำเนินการต่อ
            </button>
          </div>
        </section>
      </div>

      <div
        class="ui-modal"
        id="claimModal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="claimModalTitle"
      >
        <section class="ui-modal-card">
          <header class="ui-modal-head">
            <div>
              <h2 id="claimModalTitle">ยืนยันความเป็นเจ้าของ</h2>
              <p class="modal-copy" id="claimItemName">รายการสิ่งของ</p>
            </div>
            <button
              type="button"
              class="modal-close"
              data-modal-close="claimModal"
              aria-label="ปิด"
            >
              <svg class="icon"><use href="#i-close" /></svg>
            </button>
          </header>
          <form id="claimForm">
            <div class="modal-grid">
              <div class="modal-field">
                <label for="claimName">ชื่อผู้ขอรับ</label
                ><input id="claimName" type="text" required />
              </div>
              <div class="modal-field">
                <label for="claimContact">อีเมลสำหรับติดต่อ</label
                ><input
                  id="claimContact"
                  name="recipient_email"
                  type="email"
                  required
                  placeholder="name@example.com"
                  autocomplete="email"
                />
              </div>
            </div>
            <div class="modal-field">
              <label for="claimProof">รายละเอียดที่ใช้ยืนยัน</label
              ><textarea
                id="claimProof"
                required
                placeholder="เช่น ตำหนิ ของภายใน หรือจุดสังเกต"
              ></textarea>
            </div>
            <div class="modal-field">
              <label for="claimDate">วันที่สะดวกรับของ</label
              ><input id="claimDate" type="date" required />
            </div>
            <button type="submit" class="primary-btn modal-action">
              ส่งคำขอ
            </button>
          </form>
        </section>
      </div>

      <div
        class="ui-modal"
        id="successModal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="successModalTitle"
      >
        <section class="ui-modal-card compact">
          <header class="ui-modal-head">
            <h2 id="successModalTitle">ส่งคำขอสำเร็จ</h2>
            <button
              type="button"
              class="modal-close"
              data-modal-close="successModal"
              aria-label="ปิด"
            >
              <svg class="icon"><use href="#i-close" /></svg>
            </button>
          </header>
          <div class="success-wrap">
            <div class="success-icon">
              <svg class="icon"><use href="#i-check" /></svg>
            </div>
            <p id="successType">รอรับเรื่อง</p>
            <strong class="request-code" id="successCode">BC-0000</strong
            ><small class="success-email" id="successEmail"
              >ใช้รหัสนี้ร่วมกับอีเมลเพื่อติดตามสถานะ</small
            >
            <div class="modal-actions">
              <button type="button" class="secondary" id="viewStatusButton">
                ดูสถานะ</button
              ><button type="button" class="primary-btn" id="backHomeButton">
                กลับหน้าหลัก
              </button>
            </div>
          </div>
        </section>
      </div>

      <div
        class="toast-message"
        id="toastMessage"
        role="status"
        aria-live="polite"
      ></div>
      <div class="offline-banner" role="status">
        ขณะนี้ออฟไลน์ · คำขอจะถูกส่งเมื่อเชื่อมต่ออีกครั้ง
      </div>
    </div>
  </div>
</template>

<style>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+Thai:wght@400;500;600;700;800&display=swap");

/* design-system.css */
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

/* user-app.css */
body {
  background: radial-gradient(circle at 85px 0, #fff 0 170px, transparent 171px),
    linear-gradient(145deg, #f5f1ff 0, #fff 32%, #f8f8fc 100%);
  min-height: 100vh;
}
.app-shell {
  display: block;
  max-width: 1440px;
  margin: auto;
}
.sidebar {
  position: fixed;
  z-index: 30;
  left: 24px;
  top: 24px;
  bottom: 24px;
  width: 244px;
  padding: 22px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.8);
  border-radius: 28px;
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 3px 24px;
}
.brand-mark {
  width: 46px;
  height: 46px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  background: linear-gradient(145deg, var(--primary), #9588ff);
  color: #fff;
  font-weight: 900;
  box-shadow: 0 8px 20px rgba(109, 93, 246, 0.25);
}
.brand strong,
.brand span {
  display: block;
}
.brand strong {
  font-size: 16px;
}
.brand span {
  font-size: 11px;
  color: var(--muted);
}
.nav-label {
  margin: 4px 10px 8px;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.nav-list {
  display: grid;
  gap: 7px;
}
.nav-item {
  border: 0;
  background: transparent;
  color: #635f6c;
  border-radius: 15px;
  min-height: 50px;
  padding: 0 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 700;
  text-align: left;
}
.nav-item:hover,
.nav-item.active {
  background: var(--primary-soft);
  color: var(--primary);
}
.nav-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 0 5px rgba(109, 93, 246, 0.08);
}
.sidebar-note {
  margin-top: auto;
  border-radius: 18px;
  background: #f8f6ff;
  padding: 16px;
  color: var(--muted);
  font-size: 12px;
}
.sidebar-note strong {
  display: block;
  color: var(--ink);
  margin-bottom: 4px;
}
main {
  margin-left: 292px;
  padding: 0 42px 110px;
  min-width: 0;
}
.topbar {
  height: 88px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.mobile-menu {
  display: none;
  border: 0;
  background: #fff;
  width: 46px;
  height: 46px;
  border-radius: 15px;
  box-shadow: var(--shadow-sm);
  font-size: 21px;
}
.date-chip {
  font-size: 12px;
  color: var(--muted);
  background: rgba(255, 255, 255, 0.75);
  border: 1px solid #fff;
  border-radius: 999px;
  padding: 9px 14px;
}
.page {
  display: none;
  max-width: 1080px;
  margin: auto;
  animation: pageIn 0.32s ease;
}
.page.active {
  display: block;
}
@keyframes pageIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
}
.mobile-hero {
  position: relative;
  min-height: 220px;
  padding: 34px 300px 24px 0;
}
.mobile-hero:after {
  content: "";
  position: absolute;
  right: 20px;
  top: 0;
  width: 260px;
  height: 200px;
  background: linear-gradient(
    145deg,
    rgba(109, 93, 246, 0.04),
    rgba(109, 93, 246, 0.13)
  );
  border-radius: 42% 58% 65% 35% / 48% 38% 62% 52%;
  z-index: -1;
}
.greeting {
  font-size: 20px;
  margin-bottom: 4px;
}
.greeting-name {
  font-size: 42px;
  margin-bottom: 8px;
}
.hero-subtitle {
  font-size: 13px;
}
.header-actions {
  display: flex;
  gap: 8px;
  position: absolute;
  right: 25px;
  top: 132px;
}
.round-action {
  border: 0;
  width: 42px;
  height: 42px;
  border-radius: 14px;
  background: #fff;
  box-shadow: var(--shadow-sm);
  font-size: 18px;
}
.location-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: #fff;
  padding: 18px 20px;
  border-radius: 22px;
  box-shadow: var(--shadow-sm);
  margin-bottom: 24px;
}
.location-icon {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  border-radius: 16px;
  background: var(--primary-soft);
  color: var(--primary);
  font-size: 24px;
}
.location-copy {
  flex: 1;
}
.location-copy small,
.location-copy strong {
  display: block;
}
.location-copy small {
  font-size: 11px;
  color: var(--muted);
}
.location-copy strong {
  font-size: 17px;
}
.scan-btn {
  border: 1.5px solid var(--primary);
  background: #fff;
  color: var(--primary);
  border-radius: 16px;
  min-height: 50px;
  padding: 0 18px;
  font-weight: 800;
}
.dashboard-section {
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(255, 255, 255, 0.9);
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
  padding: 24px;
  margin-bottom: 24px;
}
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 18px;
}
.section-head h2 {
  font-size: 21px;
  margin: 0;
}
.section-link {
  border: 0;
  background: transparent;
  color: var(--primary);
  font-weight: 800;
}
.service-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin: 0;
}
.service-card {
  position: relative;
  min-height: 190px;
  border: 1px solid transparent;
  border-radius: 22px;
  padding: 22px;
  display: flex;
  flex-direction: column;
  transition: 0.25s;
  box-shadow: none;
}
.service-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-sm);
}
.service-card.repair {
  background: var(--repair-soft);
  border-color: #ffd5bc;
}
.service-card.clean {
  background: var(--clean-soft);
  border-color: #ccebcf;
}
.service-card.lost {
  background: var(--lost-soft);
  border-color: #f6dda0;
}
.service-icon {
  font-size: 38px;
  width: 62px;
  height: 62px;
  display: grid;
  place-items: center;
  border-radius: 19px;
  background: rgba(255, 255, 255, 0.7);
  margin-bottom: 15px;
}
.service-card h3 {
  font-size: 18px;
  margin-bottom: 3px;
}
.service-card p {
  font-size: 12px;
  margin-bottom: 16px;
}
.service-footer,
.lost-card-actions {
  margin-top: auto;
  display: flex;
  align-items: center;
  gap: 8px;
}
.lost-card-actions {
  flex-wrap: wrap;
}
.service-open {
  border: 0;
  background: #fff;
  color: var(--ink);
  min-height: 38px;
  padding: 0 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 800;
}
.count {
  font-size: 11px;
  color: var(--muted);
}
.request-list {
  display: grid;
}
.request-card {
  display: grid;
  grid-template-columns: 48px 1fr auto 18px;
  align-items: center;
  gap: 14px;
  padding: 15px 4px;
  border-bottom: 1px solid var(--line);
}
.request-card:last-child {
  border-bottom: 0;
}
.request-symbol {
  width: 46px;
  height: 46px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  background: var(--primary-soft);
  font-size: 21px;
}
.request-card strong,
.request-card small {
  display: block;
}
.request-card small {
  font-size: 11px;
  color: var(--muted);
}
.request-meta {
  text-align: right;
}
.request-meta .status {
  margin-bottom: 3px;
}
.status.progress {
  color: #2874d8;
  background: var(--info-soft);
}
.status.done {
  color: #258745;
  background: var(--clean-soft);
}
.status.wait {
  color: #b77800;
  background: var(--lost-soft);
}
.request-arrow {
  font-size: 24px;
  color: #aaa4b5;
}
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}
.stat-card {
  padding: 18px;
  border-radius: 20px;
  border: 1px solid var(--line);
  background: #fff;
}
.stat-card span,
.stat-card small {
  display: block;
  color: var(--muted);
  font-size: 11px;
}
.stat-card strong {
  display: block;
  font-size: 28px;
  margin: 6px 0 2px;
}
.stat-card.repair {
  border-color: #ffd5bc;
  background: var(--repair-soft);
}
.stat-card.clean {
  border-color: #ccebcf;
  background: var(--clean-soft);
}
.stat-card.lost {
  border-color: #f6dda0;
  background: var(--lost-soft);
}
.stat-card.rate {
  border-color: #ded8ff;
  background: var(--primary-soft);
}
.announcement {
  display: grid;
  grid-template-columns: 54px 1fr auto;
  gap: 15px;
  align-items: center;
  padding: 17px;
  border-radius: 18px;
  background: linear-gradient(135deg, #f7f4ff, #fff);
  border: 1px solid #e4deff;
}
.announcement-icon {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  background: var(--primary);
  color: #fff;
  display: grid;
  place-items: center;
  font-size: 24px;
}
.announcement h3 {
  font-size: 15px;
  margin: 0;
}
.announcement p {
  font-size: 12px;
  margin: 3px 0;
}
.announcement a {
  font-size: 12px;
  color: var(--primary);
  font-weight: 800;
  text-decoration: none;
}
.announcement time {
  font-size: 11px;
  color: var(--muted);
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 30px;
  margin: 10px 0 26px;
}
.page-header h2 {
  font-size: 34px;
  margin: 5px 0;
}
.page-header > p {
  font-size: 13px;
  max-width: 470px;
  margin: 0;
}
.lost-hub,
.work-layout,
.two-form-layout {
  display: grid;
  gap: 20px;
}
.lost-search-panel,
.lost-board,
.form-panel,
.list-panel {
  background: #fff;
  border: 1px solid #fff;
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
  padding: 26px;
}
.lost-search-panel {
  background: linear-gradient(135deg, #fff9e7, #fff);
}
.lost-search-panel h3 {
  font-size: 24px;
  margin: 7px 0;
}
.search-row {
  display: flex;
  gap: 10px;
}
.search-row input {
  flex: 1;
  min-height: 52px;
  border: 1px solid var(--line);
  border-radius: 15px;
  padding: 0 15px;
}
.search-row button {
  border: 0;
  border-radius: 15px;
  background: var(--lost);
  color: #fff;
  padding: 0 22px;
  font-weight: 800;
}
.lost-actions-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}
.lost-action-card {
  border: 1px solid var(--line);
  background: #fff;
  border-radius: 20px;
  padding: 20px;
  text-align: left;
  display: grid;
  gap: 6px;
  min-height: 138px;
  box-shadow: var(--shadow-sm);
}
.lost-action-card span:last-child {
  font-size: 11px;
  color: var(--muted);
}
.action-symbol {
  font-size: 25px;
  color: var(--lost);
}
.lost-tabs,
.filter-row {
  display: flex;
  gap: 8px;
  overflow: auto;
  padding-bottom: 3px;
}
.lost-tab,
.filter-chip {
  border: 0;
  background: #efedf4;
  border-radius: 999px;
  min-height: 40px;
  padding: 0 16px;
  font-weight: 800;
  white-space: nowrap;
}
.lost-tab.active,
.filter-chip.active {
  background: var(--primary);
  color: #fff;
}
.lost-view {
  display: none;
}
.lost-view.active {
  display: block;
}
.board-head {
  display: flex;
  justify-content: space-between;
}
.post-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}
.post-card {
  border: 1px solid var(--line);
  border-radius: 19px;
  overflow: hidden;
  background: #fff;
}
.post-image {
  height: 110px;
  display: grid;
  place-items: center;
  background: var(--lost-soft);
  font-size: 38px;
}
.post-body {
  padding: 15px;
}
.post-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.post-date {
  font-size: 10px;
  color: var(--muted);
}
.post-type.lost {
  background: var(--danger-soft);
  color: var(--danger);
}
.post-type.found {
  background: var(--clean-soft);
  color: var(--clean);
}
.post-body h4 {
  margin: 10px 0 3px;
}
.post-body p {
  font-size: 11px;
  min-height: 34px;
}
.post-body button {
  border: 0;
  background: var(--primary-soft);
  color: var(--primary);
  border-radius: 11px;
  min-height: 36px;
  padding: 0 12px;
  font-weight: 800;
}
.two-form-layout,
.work-layout {
  grid-template-columns: minmax(0, 1.35fr) minmax(280px, 0.65fr);
  align-items: start;
}
.form-panel {
  display: grid;
  gap: 18px;
}
.form-panel > h3 {
  font-size: 22px;
  margin-bottom: 0;
}
.form-panel > .field {
  padding: 16px;
  border: 1px solid var(--line);
  border-radius: 18px;
  background: #fff;
}
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.upload-trigger {
  border: 1px dashed #cdc8df;
  border-radius: 15px;
  min-height: 90px;
  padding: 15px;
  display: flex;
  align-items: center;
  gap: 14px;
  background: #faf9ff;
}
.upload-trigger input {
  display: none;
}
.upload-icon {
  font-size: 28px;
  color: var(--primary);
}
.upload-copy strong,
.upload-copy small {
  display: block;
}
.upload-copy small {
  color: var(--muted);
}
.image-preview {
  display: none;
  margin-top: 9px;
  align-items: center;
  gap: 10px;
}
.image-preview.visible {
  display: flex;
}
.image-preview img {
  width: 64px;
  height: 64px;
  object-fit: cover;
  border-radius: 12px;
}
.image-preview span {
  font-size: 11px;
  color: var(--muted);
  flex: 1;
}
.remove-image {
  border: 0;
  background: var(--danger-soft);
  color: var(--danger);
  border-radius: 10px;
  padding: 7px 10px;
}
.submit-btn {
  width: 100%;
}
.ticket-list {
  display: grid;
}
.ticket {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding: 15px 0;
  border-bottom: 1px solid var(--line);
}
.ticket:last-child {
  border: 0;
}
.ticket strong,
.ticket small {
  display: block;
}
.ticket small {
  font-size: 11px;
  color: var(--muted);
}
.ticket .status {
  background: var(--info-soft);
  color: var(--info);
}
.privacy-note {
  background: var(--lost-soft);
  border-radius: 16px;
  padding: 15px;
  color: #80651b;
  font-size: 12px;
}
.bottom-nav {
  display: none;
}
.offline-banner {
  position: fixed;
  left: 50%;
  top: 14px;
  transform: translateX(-50%) translateY(-120px);
  z-index: 80;
  background: #211d35;
  color: #fff;
  border-radius: 999px;
  padding: 10px 18px;
  font-size: 12px;
  box-shadow: var(--shadow);
  transition: 0.3s;
}
.offline .offline-banner {
  transform: translateX(-50%) translateY(0);
}
@media (max-width: 980px) {
  .sidebar {
    left: -280px;
    transition: 0.25s;
  }
  .sidebar.open {
    left: 16px;
  }
  .mobile-menu {
    display: grid;
    place-items: center;
  }
  .app-shell main {
    margin-left: 0;
    padding: 0 24px 110px;
  }
  .topbar {
    height: 76px;
  }
  .post-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 680px) {
  body {
    background: linear-gradient(155deg, #f3efff 0, #fff 240px, #f8f8fc 100%);
  }
  .app-shell main {
    padding: 0 16px 104px;
  }
  .topbar {
    height: 68px;
  }
  .date-chip {
    font-size: 10px;
    padding: 7px 10px;
  }
  .mobile-hero {
    min-height: 185px;
    padding: 18px 110px 10px 0;
  }
  .mobile-hero:after {
    width: 175px;
    height: 165px;
    right: -28px;
  }
  .greeting {
    font-size: 15px;
  }
  .greeting-name {
    font-size: 30px;
  }
  .hero-subtitle {
    font-size: 11px;
  }
  .header-actions {
    right: 7px;
    top: 98px;
  }
  .round-action {
    width: 38px;
    height: 38px;
  }
  .location-card {
    padding: 14px;
    gap: 10px;
    border-radius: 20px;
  }
  .location-icon {
    width: 42px;
    height: 42px;
  }
  .location-copy strong {
    font-size: 14px;
  }
  .scan-btn {
    min-height: 44px;
    padding: 0 12px;
    font-size: 12px;
  }
  .dashboard-section {
    padding: 18px;
    border-radius: 22px;
    margin-bottom: 16px;
  }
  .section-head h2 {
    font-size: 18px;
  }
  .service-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
  }
  .service-card {
    min-height: 160px;
    padding: 13px 10px;
    border-radius: 18px;
    text-align: center;
    align-items: center;
  }
  .service-icon {
    width: 50px;
    height: 50px;
    font-size: 29px;
    border-radius: 15px;
    margin-bottom: 9px;
  }
  .service-card h3 {
    font-size: 13px;
  }
  .service-card p {
    font-size: 9px;
    line-height: 1.35;
  }
  .service-footer,
  .lost-card-actions {
    justify-content: center;
  }
  .count {
    display: none;
  }
  .service-open {
    min-height: 34px;
    font-size: 9px;
    padding: 0 8px;
  }
  .lost-card-actions .service-open:nth-child(n + 2) {
    display: none;
  }
  .request-card {
    grid-template-columns: 43px 1fr auto 8px;
    gap: 9px;
  }
  .request-symbol {
    width: 42px;
    height: 42px;
  }
  .request-card strong {
    font-size: 12px;
  }
  .request-card small,
  .request-meta small {
    font-size: 9px;
  }
  .request-meta .status {
    font-size: 9px;
    padding: 2px 7px;
    min-height: 24px;
  }
  .stat-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 9px;
  }
  .stat-card {
    padding: 14px;
    border-radius: 16px;
  }
  .stat-card strong {
    font-size: 23px;
  }
  .announcement {
    grid-template-columns: 44px 1fr;
    gap: 10px;
  }
  .announcement-icon {
    width: 44px;
    height: 44px;
  }
  .announcement time {
    display: none;
  }
  .page-header {
    display: block;
    margin-top: 5px;
  }
  .page-header h2 {
    font-size: 27px;
  }
  .page-header > p {
    font-size: 11px;
  }
  .lost-search-panel,
  .lost-board,
  .form-panel,
  .list-panel {
    padding: 18px;
    border-radius: 22px;
  }
  .lost-search-panel h3 {
    font-size: 20px;
  }
  .search-row {
    display: grid;
  }
  .search-row button {
    min-height: 48px;
  }
  .lost-actions-grid {
    grid-template-columns: 1fr;
  }
  .lost-action-card {
    min-height: 108px;
  }
  .post-grid {
    grid-template-columns: 1fr;
  }
  .two-form-layout,
  .work-layout {
    grid-template-columns: 1fr;
  }
  .list-panel {
    order: -1;
  }
  .form-panel > .field {
    padding: 14px;
  }
  .form-row {
    grid-template-columns: 1fr;
  }
  .bottom-nav {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    position: fixed;
    z-index: 25;
    bottom: 0;
    left: 0;
    right: 0;
    height: 78px;
    background: rgba(255, 255, 255, 0.96);
    backdrop-filter: blur(20px);
    border-top: 1px solid var(--line);
    padding: 8px 5px max(8px, env(safe-area-inset-bottom));
    box-shadow: 0 -10px 30px rgba(34, 27, 68, 0.08);
  }
  .bottom-nav button {
    position: relative;
    border: 0;
    background: transparent;
    color: #77727f;
    display: grid;
    place-items: center;
    align-content: center;
    gap: 2px;
    font-size: 9px;
  }
  .bottom-nav .nav-glyph {
    font-size: 21px;
  }
  .bottom-nav .active {
    color: var(--primary);
  }
  .bottom-nav .new-request {
    width: 58px;
    height: 58px;
    justify-self: center;
    align-self: end;
    margin-bottom: 12px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--primary), #8e7fff);
    color: #fff;
    box-shadow: 0 10px 24px rgba(109, 93, 246, 0.32);
  }
  .bottom-nav .new-request .nav-glyph {
    font-size: 30px;
  }
  .bottom-nav .new-request span:last-child {
    display: none;
  }
}

/* typography.css */
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

/* enhancements.css */
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

/* self-contained fixes and inline SVG components */
.icon {
  width: 24px;
  height: 24px;
  display: block;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.9;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.icon-lg {
  width: 38px;
  height: 38px;
}
.icon-sm {
  width: 18px;
  height: 18px;
}
.icon-fill {
  fill: currentColor;
  stroke: none;
}
.svg-sprite {
  position: absolute;
  width: 0;
  height: 0;
  overflow: hidden;
}
.building-illustration {
  position: absolute;
  right: 140px;
  top: 20px;
  width: 190px;
  height: 155px;
  color: rgba(109, 93, 246, 0.16);
  z-index: -1;
}
.mobile-menu,
.round-action,
.location-icon,
.service-icon,
.request-symbol,
.announcement-icon,
.nav-glyph {
  display: grid;
  place-items: center;
}
.service-card.repair .service-icon {
  color: #f47c35;
}
.service-card.clean .service-icon {
  color: #36a95a;
}
.service-card.lost .service-icon {
  color: #d5960b;
}
.service-card {
  cursor: pointer;
}
.service-card .count {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 3px 9px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.82);
  font-size: 10px;
  font-weight: 800;
}
.request-card {
  border-left: 0;
  border-right: 0;
  border-top: 0;
  background: transparent;
  width: 100%;
  text-align: left;
  color: inherit;
}
.request-symbol {
  color: #6d5df6;
}
.request-symbol.repair {
  color: #f47c35;
  background: #fff2e8;
}
.request-symbol.clean {
  color: #36a95a;
  background: #ebf8ed;
}
.request-symbol.lost {
  color: #d5960b;
  background: #fff7df;
}
.announcement-icon {
  background: var(--primary-soft);
  color: var(--primary);
}
.post-image .icon {
  width: 42px;
  height: 42px;
  color: #b27a00;
}
.action-symbol {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: var(--lost-soft);
}
.action-symbol .icon {
  width: 24px;
  height: 24px;
}
.bottom-nav .nav-glyph {
  font-size: 0;
}
.bottom-nav .nav-glyph .icon {
  width: 23px;
  height: 23px;
}
.bottom-nav .new-request .nav-glyph .icon {
  width: 30px;
  height: 30px;
}
.location-card .scan-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.ui-modal {
  position: fixed;
  inset: 0;
  z-index: 90;
  display: none;
  place-items: end center;
  background: rgba(28, 23, 49, 0.42);
  backdrop-filter: blur(8px);
  padding: 18px;
}
.ui-modal.open {
  display: grid;
}
.ui-modal-card {
  width: min(520px, 100%);
  max-height: 86vh;
  overflow: auto;
  background: #fff;
  border-radius: 28px;
  padding: 22px;
  box-shadow: 0 28px 80px rgba(34, 26, 68, 0.25);
  animation: modalRise 0.22s ease;
}
.ui-modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 14px;
}
.ui-modal-head h2 {
  font-size: 20px;
  margin: 0;
}
.modal-close {
  width: 42px;
  height: 42px;
  border: 0;
  border-radius: 14px;
  background: #f1eff7;
  color: var(--ink);
  display: grid;
  place-items: center;
}
.notification-row,
.profile-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 14px 0;
  border-bottom: 1px solid var(--line);
}
.notification-row:last-child,
.profile-row:last-child {
  border-bottom: 0;
}
.notification-row > .icon,
.profile-row > .icon {
  flex: 0 0 auto;
  color: var(--primary);
}
.notification-row strong,
.notification-row small,
.profile-row strong,
.profile-row small {
  display: block;
}
.notification-row small,
.profile-row small {
  font-size: 11px;
  color: var(--muted);
}
.profile-summary {
  text-align: center;
  padding: 8px 0 18px;
}
.profile-large {
  width: 76px;
  height: 76px;
  margin: 0 auto 10px;
  border-radius: 25px;
  background: var(--primary-soft);
  color: var(--primary);
  display: grid;
  place-items: center;
}
.profile-large .icon {
  width: 42px;
  height: 42px;
}
.modal-action {
  width: 100%;
  margin-top: 14px;
}
@keyframes modalRise {
  from {
    opacity: 0;
    transform: translateY(14px);
  }
}
@media (max-width: 680px) {
  .building-illustration {
    right: 60px;
    top: 16px;
    width: 150px;
    height: 125px;
  }
  .mobile-hero {
    padding-right: 92px;
  }
  .service-card .count {
    font-size: 8px;
    padding: 2px 7px;
  }
  .ui-modal {
    padding: 0;
    align-items: end;
  }
  .ui-modal-card {
    border-radius: 26px 26px 0 0;
    padding: 20px 18px max(24px, env(safe-area-inset-bottom));
  }
}

/* Interaction and usability refinements */
button,
.clickable,
[data-card-go],
[data-request-detail],
[data-history-detail],
[data-notification-detail] {
  cursor: pointer;
}
button {
  min-height: 44px;
  transition: transform 0.16s ease, box-shadow 0.2s ease,
    background-color 0.2s ease;
}
button:active,
[data-card-go]:active,
[data-request-detail]:active {
  transform: scale(0.97);
}
button:focus-visible,
[tabindex]:focus-visible,
input:focus-visible,
select:focus-visible,
textarea:focus-visible {
  outline: 3px solid rgba(109, 93, 246, 0.3);
  outline-offset: 3px;
}
.form-panel > .field {
  box-shadow: 0 2px 10px rgba(42, 35, 85, 0.035);
}
.form-panel > .field label {
  font-size: 13px;
}
.form-panel > .field + .field {
  margin-top: -4px;
}
.form-panel > h3 {
  margin-bottom: 2px;
}
.form-panel .submit-btn {
  margin-top: 2px;
}
.sidebar-backdrop {
  position: fixed;
  inset: 0;
  z-index: 29;
  background: rgba(22, 18, 40, 0.32);
  opacity: 0;
  visibility: hidden;
  transition: 0.2s;
}
.sidebar-backdrop.open {
  opacity: 1;
  visibility: visible;
}
.modal-open {
  overflow: hidden;
}
.nav-badge {
  position: absolute;
  top: 2px;
  right: 22%;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  background: var(--danger);
  color: #fff;
  display: grid;
  place-items: center;
  font-size: 9px;
  font-weight: 800;
  border: 2px solid #fff;
}
.nav-badge.hidden {
  display: none;
}
.round-action {
  position: relative;
}
.round-action .nav-badge {
  top: -5px;
  right: -5px;
}
.ui-modal {
  align-items: center;
  justify-items: center;
  opacity: 0;
  visibility: hidden;
  display: grid;
  transition: opacity 0.2s ease;
}
.ui-modal.open {
  opacity: 1;
  visibility: visible;
}
.ui-modal-card {
  transform: translateY(16px);
  opacity: 0;
  transition: transform 0.24s ease, opacity 0.2s ease;
}
.ui-modal.open .ui-modal-card {
  transform: translateY(0);
  opacity: 1;
}
.ui-modal-card.wide {
  width: min(780px, 100%);
}
.ui-modal-card.compact {
  width: min(440px, 100%);
}
.modal-copy {
  font-size: 12px;
  margin: -7px 0 17px;
}
.modal-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.modal-field {
  display: grid;
  gap: 7px;
}
.modal-field label {
  font-size: 12px;
  font-weight: 750;
}
.modal-field input,
.modal-field select,
.modal-field textarea {
  width: 100%;
  min-height: 48px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: #fafafd;
  padding: 11px 13px;
}
.modal-field textarea {
  min-height: 104px;
  resize: vertical;
}
.modal-actions {
  display: flex;
  gap: 9px;
  justify-content: flex-end;
  margin-top: 18px;
}
.modal-actions > * {
  min-width: 120px;
}
.camera-stage {
  height: 230px;
  border-radius: 20px;
  background: linear-gradient(145deg, #211d35, #393052);
  color: #fff;
  display: grid;
  place-items: center;
  position: relative;
  overflow: hidden;
  margin-bottom: 15px;
}
.camera-stage:before,
.camera-stage:after {
  content: "";
  position: absolute;
  width: 90px;
  height: 70px;
  border-color: #a99cff;
  border-style: solid;
}
.camera-stage:before {
  left: 28px;
  top: 28px;
  border-width: 3px 0 0 3px;
  border-radius: 14px 0 0;
}
.camera-stage:after {
  right: 28px;
  bottom: 28px;
  border-width: 0 3px 3px 0;
  border-radius: 0 0 14px;
}
.camera-content {
  text-align: center;
  position: relative;
  z-index: 1;
}
.camera-content .icon {
  width: 46px;
  height: 46px;
  margin: 0 auto 8px;
  color: #b9afff;
}
.camera-status {
  display: block;
  font-size: 12px;
  color: #d9d4ff;
}
.detail-hero {
  height: 180px;
  border-radius: 20px;
  background: var(--lost-soft);
  display: grid;
  place-items: center;
  color: #b27a00;
  margin-bottom: 16px;
}
.detail-hero .icon {
  width: 68px;
  height: 68px;
}
.detail-meta {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin: 14px 0;
}
.detail-meta div {
  padding: 12px;
  border-radius: 14px;
  background: #f8f7fb;
}
.detail-meta small,
.detail-meta strong {
  display: block;
}
.detail-meta small {
  font-size: 10px;
  color: var(--muted);
}
.success-wrap {
  text-align: center;
  padding: 8px 0;
}
.success-icon {
  width: 82px;
  height: 82px;
  border-radius: 50%;
  background: var(--clean-soft);
  color: var(--clean);
  display: grid;
  place-items: center;
  margin: 0 auto 15px;
  animation: successPop 0.42s cubic-bezier(0.2, 0.8, 0.2, 1.2);
}
.success-icon .icon {
  width: 42px;
  height: 42px;
  stroke-dasharray: 40;
  stroke-dashoffset: 40;
  animation: successStroke 0.55s 0.18s ease forwards;
}
.request-code {
  display: inline-flex;
  padding: 8px 13px;
  border-radius: 12px;
  background: var(--primary-soft);
  color: var(--primary);
  font-weight: 900;
  letter-spacing: 0.06em;
  margin: 4px 0 12px;
}
.service-choice-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}
.service-choice {
  border: 1px solid var(--line);
  border-radius: 18px;
  background: #fff;
  padding: 18px 10px;
  display: grid;
  justify-items: center;
  gap: 8px;
  text-align: center;
  font-weight: 800;
}
.service-choice .icon {
  width: 34px;
  height: 34px;
  color: var(--primary);
}
.history-toolbar {
  display: grid;
  grid-template-columns: 1.4fr 0.8fr 0.8fr;
  gap: 9px;
  margin-bottom: 13px;
}
.history-toolbar input,
.history-toolbar select {
  width: 100%;
  min-height: 46px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: #fafafd;
  padding: 0 12px;
}
.history-list {
  display: grid;
  gap: 9px;
}
.history-item {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 16px;
  background: #fff;
  padding: 13px;
  display: grid;
  grid-template-columns: 42px 1fr auto;
  gap: 11px;
  align-items: center;
  text-align: left;
}
.history-item.hidden {
  display: none;
}
.history-item .request-symbol {
  width: 42px;
  height: 42px;
}
.history-item strong,
.history-item small {
  display: block;
}
.history-item small {
  font-size: 10px;
  color: var(--muted);
}
.notification-row {
  width: 100%;
  border: 0;
  background: transparent;
  text-align: left;
  position: relative;
}
.notification-row.unread {
  background: #f7f5ff;
  border-radius: 15px;
  padding-left: 12px;
  padding-right: 12px;
}
.notification-row.unread:after {
  content: "";
  position: absolute;
  right: 12px;
  top: 18px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--primary);
}
.notification-row.read {
  opacity: 0.72;
}
.notification-tools {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 6px;
}
.edit-profile-form {
  display: none;
  gap: 12px;
}
.edit-profile-form.open {
  display: grid;
}
.profile-summary.editing {
  display: none;
}
.toast-message {
  position: fixed;
  left: 50%;
  bottom: 96px;
  z-index: 120;
  max-width: min(420px, calc(100% - 28px));
  transform: translate(-50%, 18px);
  opacity: 0;
  visibility: hidden;
  background: #211d35;
  color: #fff;
  border-radius: 15px;
  padding: 12px 17px;
  box-shadow: var(--shadow);
  font-size: 12px;
  transition: 0.22s;
}
.toast-message.show {
  transform: translate(-50%, 0);
  opacity: 1;
  visibility: visible;
}
.empty-inline {
  display: none;
  text-align: center;
  color: var(--muted);
  padding: 22px;
}
.empty-inline.show {
  display: block;
}
@keyframes successPop {
  from {
    transform: scale(0.55);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}
@keyframes successStroke {
  to {
    stroke-dashoffset: 0;
  }
}
@media (hover: hover) and (pointer: fine) {
  .service-card:hover,
  .post-card:hover,
  .request-card:hover,
  .history-item:hover,
  .service-choice:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-sm);
  }
}
@media (max-width: 680px) {
  .ui-modal {
    align-items: end;
    padding: 0;
  }
  .ui-modal-card,
  .ui-modal-card.wide,
  .ui-modal-card.compact {
    width: 100%;
    max-height: 90vh;
    border-radius: 26px 26px 0 0;
    padding: 20px 18px max(24px, env(safe-area-inset-bottom));
  }
  .modal-grid,
  .detail-meta {
    grid-template-columns: 1fr;
  }
  .service-choice-grid {
    grid-template-columns: 1fr;
  }
  .service-choice {
    grid-template-columns: 38px 1fr;
    justify-items: start;
    text-align: left;
    align-items: center;
  }
  .history-toolbar {
    grid-template-columns: 1fr 1fr;
  }
  .history-toolbar input {
    grid-column: 1/-1;
  }
  .modal-actions {
    display: grid;
    grid-template-columns: 1fr;
  }
  .modal-actions > * {
    width: 100%;
  }
}
@media (max-width: 419px) {
  .service-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }
  .service-card {
    min-height: 170px;
    padding: 15px 12px;
  }
  .service-card.lost {
    grid-column: 1/-1;
    min-height: 150px;
  }
  .service-card h3 {
    font-size: 14px;
    overflow-wrap: anywhere;
  }
  .service-card .count {
    display: inline-flex;
  }
  .lost-card-actions .service-open:nth-child(n + 2) {
    display: inline-flex;
  }
  .location-card {
    flex-wrap: wrap;
  }
  .scan-btn {
    width: 100%;
  }
}
.work-layout.single-form-layout {
  grid-template-columns: minmax(0, 1fr);
  max-width: 820px;
}
@media (prefers-reduced-motion: reduce) {
  .ui-modal,
  .ui-modal-card,
  .success-icon,
  .success-icon .icon,
  .page {
    animation: none !important;
    transition: none !important;
  }
}

.tracking-box {
  display: grid;
  grid-template-columns: 1fr 1.35fr auto;
  gap: 10px;
  align-items: end;
}
.tracking-box .field {
  gap: 6px;
}
.tracking-box button {
  min-height: 50px;
}
.tracking-result {
  display: none;
  margin-top: 16px;
  border: 1px solid var(--line);
  border-radius: 18px;
  background: #fff;
  padding: 16px;
}
.tracking-result.show {
  display: block;
}
.tracking-result-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}
.tracking-result small {
  color: var(--muted);
}
.anonymous-note {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 14px 16px;
  border-radius: 16px;
  background: var(--primary-soft);
  color: #5448c8;
  font-size: 12px;
}
.anonymous-note .icon {
  flex: 0 0 auto;
  margin-top: 1px;
}
.success-email {
  display: block;
  font-size: 12px;
  color: var(--muted);
  margin: 0 0 12px;
}
@media (max-width: 680px) {
  .tracking-box {
    grid-template-columns: 1fr;
  }
  .mobile-hero {
    padding-right: 190px;
  }
  .header-actions {
    top: 28px;
    right: 12px;
  }
}
</style>