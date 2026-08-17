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
</template>
