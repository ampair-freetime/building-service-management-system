<template>
<section class="page" id="page-announcements">
          <div class="section-title">
            <div>
              <div class="eyebrow">Announcement management</div>
              <h2>ประกาศอาคาร</h2>
              <p>สร้างและจัดการประกาศที่แสดงกับผู้ใช้งาน</p>
            </div>
            <button class="primary" id="openAnnouncementModal" type="button">
              สร้างประกาศ
            </button>
          </div>
          <div class="metrics">
            <article class="metric">
              <span>เผยแพร่แล้ว</span><strong id="publishedCount">2</strong
              ><small>กำลังแสดงกับผู้ใช้</small>
            </article>
            <article class="metric">
              <span>ฉบับร่าง</span><strong id="draftCount">1</strong
              ><small>รอตรวจสอบ</small>
            </article>
            <article class="metric">
              <span>ปักหมุด</span><strong id="pinnedCount">1</strong
              ><small>แสดงเป็นลำดับแรก</small>
            </article>
            <article class="metric">
              <span>สิ้นสุดเดือนนี้</span><strong>1</strong
              ><small>ตรวจวันหมดอายุ</small>
            </article>
          </div>
          <div class="announcement-list" id="announcementList"></div>
        </section>
</template>
