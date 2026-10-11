<template>
  <section class="page clerk-custody-page" id="page-lost">
    <div class="section-title custody-heading">
      <div>
        <div class="eyebrow">Lost &amp; found custody</div>
        <h2>ของหายและรับฝาก</h2>
        <p>ตรวจสอบของที่ยังรับฝากและประกาศที่ยังเปิดอยู่</p>
      </div>
      <button class="small-btn" id="staffLostRefreshButton" type="button">รีเฟรชรายการ</button>
    </div>
    <div class="custody-toolbar">
      <label class="custody-search">ค้นหารายการ
        <input id="clerkLostSearch" type="search" placeholder="ชื่อของ รหัสรายการ หรือสถานที่" />
      </label>
      <label>สถานะรายการ
        <select id="clerkLostStatus">
          <option value="all">ทุกสถานะ</option>
          <option value="stored">รับฝาก · ยังไม่ยืนยันเจ้าของ</option>
          <option value="claimed">ยืนยันเจ้าของ · รอคืนของ</option>
          <option value="announcement">ประกาศตามหา</option>
        </select>
      </label>
      <button class="small-btn" id="clerkLostReset" type="button">ล้างตัวกรอง</button>
    </div>
    <div class="custody-list-heading">
      <div class="tabs" id="lostTabs">
        <button class="tab active" data-tab="all">ทั้งหมด <span data-custody-count="all">0</span></button>
        <button class="tab" data-tab="inventory">ของที่รับฝาก <span data-custody-count="inventory">0</span></button>
        <button class="tab" data-tab="lostposts">ประกาศของหาย <span data-custody-count="lostposts">0</span></button>
      </div>
    </div>
    <div class="lost-grid" id="lostGrid"></div>
  </section>
</template>
