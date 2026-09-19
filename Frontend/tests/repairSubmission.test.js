import test from "node:test";
import assert from "node:assert/strict";
import { useRepairSubmission } from "../src/composables/useRepairSubmission.js";
import { uploadRepairRequest } from "../src/services/repairRequests.js";

function payload(title = "air conditioner is broken") {
  const data = new FormData();
  data.append("title", title);
  data.append("description", "leaking near the window");
  data.append("priority", "urgent");
  data.append("reporter_email", "guest@example.com");
  data.append("location_id", "1");
  return data;
}

test("repair submission blocks duplicates until confirmation", async () => {
  let resolve;
  let calls = 0;
  let resets = 0;
  const state = useRepairSubmission(() => {
    calls++;
    return new Promise((done) => { resolve = done; });
  });

  const pending = state.submit(payload(), () => resets++);
  assert.equal(state.isSubmitting.value, true);
  assert.equal(state.status.value, "uploading");
  await state.submit(payload(), () => resets++);
  assert.equal(calls, 1);
  assert.equal(resets, 0);

  resolve({ request_code: "RPR-1" });
  await pending;
  assert.equal(resets, 1);
  assert.equal(state.isSubmitting.value, false);
  assert.equal(state.status.value, "success");
});

test("repair failure keeps photos and reuses the idempotency key on retry", async () => {
  const keys = [];
  let resets = 0;
  const state = useRepairSubmission(async (_, { requestId }) => {
    keys.push(requestId);
    throw new Error("offline");
  });
  const data = payload();
  data.append("image", new File(["photo"], "damage.png", { type: "image/png" }));

  await state.submit(data, () => resets++);
  assert.equal(resets, 0);
  assert.equal(data.get("image").name, "damage.png");
  assert.equal(state.status.value, "error");
  assert.equal(state.message.value, "offline");

  await state.submit(data, () => resets++);
  assert.equal(keys[0], keys[1]);
  data.set("title", "different problem");
  await state.submit(data, () => resets++);
  assert.notEqual(keys[1], keys[2]);
});

test("repair adapter uses the backend repair endpoint by default", async () => {
  let requestedUrl;
  await uploadRepairRequest(payload(), {
    requestId: "default-url",
    fetchImpl: async (url) => {
      requestedUrl = url;
      return new Response(JSON.stringify({ request_code: "RPR-1" }), { status: 201 });
    },
  });
  assert.equal(requestedUrl, "http://localhost:8000/api/v1/guest/repair-requests");
});

test("repair adapter sends multipart data and requires a receipt", async () => {
  const data = payload();
  data.append("image", new File(["photo"], "damage.png", { type: "image/png" }));
  const result = await uploadRepairRequest(data, {
    endpoint: "/repair-test",
    requestId: "same-key",
    fetchImpl: async (url, options) => {
      assert.equal(url, "/repair-test");
      assert.equal(options.method, "POST");
      assert.equal(options.body, data);
      assert.equal(options.headers["Idempotency-Key"], "same-key");
      assert.equal(options.headers["Content-Type"], undefined);
      assert.deepEqual([...options.body.keys()], [
        "title", "description", "priority", "reporter_email", "location_id", "image",
      ]);
      assert.equal(options.body.getAll("image").length, 1);
      return new Response(JSON.stringify({ request_code: "RPR-2" }), { status: 201 });
    },
  });
  assert.equal(result.request_code, "RPR-2");

  await assert.rejects(uploadRepairRequest(data, {
    endpoint: "/repair-test",
    fetchImpl: async () => new Response("<html>fallback</html>"),
  }), /ยังยืนยัน/);
});

test("repair adapter reports validation and network failures", async () => {
  await assert.rejects(uploadRepairRequest(payload(), {
    endpoint: "/repair-test",
    fetchImpl: async () => new Response(
      JSON.stringify({ detail: [{ msg: "Invalid photo" }] }),
      { status: 422 },
    ),
  }), /Invalid photo/);
  await assert.rejects(uploadRepairRequest(payload(), {
    endpoint: "/repair-test",
    fetchImpl: async () => { throw new TypeError("offline"); },
  }), /อินเทอร์เน็ต/);
});

test("repair demo success does not display an undefined receipt", async () => {
  const state = useRepairSubmission(async () => ({ demo: true }));
  let receipt;
  await state.submit(payload(), (result) => { receipt = result; });
  assert.deepEqual(receipt, { demo: true });
  assert.equal(state.message.value, "ส่งคำขอซ่อมเรียบร้อยแล้ว");
  assert.doesNotMatch(state.message.value, /undefined|รหัสติดตาม/);
});
