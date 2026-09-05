import { onMounted, onUnmounted } from "vue";
import { createLostItem } from "../services/api";

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
    const trackedRequests = new Map([
      [
        "BC-4821",
        {
          summary: "คำร้องอยู่ระหว่างการตรวจสอบ",
          status: "กำลังดำเนินการ",
          statusClass: "progress",
          requestType: "คำขอรับคืนสิ่งของ",
          itemName: "บัตรนักศึกษา",
          updatedAt: "อยู่ระหว่างเจ้าหน้าที่ตรวจสอบ",
        },
      ],
    ]);

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
    function openLostFoundDetail(card, trigger = card) {
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
      openUiModal("detailModal", trigger);
    }

    document.querySelectorAll(".post-detail-button").forEach((button) =>
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        openLostFoundDetail(button.closest(".post-card"), button);
      })
    );

    document.querySelectorAll(".post-card").forEach((card) => {
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
    });

    function openClaim(itemName, trigger) {
      const claimItemName = document.getElementById("claimItemName");
      const claimModal = document.getElementById("claimModal");
      if (!claimItemName || !claimModal) {
        showToast("ระบบคำขอรับคืนอยู่ระหว่างจัดเตรียม");
        return;
      }
      selectedClaimItem = itemName;
      claimItemName.textContent = itemName;
      openUiModal("claimModal", trigger);
    }

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

    function showSuccess(type, recipientEmail = "", requestId = "") {
      const trackingCode = requestId || `BC-${Math.floor(1000 + Math.random() * 9000)}`;
      trackedRequests.set(trackingCode, {
        summary: type,
        status: "รอเจ้าหน้าที่ตรวจสอบ",
        statusClass: "wait",
        requestType: "คำร้องที่ส่งผ่านระบบ",
        itemName: "ไม่แสดงข้อมูลส่วนบุคคล",
        updatedAt: "เพิ่งส่งคำร้อง",
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
      document.getElementById("trackingCode").value = trackingCode;
      if (recipientEmail)
        document.getElementById("trackingEmail").value = recipientEmail;
      openUiModal("successModal", document.activeElement);
    }

    function showLostFoundConfirmation(type, message) {
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
      const trackingPrefix = form.dataset.trackingPrefix;
      const requestId = trackingPrefix
        ? `${trackingPrefix}-${Math.floor(1000 + Math.random() * 9000)}`
        : "";
      clearImagePreviews(form);
      form.reset();
      if (form.dataset.confirmationMode === "lost-found") {
        showLostFoundConfirmation(
          `${type}เรียบร้อยแล้ว`,
          "โปรดนำสิ่งของไปฝากที่สำนักงานธุรการ เพื่อให้เจ้าหน้าที่ตรวจสอบและดูแลการคืนของ"
        );
      } else {
        showSuccess(`${type}เรียบร้อยแล้ว`, recipientEmail, requestId);
      }
    }

    document
      .querySelectorAll("[data-submit-type]")
      .forEach((form) =>
        form.addEventListener("submit", (event) =>
          submitDemo(event, form.dataset.submitType)
        )
      );

    const lostItemForm = document.getElementById("lostItemForm");
    const lostItemValidationRules = {
      item_category: (value) =>
        value ? "" : "กรุณาเลือกประเภทสิ่งของ",
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
      recipient_email: (value, field) => {
        if (!value.trim()) return "กรุณาระบุอีเมลสำหรับติดตามสถานะ";
        if (field.validity.typeMismatch) return "กรุณาระบุอีเมลให้ถูกต้อง";
        return "";
      },
    };

    function validateLostItemField(field) {
      const message = lostItemValidationRules[field.name]?.(field.value, field) || "";
      field.setCustomValidity(message);
      field.setAttribute("aria-invalid", String(Boolean(message)));
      document.getElementById(`${field.id}Error`).textContent = message;
      return !message;
    }

    function validateLostItemForm(form) {
      const fields = Array.from(form.querySelectorAll("select, input, textarea"));
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

    lostItemForm.querySelectorAll("select, input, textarea").forEach((field) => {
      if (!lostItemValidationRules[field.name]) return;
      const eventName = field.tagName === "SELECT" ? "change" : "input";
      field.addEventListener(eventName, () => validateLostItemField(field));
      field.addEventListener("blur", () => validateLostItemField(field));
    });

    lostItemForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = event.currentTarget;

      if (!validateLostItemForm(form)) {
        form.reportValidity();
        showToast("กรุณากรอกข้อมูลที่จำเป็นให้ครบ");
        return;
      }

      const formData = new FormData(form);
      const submitButton = form.querySelector('button[type="submit"]');
      const reporterEmail = formData.get("reporter_email").trim();

      submitButton.disabled = true;
      submitButton.textContent = "กำลังส่งประกาศ...";

      try {
        const item = await createLostItem({
          report_type: "lost",
          item_category: formData.get("item_category"),
          item_name: formData.get("item_name"),
          event_datetime: new Date(formData.get("event_datetime")).toISOString(),
          location_detail: formData.get("location_detail"),
          description: formData.get("description"),
          reporter_email: reporterEmail,
        });

        clearImagePreviews(form);
        form.reset();
        showSuccess("แจ้งของหายเรียบร้อยแล้ว", item.reporter_email || reporterEmail, item.item_code);
      } catch (error) {
        showToast(error.message || "ไม่สามารถส่งรายการของหายได้");
      } finally {
        submitButton.disabled = false;
        submitButton.textContent = "เผยแพร่ประกาศตามหา";
      }
    });

    const foundItemForm = document.getElementById("publicFoundForm");
    const foundItemValidationRules = {
      item_category: (value) => value ? "" : "กรุณาเลือกประเภทสิ่งของ",
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
        if (foundDate && new Date(`${foundDate}T${value}`).getTime() > Date.now()) {
          return "เวลาที่พบสิ่งของต้องไม่เป็นเวลาในอนาคต";
        }
        return "";
      },
      location_detail: (value) => validateRequiredText(value, "สถานที่พบสิ่งของ"),
      custody_location: (value) => validateRequiredText(value, "จุดรับฝากสิ่งของ"),
      description: (value) => validateRequiredText(value, "รายละเอียดสิ่งของ", 10),
      private_detail: (value) => validateRequiredText(value, "รายละเอียดลับ", 10),
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
      const message = foundItemValidationRules[field.name]?.(field.value, field) || "";
      field.setCustomValidity(message);
      field.setAttribute("aria-invalid", String(Boolean(message)));
      document.getElementById(`${field.id}Error`).textContent = message;
      return !message;
    }

    function validateFoundItemForm(form) {
      const fields = Array.from(form.querySelectorAll("select, input, textarea"));
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

    foundItemForm.querySelectorAll("select, input, textarea").forEach((field) => {
      if (!foundItemValidationRules[field.name]) return;
      const eventName = field.tagName === "SELECT" ? "change" : "input";
      field.addEventListener(eventName, () => validateFoundItemField(field));
      field.addEventListener("blur", () => validateFoundItemField(field));
    });

    foundItemForm.addEventListener("submit", (event) => {
      if (!validateFoundItemForm(foundItemForm)) {
        event.preventDefault();
        foundItemForm.reportValidity();
        showToast("กรุณากรอกข้อมูลที่จำเป็นให้ครบ");
        return;
      }
      submitDemo(event, "ส่งรายการพบของเพื่อรอเจ้าหน้าที่ตรวจสอบ");
    });

    document.querySelectorAll(".image-input").forEach((input) => {
      const container = input.closest(".upload-field");
      const preview = container.querySelector(".image-preview");
      const image = preview.querySelector("img");
      const fileName = preview.querySelector("span");
      const removeButton = preview.querySelector(".remove-image");
      const fileError = document.getElementById(input.dataset.errorId);
      const setFileError = (message = "") => {
        input.setCustomValidity(message);
        input.setAttribute("aria-invalid", String(Boolean(message)));
        if (fileError) fileError.textContent = message;
      };
      input.addEventListener("change", () => {
        const file = input.files[0];
        if (!file) {
          setFileError();
          return;
        }
        if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
          setFileError("รองรับเฉพาะไฟล์ JPG, PNG หรือ WebP");
          input.value = "";
          showToast("รองรับเฉพาะไฟล์ JPG, PNG หรือ WebP");
          return;
        }
        if (file.size > Number(input.dataset.maxSize)) {
          setFileError("รูปภาพต้องมีขนาดไม่เกิน 5 MB");
          input.value = "";
          showToast("รูปภาพต้องมีขนาดไม่เกิน 5 MB");
          return;
        }
        setFileError();
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
        setFileError();
        input.focus();
      });
    });

    function renderTrackingResult(code, ids) {
      const trackedRequest = trackedRequests.get(code);
      const statusBadge = document.getElementById(ids.status);
      document.getElementById(ids.code).textContent = code;

      if (trackedRequest) {
        document.getElementById(ids.text).textContent = trackedRequest.summary;
        statusBadge.textContent = trackedRequest.status;
        statusBadge.className = `status ${trackedRequest.statusClass}`;
        if (ids.details) {
          document.getElementById(ids.details).hidden = false;
          document.getElementById(ids.requestType).textContent =
            trackedRequest.requestType;
          document.getElementById(ids.itemName).textContent = trackedRequest.itemName;
          document.getElementById(ids.updatedAt).textContent = trackedRequest.updatedAt;
        }
        showToast("พบข้อมูลคำร้อง");
      } else {
        document.getElementById(ids.text).textContent =
          "ไม่พบคำร้องที่ตรงกับรหัสนี้ กรุณาตรวจสอบรหัสแล้วลองใหม่อีกครั้ง";
        statusBadge.textContent = "ไม่พบข้อมูล";
        statusBadge.className = "status not-found";
        if (ids.details) document.getElementById(ids.details).hidden = true;
        showToast("ไม่พบคำร้อง");
      }
      document.getElementById(ids.result).classList.add("show");
    }

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
        renderTrackingResult(code, {
          result: "trackingResult",
          code: "trackingResultCode",
          text: "trackingResultText",
          status: "trackingResultStatus",
        });
      });

    document
      .getElementById("lostFoundTrackingForm")
      .addEventListener("submit", (event) => {
        event.preventDefault();
        const form = event.currentTarget;
        if (!form.checkValidity()) {
          form.reportValidity();
          return;
        }
        const code = document
          .getElementById("lostFoundTrackingCode")
          .value.trim()
          .toUpperCase();
        renderTrackingResult(code, {
          result: "lostFoundTrackingResult",
          code: "lostFoundTrackingResultCode",
          text: "lostFoundTrackingResultText",
          status: "lostFoundTrackingResultStatus",
          details: "lostFoundTrackingDetails",
          requestType: "lostFoundTrackingRequestType",
          itemName: "lostFoundTrackingItemName",
          updatedAt: "lostFoundTrackingUpdatedAt",
        });
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
      const message = claimValidationRules[field.name]?.(field.value, field) || "";
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

    claimForm?.addEventListener("submit", (event) => {
      event.preventDefault();
      if (!validateClaimForm()) {
        showToast("กรุณากรอกข้อมูลยืนยันให้ครบ");
        return;
      }
      claimForm.querySelectorAll("input, textarea").forEach((field) => {
        field.value = field.value.trim();
      });
      const recipientEmail = document.getElementById("claimContact")?.value.trim() || "";
      claimForm.reset();
      const trackingCode = `CLAIM-${Math.floor(1000 + Math.random() * 9000)}`;
      showSuccess(
        `ส่งคำขอรับคืน ${selectedClaimItem} แล้ว`,
        recipientEmail,
        trackingCode
      );
    });

    const viewStatusButton = document.getElementById("viewStatusButton");
    viewStatusButton?.addEventListener("click", () => {
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
      320
    );
  });

  onUnmounted(() => {
    document.body.classList.remove("modal-open", "offline");
  });
}
