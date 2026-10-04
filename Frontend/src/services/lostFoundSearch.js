const searchableFields = ["item_name", "description", "location_detail"];

export function sortLostFoundItems(items) {
  return [...items].sort((a, b) => {
    const byDate = new Date(b.created_at) - new Date(a.created_at);
    if (byDate) return byDate;
    return a.id === b.id ? 0 : a.id < b.id ? 1 : -1;
  });
}

// กรองแต่ละ field แยกกัน เพื่อไม่ให้คำค้นตรงข้ามขอบชื่อ/รายละเอียด
export function filterLostFoundItems(items, { type = "all", search = "" } = {}) {
  if (!["all", "lost", "found"].includes(type)) {
    throw new RangeError("ประเภทประกาศไม่ถูกต้อง");
  }
  const query = search.trim().toLowerCase();
  return items.filter((item) =>
    (type === "all" || item.report_type === type) &&
    (!query || searchableFields.some((field) =>
      (item[field] ?? "").toLowerCase().includes(query),
    )),
  );
}

// cache อยู่เฉพาะในหน่วยความจำ; โหลดซ้ำเฉพาะ force หรือหลังโหลดล้มเหลว
export function createLostFoundStore(fetchItems) {
  let items = [];
  let loaded = false;
  let loadPromise = null;

  return {
    get items() { return items; },
    get loaded() { return loaded; },
    ensureLoaded({ force = false } = {}) {
      if (loadPromise) return loadPromise;
      if (loaded && !force) return Promise.resolve();
      loadPromise = Promise.resolve()
        .then(fetchItems)
        .then((result) => {
          items = sortLostFoundItems(result.items);
          loaded = true;
        })
        .finally(() => { loadPromise = null; });
      return loadPromise;
    },
  };
}
