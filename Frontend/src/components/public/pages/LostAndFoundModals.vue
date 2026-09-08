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
        <section class="ui-modal-card">
          <header class="ui-modal-head">
            <div>
              <h2 id="claimModalTitle">ยืนยันความเป็นเจ้าของ</h2>
              <p class="modal-copy" id="claimItemName">รายการสิ่งของ</p>
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
          <form id="claimForm">
            <div class="modal-grid">
              <div class="modal-field">
                <label for="claimName">ชื่อผู้ขอรับ</label
                ><input id="claimName" type="text" required />
              </div>
              <div class="modal-field">
                <label for="claimContact">อีเมลสำหรับติดต่อ</label
                ><input
                  id="claimContact"
                  name="recipient_email"
                  type="email"
                  required
                  placeholder="name@example.com"
                  autocomplete="email"
                />
              </div>
            </div>
            <div class="modal-field">
              <label for="claimProof">รายละเอียดที่ใช้ยืนยัน</label
              ><textarea
                id="claimProof"
                required
                placeholder="เช่น ตำหนิ ของภายใน หรือจุดสังเกต"
              ></textarea>
            </div>
            <div class="modal-field">
              <label for="claimDate">วันที่สะดวกรับของ</label
              ><input id="claimDate" type="date" required />
            </div>
            <button type="submit" class="primary-btn modal-action">
              ส่งคำขอ
            </button>
          </form>
        </section>
      </div>
</template>
