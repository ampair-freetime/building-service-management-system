export function taskHistoryRows(job, entries, { staff, role, statusLabels }) {
  const actions = {
    accepted: "รับงาน", assigned: "รับงาน", reassigned: "รับงาน",
    status_changed: "อัปเดตสถานะ", completed: "ปิดงาน",
    returned: "คืนงาน", cancelled: "ยกเลิกงาน",
    completion_note_added: "เพิ่มหมายเหตุ",
  };
  return entries.filter((entry) => actions[entry.action]).map((entry) => {
    const timestamp = new Date(entry.created_at);
    const date = new Intl.DateTimeFormat("en-CA", {
      timeZone: "Asia/Bangkok", year: "numeric", month: "2-digit", day: "2-digit",
    }).format(timestamp);
    const status = statusLabels[entry.new_status] || entry.new_status || job.status;
    return {
      uid: `backend-${entry.id}`, staff, role, itemId: job.id,
      sourceAction: entry.action,
      timestamp: timestamp.getTime(),
      title: job.title, category: job.category,
      action: entry.new_status === "completed" && entry.action === "status_changed"
        ? "ปิดงาน" : actions[entry.action],
      status, detail: (["returned", "completion_note_added"].includes(entry.action) ? entry.note : "") || `${statusLabels[entry.old_status] || entry.old_status || "เริ่มต้น"} → ${status}`,
      date,
      time: new Intl.DateTimeFormat("th-TH", {
        timeZone: "Asia/Bangkok", hour: "2-digit", minute: "2-digit", hourCycle: "h23",
      }).format(timestamp),
    };
  });
}
