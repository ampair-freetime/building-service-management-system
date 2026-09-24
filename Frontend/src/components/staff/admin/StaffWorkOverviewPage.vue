<template>
<section class="page" id="page-staff-overview">
          <div class="section-title">
            <div>
              <div class="eyebrow">Staff work overview</div>
              <h2>ภาพรวมภาระงานของเจ้าหน้าที่</h2>
              <p>
                ดูว่า Staff แต่ละคนกำลังรับผิดชอบงานใด ปิดงานไปแล้วกี่งาน
                และคืนงานเข้ากองกลางกี่ครั้ง
              </p>
            </div>
          </div>
          <div class="history-summary" id="staffOverviewSummary"></div>
          <div class="history-filter-panel">
            <select class="field-compact" id="overviewRoleFilter">
              <option value="all">ทุก Role</option>
              <option>แม่บ้าน</option>
              <option>ช่าง</option>
              <option>ธุรการ</option>
            </select>
            <input
              class="field-compact"
              id="overviewFrom"
              type="date"
              aria-label="วันที่เริ่มต้นของภาพรวม"
            />
            <input
              class="field-compact"
              id="overviewTo"
              type="date"
              aria-label="วันที่สิ้นสุดของภาพรวม"
            />
            <input
              class="field-compact search"
              id="overviewSearch"
              placeholder="ค้นหาชื่อ Staff หรือ Staff ID"
            />
            <button class="secondary" id="resetOverviewFilters" type="button">
              ล้างตัวกรอง
            </button>
          </div>
          <div
            class="staff-overview-grid"
            id="staffOverviewTable"
            aria-live="polite"
          ></div>
        </section>
        <Teleport to="body">
          <div
            class="modal"
            id="staffOverviewModal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="overviewDetailTitle"
          >
            <section class="modal-card staff-overview-modal-card">
              <header class="modal-head">
                <h3 id="overviewDetailTitle">รายละเอียดงานของ Staff</h3>
                <button
                  type="button"
                  class="close"
                  data-close="staffOverviewModal"
                  aria-label="ปิดรายละเอียดงาน"
                >
                  <svg class="icon"><use href="#i-close" /></svg>
                </button>
              </header>
              <span class="badge neutral" id="overviewDetailCount">0 รายการ</span>
              <div class="overview-detail-list" id="staffOverviewDetail"></div>
            </section>
          </div>
        </Teleport>
</template>
