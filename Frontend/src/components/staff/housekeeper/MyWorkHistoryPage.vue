<template>
<section class="page" id="page-my-history">
          <div class="section-title">
            <div>
              <div class="eyebrow">Personal work record</div>
              <h2>ประวัติงานของฉัน</h2>
              <p>
                ดูงานที่เคยรับ อัปเดต ปิดงาน หรือคืนกลับเข้ากองกลาง
                พร้อมกรองช่วงวันที่ได้
              </p>
            </div>
          </div>
          <div class="history-summary" id="myHistorySummary"></div>
          <div class="tabs" id="myHistoryTabs" role="tablist" aria-label="ประเภทประวัติ">
            <button type="button" class="tab active" role="tab" aria-selected="true" data-history-tab="work">ประวัติงาน</button>
            <button type="button" class="tab" role="tab" aria-selected="false" data-history-tab="returns">คืนเข้ากองกลาง</button>
          </div>
          <div class="history-filter-panel">
            <label>ตั้งแต่วันที่<input
              class="field-compact"
              id="myHistoryFrom"
              type="date"
              aria-label="วันที่เริ่มต้น"
            /></label>
            <label>ถึงวันที่<input
              class="field-compact"
              id="myHistoryTo"
              type="date"
              aria-label="วันที่สิ้นสุด"
            /></label>
            <select
              class="field-compact"
              id="myHistoryType"
              aria-label="กรองประเภทกิจกรรม"
            >
              <option value="all">ทุกกิจกรรม</option>
            </select>
            <input
              class="field-compact search"
              id="myHistorySearch"
              placeholder="ค้นหาเลขงาน ชื่องาน หรือรายละเอียด"
            />
            <button class="secondary" id="resetMyHistoryFilters" type="button">
              ล้างตัวกรอง
            </button>
          </div>
          <div class="work-history-list" id="myHistoryList"></div>
        </section>
</template>
