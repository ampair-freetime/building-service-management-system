<template>
<section class="page active" id="dashboard">
          <header class="mobile-hero">
            <div class="eyebrow">Building Care</div>
            <p class="greeting">บริการอาคาร วิทยาศาสตร์คอมพิวเตอร์ (CS)</p>
            <h1 class="greeting-name">แจ้งเรื่องได้ทันที</h1>
            <p class="hero-subtitle">
              Building Service Management System · ไม่ต้องเข้าสู่ระบบ
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
              <span class="eyebrow">เลือกได้ทันที</span>
            </div>
            <div class="service-grid">
              <article
                class="service-card repair"
                tabindex="0"
                data-card-go="repair"
              >
                <div class="service-icon">
                  <svg class="icon icon-lg"><use href="#i-tools" /></svg>
                </div>
                <h3>แจ้งซ่อม</h3>
                <p>รายงานจุดชำรุด</p>
                <div class="service-footer">
                  <span class="count">2 งานกำลังดำเนินการ</span
                  ><button type="button" class="service-open" data-go="repair">
                    เริ่มแจ้ง
                  </button>
                </div>
              </article>
              <article
                class="service-card clean"
                tabindex="0"
                data-card-go="clean"
              >
                <div class="service-icon">
                  <svg class="icon icon-lg"><use href="#i-broom" /></svg>
                </div>
                <h3>แจ้งทำความสะอาด</h3>
                <p>แจ้งพื้นที่ที่ต้องดูแล</p>
                <div class="service-footer">
                  <span class="count">1 งานใหม่</span
                  ><button type="button" class="service-open" data-go="clean">
                    เริ่มแจ้ง
                  </button>
                </div>
              </article>
              <article
                class="service-card lost"
                tabindex="0"
                data-card-go="lost"
              >
                <div class="service-icon">
                  <svg class="icon icon-lg"><use href="#i-box" /></svg>
                </div>
                <h3>ของหาย–ของได้คืน</h3>
                <p>ค้นหาและแจ้งพบของ</p>
                <div class="lost-card-actions">
                  <button
                    type="button"
                    class="service-open"
                    data-go="lost"
                    data-lost-tab="browse"
                  >
                    ค้นหาของ
                  </button>
                  <button
                    type="button"
                    class="service-open"
                    data-go="lost"
                    data-lost-tab="report-lost"
                  >
                    แจ้งของหาย
                  </button>
                  <button
                    type="button"
                    class="service-open"
                    data-go="lost"
                    data-lost-tab="report-found"
                  >
                    แจ้งพบของ
                  </button>
                </div>
              </article>
            </div>
          </section>

          <section class="dashboard-section" id="trackingSection">
            <div class="section-head">
              <div>
                <h2>ติดตามสถานะงาน</h2>
                <p style="margin: 4px 0 0; font-size: 12px">
                  ใช้รหัสคำร้องและอีเมลเดียวกับที่กรอกตอนแจ้งเรื่อง
                </p>
              </div>
              <span class="eyebrow">ไม่ต้องล็อกอิน</span>
            </div>
            <form class="tracking-box" id="trackingForm">
              <div class="field">
                <label for="trackingCode">รหัสคำร้อง</label
                ><input
                  id="trackingCode"
                  type="text"
                  required
                  placeholder="เช่น BC-4821"
                  autocomplete="off"
                />
              </div>
              <div class="field">
                <label for="trackingEmail">อีเมล</label
                ><input
                  id="trackingEmail"
                  type="email"
                  required
                  placeholder="name@example.com"
                  autocomplete="email"
                />
              </div>
              <button type="submit" class="primary-btn">ตรวจสอบสถานะ</button>
            </form>
            <div class="tracking-result" id="trackingResult">
              <div class="tracking-result-head">
                <div>
                  <small>รหัสคำร้อง</small
                  ><strong id="trackingResultCode">BC-4821</strong>
                  <p id="trackingResultText" style="margin: 5px 0 0">
                    ช่างรับงานแล้วและกำลังตรวจสอบ
                  </p>
                </div>
                <span class="status progress" id="trackingResultStatus"
                  >กำลังดำเนินการ</span
                >
              </div>
            </div>
          </section>

          <section class="dashboard-section">
            <div class="section-head">
              <h2>สถิติเดือนนี้</h2>
              <span class="eyebrow">กรกฎาคม 2569</span>
            </div>
            <div class="stat-grid">
              <article class="stat-card repair">
                <span>แจ้งซ่อม</span><strong>18</strong><small>รายการ</small>
              </article>
              <article class="stat-card clean">
                <span>ทำความสะอาด</span><strong>24</strong><small>รายการ</small>
              </article>
              <article class="stat-card lost">
                <span>ของหาย</span><strong>7</strong><small>รายการ</small>
              </article>
              <article class="stat-card rate">
                <span>สำเร็จ</span><strong>86%</strong><small>ตรงเวลา</small>
              </article>
            </div>
          </section>
        </section>
</template>
