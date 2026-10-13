<template>
<section class="page" id="page-my-history">
          <div class="section-title">
            <div>
              <div class="eyebrow">Personal work record</div>
              <h2>ประวัติงานของฉัน</h2>
            </div>
          </div>
          <div class="history-summary" id="myHistorySummary"></div>
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
            <button class="primary" id="applyMyHistoryFilters" type="button">
              แสดงผล
            </button>
          </div>
          <div class="work-history-list" id="myHistoryList"></div>
        </section>
</template>
