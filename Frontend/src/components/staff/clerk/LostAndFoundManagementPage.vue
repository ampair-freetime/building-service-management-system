<template>
<section class="page" id="page-lost">
          <div class="section-title">
            <div>
              <div class="eyebrow">Lost &amp; found custody</div>
              <h2>ของหายและรับฝาก</h2>
              <p>จัดการของที่รับฝากและประกาศของหาย</p>
            </div>

          </div>
          <button class="small-btn" id="staffLostRefreshButton" type="button">รีเฟรชประกาศ</button>
          <div class="tabs" id="lostTabs">
            <button class="tab active" data-tab="all">ทั้งหมด</button>
            <button class="tab" data-tab="inventory">ของที่รับฝาก</button
            ><button class="tab" data-tab="lostposts">ประกาศของหาย</button>
          </div>
          <div class="lost-grid" id="lostGrid"></div>
        </section>
</template>
