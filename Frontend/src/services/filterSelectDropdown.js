const enhancedSelects = new WeakMap();

function icon(path) {
  return `<svg viewBox="0 0 20 20" aria-hidden="true"><path d="${path}" /></svg>`;
}

export function enhanceFilterSelects(root = document) {
  const cleanups = [];

  root.querySelectorAll("select.field-compact").forEach((select) => {
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
    const label = select.getAttribute("aria-label") || "ตัวกรอง";
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
      menu.replaceChildren();
      options.forEach((option) => {
        const item = document.createElement("button");
        item.type = "button";
        item.className = "filter-select-option";
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
      const items = [...menu.querySelectorAll(".filter-select-option")];
      const index = items.indexOf(document.activeElement);
      const step = event.key === "ArrowDown" ? 1 : -1;
      items[(index + step + items.length) % items.length]?.focus();
    }

    trigger.addEventListener("click", toggle);
    wrapper.addEventListener("keydown", handleKeydown);
    select.addEventListener("change", sync);
    document.addEventListener("pointerdown", handleOutside);
    const observer = new MutationObserver(sync);
    observer.observe(select, { childList: true, subtree: true });
    sync();

    const cleanup = () => {
      observer.disconnect();
      document.removeEventListener("pointerdown", handleOutside);
      enhancedSelects.delete(select);
    };
    enhancedSelects.set(select, cleanup);
    cleanups.push(cleanup);
  });

  return () => cleanups.forEach((cleanup) => cleanup());
}
