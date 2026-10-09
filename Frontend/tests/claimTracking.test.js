import test from "node:test";
import assert from "node:assert/strict";
import {trackClaim, submitClaimAdditionalInfo} from "../src/services/api.js";
import {requestStatusPresentation, requestProgress} from "../src/services/requestStatus.js";
import {mapOwnershipClaim, mapPendingFoundItem} from "../src/view-logic/staff-dashboard/lost-found-mappers.js";

test("claim tracking normalizes credentials and hides not-found results", async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async url => {
    assert.match(url, /\/guest\/claims\/CLM-20261008-12345678\?claimant_email=guest%40example.com$/);
    return new Response("{}", {status: 404});
  };
  try { assert.equal(await trackClaim(" clm-20261008-12345678 ", " GUEST@example.com "), null); }
  finally { globalThis.fetch = original; }
});
test("additional proof is sent with email; rejection is shown to caller", async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async (url, options) => {
    assert.equal(options.method, "POST");
    assert.match(url, /\/additional-info$/);
    assert.deepEqual(JSON.parse(options.body), {claimant_email: "g@example.com", proof_detail: "serial 123"});
    return new Response(JSON.stringify({detail: "คำขอไม่ได้รอหลักฐาน"}), {status: 409});
  };
  try { await assert.rejects(submitClaimAdditionalInfo("CLM-X", "g@example.com", "serial 123"), /ไม่ได้รอหลักฐาน/); }
  finally { globalThis.fetch = original; }
});
test("claim statuses describe ownership rather than publication", () => {
  assert.equal(requestStatusPresentation({status: "approved"}, "CLM-X").label, "ยืนยันเจ้าของแล้ว · รอนัดรับของ");
  assert.equal(requestProgress({status: "scheduled"}, "CLM-X").currentIndex, 2);
  assert.equal(requestProgress({status: "additional_info_required"}, "CLM-X").steps[1].label, "กรุณาส่งหลักฐานเพิ่มเติม");
});
test("clerk mapping separates API UUID, display code, place and proof", () => {
  const mapped = mapOwnershipClaim({id: "internal-uuid", claim_code: "CLM-X", item_code: "FOUND-X",
    location_detail: "Lobby", proof_detail: "serial 123", custody_location: "Office", status: "pending",
    created_at: "2026-10-08T00:00:00Z"}, status => status, () => "pending");
  assert.equal(mapped.backendId, "internal-uuid");
  assert.equal(mapped.id, "CLM-X");
  assert.equal(mapped.displayCode, "CLM-X");
  assert.equal(mapped.place, "Lobby");
  assert.equal(mapped.evidence, "serial 123");
  assert.equal(mapped.custodyLocation, "Office");
  const found = mapPendingFoundItem({id: "uuid", item_code: "FOUND-X", created_at: "2026-10-08T00:00:00Z"});
  assert.equal(found.reportedAt, "2026-10-08T00:00:00Z");
  assert.equal(found.custody, undefined);
});
