<template>
  <section class="page active" id="page-dashboard">
    <div class="section-title">
      <div>
        <div class="eyebrow">Clerk approvals</div>
        <h2>ภาพรวมงานอนุมัติ</h2>
        <p>ติดตามรายการที่ต้องตรวจสอบและเปิดรายละเอียดเพื่อดำเนินการต่อ</p>
      </div>
    </div>
    <div class="metrics" id="clerkApprovalMetrics" aria-live="polite"></div>
    <div class="grid-2 clerk-approvals-overview">
      <section class="panel">
        <div class="panel-head">
          <div>
            <h3>รายการรอพิจารณา</h3>
            <p>ของที่พบและประกาศของหายที่ยังรอผลอนุมัติ</p>
          </div>
          <button class="text-btn" type="button" data-clerk-overview-view="approvals">ดูทั้งหมด →</button>
        </div>
        <div class="panel-body">
          <div class="clerk-approval-preview" id="clerkApprovalPreview" aria-live="polite"></div>
        </div>
      </section>
      <section class="panel">
        <div class="panel-head">
          <div>
            <h3>ไปยังงานที่ต้องดำเนินการ</h3>
            <p>เปิดรายการตามประเภทเพื่อพิจารณาต่อ</p>
          </div>
        </div>
        <div class="panel-body">
          <div class="clerk-approval-shortcuts" id="clerkApprovalShortcuts"></div>
        </div>
      </section>
    </div>
  </section>
</template>
