import test from "node:test";
import assert from "node:assert/strict";
import { trackServiceRequest } from "../src/services/api.js";

test("retrieves repair and cleaning status with normalized code and email", async () => {
  const cases = [
    ["repair-20260916-abcd", /\/guest\/service-requests\/REPAIR-20260916-/],
    ["cln-123456789abc", /\/guest\/cleaning-requests\/CLN-123456789ABC/],
  ];
  for (const [code, endpointPattern] of cases) {
    const result = await trackServiceRequest(code, " Guest@Example.com ", {
      fetchImpl: async (url, options) => {
        assert.match(url, endpointPattern);
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
  const result = await trackServiceRequest("CLN-MISSING", "guest@example.com", {
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
