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
        <button class="primary" id="createStaffButton" style="width: 100%">
          สร้างบัญชี
        </button>
      </form>
    </div>
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
