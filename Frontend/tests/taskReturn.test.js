import test from "node:test";
import assert from "node:assert/strict";
import { returnCleaningTask } from "../src/services/housekeeperAPI.js";
import { returnRepairRequest } from "../src/services/technicianAPI.js";

function mockFetch(t, status, body) {
  const calls = [];
  const previousFetch = globalThis.fetch;
  const previousStorage = globalThis.localStorage;
  globalThis.localStorage = { getItem: () => "test-token" };
  globalThis.fetch = async (url, options) => {
    calls.push({ url, options });
    return { ok: status >= 200 && status < 300, status, json: async () => body };
  };
  t.after(() => {
    globalThis.fetch = previousFetch;
    globalThis.localStorage = previousStorage;
  });
  return calls;
}

for (const [name, fn, path] of [
  ["cleaning", returnCleaningTask, "/cleaning-tasks/task-1/return"],
  ["repair", returnRepairRequest, "/repair-requests/task-1/return"],
]) {
  test(`${name} return posts reason and note with the staff token`, async (t) => {
    const calls = mockFetch(t, 200, { status: "waiting", assigned_staff: null });
    const result = await fn("task-1", { reason: "ไม่สามารถเข้าพื้นที่ได้", note: "ห้องล็อก" });
    assert.equal(result.status, "waiting");
    assert.ok(calls[0].url.endsWith(path));
    assert.equal(calls[0].options.method, "POST");
    assert.equal(calls[0].options.headers.Authorization, "Bearer test-token");
    assert.deepEqual(JSON.parse(calls[0].options.body), {
      reason: "ไม่สามารถเข้าพื้นที่ได้",
      note: "ห้องล็อก",
    });
  });

  test(`${name} return keeps the HTTP status on conflict`, async (t) => {
    mockFetch(t, 409, { detail: "Cannot return a task with status completed" });
    await assert.rejects(fn("task-1", { reason: "x", note: "" }), (error) => {
      assert.equal(error.status, 409);
      return true;
    });
  });
}

test("cleaning task list and detail use the housekeeper token", async (t) => {
  const { getCleaningTasks, getCleaningTaskDetail } = await import("../src/services/housekeeperAPI.js");
  const calls = mockFetch(t, 200, { requests: [] });
  assert.deepEqual(await getCleaningTasks(), { requests: [] });
  await getCleaningTaskDetail("task 1");
  assert.ok(calls[0].url.endsWith("/cleaning-tasks"));
  assert.ok(calls[1].url.endsWith("/cleaning-tasks/task%201"));
  assert.equal(calls[0].options.method, "GET");
  assert.equal(calls[1].options.headers.Authorization, "Bearer test-token");
});
