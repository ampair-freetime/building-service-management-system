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
      <form id="staffForm">
        <div class="form-row">
          <div class="field">
            <label for="newName">ชื่อ-นามสกุล</label
            ><input id="newName" required />
          </div>
        </div>
        <div class="form-row">
          <div class="field">
            <label for="newEmail">อีเมล</label
            ><input id="newEmail" type="email" autocomplete="email" required />
          </div>
        </div>
        <div class="form-row">
          <div class="field">
            <label for="newRole">Role</label
            ><select id="newRole" required>
              <option value="housekeeper">แม่บ้าน</option>
              <option value="technician">ช่าง</option>
              <option value="clerk">ธุรการ</option>
              <option value="admin">แอดมิน</option>
            </select>
          </div>
        </div>
        <p class="form-hint">
          ระบบจะสร้างรหัสผ่านชั่วคราวและส่งไปยังอีเมลของ Staff
        </p>
        <button class="primary" id="createStaffButton" style="width: 100%">
          สร้างบัญชี
        </button>
      </form>
    </div>
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
          <label for="editStaffName">ชื่อ-นามสกุล</label
          ><input id="editStaffName" required />
        </div>
        <div class="field">
          <label for="editStaffEmail">อีเมล</label
          ><input id="editStaffEmail" type="email" required />
        </div>
        <div class="form-row">
          <div class="field">
            <label for="editStaffRole">Role</label
            ><select id="editStaffRole">
              <option>แม่บ้าน</option>
              <option>ช่าง</option>
              <option>ธุรการ</option>
              <option>แอดมิน</option>
            </select>
          </div>
          <div class="field">
            <label for="editStaffZone">พื้นที่รับผิดชอบ</label
            ><input id="editStaffZone" />
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
          <span class="eyebrow">ชื่อสถานที่</span>
          <h3 id="qrRoomName">-</h3>
          <p class="qr-detail-floor" id="qrRoomFloor"></p>
        </div>
        <button class="primary" id="downloadQr" type="button">
          ดาวน์โหลด QR Code
        </button>
      </div>
    </section>
  </div>
</template>
