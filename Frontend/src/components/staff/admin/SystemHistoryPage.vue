<template>
<section class="page" id="page-history">
          <div class="section-title">
            <div>
              <div class="eyebrow">Lost &amp; found</div>
              <h2>ของหายและรับฝาก</h2>
              <p>ดูรายการตามหมวด หรือแยกตามผลการอนุมัติ</p>
            </div>
          </div>
          <div class="history-summary" id="adminLostSummary"></div>
          <div class="history-controls admin-history-controls">
            <input
              class="field-compact search"
              id="historySearch"
              placeholder="ค้นหารหัส ชื่อรายการ สถานที่ หรือสถานะ"
            />
            <button class="primary" id="addFoundBtn" type="button">
              + รับฝากของใหม่
            </button>
          </div>
          <section class="history-lost-section" id="historyLostSection">
            <div class="tabs admin-lost-tabs" id="lostTabs" role="tablist" aria-label="กรองรายการของหายและรับฝาก">
              <button class="tab active" type="button" role="tab" aria-selected="true" data-tab="inventory">ของที่รับฝาก <span class="tab-count" data-lost-count="inventory">0</span></button>
              <button class="tab" type="button" role="tab" aria-selected="false" data-tab="lostposts">ประกาศตามหา <span class="tab-count" data-lost-count="lostposts">0</span></button>
              <button class="tab" type="button" role="tab" aria-selected="false" data-tab="claims">คำขอรับของ <span class="tab-count" data-lost-count="claims">0</span></button>
              <button class="tab status-tab approved-tab" type="button" role="tab" aria-selected="false" data-tab="approved">อนุมัติแล้ว <span class="tab-count" data-lost-count="approved">0</span></button>
              <button class="tab status-tab rejected-tab" type="button" role="tab" aria-selected="false" data-tab="rejected">ไม่อนุมัติ <span class="tab-count" data-lost-count="rejected">0</span></button>
            </div>
            <div class="lost-grid" id="lostGrid"></div>
          </section>
        </section>
</template>
