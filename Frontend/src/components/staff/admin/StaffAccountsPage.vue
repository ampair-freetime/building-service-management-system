<template>
<section class="page" id="page-staff">
          <div class="section-title">
            <div>
              <div class="eyebrow">Access administration</div>
              <h2>บัญชีและสิทธิ์เจ้าหน้าที่</h2>
              <p>สร้างบัญชี เปลี่ยน Role ปิดใช้งาน หรือลบบัญชีออกจากระบบ</p>
            </div>
            <button class="primary" id="openStaffModal">
              + สร้างบัญชี Staff
            </button>
          </div>
          <div class="metrics">
            <article class="metric">
              <span>บัญชีทั้งหมด</span><strong id="staffTotal">7</strong
              ><small>ใช้งาน 6 บัญชี</small>
            </article>
            <article class="metric">
              <span>แม่บ้าน</span><strong>3</strong
              ><small>พร้อมรับงาน 2 คน</small>
            </article>
            <article class="metric">
              <span>ช่าง</span><strong>2</strong
              ><small>กำลังปฏิบัติงาน 2 คน</small>
            </article>
            <article class="metric warn">
              <span>บัญชีถูกระงับ</span><strong>1</strong
              ><small>รอตรวจสอบ</small>
            </article>
          </div>
          <div class="table-wrap">
            <table class="data-table">
              <thead>
                <tr>
                  <th>เจ้าหน้าที่</th>
                  <th>Staff ID</th>
                  <th>Role</th>
                  <th>พื้นที่รับผิดชอบ</th>
                  <th>สถานะ</th>
                  <th>จัดการ</th>
                </tr>
              </thead>
              <tbody id="staffTable"></tbody>
            </table>
          </div>
        </section>
</template>
