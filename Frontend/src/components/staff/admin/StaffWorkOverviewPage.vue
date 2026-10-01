<template>
<section class="page" id="page-staff-overview">
          <div class="section-title">
            <div>
              <div class="eyebrow">Staff work overview</div>
              <h2>ภาพรวมภาระงานของเจ้าหน้าที่</h2>
              <p>
                ดูจำนวนงานที่กำลังรับผิดชอบ งานที่ปิดแล้ว และงานที่คืนเข้ากองกลาง
                ของทีมแม่บ้านและช่าง
              </p>
            </div>
          </div>
          <div class="history-summary" id="staffOverviewSummary" aria-live="polite"></div>
          <div class="history-filter-panel">
            <label class="overview-work-type-filter" for="overviewRoleFilter">
              <select class="field-compact" id="overviewRoleFilter">
                <option value="all">ทุกประเภทงาน</option>
                <option value="แม่บ้าน">งานทำความสะอาด</option>
                <option value="ช่าง">งานซ่อม</option>
              </select>
            </label>
            <input
              class="field-compact search"
              id="overviewSearch"
              placeholder="ค้นหาชื่อหรืออีเมล Staff"
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
              <p class="overview-staff-email" id="overviewDetailEmail"></p>
              <div class="staff-overview-card-stats overview-person-stats" id="overviewPersonStats"></div>
              <h4 class="overview-work-heading">งานที่กำลังรับผิดชอบ <span class="badge neutral" id="overviewDetailCount">0 รายการ</span></h4>
              <div class="overview-detail-list" id="staffOverviewDetail" aria-live="polite"></div>
            </section>
          </div>
        </Teleport>
        <Teleport to="body">
          <div class="modal" id="overviewWorkItemsModal" role="dialog" aria-modal="true" aria-labelledby="overviewWorkItemsTitle">
            <section class="modal-card staff-overview-modal-card">
              <header class="modal-head">
                <h3 id="overviewWorkItemsTitle">งานที่กำลังรับผิดชอบทั้งหมด</h3>
                <button type="button" class="close" data-close="overviewWorkItemsModal" aria-label="ปิดรายการงาน">
                  <svg class="icon"><use href="#i-close" /></svg>
                </button>
              </header>
              <span class="badge neutral" id="overviewWorkItemsCount">กำลังโหลด…</span>
              <div class="overview-detail-list" id="overviewWorkItemsList" aria-live="polite"></div>
            </section>
          </div>
        </Teleport>
</template>
