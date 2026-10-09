<template>
<div
      class="modal"
      id="rejectModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="rejectModalTitle"
    >
      <div class="modal-card">
        <div class="modal-head">
          <h3 id="rejectModalTitle">ไม่อนุมัติรายการ</h3>
          <button class="close" data-close="rejectModal" aria-label="ปิด">
            ×
          </button>
        </div>
        <form id="rejectForm">
          <input type="hidden" id="rejectSource" /><input
            type="hidden"
            id="rejectItemId"
          />
          <div class="field">
            <label for="rejectReason">เหตุผลที่ไม่อนุมัติ</label
            ><select id="rejectReason" required>
              <option value="">เลือกเหตุผล</option>
              <option>ข้อมูลไม่ตรงกับสิ่งของจริง</option>
              <option>ไม่พบสิ่งของหรือหลักฐานตามที่แจ้ง</option>
              <option>ข้อมูลไม่ครบหรือไม่สามารถยืนยันได้</option>
              <option>เป็นรายการซ้ำ</option>
              <option>มีข้อมูลส่วนตัวหรือเนื้อหาไม่เหมาะสม</option>
              <option>อยู่นอกขอบเขตการรับฝาก</option>
              <option>เหตุผลอื่น</option>
            </select>
          </div>
          <div class="field">
            <label for="rejectReasonDetail">รายละเอียดเหตุผล</label
            ><textarea
              id="rejectReasonDetail"
              placeholder="อธิบายสิ่งที่ตรวจพบ เพื่อให้ตรวจสอบย้อนหลังได้"
              minlength="5"
              maxlength="500"
              required
            ></textarea>
          </div>
          <button class="danger" style="width: 100%" type="submit">
            ยืนยันไม่อนุมัติ
          </button>
        </form>
      </div>
    </div>

<div
      class="modal job-detail-modal"
      id="claimDetailModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="claimDetailTitle"
    >
      <section class="modal-card">
        <header class="modal-head">
          <div>
            <h3 id="claimDetailTitle">รายละเอียดคำขอรับคืน</h3>
            <small id="claimDetailCode">CLM-000</small>
          </div>
          <button
            type="button"
            class="close"
            data-close="claimDetailModal"
            aria-label="ปิด"
          >
            <svg class="icon"><use href="#i-close" /></svg>
          </button>
        </header>
        <div class="inline-summary">
          <div>
            <small>ผู้ขอรับ</small><strong id="claimRequester">–</strong>
          </div>
          <div><small>ติดต่อ</small><strong id="claimContact">–</strong></div>
          <div>
            <small>วันที่ส่งคำขอ</small><strong id="claimDate">–</strong>
          </div>
          <div><small>สถานะการคืนของ</small><strong id="claimReturnStatus">รอตรวจสอบคำขอ</strong></div>
        </div>
        <section class="claim-general-section">
          <h4>รายละเอียดทั่วไปของสิ่งของ</h4>
          <p id="claimGeneralDescription"></p>
        </section>
        <section class="claim-evidence-section">
          <h4>ตรวจสอบความเป็นเจ้าของ</h4>
          <div class="claim-evidence-columns">
            <div><strong>หลักฐานจากผู้ขอรับคืน</strong><p id="claimEvidence"></p></div>
            <div class="claim-secret"><strong>ข้อมูลลับของสิ่งของ · เฉพาะเจ้าหน้าที่</strong><p id="claimSecret"></p></div>
          </div>
        </section>
        <section id="claimAppointmentGroup" hidden>
          <h4>นัดหมายรับของ</h4>
          <div class="inline-summary">
            <div><small>วันที่นัดรับ</small><strong id="claimPickupDate">–</strong></div>
            <div><small>เวลานัดรับ</small><strong id="claimPickupTime">–</strong></div>
            <div><small>จุดรับของ</small><strong id="claimPickupLocation">–</strong></div>
            <div><small>สิ่งที่ต้องนำมาเพื่อยืนยันการรับคืน</small><strong id="claimPickupNote">–</strong></div>
          </div>
        </section>
        <p id="claimNextStep" class="claim-next-step"></p>
        <details class="claim-history"><summary>ลำดับการดำเนินการ</summary><div class="timeline" id="claimTimeline"></div></details>
        <div class="quick-action-grid" id="claimActions"></div>
      </section>
    </div>

