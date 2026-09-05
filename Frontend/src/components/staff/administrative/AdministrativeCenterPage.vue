<template>
  <section class="page" id="page-administrative-center">
    <div class="section-title">
      <div>
        <div class="eyebrow">Administrative work center</div>
        <h2>ศูนย์รับงาน</h2>
        <p>รวมคำขอที่ธุรการต้องดำเนินการไว้ในที่เดียว โดยแยกคำขอที่ต้องพิจารณาอนุมัติออกจากคำขอรับของ</p>
      </div>
    </div>
    <div class="tabs administrative-center-tabs" id="administrativeCenterTabs">
      <button class="tab active" type="button" data-administrative-center-view="approvals">คำขอรออนุมัติ <span id="pendingApprovalTabCount">0</span></button>
      <button class="tab" type="button" data-administrative-center-view="claims">คำขอรับของ <span id="activeClaimTabCount">0</span></button>
    </div>
    <div class="administrative-center-grid single-view">
      <section class="administrative-center-box administrative-center-view active" data-administrative-center-panel="approvals">
        <div class="administrative-center-head"><div><span class="center-kicker approval">ต้องพิจารณา</span><h3>คำขอรออนุมัติ</h3><p>รวมคำขอ “ของที่รับฝาก” และ “ประกาศตามหา” ที่ยังไม่ผ่านการอนุมัติ</p></div><span class="center-count" id="pendingApprovalCount">0</span></div>
        <div class="administrative-request-list" id="pendingApprovalList"></div>
      </section>
      <section class="administrative-center-box administrative-center-view" data-administrative-center-panel="claims">
        <div class="administrative-center-head"><div><span class="center-kicker claim">ไม่ต้องอนุมัติ</span><h3>คำขอรับของ</h3><p>คำขอรับของจะเข้าสู่ระบบอัตโนมัติ ธุรการตรวจรายละเอียด นัดหมาย และยืนยันการส่งคืนได้</p></div><span class="center-count" id="activeClaimCount">0</span></div>
        <div class="administrative-request-list" id="activeClaimList"></div>
      </section>
    </div>
  </section>
</template>
