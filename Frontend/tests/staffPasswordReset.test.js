import test from "node:test";
import assert from "node:assert/strict";
import { isStrongPassword, passwordRequirements } from "../src/services/passwordRules.js";
import {
  confirmPasswordReset,
  requestPasswordReset,
  validatePasswordResetToken,
} from "../src/services/staffPasswordResetApi.js";

function mockFetch(t, status, body) {
  const calls = [];
  const previous = globalThis.fetch;
  globalThis.fetch = async (url, options) => {
    calls.push({ url, options });
    return {
      ok: status >= 200 && status < 300,
      status,
      json: async () => {
        if (body === undefined) throw new SyntaxError("no body");
        return body;
      },
    };
  };
  t.after(() => { globalThis.fetch = previous; });
  return calls;
}

test("password rules match the backend policy", () => {
  assert.equal(isStrongPassword("Good-Pass1"), true);
  for (const weak of ["Aa1!aaa", "lower-case1", "UPPER-CASE1", "No-Digits!", "NoSpecial12"]) {
    assert.equal(isStrongPassword(weak), false, weak);
  }
  assert.equal(isStrongPassword(`Aa1!${"a".repeat(125)}`), false);
  assert.equal(passwordRequirements("").length, 5);
});

test("requesting a reset posts only the email", async (t) => {
  const calls = mockFetch(t, 202, { detail: "accepted" });
  await requestPasswordReset("staff@example.com");
  assert.match(calls[0].url, /\/auth\/password-reset-requests$/);
  assert.deepEqual(JSON.parse(calls[0].options.body), { email: "staff@example.com" });
});

test("validation errors keep the HTTP status for the page to react", async (t) => {
  mockFetch(t, 400, { detail: "Invalid or expired reset link. Request a new one." });
  await assert.rejects(validatePasswordResetToken("x".repeat(30)), (error) => {
    assert.equal(error.status, 400);
    return true;
  });
});

test("confirm sends new_password and accepts an empty 204 body", async (t) => {
  const calls = mockFetch(t, 204, undefined);
  await confirmPasswordReset("token-value-token-value", "Good-Pass1");
  assert.match(calls[0].url, /\/auth\/password-reset\/confirm$/);
  assert.deepEqual(JSON.parse(calls[0].options.body), {
    token: "token-value-token-value",
    new_password: "Good-Pass1",
  });
});
