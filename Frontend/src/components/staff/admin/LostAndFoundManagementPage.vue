<template>
<section class="page" id="page-lost">
          <div class="section-title">
            <div>
              <div class="eyebrow">Lost &amp; found custody</div>
              <h2>ของหาย จุดรับฝาก และคำขอรับคืน</h2>
              <p>ตรวจสอบรายการและบันทึกเหตุผลทุกการตัดสินใจ</p>
            </div>
            <button class="primary" id="addFoundBtn" type="button">
              + รับฝากของใหม่
            </button>
          </div>
          <div class="tabs" id="lostTabs">
            <button class="tab active" data-tab="inventory">ของที่รับฝาก</button
            ><button class="tab" data-tab="lostposts">ประกาศตามหา</button
            ><button class="tab" data-tab="claims">คำขอรับของ</button>
          </div>
          <div class="lost-grid" id="lostGrid"></div>
        </section>
</template>
