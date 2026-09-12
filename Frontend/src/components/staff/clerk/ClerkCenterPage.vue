<template>
  <section class="page" id="page-clerk-center">
    <div class="section-title">
      <div>
        <div class="eyebrow">Clerk work center</div>
        <h2>ศูนย์รับงาน</h2>
        <p>
          รวมคำขอที่ธุรการต้องดำเนินการไว้ในที่เดียว
          โดยแยกคำขอที่ต้องพิจารณาอนุมัติออกจากคำขอรับของ
        </p>
      </div>
    </div>
    <div class="tabs clerk-center-tabs" id="clerkCenterTabs">
      <button
        class="tab active"
        type="button"
        data-clerk-center-view="approvals"
      >
        คำขอรออนุมัติ <span id="pendingApprovalTabCount">0</span>
      </button>
      <button
        class="tab"
        type="button"
        data-clerk-center-view="lost-announcements"
      >
        ประกาศของหาย <span id="pendingLostAnnouncementTabCount">0</span>
      </button>
      <button class="tab" type="button" data-clerk-center-view="claims">
        คำขอแสดงความเป็นเจ้าของ <span id="activeClaimTabCount">0</span>
      </button>
    </div>
    <div class="clerk-center-grid single-view">
      <section
        class="clerk-center-box clerk-center-view active"
        data-clerk-center-panel="approvals"
      >
        <div class="clerk-center-head">
          <div>
            <span class="center-kicker approval">ต้องพิจารณา</span>
            <h3>คำขอรออนุมัติ</h3>
            <p>รายการ “ของที่รับฝาก” ซึ่งยังไม่ผ่านการอนุมัติ</p>
          </div>
          <span class="center-count" id="pendingApprovalCount">0</span>
        </div>
        <div class="clerk-request-list" id="pendingApprovalList"></div>
      </section>
      <section
        class="clerk-center-box clerk-center-view"
        data-clerk-center-panel="lost-announcements"
      >
        <div class="clerk-center-head">
          <div>
            <span class="center-kicker approval">รอตรวจประกาศ</span>
            <h3>ประกาศของหายรออนุมัติ</h3>
            <p>ตรวจข้อมูลก่อนอนุมัติให้ประกาศแสดงต่อผู้ใช้งานทั่วไป</p>
          </div>
          <span class="center-count" id="pendingLostAnnouncementCount">0</span>
        </div>
        <div
          class="clerk-request-list"
          id="pendingLostAnnouncementList"
        ></div>
      </section>
      <section
        class="clerk-center-box clerk-center-view"
        data-clerk-center-panel="claims"
      >
        <div class="clerk-center-head">
          <div>
            <span class="center-kicker claim">ไม่ต้องอนุมัติ</span>
            <h3>คำขอแสดงความเป็นเจ้าของ</h3>
            <p>
              ตรวจสอบผู้ยื่นคำขอ หลักฐานความเป็นเจ้าของ สถานะ และดำเนินการนัดรับ
            </p>
          </div>
          <span class="center-count" id="activeClaimCount">0</span>
        </div>
        <div class="clerk-request-list" id="activeClaimList"></div>
      </section>
    </div>
  </section>
</template>
