const enhancedSelects = new WeakMap();

function icon(path) {
  return `<svg viewBox="0 0 20 20" aria-hidden="true"><path d="${path}" /></svg>`;
}

export function enhanceFilterSelects(root = document) {
  const cleanups = [];

  root.querySelectorAll("select:not([multiple]):not([data-native-select])").forEach((select) => {
    if (enhancedSelects.has(select)) return;
    const wrapper = document.createElement("div");
    wrapper.className = "filter-select-dropdown";
    const trigger = document.createElement("button");
    trigger.className = "filter-select-trigger";
    trigger.type = "button";
    trigger.setAttribute("aria-haspopup", "listbox");
    trigger.setAttribute("aria-expanded", "false");
    trigger.innerHTML = `<span></span><span class="filter-select-chevron">${icon("m5 7.5 5 5 5-5")}</span>`;
    const menu = document.createElement("div");
    menu.className = "filter-select-menu";
    menu.setAttribute("role", "listbox");
    menu.hidden = true;

    select.parentNode.insertBefore(wrapper, select);
    wrapper.append(select, trigger, menu);
    select.classList.add("filter-select-native");
    const label = select.getAttribute("aria-label")
      || select.labels?.[0]?.textContent?.trim()
      || "เลือกรายการ";
    trigger.setAttribute("aria-label", label);

    function close() {
      menu.hidden = true;
      trigger.setAttribute("aria-expanded", "false");
      wrapper.classList.remove("is-open");
    }

    function sync() {
      const options = [...select.options];
      const selected = options.find((option) => option.value === select.value) || options[0];
      trigger.querySelector("span").textContent = selected?.textContent || label;
      trigger.disabled = select.disabled;
      trigger.setAttribute("aria-invalid", select.getAttribute("aria-invalid") || "false");
      menu.replaceChildren();
      options.forEach((option) => {
        const item = document.createElement("button");
        item.type = "button";
        item.className = "filter-select-option";
        item.disabled = option.disabled;
        item.setAttribute("role", "option");
        item.setAttribute("aria-selected", String(option.value === select.value));
        const text = document.createElement("span");
        text.textContent = option.textContent;
        item.append(text);
        if (option.value === select.value) {
          item.insertAdjacentHTML("beforeend", icon("m4.5 10 3.2 3.2L15.5 5.5"));
        }
        item.addEventListener("click", () => {
          select.value = option.value;
          select.dispatchEvent(new Event("change", { bubbles: true }));
          sync();
          close();
          trigger.focus();
        });
        menu.append(item);
      });
    }

    function toggle() {
      if (!menu.hidden) return close();
      document.querySelectorAll(".filter-select-dropdown.is-open").forEach((open) => {
        if (open !== wrapper) open.querySelector(".filter-select-trigger")?.click();
      });
      sync();
      menu.hidden = false;
      trigger.setAttribute("aria-expanded", "true");
      wrapper.classList.add("is-open");
      menu.querySelector('[aria-selected="true"]')?.focus();
    }

    function handleOutside(event) {
      if (!wrapper.contains(event.target)) close();
    }

    function handleKeydown(event) {
      if (event.key === "Escape") {
        close();
        trigger.focus();
        return;
      }
      if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return;
      event.preventDefault();
      if (menu.hidden) return toggle();
      const items = [
        ...menu.querySelectorAll(".filter-select-option:not(:disabled)"),
      ];
      const index = items.indexOf(document.activeElement);
      const step = event.key === "ArrowDown" ? 1 : -1;
      items[(index + step + items.length) % items.length]?.focus();
    }

    function handleFormReset() {
      requestAnimationFrame(sync);
    }

    trigger.addEventListener("click", toggle);
    wrapper.addEventListener("keydown", handleKeydown);
    select.addEventListener("change", sync);
    select.form?.addEventListener("reset", handleFormReset);
    document.addEventListener("pointerdown", handleOutside);
    const observer = new MutationObserver(sync);
    observer.observe(select, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["disabled", "aria-invalid"],
    });
    sync();

    const cleanup = () => {
      observer.disconnect();
      select.form?.removeEventListener("reset", handleFormReset);
      document.removeEventListener("pointerdown", handleOutside);
      enhancedSelects.delete(select);
    };
    enhancedSelects.set(select, cleanup);
    cleanups.push(cleanup);
  });

  return () => cleanups.forEach((cleanup) => cleanup());
}

