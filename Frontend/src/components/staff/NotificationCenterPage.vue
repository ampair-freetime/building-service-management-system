<template>
  <section class="page notification-center-page" id="page-notifications">
    <div class="notification-center-hero">
      <div>
        <div class="eyebrow">Notification Center</div>
        <h2 id="notificationTitle">ศูนย์การแจ้งเตือน</h2>
        <p>ติดตามงานใหม่ การเปลี่ยนแปลงสถานะ และรายการที่ต้องดำเนินการ</p>
      </div>
      <button type="button" class="notification-mark-all" id="markAllRead">
        <svg class="icon" aria-hidden="true"><use href="#i-check" /></svg>
        อ่านทั้งหมดแล้ว
      </button>
    </div>

    <div class="notification-center-summary" aria-live="polite">
      <div class="notification-summary-icon" aria-hidden="true">
        <svg class="icon"><use href="#i-bell" /></svg>
      </div>
      <div>
        <strong id="notificationSummaryTitle">รายการแจ้งเตือนของคุณ</strong>
        <p id="notificationSummaryText">กำลังโหลดรายการล่าสุด</p>
      </div>
      <span class="notification-center-count" id="notificationPageCount">0</span>
    </div>

    <section class="panel notification-center-panel" aria-labelledby="notificationListTitle">
      <div class="panel-head">
        <div>
          <h3 id="notificationListTitle">รายการล่าสุด</h3>
          <p>เลือกรายการเพื่อเปิดงานหรือรายละเอียดที่เกี่ยวข้อง</p>
        </div>
      </div>
      <div class="notification-list notification-center-list" id="notificationList"></div>
    </section>
  </section>
</template>
