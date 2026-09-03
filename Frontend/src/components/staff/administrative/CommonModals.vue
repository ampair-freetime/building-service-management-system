<template>
<div
      class="modal"
      id="confirmModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirmModalTitle"
    >
      <section class="modal-card confirmation">
        <header class="modal-head">
          <span></span
          ><button
            type="button"
            class="close"
            data-close="confirmModal"
            aria-label="ปิด"
          >
            <svg class="icon"><use href="#i-close" /></svg>
          </button>
        </header>
        <div class="confirm-icon">
          <svg class="icon"><use href="#i-check" /></svg>
        </div>
        <h3 id="confirmModalTitle">ยืนยันการดำเนินการ</h3>
        <p id="confirmModalText">กรุณาตรวจสอบข้อมูลก่อนยืนยัน</p>
        <div class="modal-actions">
          <button type="button" class="secondary" data-close="confirmModal">
            ยกเลิก</button
          ><button type="button" class="danger" id="confirmActionButton">
            ยืนยัน
          </button>
        </div>
      </section>
    </div>

<div
      class="modal"
      id="profileModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="profileModalTitle"
    >
      <section class="modal-card">
        <header class="modal-head">
          <h3 id="profileModalTitle">โปรไฟล์เจ้าหน้าที่</h3>
          <button
            type="button"
            class="close"
            data-close="profileModal"
            aria-label="ปิด"
          >
            <svg class="icon"><use href="#i-close" /></svg>
          </button>
        </header>
        <div class="profile-grid">
          <div class="profile-avatar-large" id="profileAvatar">AD</div>
          <div class="profile-data">
            <div>
              <small>ชื่อ</small
              ><strong id="profileName">พิมพ์ชนก วัฒนา</strong>
            </div>
            <div>
              <small>อีเมล</small
              ><strong id="profileEmail">staff@building.local</strong>
            </div>
            <div>
              <small>รหัสเจ้าหน้าที่</small
              ><strong id="profileStaffId">ADM-001</strong>
            </div>
            <div>
              <small>Role</small><strong id="profileRole">แอดมิน</strong>
            </div>
            <div>
              <small>แผนก</small
              ><strong id="profileDepartment">บริหารระบบ</strong>
            </div>
            <div>
              <small>สถานะ</small
              ><strong style="color: #258745">พร้อมปฏิบัติงาน</strong>
            </div>
          </div>
        </div>
        <div class="modal-actions">
          <button type="button" class="secondary" id="notificationSettings">
            ตั้งค่าการแจ้งเตือน</button
          ><button type="button" class="secondary" id="changePassword">
            เปลี่ยนรหัสผ่าน</button
          ><button type="button" class="danger" id="profileLogout">
            ออกจากระบบ
          </button>
        </div>
      </section>
    </div>

<div
      class="modal"
      id="quickActionModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="quickActionTitle"
    >
      <section class="modal-card">
        <header class="modal-head">
          <h3 id="quickActionTitle">ดำเนินการด่วน</h3>
          <button
            type="button"
            class="close"
            data-close="quickActionModal"
            aria-label="ปิด"
          >
            <svg class="icon"><use href="#i-close" /></svg>
          </button>
        </header>
        <div class="service-choice-grid" id="mobileQuickActions"></div>
      </section>
    </div>

<div
      class="modal"
      id="successModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="successModalTitle"
    >
      <section class="modal-card confirmation">
        <header class="modal-head">
          <span></span
          ><button
            type="button"
            class="close"
            data-close="successModal"
            aria-label="ปิด"
          >
            <svg class="icon"><use href="#i-close" /></svg>
          </button>
        </header>
        <div class="success-check">
          <svg class="icon"><use href="#i-check" /></svg>
        </div>
        <h3 id="successModalTitle">บันทึกสำเร็จ</h3>
        <p id="successModalText">ระบบบันทึกข้อมูลเรียบร้อยแล้ว</p>
        <button type="button" class="primary" data-close="successModal">
          ตกลง
        </button>
      </section>
    </div>
</template>
