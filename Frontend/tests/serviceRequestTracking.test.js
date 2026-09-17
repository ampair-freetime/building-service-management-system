import test from "node:test";
import assert from "node:assert/strict";
import { trackServiceRequest } from "../src/services/api.js";

test("retrieves repair and cleaning status with normalized code and email", async () => {
  for (const code of ["repair-20260916-abcd", "clean-20260916-efgh"]) {
    const result = await trackServiceRequest(code, " Guest@Example.com ", {
      fetchImpl: async (url, options) => {
        assert.match(url, /\/guest\/service-requests\/(REPAIR|CLEAN)-20260916-/);
        assert.match(url, /reporter_email=guest%40example.com/);
        assert.ok(options.signal);
        return new Response(JSON.stringify({
          request_code: code.toUpperCase(),
          status: "in_progress",
        }));
      },
    });
    assert.equal(result.status, "in_progress");
  }
});

test("returns null when a service request is not found", async () => {
  const result = await trackServiceRequest("CLEAN-20260916-NONE", "guest@example.com", {
    fetchImpl: async () => new Response(null, { status: 404 }),
  });
  assert.equal(result, null);
});

test("rejects unsupported request codes without sending a request", async () => {
  await assert.rejects(
    trackServiceRequest("LOST-20260916-1234", "guest@example.com", {
      fetchImpl: async () => assert.fail("must not send"),
    }),
    /ไม่ถูกต้อง/,
  );
});
