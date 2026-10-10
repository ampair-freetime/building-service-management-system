// backendId is an API UUID; id/displayCode are human-readable UI codes.
export function mapPendingFoundItem(item) {
  return {
    backendId: item.id,
    id: item.item_code,
    displayCode: item.item_code,
    title: item.item_name,
    eventDatetime: item.event_datetime,
    reporterEmail: item.reporter_email,
    custodyLocation: item.custody_location,
    category: item.item_category,
    place: item.location_detail || "ไม่ระบุสถานที่พบ",
    description: item.description || "ไม่มีรายละเอียดเพิ่มเติม",
    activityLabel: `รายงานเมื่อ ${new Date(item.created_at).toLocaleString("th-TH")}`,
    status: "รออนุมัติรับฝาก",
    reportedAt: item.created_at,
    createdAt: item.created_at,
    imageUrl: item.images?.[0]?.url || "",
    assignee: null,
  };
}

export function mapPendingLostItem(item) {
  return {
    backendId: item.id,
    id: item.item_code,
    displayCode: item.item_code,
    title: item.item_name,
    eventDatetime: item.event_datetime,
    reporterEmail: item.reporter_email,
    custodyLocation: item.custody_location,
    category: item.item_category,
    place: item.location_detail || "ไม่ระบุสถานที่คาดว่าหาย",
    description: item.description || "ไม่มีรายละเอียดเพิ่มเติม",
    activityLabel: `ส่งประกาศเมื่อ ${new Date(item.created_at).toLocaleString("th-TH")}`,
    status: "รออนุมัติเผยแพร่",
    reportedAt: item.created_at,
    createdAt: item.created_at,
    imageUrl: item.images?.[0]?.url || "",
    assignee: null,
  };
}

export function mapApprovedItem(item, tab) {
  return {
    publicListItem: true,
    backendStatus: item.status,
    backendId: item.id,
    id: item.item_code,
    displayCode: item.item_code,
    title: item.item_name,
    custodyLocation: item.custody_location,
    category: item.item_category,
    place: item.location_detail || "ไม่ระบุสถานที่",
    description: item.description || "ไม่มีรายละเอียดเพิ่มเติม",
    activityLabel: tab === "inventory" ? "รับฝากโดยธุรการ" : "เผยแพร่แล้ว",
    status: item.status === "claimed" ? "ยืนยันเจ้าของแล้ว · รอคืนของ"
      : item.status === "closed" ? "ปิดรายการแล้ว"
      : item.status === "rejected" ? "ไม่อนุมัติ"
      : tab === "inventory" ? "อนุมัติรับฝาก" : "อนุมัติเผยแพร่",
    eventDatetime: item.event_datetime,
    imageUrl: item.images?.[0]?.url || "",
    reporterEmail: item.reporter_email || null,
    reviewerId: item.reviewed_by || null,
    reviewerName: item.reviewer_name || item.reviewer?.full_name || null,
    assignee: null,
  };
}

export function mapOwnershipClaim(claim, ownershipStatusLabel, foundItemReturnStatus) {
  return {
    backendId: claim.id,
    foundItemBackendId: claim.found_item_id,
    id: claim.claim_code,
    displayCode: claim.claim_code,
    itemCode: claim.item_code,
    title: `คำขอรับ${claim.item_name || "ของคืน"}`,
    place: claim.location_detail || "ไม่ระบุสถานที่พบ",
    activityLabel: ownershipStatusLabel(claim.status),
    backendStatus: claim.status,
    status: ownershipStatusLabel(claim.status),
    returnStatusCode: claim.return_status,
    returnStatus: foundItemReturnStatus(
      claim.return_status,
      claim.status,
    ),
    requester: claim.claimant_name,
    contact: claim.claimant_email,
    requestDate: new Date(
      claim.created_at,
    ).toLocaleString("th-TH"),
    reportedAt: claim.created_at,
    createdAt: claim.created_at,
    pickupEndTime: claim.pickup_end_datetime ? new Intl.DateTimeFormat("en-GB", {timeZone: "Asia/Bangkok", hour: "2-digit", minute: "2-digit"}).format(new Date(claim.pickup_end_datetime)) : "",
    evidence: claim.proof_detail,
    generalDescription: claim.description,
    secret: claim.private_verification_detail,
    custodyLocation: claim.custody_location,
    pickupDate: claim.pickup_date || (claim.pickup_datetime ? new Intl.DateTimeFormat("en-CA", {timeZone: "Asia/Bangkok", year: "numeric", month: "2-digit", day: "2-digit"}).format(new Date(claim.pickup_datetime)) : ""),
    pickupTime: claim.pickup_time || (claim.pickup_datetime ? new Intl.DateTimeFormat("en-GB", {timeZone: "Asia/Bangkok", hour: "2-digit", minute: "2-digit"}).format(new Date(claim.pickup_datetime)) : ""),
    pickupLocation:
      claim.pickup_location || claim.appointment?.pickup_location || "",
    pickupNote: claim.pickup_note || claim.appointment?.note || "",
    appointment: claim.pickup_date
      ? `${claim.pickup_date} เวลา ${claim.pickup_time || "–"}`
      : "ยังไม่มีนัดหมาย",
    assignee: null,
  };
}
