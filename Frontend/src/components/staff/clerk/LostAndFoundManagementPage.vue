<template>
  <section class="page clerk-custody-page" id="page-lost">
    <div class="section-title custody-heading">
      <div>
        <div class="eyebrow">Lost &amp; found custody</div>
        <h2>ของหายและรับฝาก</h2>
      </div>
    </div>
    <form class="custody-toolbar" id="clerkLostFilters">
      <label class="custody-search">ค้นหารายการ
        <input
          class="field-compact search"
          id="clerkLostSearch"
          type="search"
          placeholder="ค้นหาชื่อของ รหัสรายการ หรือสถานที่"
        />
      </label>
      <label>สถานะรายการ
        <select id="clerkLostStatus">
          <option value="all">ทุกสถานะ</option>
          <option value="stored">รับฝาก · ยังไม่ยืนยันเจ้าของ</option>
          <option value="claimed">ยืนยันเจ้าของ · รอคืนของ</option>
          <option value="announcement">ประกาศตามหา</option>
        </select>
      </label>
      <div class="custody-toolbar-actions">
        <button class="secondary" id="clerkLostReset" type="button">ล้างตัวกรอง</button>
        <button class="primary" id="clerkLostApply" type="submit">แสดงผล</button>
      </div>
    </form>
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
