import test from "node:test";
import assert from "node:assert/strict";
import {
  requestProgress,
  requestStatusPresentation,
  serviceProgress,
  serviceTypeForRequest,
} from "../src/services/requestStatus.js";

test("maps every service status to a clear Thai label and badge style", () => {
  const cases = [
    ["waiting", "รอเจ้าหน้าที่รับเรื่อง", "wait", 0],
    ["in_progress", "กำลังดำเนินการ", "progress", 1],
    ["completed", "ดำเนินการเสร็จสิ้น", "done", 2],
  ];

  for (const [status, label, className, currentIndex] of cases) {
    const item = { request_type: "cleaning", status };
    const presentation = requestStatusPresentation(item);
    assert.equal(presentation.label, label);
    assert.equal(presentation.className, className);
    assert.equal(serviceProgress(item).currentIndex, currentIndex);
  }
});

test("recognizes repair and cleaning request codes and Thai status aliases", () => {
  assert.equal(serviceTypeForRequest({}, "CLEAN-20260916-1234"), "cleaning");
  assert.equal(serviceTypeForRequest({}, "REPAIR-20260916-1234"), "repair");
  const presentation = requestStatusPresentation(
    { status: "กำลังดำเนินการ" },
    "REPAIR-20260916-1234",
  );
  assert.equal(presentation.status, "in_progress");
  assert.equal(presentation.label, "กำลังดำเนินการ");
  assert.equal(
    requestStatusPresentation({ request_type: "repair", status: "assigned" }).status,
    "in_progress",
  );
});

test("keeps lost-and-found labels while mapping them to existing badge styles", () => {
  assert.deepEqual(requestStatusPresentation({ status: "pending" }), {
    status: "pending",
    label: "รอเจ้าหน้าที่ตรวจสอบ",
    className: "wait",
    isService: false,
  });
  assert.equal(requestStatusPresentation({ status: "approved" }).className, "done");
  assert.equal(serviceProgress({ status: "pending" }), null);
});

test("renders lost-and-found as a three-step progress indicator", () => {
  const expectedIndexes = {
    pending: 0,
    approved: 1,
    claimed: 1,
    closed: 2,
    rejected: 2,
  };

  for (const [status, currentIndex] of Object.entries(expectedIndexes)) {
    const progress = requestProgress({ report_type: "found", status });
    assert.equal(progress.steps.length, 3);
    assert.equal(progress.currentIndex, currentIndex);
  }

  assert.equal(
    requestProgress({ report_type: "found", status: "rejected" }).steps[2].label,
    "ไม่อนุมัติ",
  );
  assert.equal(
    requestProgress({ report_type: "lost", status: "closed" }).steps[2].label,
    "พบของแล้ว",
  );
  assert.equal(
    requestProgress({ report_type: "found", status: "closed" }).steps[2].label,
    "คืนเจ้าของแล้ว",
  );
  assert.equal(
    requestProgress({ status: "approved" }, "LOST-20260916-1234").steps[2].label,
    "พบของแล้ว",
  );
});
