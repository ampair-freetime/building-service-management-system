<template>
<div
      class="modal"
      id="foundModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="foundModalTitle"
    >
      <div class="modal-card">
        <div class="modal-head">
          <h3 id="foundModalTitle">รับฝากของใหม่</h3>
          <button class="close" data-close="foundModal" aria-label="ปิด">
            ×
          </button>
        </div>
        <form id="foundForm">
          <div class="field">
            <label for="foundName">ชื่อสิ่งของ</label
            ><input id="foundName" placeholder="เช่น กระเป๋าผ้าสีดำ" required />
          </div>
          <div class="form-row">
            <div class="field">
              <label for="foundLocation">สถานที่พบ</label
              ><input id="foundLocation" required />
            </div>
            <div class="field">
              <label for="custodyPoint">จุดรับฝาก</label
              ><input id="custodyPoint" value="ประชาสัมพันธ์ชั้น 1" required />
            </div>
          </div>
          <div class="field">
            <label for="privateDetail">รายละเอียดลับสำหรับยืนยันเจ้าของ</label
            ><textarea
              id="privateDetail"
              placeholder="ข้อมูลที่ไม่แสดงต่อสาธารณะ"
            ></textarea>
          </div>
          <button class="primary" style="width: 100%">บันทึกรับฝาก</button>
        </form>
      </div>
    </div>

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
            <label for="rejectNote">หมายเหตุเพิ่มเติม</label
            ><textarea
              id="rejectNote"
              placeholder="อธิบายสิ่งที่ตรวจพบ เพื่อให้ตรวจสอบย้อนหลังได้"
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
            <span class="eyebrow" id="claimDetailCode">CLM-000</span>
            <h3 id="claimDetailTitle">รายละเอียดคำขอรับคืน</h3>
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
          <div>
            <small>นัดหมาย</small
            ><strong id="claimAppointment">ยังไม่มีนัดหมาย</strong>
          </div>
        </div>
        <h4>หลักฐานและรายละเอียด</h4>
        <p id="claimEvidence"></p>
        <div class="claim-secret">
          <strong>ข้อมูลลับสำหรับตรวจสอบ</strong>
          <p id="claimSecret"></p>
        </div>
        <div class="timeline" id="claimTimeline"></div>
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
          <h3 id="appointmentTitle">นัดหมายรับของ</h3>
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
          <input type="hidden" id="appointmentItemId" />
          <div class="form-row">
            <div class="field">
              <label for="appointmentDate">วันที่รับของ</label
              ><input id="appointmentDate" type="date" required />
            </div>
            <div class="field">
              <label for="appointmentTime">เวลา</label
              ><input id="appointmentTime" type="time" required />
            </div>
          </div>
          <div class="field">
            <label for="appointmentPlace">จุดรับของ</label
            ><input
              id="appointmentPlace"
              value="ประชาสัมพันธ์ ชั้น 1"
              required
            />
          </div>
          <div class="field">
            <label for="appointmentNote">หมายเหตุ</label
            ><textarea
              id="appointmentNote"
              placeholder="เอกสารที่ต้องนำมาแสดง"
            ></textarea>
          </div>
          <button type="submit" class="primary" style="width: 100%">
            ยืนยันนัดหมาย
          </button>
        </form>
      </section>
    </div>
</template>
