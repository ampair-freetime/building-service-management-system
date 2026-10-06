<template>
<section class="page" id="page-staff">
          <div class="section-title">
            <div>
              <div class="eyebrow">Access administration</div>
              <h2>บัญชีและสิทธิ์เจ้าหน้าที่</h2>
              <p>สร้างและจัดการบัญชีเจ้าหน้าที่</p>
            </div>
            <button class="primary" id="openStaffModal">
              + สร้างบัญชี Staff
            </button>
          </div>
          <div class="metrics">
            <article class="metric">
              <span>บัญชีทั้งหมด</span><strong id="staffTotal">0</strong
              ><small id="staffActiveTotal">ใช้งาน 0 บัญชี</small>
            </article>
            <article class="metric">
              <span>แม่บ้าน</span><strong id="housekeeperTotal">0</strong
              ><small>บัญชีแม่บ้าน</small>
            </article>
            <article class="metric">
              <span>ช่าง</span><strong id="technicianTotal">0</strong
              ><small>บัญชีช่าง</small>
            </article>
            <article class="metric">
              <span>บัญชีธุรการ</span><strong id="clerkTotal">0</strong
              ><small>บัญชีเจ้าหน้าที่ธุรการ</small>
            </article>
            <article class="metric">
              <span>บัญชีแอดมิน</span><strong id="adminTotal">0</strong
              ><small>บัญชีผู้ดูแลระบบ</small>
            </article>
          </div>
          <div class="staff-account-filters">
            <select class="field-compact" id="staffRoleFilter" aria-label="กรองตาม Role">
              <option value="all">ทุก Role</option>
              <option value="admin">แอดมิน</option>
              <option value="clerk">ธุรการ</option>
              <option value="housekeeper">แม่บ้าน</option>
              <option value="technician">ช่าง</option>
            </select>
            <input
              class="field-compact search"
              id="staffAccountSearch"
              type="search"
              placeholder="ค้นหาชื่อหรือ Role"
              aria-label="ค้นหาบัญชีเจ้าหน้าที่"
            />
            <button class="secondary" id="resetStaffAccountFilters" type="button">
              ล้างตัวกรอง
            </button>
          </div>
          <div class="staff-account-grid" id="staffTable" aria-live="polite"></div>
        </section>
  <div class="modal" id="staffAccountDetailModal" role="dialog" aria-modal="true" aria-labelledby="staffAccountDetailTitle">
    <section class="modal-card staff-overview-modal-card">
      <header class="modal-head">
        <h3 id="staffAccountDetailTitle">รายละเอียดบัญชีเจ้าหน้าที่</h3>
        <button type="button" class="close" data-close="staffAccountDetailModal" aria-label="ปิดรายละเอียด"><svg class="icon"><use href="#i-close" /></svg></button>
      </header>
      <div class="detail-meta" id="staffAccountDetailInfo"></div>
      <div id="staffAccountDetailWork" aria-live="polite"></div>
    </section>
  </div>
</template>
