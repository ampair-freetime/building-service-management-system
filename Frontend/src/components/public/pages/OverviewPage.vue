<script setup>
import { onMounted, ref } from "vue";
import { resolveCleaningLocationByQr } from "../../../services/cleaningRequests.js";

const params = new URLSearchParams(window.location.search);
const qrToken = params.get("token")?.trim() ?? "";
const currentQrLocation = ref(null);

function formatQrLocation(location) {
  if (!location) return "";
  return location.floor
    ? `ชั้น ${location.floor} · ${location.area}`
    : location.area;
}

onMounted(async () => {
  if (!qrToken || qrToken.length > 255) return;

  try {
    currentQrLocation.value = await resolveCleaningLocationByQr(qrToken);
  } catch {
    // ซ่อนตำแหน่งไว้เมื่อ QR ใช้ไม่ได้หรือเชื่อมต่อระบบไม่ได้
    currentQrLocation.value = null;
  }
});
</script>

<template>
<section class="page active" id="dashboard">
          <header class="mobile-hero">
            <div class="eyebrow">CS Building Care</div>

            <h1 class="greeting-name">แจ้งเรื่องได้ทันที</h1>
            <p class="hero-subtitle">
              ระบบบริหารจัดการงานบริการอาคารเรียน<br />
              ภาควิชาวิทยาการคอมพิวเตอร์
            </p>
            <img
              class="building-illustration"
              src="/images/cs-building-line-art.svg"
              alt=""
              aria-hidden="true"
            />
          </header>

          <section
            v-if="currentQrLocation"
            class="location-card"
            aria-label="ตำแหน่งปัจจุบัน"
          >
            <div class="location-icon">
              <svg class="icon"><use href="#i-pin" /></svg>
            </div>
            <div class="location-copy">
              <small>ตำแหน่งปัจจุบัน</small
              ><strong>{{ formatQrLocation(currentQrLocation) }}</strong>
            </div>
          </section>

          <section class="dashboard-section service-menu-section">
            <div class="section-head">
              <h2>เมนูบริการ</h2>
            </div>
            <div class="service-grid primary-service-menu">
              <button type="button" class="service-card repair" data-go="repair">
                <span class="service-icon" aria-hidden="true">
                  <svg class="icon icon-lg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.106-3.105c.32-.322.863-.22.983.218a6 6 0 0 1-8.259 7.057l-7.91 7.91a1 1 0 0 1-2.999-3l7.91-7.91a6 6 0 0 1 7.057-8.259c.438.12.54.662.219.984z" />
                  </svg>
                </span>
                <span class="service-name">แจ้งซ่อม</span>
              </button>
              <button type="button" class="service-card clean" data-go="clean">
                <span class="service-icon" aria-hidden="true">
                  <svg class="icon icon-lg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M11 2v2" /><path d="M12 3h-2" /><path d="M13.5 10.5 22 2" /><path d="M14.734 13.841a2 2 0 0 0-.314-2.42L12.58 9.58a2 2 0 0 0-2.421-.314l-7.657 4.461A1 1 0 0 0 2.3 15.3l6.403 6.403a1 1 0 0 0 1.571-.204z" /><path d="M20 15v4" /><path d="M22 17h-4" /><path d="M4 4v4" /><path d="m5 18 2-2" /><path d="M6 6H2" /><path d="m7.699 10.7 5.602 5.601" />
                  </svg>
                </span>
                <span class="service-name">แจ้งทำความสะอาด</span>
              </button>
              <button type="button" class="service-card lost" data-go="lost" data-lost-tab="browse">
                <span class="service-icon" aria-hidden="true">
                  <svg class="icon icon-lg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect width="20" height="5" x="2" y="3" rx="1" /><path d="M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8" /><path d="M10 12h4" />
                  </svg>
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
                  placeholder="เช่น CLN-123456789ABC"
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
                  ><strong id="trackingResultCode">–</strong>
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
              <p id="trackingPhotosNotice" role="status" hidden>
                รูปหลังทำงานยังไม่พร้อมแสดง กรุณารีเฟรชภายหลัง
              </p>
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
