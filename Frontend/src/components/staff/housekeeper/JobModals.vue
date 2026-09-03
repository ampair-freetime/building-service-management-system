<template>
<div
      class="modal"
      id="returnJobModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="returnJobModalTitle"
    >
      <div class="modal-card">
        <div class="modal-head">
          <h3 id="returnJobModalTitle">คืนงานเข้าคิวกลาง</h3>
          <button class="close" data-close="returnJobModal" aria-label="ปิด">
            ×
          </button>
        </div>
        <form id="returnJobForm">
          <input type="hidden" id="returnJobId" />
          <div class="field">
            <label for="returnReason">เหตุผลในการคืนงาน</label
            ><select id="returnReason" required>
              <option value="">เลือกเหตุผล</option>
              <option>รับงานผิดประเภท</option>
              <option>ไม่สามารถเข้าพื้นที่ได้</option>
              <option>ต้องใช้ผู้เชี่ยวชาญอื่น</option>
              <option>งานเกินขอบเขตหน้าที่</option>
              <option>อื่น ๆ</option>
            </select>
          </div>
          <div class="field">
            <label for="returnNote">รายละเอียดเพิ่มเติม</label
            ><textarea
              id="returnNote"
              required
              placeholder="ข้อมูลสำหรับ Staff คนถัดไป"
            ></textarea>
          </div>
          <div class="security-note" style="margin-bottom: 14px">
            ระบบจะขอยืนยันอีกครั้งก่อนคืนงาน ประวัติเดิมทั้งหมดจะยังอยู่
          </div>
          <button class="return-btn" style="width: 100%" type="submit">
            ดำเนินการต่อ
          </button>
        </form>
      </div>
    </div>

<div
      class="modal job-detail-modal"
      id="jobDetailModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="jobDetailTitle"
    >
      <section class="modal-card">
        <header class="modal-head">
          <div>
            <span class="eyebrow" id="jobDetailCode">JOB-000</span>
            <h3 id="jobDetailTitle">รายละเอียดงาน</h3>
          </div>
          <button
            type="button"
            class="close"
            data-close="jobDetailModal"
            aria-label="ปิด"
          >
            <svg class="icon"><use href="#i-close" /></svg>
          </button>
        </header>
        <div class="detail-layout">
          <div>
            <div class="detail-photo">
              <svg class="icon" id="jobDetailIcon"><use href="#i-tools" /></svg>
            </div>
            <div class="timeline" id="jobTimeline"></div>
          </div>
          <div>
            <div class="job-meta" id="jobDetailBadges"></div>
            <p id="jobDetailDescription"></p>
            <div class="detail-meta">
              <div>
                <small>สถานที่</small><strong id="jobDetailRoom">–</strong>
              </div>
              <div>
                <small>ผู้แจ้ง</small><strong id="jobDetailReporter">–</strong>
              </div>
              <div>
                <small>ติดต่อ</small
                ><strong id="jobDetailContact">staff@cmu.ac.th</strong>
              </div>
              <div>
                <small>ผู้รับผิดชอบ</small
                ><strong id="jobDetailAssignee">–</strong>
              </div>
            </div>
            <div class="detail-notes">
              <strong>หมายเหตุล่าสุด</strong
              ><small id="jobDetailNotes">ยังไม่มีหมายเหตุ</small>
            </div>
            <div class="quick-action-grid" id="jobQuickActions"></div>
          </div>
        </div>
      </section>
    </div>

<div
      class="modal"
      id="assignModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="assignModalTitle"
    >
      <section class="modal-card">
        <header class="modal-head">
          <h3 id="assignModalTitle">มอบหมายงาน</h3>
          <button
            type="button"
            class="close"
            data-close="assignModal"
            aria-label="ปิด"
          >
            <svg class="icon"><use href="#i-close" /></svg>
          </button>
        </header>
        <form id="assignForm">
          <input type="hidden" id="assignJobId" /><input
            type="hidden"
            id="assignStaff"
            required
          />
          <div class="form-row">
            <div class="field">
              <label for="assignSearch">ค้นหา Staff</label
              ><input id="assignSearch" placeholder="ค้นหาชื่อหรือพื้นที่" />
            </div>
            <div class="field">
              <label for="assignRole">Role</label
              ><select id="assignRole">
                <option>ช่าง</option>
                <option>แม่บ้าน</option>
                <option>ธุรการ</option>
                <option>แอดมิน</option>
              </select>
            </div>
          </div>
          <div class="staff-choice-list" id="assignStaffList"></div>
          <div class="field">
            <label for="assignNote">หมายเหตุ</label
            ><textarea
              id="assignNote"
              placeholder="ข้อมูลที่เจ้าหน้าที่ควรทราบ"
            ></textarea>
          </div>
          <button type="submit" class="primary" style="width: 100%">
            ยืนยันมอบหมาย
          </button>
        </form>
      </section>
    </div>

