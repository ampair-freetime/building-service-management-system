<template>
  <div
    class="modal job-detail-modal"
    id="jobDetailModal"
    role="dialog"
    aria-modal="true"
    aria-labelledby="jobDetailTitle"
  >
    <section class="modal-card">
      <header class="modal-head">
        <div>
          <span class="eyebrow" id="jobDetailCode">FOUND-000</span>
          <h3 id="jobDetailTitle">รายละเอียดของที่พบ</h3>
        </div>
        <button
          type="button"
          class="close"
          data-close="jobDetailModal"
          aria-label="ปิด"
        >
          <svg class="icon"><use href="#i-close" /></svg>
        </button>
      </header>

      <div class="detail-layout">
        <div>
          <div class="detail-photo">
            <svg class="icon" id="jobDetailIcon"><use href="#i-box" /></svg>
          </div>
          <div class="timeline" id="jobTimeline"></div>
        </div>

        <div>
          <div class="job-meta" id="jobDetailBadges"></div>
          <p id="jobDetailDescription"></p>
          <div class="detail-meta">
            <div>
              <small>สถานที่พบ</small>
              <strong id="jobDetailRoom">–</strong>
            </div>
            <div>
              <small>ผู้แจ้ง</small>
              <strong id="jobDetailReporter">–</strong>
            </div>
            <div>
              <small>ช่องทางติดต่อ</small>
              <strong id="jobDetailContact">–</strong>
            </div>
            <div>
              <small>ผู้รับผิดชอบ</small>
              <strong id="jobDetailAssignee">–</strong>
            </div>
          </div>
          <div class="detail-notes">
            <strong>หมายเหตุล่าสุด</strong>
            <small id="jobDetailNotes">ยังไม่มีหมายเหตุ</small>
          </div>
          <div class="quick-action-grid" id="jobQuickActions"></div>
        </div>
      </div>
    </section>
  </div>
</template>