const enhancedDates = new WeakMap();
const thaiDateFormatter = new Intl.DateTimeFormat("th-TH", {
  day: "numeric",
  month: "short",
  year: "numeric",
});
const thaiMonthFormatter = new Intl.DateTimeFormat("th-TH", {
  month: "long",
  year: "numeric",
});
const thaiDateTimeFormatter = new Intl.DateTimeFormat("th-TH", {
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

function parseDateValue(value) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(
    (value || "").slice(0, 10),
  );
  return match
    ? new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]))
    : null;
}

function dateValue(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function currentLocalDateTimeValue() {
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, "0");
  const minutes = String(now.getMinutes()).padStart(2, "0");
  return `${dateValue(now)}T${hours}:${minutes}`;
}

export function enhanceDatePickers(root = document) {
  const cleanups = [];
  root.querySelectorAll('input:is([type="date"], [type="datetime-local"]):not([data-native-date])').forEach((input) => {
    if (enhancedDates.has(input)) return;

    const wrapper = document.createElement("div");
    wrapper.className = "date-picker-dropdown";
    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "date-picker-trigger";
    trigger.setAttribute("aria-haspopup", "dialog");
    trigger.setAttribute("aria-expanded", "false");
    trigger.innerHTML = `<span></span><span class="date-picker-icon">${icon("M5.5 2.8v2.4m9-2.4v2.4M3.2 7.2h13.6M4.5 4.3h11a1.5 1.5 0 0 1 1.5 1.5v10a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 3 15.8v-10a1.5 1.5 0 0 1 1.5-1.5Z")}</span>`;
    const menu = document.createElement("div");
    menu.className = "date-picker-menu";
    menu.setAttribute("role", "dialog");
    menu.setAttribute("aria-label", input.getAttribute("aria-label") || "เลือกวันที่");
    menu.hidden = true;

    input.parentNode.insertBefore(wrapper, input);
    wrapper.append(input, trigger, menu);
    input.classList.add("date-picker-native");
    const includesTime = input.type === "datetime-local";
    if (includesTime && input.hasAttribute("data-default-now") && !input.value) {
      input.value = currentLocalDateTimeValue();
    }
    let visibleMonth = parseDateValue(input.value) || new Date();
    visibleMonth = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth(), 1);

    function inRange(value) {
      const minimum = input.min.slice(0, 10);
      const maximum = input.max.slice(0, 10);
      return (!minimum || value >= minimum) && (!maximum || value <= maximum);
    }

    function syncTrigger() {
      const selected = parseDateValue(input.value);
      trigger.querySelector("span").textContent = selected
        ? includesTime
          ? thaiDateTimeFormatter.format(
              new Date(`${input.value.slice(0, 16)}:00`),
            )
          : thaiDateFormatter.format(selected)
        : "เลือกวันที่";
      trigger.disabled = input.disabled;
      trigger.setAttribute("aria-invalid", input.getAttribute("aria-invalid") || "false");
    }

    function render() {
      menu.replaceChildren();
      menu.classList.toggle("has-time", includesTime);
      const content = document.createElement("div");
      content.className = "date-picker-content";
      const calendar = document.createElement("div");
      calendar.className = "date-picker-calendar";
      const header = document.createElement("div");
      header.className = "date-picker-header";
      const previous = document.createElement("button");
      previous.type = "button";
      previous.className = "date-picker-nav";
      previous.setAttribute("aria-label", "เดือนก่อนหน้า");
      previous.innerHTML = icon("m12.5 4.5-5.5 5.5 5.5 5.5");
      const title = document.createElement("strong");
      title.textContent = thaiMonthFormatter.format(visibleMonth);
      const next = document.createElement("button");
      next.type = "button";
      next.className = "date-picker-nav";
      next.setAttribute("aria-label", "เดือนถัดไป");
      next.innerHTML = icon("m7.5 4.5 5.5 5.5-5.5 5.5");
      header.append(previous, title, next);

      const weekdays = document.createElement("div");
      weekdays.className = "date-picker-weekdays";
      ["อา", "จ", "อ", "พ", "พฤ", "ศ", "ส"].forEach((day) => {
        const label = document.createElement("span");
        label.textContent = day;
        weekdays.append(label);
      });
      const grid = document.createElement("div");
      grid.className = "date-picker-grid";
      const firstDay = visibleMonth.getDay();
      const daysInMonth = new Date(
        visibleMonth.getFullYear(),
        visibleMonth.getMonth() + 1,
        0,
      ).getDate();
      for (let blank = 0; blank < firstDay; blank += 1) {
        grid.append(document.createElement("span"));
      }
      const today = dateValue(new Date());
      for (let day = 1; day <= daysInMonth; day += 1) {
        const date = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth(), day);
        const value = dateValue(date);
        const button = document.createElement("button");
        button.type = "button";
        button.className = "date-picker-day";
        button.textContent = String(day);
        button.disabled = !inRange(value);
        button.setAttribute("aria-label", thaiDateFormatter.format(date));
        button.setAttribute("aria-selected", String(input.value.slice(0, 10) === value));
        if (value === today) button.classList.add("is-today");
        button.addEventListener("click", () => {
          const currentTime = input.value.slice(11, 16) || "00:00";
          input.value = includesTime ? `${value}T${currentTime}` : value;
          input.dispatchEvent(new Event("input", { bubbles: true }));
          input.dispatchEvent(new Event("change", { bubbles: true }));
          syncTrigger();
          if (includesTime) render();
          else {
            close();
            trigger.focus();
          }
        });
        grid.append(button);
      }
      previous.addEventListener("click", () => {
        visibleMonth = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() - 1, 1);
        render();
      });
      next.addEventListener("click", () => {
        visibleMonth = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() + 1, 1);
        render();
      });
      calendar.append(header, weekdays, grid);
      content.append(calendar);
      if (includesTime) {
        const timePanel = document.createElement("div");
        timePanel.className = "date-picker-time-panel";
        const timeTitle = document.createElement("strong");
        timeTitle.textContent = "เลือกเวลา";
        const timeColumns = document.createElement("div");
        timeColumns.className = "date-picker-time-columns";
        const [selectedHour = "00", selectedMinute = "00"] =
          (input.value.slice(11, 16) || "00:00").split(":");

        function createTimeColumn(label, count, selectedValue, updatePart) {
          const column = document.createElement("div");
          column.className = "date-picker-time-column";
          const heading = document.createElement("span");
          heading.textContent = label;
          const list = document.createElement("div");
          list.className = "date-picker-time-list";
          for (let index = 0; index < count; index += 1) {
            const value = String(index).padStart(2, "0");
            const option = document.createElement("button");
            option.type = "button";
            option.textContent = value;
            option.setAttribute("aria-label", `${label} ${value}`);
            option.setAttribute("aria-selected", String(value === selectedValue));
            option.addEventListener("click", () => {
              const selectedDate = input.value.slice(0, 10) || dateValue(new Date());
              const current = (input.value.slice(11, 16) || "00:00").split(":");
              current[updatePart] = value;
              input.value = `${selectedDate}T${current.join(":")}`;
              input.dispatchEvent(new Event("input", { bubbles: true }));
              input.dispatchEvent(new Event("change", { bubbles: true }));
              syncTrigger();
              list.querySelectorAll("button").forEach((item) =>
                item.setAttribute("aria-selected", String(item === option)),
              );
            });
            list.append(option);
          }
          column.append(heading, list);
          requestAnimationFrame(() =>
            list.querySelector('[aria-selected="true"]')?.scrollIntoView({ block: "center" }),
          );
          return column;
        }

        timeColumns.append(
          createTimeColumn("ชั่วโมง", 24, selectedHour, 0),
          createTimeColumn("นาที", 60, selectedMinute, 1),
        );
        const confirm = document.createElement("button");
        confirm.type = "button";
        confirm.className = "date-picker-confirm";
        confirm.textContent = "ตกลง";
        confirm.addEventListener("click", () => {
          if (!input.value) {
            input.value = `${dateValue(new Date())}T${selectedHour}:${selectedMinute}`;
            input.dispatchEvent(new Event("input", { bubbles: true }));
            input.dispatchEvent(new Event("change", { bubbles: true }));
          }
          syncTrigger();
          close();
          trigger.focus();
        });
        timePanel.append(timeTitle, timeColumns, confirm);
        content.append(timePanel);
      }
      menu.append(content);
    }

    function keepMenuInsideViewport() {
      if (menu.hidden || window.innerWidth > 720) {
        menu.style.removeProperty("--date-picker-offset-x");
        return;
      }
      menu.style.setProperty("--date-picker-offset-x", "0px");
      const rect = menu.getBoundingClientRect();
      const viewportMargin = 14;
      let offset = 0;
      if (rect.left < viewportMargin) offset += viewportMargin - rect.left;
      if (rect.right + offset > window.innerWidth - viewportMargin) {
        offset -= rect.right + offset - (window.innerWidth - viewportMargin);
      }
      menu.style.setProperty("--date-picker-offset-x", `${offset}px`);
    }

    function close() {
      menu.hidden = true;
      menu.style.removeProperty("--date-picker-offset-x");
      trigger.setAttribute("aria-expanded", "false");
      wrapper.classList.remove("is-open");
    }

    function toggle() {
      if (!menu.hidden) return close();
      document.querySelectorAll(".date-picker-dropdown.is-open").forEach((open) => {
        if (open !== wrapper) open.querySelector(".date-picker-trigger")?.click();
      });
      const selected = parseDateValue(input.value);
      if (selected) visibleMonth = new Date(selected.getFullYear(), selected.getMonth(), 1);
      render();
      menu.hidden = false;
      trigger.setAttribute("aria-expanded", "true");
      wrapper.classList.add("is-open");
      requestAnimationFrame(keepMenuInsideViewport);
    }

    function handleOutside(event) {
      if (!wrapper.contains(event.target)) close();
    }
    function handleKeydown(event) {
      if (event.key !== "Escape") return;
      close();
      trigger.focus();
    }
    function handleReset() {
      requestAnimationFrame(() => {
        if (includesTime && input.hasAttribute("data-default-now")) {
          input.value = currentLocalDateTimeValue();
          input.dispatchEvent(new Event("input", { bubbles: true }));
        }
        syncTrigger();
        render();
      });
    }

    trigger.addEventListener("click", toggle);
    wrapper.addEventListener("keydown", handleKeydown);
    input.addEventListener("input", syncTrigger);
    input.addEventListener("change", syncTrigger);
    input.form?.addEventListener("reset", handleReset);
    document.addEventListener("pointerdown", handleOutside);
    window.addEventListener("resize", keepMenuInsideViewport);
    const observer = new MutationObserver(syncTrigger);
    observer.observe(input, {
      attributes: true,
      attributeFilter: ["disabled", "min", "max", "aria-invalid"],
    });
    syncTrigger();

    const cleanup = () => {
      observer.disconnect();
      input.form?.removeEventListener("reset", handleReset);
      document.removeEventListener("pointerdown", handleOutside);
      window.removeEventListener("resize", keepMenuInsideViewport);
      enhancedDates.delete(input);
    };
    enhancedDates.set(input, cleanup);
    cleanups.push(cleanup);
  });
  return () => cleanups.forEach((cleanup) => cleanup());
}
