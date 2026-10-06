import test from "node:test";
import assert from "node:assert/strict";
import { taskHistoryRows } from "../src/view-logic/staff-dashboard/work-history.js";

const options = { staff: "แม่บ้าน", role: "แม่บ้าน", statusLabels: {
  assigned: "รับงานแล้ว", in_progress: "กำลังดำเนินการ", completed: "เสร็จสิ้น",
} };
const job = { id: "CLN-1", title: "ทำความสะอาด", category: "งานทำความสะอาด", status: "เสร็จสิ้น" };
const entry = { id: "history-1", action: "status_changed", old_status: "in_progress",
  new_status: "completed", created_at: "2026-10-05T21:25:00Z" };

test("restores persisted completion events with the local date and time", () => {
  const [row] = taskHistoryRows(job, [entry], options);
  assert.equal(row.action, "ปิดงาน");
  assert.equal(row.status, "เสร็จสิ้น");
  assert.equal(row.date, "2026-10-06");
  assert.equal(row.time, "04:25");
  assert.equal(row.staff, options.staff);
  assert.equal(row.itemId, job.id);
  assert.equal(row.uid, "backend-history-1");
  assert.deepEqual(taskHistoryRows(job, [entry], options), taskHistoryRows(job, [entry], options));
});

test("excludes guest creation and distinguishes completion notes from closed work", () => {
  const rows = taskHistoryRows(job, [
    { ...entry, id: "created", action: "created" },
    { ...entry, id: "accepted", action: "accepted", new_status: "assigned" },
    { ...entry, id: "completed", action: "completed" },
    { ...entry, id: "note", action: "completion_note_added", note: "เรียบร้อย" },
  ], options);
  assert.deepEqual(rows.map(row => row.action), ["รับงาน", "ปิดงาน", "เพิ่มหมายเหตุ"]);
  assert.equal(rows[2].detail, "เรียบร้อย");
});
