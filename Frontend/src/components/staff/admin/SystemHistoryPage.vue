<script setup>
import ClerkApprovalsOverviewPage from "./ClerkApprovalsOverviewPage.vue";
</script>

<template>
  <section class="page" id="page-history">
    <div class="section-title">
      <div>
        <div class="eyebrow">Lost &amp; found overview</div>
        <h2>ของหายและรับฝาก</h2>
        <p>ติดตามผลการอนุมัติและดูรายการของหาย ของที่รับฝาก และคำขอรับของ</p>
      </div>
    </div>

    <ClerkApprovalsOverviewPage />

    <section class="admin-history-items" id="historyLostSection" aria-labelledby="adminHistoryItemsTitle">
      <div class="admin-history-items-heading">
        <h3 id="adminHistoryItemsTitle">รายการของหายและรับฝาก</h3>
        <p>ค้นหาและเปิดดูโพสต์ที่ธุรการอนุมัติแล้ว รวมถึงคำขอรับของ</p>
      </div>
      <form class="history-controls admin-history-controls" id="historySearchForm" role="search">
        <input class="field-compact search" id="historySearch" type="search" placeholder="ค้นหารหัส ชื่อรายการ สถานที่ หรือสถานะ" aria-label="ค้นหารายการของหายและรับฝาก" />
        <button class="primary" type="submit">แสดงผล</button>
      </form>
      <div class="tabs admin-lost-tabs" id="lostTabs" role="tablist" aria-label="กรองรายการของหายและรับฝาก">
        <button class="tab" type="button" role="tab" aria-selected="false" data-tab="inventory">ของที่รับฝาก <span class="tab-count" data-lost-count="inventory">0</span></button>
        <button class="tab" type="button" role="tab" aria-selected="false" data-tab="lostposts">ประกาศตามหา <span class="tab-count" data-lost-count="lostposts">0</span></button>
        <button class="tab" type="button" role="tab" aria-selected="false" data-tab="claims">คำขอรับของ <span class="tab-count" data-lost-count="claims">0</span></button>
        <button class="tab active status-tab approved-tab" type="button" role="tab" aria-selected="true" data-tab="approved">อนุมัติแล้ว <span class="tab-count" data-lost-count="approved">0</span></button>
        <button class="tab status-tab rejected-tab" type="button" role="tab" aria-selected="false" data-tab="rejected">ไม่อนุมัติ <span class="tab-count" data-lost-count="rejected">0</span></button>
      </div>
      <div class="lost-grid" id="lostGrid"></div>
    </section>
  </section>
</template>
