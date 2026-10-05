import test from "node:test";
import assert from "node:assert/strict";
import {
  rememberInvitationDelivery,
  toDashboardStaff,
  toUpdatedDashboardStaff,
  updateStaffProfile,
} from "../src/view-logic/staff-dashboard/staff-accounts.js";

const account = {
  id: "staff-id", email: "old@example.com", full_name: "Staff",
  role: "technician", status: "active",
};

function mockStorage(t) {
  const data = new Map([["buildingCareAccessToken", "test-token"]]);
  const previous = globalThis.localStorage;
  globalThis.localStorage = {
    getItem: (key) => data.get(key) ?? null,
    setItem: (key, value) => data.set(key, value),
  };
  t.after(() => { globalThis.localStorage = previous; });
  return data;
}

test("profile PATCH sends changed fields with authentication and returns server profile", async (t) => {
  mockStorage(t);
  const previousFetch = globalThis.fetch;
  t.after(() => { globalThis.fetch = previousFetch; });
  globalThis.fetch = async (url, options) => {
    assert.equal(url, "http://localhost:8000/api/v1/staff/staff-id");
    assert.equal(options.method, "PATCH");
    assert.equal(options.headers.Authorization, "Bearer test-token");
    assert.deepEqual(JSON.parse(options.body), { full_name: "New Name" });
    return new Response(JSON.stringify({ ...account, full_name: "New Name" }));
  };
  assert.equal((await updateStaffProfile(account.id, { full_name: "New Name" })).full_name, "New Name");
});

test("failed profile update preserves invitation delivery cache", async (t) => {
  const data = mockStorage(t);
  rememberInvitationDelivery(account, "sent");
  const before = data.get("buildingCareInvitationDeliveryResults");
  const previousFetch = globalThis.fetch;
  t.after(() => { globalThis.fetch = previousFetch; });
  globalThis.fetch = async () => new Response(JSON.stringify({ detail: "Email already exists" }), { status: 409 });
  await assert.rejects(updateStaffProfile(account.id, { email: "taken@example.com" }),
    (error) => error.status === 409);
  assert.equal(data.get("buildingCareInvitationDeliveryResults"), before);
});

test("changing only the name preserves delivery status; changing email clears old delivery", (t) => {
  const data = mockStorage(t);
  rememberInvitationDelivery(account, "sent");
  const before = toDashboardStaff(account);
  const renamed = toUpdatedDashboardStaff(before, { ...account, full_name: "New Name" });
  assert.equal(renamed.invitationDeliveryStatus, "sent");
  assert.equal(renamed.name, "New Name");
  const newEmail = toUpdatedDashboardStaff(before, { ...account, email: "new@example.com" });
  assert.equal(newEmail.invitationDeliveryStatus, "unknown");
  assert.equal(newEmail.role, before.role);
  assert.equal(JSON.parse(data.get("buildingCareInvitationDeliveryResults"))[account.id], undefined);
});
