<script setup>
import { onMounted } from "vue";

onMounted(() => {
  document.title = "เลือกพื้นที่ใช้งาน | Building Care";
});
</script>

<template>
  <div class="portal-page">
    <svg width="0" height="0" aria-hidden="true" style="position: absolute">
      <symbol id="i-building" viewBox="0 0 24 24">
        <path
          d="M4 21V7l8-4 8 4v14M8 10h1m3 0h1m3 0h1M8 14h1m3 0h1m3 0h1M9 21v-3h6v3"
        />
      </symbol>
      <symbol id="i-user" viewBox="0 0 24 24">
        <circle cx="12" cy="8" r="4" />
        <path d="M4.5 21a7.5 7.5 0 0 1 15 0" />
      </symbol>
      <symbol id="i-shield" viewBox="0 0 24 24">
        <path d="M12 22s8-3.5 8-10V5l-8-3-8 3v7c0 6.5 8 10 8 10Z" />
        <path d="m9 12 2 2 4-4" />
      </symbol>
      <symbol id="i-arrow" viewBox="0 0 24 24">
        <path d="M5 12h14m-5-5 5 5-5 5" />
      </symbol>
    </svg>
    <main class="shell">
      <div class="brand">
        <span class="brand-mark"
          ><svg class="icon"><use href="#i-building" /></svg></span
        ><span
          ><strong>Building Care</strong
          ><small>ระบบบริหารจัดการบริการอาคาร</small></span
        >
      </div>
      <header class="intro">
        <h1>เลือกพื้นที่ใช้งาน</h1>
        <p>เลือกประเภทผู้ใช้งานเพื่อเข้าสู่บริการที่เหมาะกับคุณ</p>
      </header>
      <section class="portal-grid" aria-label="ประเภทผู้ใช้งาน">
        <RouterLink class="portal-card" to="/user"
          ><span class="portal-icon"
            ><svg class="icon"><use href="#i-user" /></svg
          ></span>
          <h2>ผู้ใช้งานทั่วไป</h2>
          <p>แจ้งซ่อม ขอทำความสะอาด ค้นหาของหาย และติดตามคำร้อง</p>
          <span class="portal-action"
            >เข้าสู่หน้าผู้ใช้งาน
            <svg class="icon"><use href="#i-arrow" /></svg></span
        ></RouterLink>
        <RouterLink class="portal-card staff" to="/staff-login"
          ><span class="portal-icon"
            ><svg class="icon"><use href="#i-shield" /></svg
          ></span>
          <h2>เจ้าหน้าที่</h2>
          <p>สำหรับช่าง แม่บ้าน ธุรการ และผู้ดูแลระบบ</p>
          <span class="portal-action"
            >เข้าสู่ Staff Portal
            <svg class="icon"><use href="#i-arrow" /></svg></span
        ></RouterLink>
      </section>
      <p class="footer-note">Building Care · Secure Service Portal</p>
    </main>
  </div>
</template>

<style>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+Thai:wght@400;500;600;700;800&display=swap");
:root {
  --primary: #6d5df6;
  --primary-soft: #f0edff;
  --ink: #1d1b2a;
  --muted: #716d7b;
  --line: #e9e7ef;
  --shadow: 0 22px 65px rgba(45, 38, 82, 0.11);
  --font: "Noto Sans Thai", "Inter", sans-serif;
}
* {
  box-sizing: border-box;
}
html {
  scroll-behavior: smooth;
}
body {
  margin: 0;
  min-height: 100vh;
  background: radial-gradient(circle at 80% 0, #e9e3ff 0, transparent 35%),
    linear-gradient(145deg, #f7f6fb, #fff 50%, #f2efff);
  color: var(--ink);
  font-family: var(--font);
  -webkit-font-smoothing: antialiased;
}
.shell {
  width: min(1080px, calc(100% - 40px));
  min-height: 100vh;
  margin: auto;
  padding: 48px 0;
  display: grid;
  align-content: center;
}
.brand {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 34px;
}
.brand-mark {
  width: 52px;
  height: 52px;
  border-radius: 17px;
  background: linear-gradient(135deg, var(--primary), #8b7dfb);
  color: #fff;
  display: grid;
  place-items: center;
  box-shadow: 0 12px 28px rgba(109, 93, 246, 0.25);
}
.icon {
  width: 26px;
  height: 26px;
  display: block;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.brand strong,
.brand small {
  display: block;
}
.brand strong {
  font-size: 18px;
}
.brand small {
  font-size: 11px;
  color: var(--muted);
}
.intro {
  text-align: center;
  margin-bottom: 28px;
}
.intro h1 {
  font-size: clamp(28px, 4vw, 42px);
  line-height: 1.15;
  margin: 0 0 9px;
}
.intro p {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
}
.portal-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}
.portal-card {
  position: relative;
  min-height: 330px;
  padding: 30px;
  border: 1px solid rgba(229, 226, 239, 0.9);
  border-radius: 26px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: var(--shadow);
  color: var(--ink);
  text-decoration: none;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  overflow: hidden;
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}
.portal-card:before {
  content: "";
  position: absolute;
  width: 180px;
  height: 180px;
  border-radius: 50%;
  right: -70px;
  top: -75px;
  background: var(--primary-soft);
}
.portal-icon {
  position: relative;
  width: 74px;
  height: 74px;
  border-radius: 22px;
  background: var(--primary-soft);
  color: var(--primary);
  display: grid;
  place-items: center;
  margin-bottom: 28px;
}
.portal-icon .icon {
  width: 38px;
  height: 38px;
}
.portal-card h2 {
  font-size: 24px;
  margin: 0 0 8px;
}
.portal-card p {
  font-size: 13px;
  line-height: 1.7;
  color: var(--muted);
  margin: 0;
  max-width: 390px;
}
.portal-action {
  margin-top: auto;
  width: 100%;
  min-height: 52px;
  border-radius: 16px;
  background: var(--primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  font-size: 13px;
  font-weight: 800;
  box-shadow: 0 12px 26px rgba(109, 93, 246, 0.2);
}
.portal-action .icon {
  width: 18px;
  height: 18px;
}
.portal-card:hover {
  transform: translateY(-4px);
  border-color: #cfc8ff;
  box-shadow: 0 28px 75px rgba(45, 38, 82, 0.15);
}
.portal-card:active {
  transform: scale(0.97);
}
.portal-card:focus-visible {
  outline: 3px solid rgba(109, 93, 246, 0.3);
  outline-offset: 4px;
}
.portal-card.staff .portal-icon {
  background: #edf4ff;
  color: #3575df;
}
.portal-card.staff:before {
  background: #edf4ff;
}
.footer-note {
  text-align: center;
  color: #9a96a3;
  font-size: 10px;
  margin: 24px 0 0;
}
@media (max-width: 720px) {
  .shell {
    width: min(100% - 28px, 560px);
    padding: 28px 0;
  }
  .brand {
    margin-bottom: 26px;
  }
  .portal-grid {
    grid-template-columns: 1fr;
    gap: 14px;
  }
  .portal-card {
    min-height: 245px;
    padding: 22px;
    border-radius: 22px;
  }
  .portal-icon {
    width: 62px;
    height: 62px;
    border-radius: 19px;
    margin-bottom: 18px;
  }
  .portal-card h2 {
    font-size: 21px;
  }
  .portal-card p {
    margin-bottom: 20px;
  }
  .intro h1 {
    font-size: 30px;
  }
}
@media (prefers-reduced-motion: reduce) {
  * {
    scroll-behavior: auto !important;
    transition: none !important;
  }
}
</style>