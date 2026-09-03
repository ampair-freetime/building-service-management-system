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
          <div class="table-wrap">
            <table class="data-table">
              <thead>
                <tr>
                  <th>เจ้าหน้าที่</th>
                  <th>Role</th>
                  <th>กำลังรับผิดชอบ</th>
                  <th>ปิดแล้ว</th>
                  <th>คืนเข้ากองกลาง</th>
                  <th>กิจกรรมล่าสุด</th>
                  <th>รายละเอียด</th>
                </tr>
              </thead>
              <tbody id="staffOverviewTable"></tbody>
            </table>
          </div>
          <section class="panel overview-detail-panel">
            <div class="panel-body">
              <div class="overview-detail-head">
                <h3 id="overviewDetailTitle">
                  เลือก Staff เพื่อดูรายละเอียดงาน
                </h3>
                <span class="badge neutral" id="overviewDetailCount"
                  >0 รายการ</span
                >
              </div>
              <div class="overview-detail-list" id="staffOverviewDetail">
                <div class="empty">กด “ดูรายละเอียด” จากตารางด้านบน</div>
              </div>
            </div>
          </section>
        </section>
</template>
