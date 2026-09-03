<template>
  <section class="page" id="page-clerk-center">
    <div class="section-title">
      <div>
        <div class="eyebrow">Administrative work center</div>
        <h2>ศูนย์รับงาน</h2>
        <p>รวมคำขอที่ธุรการต้องดำเนินการไว้ในที่เดียว โดยแยกคำขอที่ต้องพิจารณาอนุมัติออกจากคำขอรับของ</p>
      </div>
    </div>
    <div class="tabs clerk-center-tabs" id="clerkCenterTabs">
      <button class="tab active" type="button" data-clerk-center-view="approvals">คำขอรออนุมัติ <span id="pendingApprovalTabCount">0</span></button>
      <button class="tab" type="button" data-clerk-center-view="claims">คำขอรับของ <span id="activeClaimTabCount">0</span></button>
    </div>
    <div class="clerk-center-grid single-view">
      <section class="clerk-center-box clerk-center-view active" data-clerk-center-panel="approvals">
        <div class="clerk-center-head"><div><span class="center-kicker approval">ต้องพิจารณา</span><h3>คำขอรออนุมัติ</h3><p>รวมคำขอ “ของที่รับฝาก” และ “ประกาศตามหา” ที่ยังไม่ผ่านการอนุมัติ</p></div><span class="center-count" id="pendingApprovalCount">0</span></div>
        <div class="clerk-request-list" id="pendingApprovalList"></div>
      </section>
      <section class="clerk-center-box clerk-center-view" data-clerk-center-panel="claims">
        <div class="clerk-center-head"><div><span class="center-kicker claim">ไม่ต้องอนุมัติ</span><h3>คำขอรับของ</h3><p>คำขอรับของจะเข้าสู่ระบบอัตโนมัติ ธุรการตรวจรายละเอียด นัดหมาย และยืนยันการส่งคืนได้</p></div><span class="center-count" id="activeClaimCount">0</span></div>
        <div class="clerk-request-list" id="activeClaimList"></div>
      </section>
    </div>
  </section>
</template>
