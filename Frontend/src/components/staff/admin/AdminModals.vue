<template>
  <div
    class="modal"
    id="staffModal"
    role="dialog"
    aria-modal="true"
    aria-labelledby="staffModalTitle"
  >
    <div class="modal-card">
      <div class="modal-head">
        <h3 id="staffModalTitle">สร้างบัญชี Staff</h3>
        <button class="close" data-close="staffModal" aria-label="ปิด">
          ×
        </button>
      </div>
      <form id="staffForm" novalidate>
        <div class="form-row staff-name-row">
          <div class="field">
            <label for="newFirstName">ชื่อ</label>
            <input
              id="newFirstName"
              required
              minlength="2"
              maxlength="149"
              autocomplete="given-name"
              aria-describedby="newFirstNameError"
            />
            <p
              id="newFirstNameError"
              class="field-error"
              aria-live="polite"
            ></p>
          </div>
          <div class="field">
            <label for="newLastName">นามสกุล</label>
            <input
              id="newLastName"
              required
              minlength="2"
              maxlength="149"
              autocomplete="family-name"
              aria-describedby="newLastNameError"
            />
            <p
              id="newLastNameError"
              class="field-error"
              aria-live="polite"
            ></p>
          </div>
        </div>
        <div class="field">
          <label for="newEmail">อีเมล</label>
          <input
            id="newEmail"
            type="email"
            maxlength="254"
            autocomplete="email"
            aria-describedby="newEmailError"
            required
          />
          <p id="newEmailError" class="field-error" aria-live="polite"></p>
        </div>
        <div class="field">
          <label for="newRole">Role</label
          ><select
            class="field-compact"
            id="newRole"
            aria-label="เลือก Role"
            aria-describedby="newRoleError"
            required
          >
            <option value="" disabled selected>เลือก Role</option>
            <option value="housekeeper">แม่บ้าน</option>
            <option value="technician">ช่าง</option>
            <option value="clerk">ธุรการ</option>
            <option value="admin">แอดมิน</option>
          </select>
          <p id="newRoleError" class="field-error" aria-live="polite"></p>
        </div>
        <p class="form-hint">
          ระบบจะส่งลิงก์ไปยังอีเมลของ Staff เพื่อให้ตั้งรหัสผ่านด้วยตนเอง
        </p>
        <button class="primary" id="createStaffButton" style="width: 100%">
          สร้างบัญชี
        </button>
      </form>
    </div>
  </div>

  <div
    class="modal"
    id="staffCredentialsModal"
    role="dialog"
    aria-modal="true"
    aria-labelledby="staffCredentialsTitle"
  >
    <section class="modal-card staff-credentials-modal-card">
      <header class="modal-head">
        <h3 id="staffCredentialsTitle">สร้างบัญชี Staff สำเร็จ</h3>
        <button
          type="button"
          class="close"
          data-close="staffCredentialsModal"
          aria-label="ปิด"
        >
          <svg class="icon"><use href="#i-close" /></svg>
        </button>
      </header>
      <div
        class="success-check staff-credentials-success-check"
        aria-hidden="true"
      >
        <svg class="icon"><use href="#i-check" /></svg>
      </div>
      <p class="generated-password-notice">
        รหัสผ่านนี้จะแสดงเพียงครั้งเดียว กรุณาคัดลอกและส่งให้ Staff อย่างปลอดภัย
      </p>
      <div class="generated-password-box">
        <code id="generatedStaffPassword" aria-label="รหัสผ่านชั่วคราว"></code>
        <button
          type="button"
          class="secondary generated-password-copy"
          id="copyGeneratedPassword"
          aria-label="คัดลอกรหัสผ่าน"
          title="คัดลอกรหัสผ่าน"
        >
          <svg class="icon" aria-hidden="true"><use href="#i-copy" /></svg>
        </button>
      </div>
      <p
        class="generated-password-email-status"
        id="generatedPasswordEmailStatus"
      ></p>
      <button
        type="button"
        class="primary generated-password-done"
        data-close="staffCredentialsModal"
      >
        เสร็จสิ้น
      </button>
    </section>
  </div>

  <div
    class="modal"
    id="editStaffModal"
    role="dialog"
    aria-modal="true"
    aria-labelledby="editStaffTitle"
  >
    <section class="modal-card">
      <header class="modal-head">
        <h3 id="editStaffTitle">แก้ไข Staff</h3>
        <button
          type="button"
          class="close"
          data-close="editStaffModal"
          aria-label="ปิด"
        >
          <svg class="icon"><use href="#i-close" /></svg>
        </button>
      </header>
      <form id="editStaffForm">
        <input type="hidden" id="editStaffIndex" />
        <div class="field">
          <label for="editStaffName">ชื่อ-นามสกุล</label>
          <!-- ตรวจว่าชื่อมี 2-150 ตัวอักษร -->
          <input
            id="editStaffName"
            required
            minlength="2"
            maxlength="150"
            autocomplete="name"
          />
        </div>

        <div class="field">
          <label for="editStaffEmail">อีเมล</label>
          <!-- ตรวจรูปแบบอีเมลด้วย Browser -->
          <input
            id="editStaffEmail"
            type="email"
            required
            maxlength="254"
            autocomplete="email"
          />
        </div>

        <div class="form-row">
          <div class="field">
            <label for="editStaffRole">บทบาท</label>
            <!-- บังคับให้เลือก Role -->
            <select id="editStaffRole" required>
              <option value="" disabled>เลือกบทบาทเจ้าหน้าที่</option>
              <option value="แม่บ้าน">แม่บ้าน</option>
              <option value="ช่าง">ช่าง</option>
              <option value="ธุรการ">ธุรการ</option>
              <option value="แอดมิน">แอดมิน</option>
            </select>
          </div>

          <div class="field">
            <label for="editStaffZone">พื้นที่รับผิดชอบ</label>
            <input id="editStaffZone" maxlength="100" />
          </div>
        </div>
        <button type="submit" class="primary" style="width: 100%">
          บันทึกข้อมูล
        </button>
      </form>
    </section>
  </div>

  <div
    class="modal"
    id="qrFormModal"
    role="dialog"
    aria-modal="true"
    aria-labelledby="qrFormModalTitle"
  >
    <section class="modal-card">
      <header class="modal-head">
        <h3 id="qrFormModalTitle">เพิ่มสถานที่ใหม่</h3>
        <button
          type="button"
          class="close"
          data-close="qrFormModal"
          aria-label="ปิด"
        >
          <svg class="icon"><use href="#i-close" /></svg>
        </button>
      </header>
      <form id="qrForm">
        <div class="field">
          <label for="qrLocationFloor">ชั้น</label>
          <input
            id="qrLocationFloor"
            required
            maxlength="30"
            autocomplete="off"
            placeholder="เช่น 1, 2 หรือชั้นใต้ดิน"
          />
        </div>
        <div class="field">
          <label for="qrLocationName">ชื่อสถานที่</label>
          <input
            id="qrLocationName"
            required
            maxlength="100"
            autocomplete="off"
            placeholder="เช่น ห้อง CSB-307 หรือโถงชั้น 1"
          />
          <small>ระบบจะสร้าง QR Code ของสถานที่นี้ให้อัตโนมัติ</small>
        </div>
        <div class="field">
          <label for="qrServiceType">ประเภทบริการ</label>
          <select id="qrServiceType" required>
            <option value="repair">แจ้งซ่อม</option>
            <option value="clean">แจ้งทำความสะอาด</option>
          </select>
        </div>
        <button type="submit" class="primary" style="width: 100%">
          เพิ่มสถานที่และสร้าง QR
        </button>
      </form>
    </section>
  </div>

  <div
    class="modal"
    id="qrDetailModal"
    role="dialog"
    aria-modal="true"
    aria-labelledby="qrDetailTitle"
  >
    <section class="modal-card qr-detail-modal-card">
      <header class="modal-head">
        <h3 id="qrDetailTitle">รายละเอียดสถานที่</h3>
        <button
          type="button"
          class="close"
          data-close="qrDetailModal"
          aria-label="ปิด"
        >
          <svg class="icon"><use href="#i-close" /></svg>
        </button>
      </header>
      <div class="qr-detail-content">
        <div class="qr-code" id="qrCode">
          <div class="qr-fallback"></div>
        </div>
        <div>
          <h3 id="qrRoomName">-</h3>
          <p class="qr-detail-floor" id="qrRoomFloor"></p>
        </div>
        <div class="qr-detail-actions">
          <button class="primary" id="downloadQr" type="button">
            ดาวน์โหลด QR Code
          </button>
          <button class="secondary" id="printQr" type="button">
            พิมพ์ QR Code
          </button>
        </div>
      </div>
    </section>
  </div>
</template>
