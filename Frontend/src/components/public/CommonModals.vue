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
</template>
