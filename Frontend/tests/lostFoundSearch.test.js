import test from "node:test";
import assert from "node:assert/strict";
import { fetchPublicLostFoundItems } from "../src/services/api.js";
import { getApprovedLostFoundItems } from "../src/services/clerkApi.js";
import { createLostFoundStore, filterLostFoundItems, sortLostFoundItems } from "../src/services/lostFoundSearch.js";

const makeItem = (id, overrides = {}) => ({
  id: String(id).padStart(4, "0"),
  report_type: "found",
  item_name: "กระเป๋า BLACK",
  description: null,
  location_detail: null,
  created_at: "2026-01-01T00:00:00Z",
  ...overrides,
});

test("search handles Thai, case, whitespace, nulls, type and literal wildcards", () => {
  const items = [makeItem(1), makeItem(2, {
    report_type: "lost", item_name: "กุญแจ", description: "รอย 50%_", location_detail: "โถง",
  })];
  assert.equal(filterLostFoundItems(items, { search: " กระเป๋า " }).length, 1);
  assert.equal(filterLostFoundItems(items, { search: "black" }).length, 1);
  assert.equal(filterLostFoundItems(items, { search: "   " }).length, 2);
  assert.equal(filterLostFoundItems(items, { search: "50%_" }).length, 1);
  assert.equal(filterLostFoundItems(items, { search: "%" }).length, 1);
  assert.equal(filterLostFoundItems(items, { search: "โถง", type: "found" }).length, 0);
  assert.equal(filterLostFoundItems(items, { type: "lost" }).length, 1);
  assert.equal(filterLostFoundItems(items, { type: "found" }).length, 1);
  assert.equal(filterLostFoundItems(items, { type: "all" }).length, 2);
  assert.equal(filterLostFoundItems(items, { search: "ไม่พบ" }).length, 0);
  assert.throws(() => filterLostFoundItems(items, { type: "invalid" }), RangeError);
});

test("a phrase must match one field, and rows after 200 remain searchable", () => {
  const items = Array.from({ length: 500 }, (_, i) => makeItem(i, { item_name: "อื่น" }));
  items[499] = makeItem(499, { item_name: "คำค้นเฉพาะ", description: "รายละเอียด" });
  const snapshot = structuredClone(items);
  assert.equal(filterLostFoundItems(items, { search: "คำค้นเฉพาะ" })[0], items[499]);
  assert.equal(filterLostFoundItems(items, { search: "คำค้นเฉพาะ รายละเอียด" }).length, 0);
  assert.deepEqual(items, snapshot);
});

test("sorting uses newest first and descending id for ties without mutating input", () => {
  const items = [makeItem(1), makeItem(3), makeItem(2, { created_at: "2026-02-01T00:00:00Z" })];
  const snapshot = structuredClone(items);
  assert.deepEqual(sortLostFoundItems(items).map((item) => item.id), ["0002", "0003", "0001"]);
  assert.deepEqual(items, snapshot);
});

test("cache coalesces initial requests and refreshes, including an empty result", async () => {
  let calls = 0;
  let resolveFetch;
  const store = createLostFoundStore(() => {
    calls++;
    return new Promise((resolve) => { resolveFetch = resolve; });
  });
  const first = store.ensureLoaded();
  assert.equal(store.ensureLoaded(), first);
  await Promise.resolve();
  resolveFetch({ items: [] });
  await first;
  assert.equal(store.loaded, true);
  await store.ensureLoaded();
  assert.equal(calls, 1);
  const refresh = store.ensureLoaded({ force: true });
  assert.equal(store.ensureLoaded({ force: true }), refresh);
  await Promise.resolve();
  resolveFetch({ items: [makeItem(1)] });
  await refresh;
  assert.equal(calls, 2);
  assert.equal(store.items.length, 1);
});

test("failed initial loads can retry and failed refreshes preserve the successful cache", async () => {
  let fail = true;
  let nextItems = [makeItem(1)];
  const store = createLostFoundStore(async () => {
    if (fail) throw new Error("offline");
    return { items: nextItems };
  });
  await assert.rejects(store.ensureLoaded(), /offline/);
  assert.equal(store.loaded, false);
  fail = false;
  await store.ensureLoaded();
  fail = true;
  await assert.rejects(store.ensureLoaded({ force: true }), /offline/);
  assert.equal(store.loaded, true);
  assert.equal(store.items[0].id, "0001");
  fail = false;
  nextItems = [makeItem(2)];
  await store.ensureLoaded({ force: true });
  assert.equal(store.items[0].id, "0002");
});

test("Guest and Clerk load both complete lists without search or pagination parameters", async (t) => {
  const urls = [];
  t.mock.method(globalThis, "fetch", async (url) => {
    urls.push(url);
    const type = url.endsWith("lost-items") ? "lost" : "found";
    const items = Array.from({ length: 250 }, (_, i) => makeItem(i, { report_type: type }));
    return { ok: true, json: async () => ({ items, total: items.length }) };
  });
  const store = createLostFoundStore(fetchPublicLostFoundItems);
  await store.ensureLoaded();
  assert.equal(store.items.length, 500);
  filterLostFoundItems(store.items, { search: "กระเป๋า", type: "lost" });
  await store.ensureLoaded();
  assert.equal(urls.length, 2);
  await store.ensureLoaded({ force: true });
  assert.equal(urls.length, 4);
  const clerk = await getApprovedLostFoundItems();
  assert.equal(clerk.foundItems.length, 250);
  assert.equal(clerk.lostItems.length, 250);
  assert.equal(urls.length, 6);
  for (const url of urls) assert.equal(new URL(url).search, "");
});

test("one failed endpoint or an incomplete list never marks the store as loaded", async (t) => {
  let mode = "failure";
  t.mock.method(globalThis, "fetch", async (url) => ({
    ok: !url.endsWith("found-items") || mode !== "failure",
    json: async () => ({ items: [makeItem(1)], total: mode === "incomplete" ? 250 : 1 }),
  }));
  const store = createLostFoundStore(fetchPublicLostFoundItems);
  await assert.rejects(store.ensureLoaded(), /ไม่สามารถโหลด/);
  assert.equal(store.loaded, false);
  assert.deepEqual(store.items, []);
  mode = "incomplete";
  await assert.rejects(store.ensureLoaded(), /ไม่ครบ/);
  assert.equal(store.loaded, false);
  mode = "success";
  await store.ensureLoaded();
  assert.equal(store.items.length, 2);
});