<div
      class="modal"
      id="statusUpdateModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="statusUpdateTitle"
    >
      <section class="modal-card">
        <header class="modal-head">
          <h3 id="statusUpdateTitle">อัปเดตสถานะ</h3>
          <button
            type="button"
            class="close"
            data-close="statusUpdateModal"
            aria-label="ปิด"
          >
            <svg class="icon"><use href="#i-close" /></svg>
          </button>
        </header>
        <form id="statusUpdateForm">
          <input type="hidden" id="statusJobId" />
          <div class="field">
            <label for="newJobStatus">สถานะใหม่</label
            ><select id="newJobStatus" required></select>
          </div>
          <div class="field">
            <label for="statusNote">หมายเหตุ</label
            ><textarea
              id="statusNote"
              required
              placeholder="สรุปความคืบหน้า"
            ></textarea>
          </div>
          <div class="field">
            <label for="statusImage">รูปความคืบหน้า (ถ้ามี)</label
            ><input
              id="statusImage"
              type="file"
              accept="image/jpeg,image/png,image/webp"
            />
          </div>
          <div class="field">
            <label for="statusTime">วันที่และเวลา</label
            ><input id="statusTime" readonly />
          </div>
          <button type="submit" class="primary" style="width: 100%">
            บันทึกสถานะ
          </button>
        </form>
      </section>
    </div>

<div
      class="modal"
      id="noteModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="noteModalTitle"
    >
      <section class="modal-card">
        <header class="modal-head">
          <h3 id="noteModalTitle">เพิ่มหมายเหตุ</h3>
          <button
            type="button"
            class="close"
            data-close="noteModal"
            aria-label="ปิด"
          >
            <svg class="icon"><use href="#i-close" /></svg>
          </button>
        </header>
        <form id="noteForm">
          <input type="hidden" id="noteJobId" />
          <div class="field">
            <label for="noteText">หมายเหตุ</label
            ><textarea
              id="noteText"
              required
              placeholder="เขียนข้อมูลที่ช่วยให้ทีมทำงานต่อได้"
            ></textarea>
          </div>
          <label class="remember"
            ><input id="notePrivate" type="checkbox" /> แสดงเฉพาะ Staff</label
          >
          <div class="modal-actions">
            <button type="button" class="secondary" data-close="noteModal">
              ยกเลิก</button
            ><button type="submit" class="primary">บันทึก</button>
          </div>
        </form>
      </section>
    </div>

<div
      class="modal"
      id="uploadModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="uploadModalTitle"
    >
      <section class="modal-card">
        <header class="modal-head">
          <h3 id="uploadModalTitle">เพิ่มรูปความคืบหน้า</h3>
          <button
            type="button"
            class="close"
            data-close="uploadModal"
            aria-label="ปิด"
          >
            <svg class="icon"><use href="#i-close" /></svg>
          </button>
        </header>
        <form id="uploadForm">
          <input type="hidden" id="uploadJobId" /><label
            class="drop-zone"
            id="uploadDropZone"
            for="progressImage"
            ><input
              id="progressImage"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              required
            /><span
              ><svg class="icon" style="margin: auto">
                <use href="#i-upload" /></svg
              ><strong>ลากรูปมาวาง หรือเลือกจากเครื่อง</strong
              ><small>JPG, PNG, WebP · ไม่เกิน 5 MB</small></span
            ></label
          >
          <div class="upload-preview" id="progressPreview">
            <img alt="ตัวอย่างรูปความคืบหน้า" /><span></span
            ><button type="button" class="small-btn" id="removeProgressImage">
              ลบรูป
            </button>
          </div>
          <div class="field">
            <label for="uploadDescription">คำอธิบายรูป</label
            ><textarea
              id="uploadDescription"
              required
              placeholder="รูปนี้แสดงความคืบหน้าอะไร"
            ></textarea>
          </div>
          <button type="submit" class="primary" style="width: 100%">
            อัปโหลดรูป
          </button>
        </form>
      </section>
    </div>

<div
      class="modal"
      id="completeModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="completeModalTitle"
    >
      <section class="modal-card">
        <header class="modal-head">
          <h3 id="completeModalTitle">สรุปและปิดงาน</h3>
          <button
            type="button"
            class="close"
            data-close="completeModal"
            aria-label="ปิด"
          >
            <svg class="icon"><use href="#i-close" /></svg>
          </button>
        </header>
        <form id="completeForm">
          <input type="hidden" id="completeJobId" />
          <div class="field">
            <label for="completeResult">ผลการดำเนินงาน</label
            ><textarea id="completeResult" required></textarea>
          </div>
          <div class="field">
            <label for="completeNote">หมายเหตุปิดงาน</label
            ><textarea id="completeNote" required></textarea>
          </div>
          <div class="field">
            <label for="completeImage">รูปหลังดำเนินการ</label
            ><input
              id="completeImage"
              type="file"
              accept="image/jpeg,image/png,image/webp"
            />
          </div>
          <div class="field">
            <label for="completeDate">วันที่เสร็จ</label
            ><input id="completeDate" type="date" required />
          </div>
          <button type="submit" class="primary" style="width: 100%">
            ยืนยันปิดงาน
          </button>
        </form>
      </section>
    </div>
</template>
