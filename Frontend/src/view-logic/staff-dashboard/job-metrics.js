import { isTerminalStatus } from "./utils.js";

export function jobMetrics(jobs, history, staff, today) {
  const completedToday = new Set(history.filter((entry) =>
    entry.staff === staff && entry.action === "ปิดงาน" && entry.date === today,
  ).map((entry) => entry.itemId));
  return {
    unassigned: jobs.filter(job => !job.assignee && !isTerminalStatus(job.status) && job.backendStatus !== "cancelled").length,
    mine: jobs.filter(job => job.assignee === staff && !isTerminalStatus(job.status) && job.backendStatus !== "cancelled" && job.status !== "ยกเลิก").length,
    urgent: jobs.filter(job => job.priority === "เร่งด่วน" && !isTerminalStatus(job.status) && job.backendStatus !== "cancelled").length,
    completed: jobs.filter(job => job.assignee === staff && job.status === "เสร็จสิ้น" && completedToday.has(job.id)).length,
  };
}
