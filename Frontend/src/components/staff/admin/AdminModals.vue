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
          <div class="field">
            <label for="newId">Username / Staff ID</label
            ><input
              id="newId"
              placeholder="เช่น TECH001"
              minlength="2"
              maxlength="30"
              pattern="[A-Za-z0-9_\-]+"
              autocomplete="username"
              required
            />
          </div>
        </div>
        <div class="form-row">
          <div class="field">
            <label for="newEmail">อีเมล</label
            ><input id="newEmail" type="email" autocomplete="email" required />
          </div>
          <div class="field">
            <label for="newPassword">รหัสผ่านเริ่มต้น</label
            ><input
              id="newPassword"
              minlength="8"
              maxlength="128"
              autocomplete="new-password"
              required
            />
            <small>อย่างน้อย 8 ตัวอักษร</small>
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
          <div class="field">
            <label for="newZone">พื้นที่รับผิดชอบ</label
            ><input id="newZone" placeholder="เช่น CSB ชั้น 1–3" />
          </div>
        </div>
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
        <h3 id="qrFormModalTitle">สร้าง QR ประจำห้อง</h3>
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
          <label for="building">อาคาร</label
          ><input id="building" value="อาคารเรียนรวม CSB" required />
        </div>
        <div class="form-row">
          <div class="field">
            <label for="floor">ชั้น</label
            ><input id="floor" value="3" required />
          </div>
          <div class="field">
            <label for="room">ชื่อ/เลขห้อง</label
            ><input id="room" value="CSB-307" required />
          </div>
        </div>
        <div class="field">
          <label for="service">หน้าปลายทาง</label
          ><select id="service">
            <option value="report">เลือกประเภทบริการภายหลัง</option>
            <option value="repair">แจ้งซ่อม</option>
            <option value="clean">แจ้งทำความสะอาด</option>
          </select>
        </div>
        <div class="field">
          <label for="qrToken">Token หรือลิงก์ QR ของสถานที่</label>
          <input id="qrToken" required autocomplete="off" placeholder="วาง token หรือลิงก์ที่มี ?token=..." />
          <small>ใช้ token ที่ระบบออกให้สถานที่จริง ไม่ใช่ชื่อห้องหรือรหัสที่ตั้งขึ้นเอง</small>
        </div>
        <div class="field">
          <label for="baseUrl">URL หน้าแบบฟอร์ม (เว้นว่างเพื่อใช้เว็บนี้)</label
          ><input
            id="baseUrl"
            type="url"
            placeholder="https://example.com/user"
          />
        </div>
        <button class="primary" style="width: 100%">
          สร้าง QR และเพิ่มห้อง
        </button>
      </form>
    </section>
  </div>

  <div
    class="modal"
    id="bulkQrModal"
    role="dialog"
    aria-modal="true"
    aria-labelledby="bulkQrTitle"
  >
    <section class="modal-card">
      <header class="modal-head">
        <h3 id="bulkQrTitle">สร้าง QR หลายห้อง</h3>
        <button
          type="button"
          class="close"
          data-close="bulkQrModal"
          aria-label="ปิด"
        >
          <svg class="icon"><use href="#i-close" /></svg>
        </button>
      </header>
      <form id="bulkQrForm">
        <div class="field">
          <label for="bulkRooms">เลขห้อง</label
          ><textarea
            id="bulkRooms"
            required
            placeholder="เช่น CSB-301, CSB-302, CSB-303"
          ></textarea>
        </div>
        <button type="submit" class="primary" style="width: 100%">
          สร้าง QR ทุกห้อง
        </button>
      </form>
    </section>
  </div>
</template>
