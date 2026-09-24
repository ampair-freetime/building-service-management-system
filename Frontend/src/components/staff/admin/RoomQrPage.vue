<template>
  <section class="page" id="page-qr">
    <div class="section-title">
      <div>
        <div class="eyebrow">Location QR system</div>
        <h2>QR Code สถานที่</h2>
        <p>เพิ่มสถานที่และสร้าง QR Code สำหรับเปิดหน้าบริการของสถานที่นั้น</p>
      </div>
      <button class="primary" id="openQrModal" type="button">
        + เพิ่มสถานที่ใหม่
      </button>
    </div>

    <div class="qr-location-filters">
      <select class="field-compact" id="qrFloorFilter" aria-label="กรองตามชั้น">
        <option value="all">ทุกชั้น</option>
      </select>
      <input
        class="field-compact search"
        id="qrLocationSearch"
        type="search"
        placeholder="ค้นหาชื่อสถานที่หรือชั้น"
        aria-label="ค้นหาสถานที่"
      />
      <button class="secondary" id="resetQrLocationFilters" type="button">
        ล้างตัวกรอง
      </button>
    </div>

    <section class="qr-location-panel">
      <header class="qr-location-head">
        <div>
          <h3>สถานที่ทั้งหมด</h3>
          <p>เลือกดูรายละเอียดของแต่ละสถานที่เพื่อเปิด QR Code</p>
        </div>
        <span class="qr-location-count" id="qrLocationCount">0</span>
      </header>
      <div class="room-list qr-location-list" id="roomList"></div>
    </section>
  </section>
</template>