<div
      class="modal"
      id="appointmentModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="appointmentTitle"
    >
      <section class="modal-card">
        <header class="modal-head">
          <div><h3 id="appointmentTitle">นัดหมายรับของ</h3><small id="appointmentCode" class="lost-record-code"></small></div>
          <button
            type="button"
            class="close"
            data-close="appointmentModal"
            aria-label="ปิด"
          >
            <svg class="icon"><use href="#i-close" /></svg>
          </button>
        </header>
        <form id="appointmentForm">
          <p class="form-intro">บันทึกนัดหมายแล้วระบบจะส่งวัน เวลา จุดรับของ และสิ่งที่ต้องนำมาเพื่อยืนยันการรับคืนไปยังอีเมลของผู้ขอ</p>
          <input type="hidden" id="appointmentItemId" />
          <div class="form-row">
            <div class="field">
              <label for="appointmentDate">วันที่รับของ</label
              ><input id="appointmentDate" type="date" required />
            </div>
            <div class="field">
              <label for="appointmentTime">ตั้งแต่เวลา</label
              > <select id="appointmentTime" required aria-describedby="appointmentDateTimeHint">
                <option value="">เลือกเวลา (24 ชั่วโมง)</option>
                <option v-for="minutes in 17" :key="minutes" :value="`${String(Math.floor((510 + (minutes - 1) * 30) / 60)).padStart(2, '0')}:${String((510 + (minutes - 1) * 30) % 60).padStart(2, '0')}`">{{ `${String(Math.floor((510 + (minutes - 1) * 30) / 60)).padStart(2, '0')}:${String((510 + (minutes - 1) * 30) % 60).padStart(2, '0')}` }} น.</option>
              </select>
            </div>
            <div class="field">
              <label for="appointmentEndTime">ถึงเวลา</label>
              <select id="appointmentEndTime" required>
                <option value="">เลือกเวลาสิ้นสุด</option>
                <option v-for="minutes in 17" :key="minutes" :value="`${String(Math.floor((510 + (minutes - 1) * 30) / 60)).padStart(2, '0')}:${String((510 + (minutes - 1) * 30) % 60).padStart(2, '0')}`">{{ `${String(Math.floor((510 + (minutes - 1) * 30) / 60)).padStart(2, '0')}:${String((510 + (minutes - 1) * 30) % 60).padStart(2, '0')}` }} น.</option>
              </select>
            </div>
          </div>
          <small class="field-hint" id="appointmentDateTimeHint">
            รับของจันทร์–ศุกร์ เวลา 08:30–16:30 น. (เวลาไทย)
          </small>
          <div class="field">
            <label for="appointmentPlace">จุดรับของ</label
            ><input
              id="appointmentPlace"
              value="ประชาสัมพันธ์ ชั้น 1"
              required
            />
          </div>
          <div class="field">
            <label for="appointmentNote">สิ่งที่ต้องนำมาเพื่อยืนยันการรับคืน</label
            ><textarea
              id="appointmentNote"
              placeholder="เช่น รูปถ่ายสิ่งของหรือหลักฐานการเป็นเจ้าของ"
            ></textarea>
          </div>
          <button type="submit" class="primary" style="width: 100%">
            ยืนยันนัดหมาย
          </button>
        </form>
      </section>
    </div>
<div class="modal" id="claimMoreModal" role="dialog" aria-modal="true" aria-labelledby="claimMoreTitle">
  <section class="modal-card">
    <header class="modal-head"><h3 id="claimMoreTitle">ขอข้อมูลเพิ่มเติมจากผู้ขอรับคืน</h3><button type="button" class="close" data-close="claimMoreModal" aria-label="ปิด">×</button></header>
    <form id="claimMoreForm">
      <input type="hidden" id="claimMoreId" /><input type="hidden" id="claimMoreAction" />
      <div class="field"><label id="claimMoreLabel" for="claimMoreMessage">ข้อมูลที่ต้องการให้ส่งเพิ่ม</label><textarea id="claimMoreMessage" required maxlength="2000" placeholder="เช่น ระบุลักษณะรอยตำหนิ หรือสิ่งของที่อยู่ภายใน"></textarea></div>
      <button id="claimMoreSubmit" type="submit" class="primary">ดำเนินการต่อ</button>
    </form>
  </section>
</div>
</template>
