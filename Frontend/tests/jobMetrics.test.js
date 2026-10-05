import test from "node:test";
import assert from "node:assert/strict";
import { jobMetrics } from "../src/view-logic/staff-dashboard/job-metrics.js";

test("counts only owned open work and distinct completions on today's date", () => {
  const jobs = [
    ...["รับงานแล้ว", "รับเรื่องแล้ว", "กำลังดำเนินการ"].map((status, i) => ({id: `active-${i}`, status, assignee: "ฉัน"})),
    {id: "today", status: "เสร็จสิ้น", assignee: "ฉัน"},
    {id: "yesterday", status: "เสร็จสิ้น", assignee: "ฉัน"},
    {id: "cancelled", status: "ยกเลิก", backendStatus: "cancelled", assignee: "ฉัน"},
    {id: "other", status: "กำลังดำเนินการ", assignee: "คนอื่น"},
    {id: "waiting", status: "รอรับงาน", assignee: null, priority: "เร่งด่วน"},
  ];
  const history = [
    {itemId: "today", staff: "ฉัน", action: "ปิดงาน", date: "2026-10-06"},
    {itemId: "today", staff: "ฉัน", action: "ปิดงาน", date: "2026-10-06"},
    {itemId: "yesterday", staff: "ฉัน", action: "ปิดงาน", date: "2026-10-05"},
  ];
  assert.deepEqual(jobMetrics(jobs, history, "ฉัน", "2026-10-06"), {mine: 3, completed: 1, urgent: 1, unassigned: 1});
  jobs[0].status = "เสร็จสิ้น";
  history.push({itemId: "active-0", staff: "ฉัน", action: "ปิดงาน", date: "2026-10-06"});
  assert.equal(jobMetrics(jobs, history, "ฉัน", "2026-10-06").mine, 2);
  assert.equal(jobMetrics(jobs, history, "ฉัน", "2026-10-06").completed, 2);
});
