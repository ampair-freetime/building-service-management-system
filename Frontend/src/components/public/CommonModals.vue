<template>
<div
        class="ui-modal"
        id="serviceChooserModal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="serviceChooserTitle"
      >
        <section class="ui-modal-card compact">
          <header class="ui-modal-head">
            <div>
              <h2 id="serviceChooserTitle">เลือกบริการ</h2>
              <p class="modal-copy">ต้องการแจ้งเรื่องใด</p>
            </div>
            <button
              type="button"
              class="modal-close"
              data-modal-close="serviceChooserModal"
              aria-label="ปิด"
            >
              <svg class="icon"><use href="#i-close" /></svg>
            </button>
          </header>
          <div class="service-choice-grid">
            <button
              type="button"
              class="service-choice"
              data-service-choice="repair"
            >
              <svg class="icon"><use href="#i-tools" /></svg
              ><span>แจ้งซ่อม</span></button
            ><button
              type="button"
              class="service-choice"
              data-service-choice="clean"
            >
              <svg class="icon"><use href="#i-broom" /></svg
              ><span>แจ้งทำความสะอาด</span></button
            ><button
              type="button"
              class="service-choice"
              data-service-choice="lost"
            >
              <svg class="icon"><use href="#i-box" /></svg
              ><span>ของหาย–ของได้คืน</span>
            </button>
          </div>
        </section>
      </div>

      <div
        class="ui-modal"
        id="successModal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="successModalTitle"
      >
        <section class="ui-modal-card compact">
          <header class="ui-modal-head">
            <h2 id="successModalTitle">ส่งรายการสำเร็จ</h2>
            <button
              type="button"
              class="modal-close"
              data-modal-close="successModal"
              aria-label="ปิด"
            >
              <svg class="icon"><use href="#i-close" /></svg>
            </button>
          </header>
          <div class="success-wrap">
            <div class="success-icon" aria-hidden="true">
              <svg class="icon"><use href="#i-check" /></svg>
            </div>
            <h3 id="successType">ส่งรายการเรียบร้อยแล้ว</h3>
            <dl id="successRequestDetails" class="success-request-details" hidden>
              <div><dt>สถานที่</dt><dd id="successLocation"></dd></div>
              <div><dt>ปัญหาที่พบ</dt><dd id="successProblem"></dd></div>
            </dl>
            <p id="successInstruction">เก็บรหัสคำร้องนี้ไว้เพื่อติดตามสถานะ</p>
            <strong class="request-code" id="successCode">LOST-20260912-3BE8986F</strong>
            <small class="success-email" id="successEmail"></small>
          </div>
          <div class="modal-actions">
            <button type="button" class="secondary" id="backHomeButton">
              กลับหน้าหลัก
            </button>
            <button type="button" class="primary-btn" id="viewStatusButton">
              ติดตามสถานะ
            </button>
          </div>
        </section>
      </div>
</template>

<style scoped>
.success-request-details {
  width: 100%;
  margin: 18px 0 0;
  text-align: center;
  font-size: 15px;
  color: var(--muted);
}
.success-request-details div {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 8px;
}
.success-request-details:not([hidden]) + #successInstruction {
  margin-top: 28px;
}
.success-request-details div + div {
  margin-top: 6px;
}
.success-request-details dt {
  flex-shrink: 0;
  font-weight: 700;
  color: var(--muted);
}
.success-request-details dd {
  margin: 0;
  min-width: 0;
  overflow-wrap: anywhere;
  font-weight: 400;
  color: var(--muted);
}
</style>
