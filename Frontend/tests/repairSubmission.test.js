import test from "node:test";
import assert from "node:assert/strict";
import { useRepairSubmission } from "../src/composables/useRepairSubmission.js";
import { uploadRepairRequest } from "../src/services/repairRequests.js";

function payload(problem = "air conditioner is broken") {
  const data = new FormData();
  data.append("problem", problem);
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

  resolve({ request_code: "REPAIR-1" });
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
  data.set("problem", "different problem");
  await state.submit(data, () => resets++);
  assert.notEqual(keys[1], keys[2]);
});

test("repair adapter sends multipart data and requires a receipt", async () => {
  const data = payload();
  const result = await uploadRepairRequest(data, {
    endpoint: "/repair-test",
    requestId: "same-key",
    fetchImpl: async (url, options) => {
      assert.equal(url, "/repair-test");
      assert.equal(options.method, "POST");
      assert.equal(options.body, data);
      assert.equal(options.headers["Idempotency-Key"], "same-key");
      assert.equal(options.headers["Content-Type"], undefined);
      return new Response(JSON.stringify({ request_code: "REPAIR-2" }), { status: 201 });
    },
  });
  assert.equal(result.request_code, "REPAIR-2");

  await assert.rejects(uploadRepairRequest(data, {
    endpoint: "/repair-test",
    fetchImpl: async () => new Response("<html>fallback</html>"),
  }), /ยังยืนยัน/);
});

test("repair adapter reports unavailable, validation, and network failures", async () => {
  await assert.rejects(uploadRepairRequest(payload(), {
    endpoint: "",
    fetchImpl: async () => assert.fail("must not send"),
  }), /ยังไม่พร้อม/);
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
