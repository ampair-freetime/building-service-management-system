import { onMounted, onUnmounted } from "vue";

export function usePublicServicePortal() {
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
      if (viewName === "report-found") {
        const now = new Date();
        const offsetDate = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
        const dateInput = document.getElementById("publicFoundDate");
        const timeInput = document.getElementById("publicFoundTime");
        if (dateInput && !dateInput.value) dateInput.value = offsetDate.toISOString().slice(0, 10);
        if (timeInput && !timeInput.value) timeInput.value = offsetDate.toISOString().slice(11, 16);
      }
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
}
