<template>
<section class="page" id="page-history">
          <div class="section-title">
            <div>
              <div class="eyebrow">Audit &amp; recovery center</div>
              <h2>ประวัติทั้งหมดและรายการที่ลบแล้ว</h2>
              <p>ตรวจสอบกิจกรรมและกู้คืนรายการที่ถูกลบแบบ Soft Delete</p>
            </div>
          </div>
          <div class="history-summary" id="historySummary"></div>
          <div class="board-tabs" id="historyTabs">
            <button class="board-tab active" data-history-view="activity">
              กิจกรรมทั้งหมด
            </button>
            <button class="board-tab" data-history-view="deleted">
              รายการที่ลบแล้ว
            </button>
          </div>
          <div class="history-controls">
            <input
              class="field-compact search"
              id="historySearch"
              placeholder="ค้นหารหัส รายการ ผู้ดำเนินการ หรือรายละเอียด"
            />
            <select class="field-compact" id="historySourceFilter">
              <option value="all">ทุกส่วนของระบบ</option>
              <option value="jobs">งานแม่บ้านและช่าง</option>
              <option value="lost">ของหาย–ของได้คืน</option>
              <option value="staff">บัญชี Staff</option>
              <option value="qr">QR และห้อง</option>
            </select>
            <select class="field-compact" id="historyActionFilter">
              <option value="all">ทุกการดำเนินการ</option>
              <option value="อนุมัติ">อนุมัติ</option>
              <option value="ไม่อนุมัติ">ไม่อนุมัติ</option>
              <option value="อัปเดต">อัปเดต</option>
              <option value="ลบ">ลบ</option>
              <option value="กู้คืน">กู้คืน</option>
            </select>
          </div>
          <div class="table-wrap">
            <table class="data-table history-table">
              <thead id="historyHead"></thead>
              <tbody id="historyTable"></tbody>
            </table>
          </div>
        </section>
</template>
