<template>
<section class="page active" id="dashboard">
          <header class="mobile-hero">
            <div class="eyebrow">CS Building Care</div>

            <h1 class="greeting-name">แจ้งเรื่องได้ทันที</h1>
            <p class="hero-subtitle">
              ระบบบริหารจัดการงานบริการอาคารเรียน<br />
              ภาควิชาวิทยาการคอมพิวเตอร์
            </p>
            <svg
              class="building-illustration"
              viewBox="0 0 220 170"
              aria-hidden="true"
            >
              <path
                d="M12 154h196M28 154V76h46v78M74 154V42h72v112M146 154V66h48v88M94 42V25h32v17M40 93h10m10 0h7M40 111h10m10 0h7M40 129h10m10 0h7M91 62h12m18 0h12M91 84h12m18 0h12M91 106h12m18 0h12M91 128h12m18 0h12M160 85h10m10 0h6M160 105h10m10 0h6M160 125h10m10 0h6M104 154v-22h14v22"
                fill="none"
                stroke="currentColor"
                stroke-width="5"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </header>

          <section class="location-card" aria-label="ตำแหน่งปัจจุบัน">
            <div class="location-icon">
              <svg class="icon"><use href="#i-pin" /></svg>
            </div>
            <div class="location-copy">
              <small>ตำแหน่งปัจจุบัน</small
              ><strong>อาคาร วิทยาศาสตร์คอมพิวเตอร์ (CS)</strong>
            </div>
          </section>

          <section class="dashboard-section">
            <div class="section-head">
              <h2>เมนูบริการ</h2>
            </div>
            <div class="service-grid primary-service-menu">
              <button type="button" class="service-card repair" data-go="repair">
                <span class="service-icon" aria-hidden="true">
                  <svg class="icon icon-lg"><use href="#i-tools" /></svg>
                </span>
                <span class="service-name">แจ้งซ่อม</span>
              </button>
              <button type="button" class="service-card clean" data-go="clean">
                <span class="service-icon" aria-hidden="true">
                  <svg class="icon icon-lg"><use href="#i-broom" /></svg>
                </span>
                <span class="service-name">แจ้งทำความสะอาด</span>
              </button>
              <button type="button" class="service-card lost" data-go="lost" data-lost-tab="browse">
                <span class="service-icon" aria-hidden="true">
                  <svg class="icon icon-lg"><use href="#i-box" /></svg>
                </span>
                <span class="service-name">ของหาย-ได้คืน</span>
              </button>
            </div>
          </section>

          <section class="dashboard-section" id="trackingSection">
            <div class="section-head">
              <div>
                <h2>ติดตามสถานะคำร้องทั้งหมด</h2>
                <p style="margin: 4px 0 0; font-size: 12px">
                  ตรวจสอบได้ทั้งงานบริการ ของหายและของที่พบ
                </p>
              </div>
            </div>
            <form class="tracking-box" id="trackingForm" novalidate>
              <div class="field">
                <label for="trackingCode">รหัสคำร้อง</label
                ><input
                  id="trackingCode"
                  type="text"
                  required
                  aria-describedby="trackingCodeError"
                  placeholder="เช่น LOST-20260912-3BE8986F"
                  autocomplete="off"
                />
                <p
                  id="trackingCodeError"
                  class="field-error"
                  aria-live="polite"
                ></p>
              </div>
              <div class="field">
                <label for="trackingEmail">อีเมล</label
                ><input
                  id="trackingEmail"
                  type="email"
                  required
                  aria-describedby="trackingEmailError"
                  placeholder="name@example.com"
                  autocomplete="email"
                />
                <p
                  id="trackingEmailError"
                  class="field-error"
                  aria-live="polite"
                ></p>
              </div>
              <button type="submit" class="primary-btn">ตรวจสอบสถานะ</button>
            </form>
            <div class="tracking-result" id="trackingResult" role="status" aria-live="polite">
              <div class="tracking-result-head">
                <div>
                  <small>รหัสคำร้อง  </small
                  ><strong id="trackingResultCode">LOST-20260912-3BE8986F</strong>
                  <p id="trackingResultText" style="margin: 5px 0 0"></p>
                </div>
                <span class="status progress" id="trackingResultStatus"
                  >กำลังดำเนินการ</span
                >
              </div>
              <div
                id="trackingDetails"
                class="tracking-request-details"
                hidden
              >
                <div>
                  <small>ประเภทคำร้อง</small>
                  <strong id="trackingRequestType">–</strong>
                </div>
                <div>
                  <small>รายการ</small>
                  <strong id="trackingItemName">–</strong>
                </div>
                <div>
                  <small>อัปเดตล่าสุด</small>
                  <strong id="trackingUpdatedAt">–</strong>
                </div>
              </div>
              <div
                id="trackingProgress"
                class="tracking-progress"
                aria-labelledby="trackingProgressTitle"
                hidden
              >
                <strong id="trackingProgressTitle">ความคืบหน้าของคำร้อง</strong>
                <ol id="trackingProgressSteps" class="tracking-progress-steps"></ol>
              </div>
              <div class="tracking-result-actions">
                <small id="trackingRefreshTime"></small>
                <button
                  type="button"
                  class="secondary"
                  id="refreshTrackingStatus"
                >
                  รีเฟรชสถานะ
                </button>
              </div>
            </div>
          </section>


        </section>
</template>
