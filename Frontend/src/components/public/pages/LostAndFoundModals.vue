<template>
<div
        class="ui-modal"
        id="detailModal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="detailModalTitle"
      >
        <section class="ui-modal-card">
          <header class="ui-modal-head">
            <h2 id="detailModalTitle">รายละเอียด</h2>
            <button
              type="button"
              class="modal-close"
              data-modal-close="detailModal"
              aria-label="ปิด"
            >
              <svg class="icon"><use href="#i-close" /></svg>
            </button>
          </header>
          <div class="detail-hero">
            <svg class="icon" id="detailIcon"><use href="#i-box" /></svg>
          </div>
          <h3 id="detailTitle">รายการ</h3>
          <p id="detailDescription"></p>
          <div class="detail-meta">
            <div><small>วันที่</small><strong id="detailDate">–</strong></div>
            <div>
              <small>สถานที่</small><strong id="detailLocation">–</strong>
            </div>
            <div><small>สถานะ</small><strong id="detailStatus">–</strong></div>
            <div><small>หมายเลข</small><strong id="detailCode">–</strong></div>
          </div>
          <div class="modal-actions">
            <button
              type="button"
              class="secondary"
              data-modal-close="detailModal"
            >
              ปิด</button
            ><button
              type="button"
              class="primary-btn"
              id="detailContinueButton"
            >
              ดำเนินการต่อ
            </button>
          </div>
        </section>
      </div>

      <div
        class="ui-modal"
        id="claimModal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="claimModalTitle"
      >
        <section class="ui-modal-card wide">
          <header class="ui-modal-head">
            <div>
              <h2 id="claimModalTitle">ขอรับคืนสิ่งของ</h2>
              <p class="modal-copy">
                กรอกรายละเอียดเพื่อให้เจ้าหน้าที่ตรวจสอบความเป็นเจ้าของ
              </p>
            </div>
            <button
              type="button"
              class="modal-close"
              data-modal-close="claimModal"
              aria-label="ปิด"
            >
              <svg class="icon"><use href="#i-close" /></svg>
            </button>
          </header>

          <form id="claimForm" class="form-panel" novalidate>
            <div class="field">
              <label>สิ่งของที่ต้องการขอรับคืน</label>
              <strong id="claimItemName">–</strong>
            </div>
            <div class="field">
              <label for="claimName">ชื่อผู้ขอรับคืน</label>
              <input
                id="claimName"
                name="claimant_name"
                type="text"
                required
                minlength="2"
                maxlength="150"
                aria-describedby="claimNameError"
                autocomplete="name"
                placeholder="ชื่อ-นามสกุล"
              />
              <p id="claimNameError" class="field-error" aria-live="polite"></p>
            </div>
            <div class="field">
              <label for="claimContact">อีเมลสำหรับติดต่อ</label>
              <input
                id="claimContact"
                name="claimant_email"
                type="email"
                required
                maxlength="255"
                aria-describedby="claimContactError"
                autocomplete="email"
                placeholder="name@example.com"
              />
              <p id="claimContactError" class="field-error" aria-live="polite"></p>
            </div>
            <div class="field">
              <label for="claimProofDetail">รายละเอียดเพื่อยืนยันความเป็นเจ้าของ</label>
              <textarea
                id="claimProofDetail"
                name="proof_detail"
                required
                minlength="10"
                maxlength="1000"
                aria-describedby="claimProofDetailError"
                placeholder="เช่น สี ยี่ห้อ ตำหนิ ของที่อยู่ภายใน หรือข้อมูลเฉพาะที่เจ้าของทราบ"
              ></textarea>
              <p id="claimProofDetailError" class="field-error" aria-live="polite"></p>
            </div>
            <p class="privacy-note">
              อย่าใส่รหัสผ่าน เลขบัตร หรือข้อมูลส่วนบุคคลที่ละเอียดอ่อน
              เจ้าหน้าที่จะใช้ข้อมูลนี้เพื่อตรวจสอบก่อนนัดรับคืน
            </p>
            <div class="modal-actions">
              <button type="button" class="secondary" data-modal-close="claimModal">
                ยกเลิก
              </button>
              <button type="submit" class="primary-btn">ส่งคำขอรับคืน</button>
            </div>
          </form>
        </section>
      </div>
</template>
