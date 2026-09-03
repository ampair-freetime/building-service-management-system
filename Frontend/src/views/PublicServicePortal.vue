<script setup>
import PublicCommonModals from "../components/public/CommonModals.vue";
import PublicLostFoundModals from "../components/public/pages/LostAndFoundModals.vue";
import PublicDashboardPage from "../components/public/pages/OverviewPage.vue";
import PublicLostPage from "../components/public/pages/LostAndFoundPage.vue";
import PublicRepairPage from "../components/public/pages/RepairRequestPage.vue";
import PublicCleanPage from "../components/public/pages/CleaningRequestPage.vue";
import { usePublicServicePortal } from "../view-logic/usePublicServicePortal.js";

usePublicServicePortal();
</script>

<template>
  <div class="user-page">
    <svg class="svg-sprite" aria-hidden="true" focusable="false">
      <symbol id="i-menu" viewBox="0 0 24 24">
        <path d="M4 7h16M4 12h16M4 17h16" />
      </symbol>
      <symbol id="i-user" viewBox="0 0 24 24">
        <circle cx="12" cy="8" r="4" />
        <path d="M4 21a8 8 0 0 1 16 0" />
      </symbol>
      <symbol id="i-pin" viewBox="0 0 24 24">
        <path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" />
        <circle cx="12" cy="10" r="2.5" />
      </symbol>
      <symbol id="i-qr" viewBox="0 0 24 24">
        <path
          d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h2v2h-2zM18 14h2v6h-4v-2h-2"
        />
      </symbol>
      <symbol id="i-tools" viewBox="0 0 24 24">
        <path
          d="m14.7 6.3 3-3a5 5 0 0 1-6.4 6.4l-6.7 6.7a2 2 0 0 0 3 3l6.7-6.7a5 5 0 0 0 6.4-6.4l-3 3-3-3Z"
        />
        <path d="m5 4 4 4" />
      </symbol>
      <symbol id="i-broom" viewBox="0 0 24 24">
        <path d="m14 11 6-8M12 10l4 3-5 8H4l5-11zM7 16h6M6 19h5" />
      </symbol>
      <symbol id="i-box" viewBox="0 0 24 24">
        <path d="m3 7 9-4 9 4-9 4-9-4Z" />
        <path d="m3 7 9 4 9-4v10l-9 4-9-4V7Zm9 4v10" />
      </symbol>
      <symbol id="i-search" viewBox="0 0 24 24">
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-4-4" />
      </symbol>
      <symbol id="i-home" viewBox="0 0 24 24">
        <path d="m3 11 9-8 9 8v9h-6v-6H9v6H3z" />
      </symbol>
      <symbol id="i-history" viewBox="0 0 24 24">
        <path d="M3 12a9 9 0 1 0 3-6.7L3 8" />
        <path d="M3 3v5h5M12 7v5l3 2" />
      </symbol>
      <symbol id="i-plus" viewBox="0 0 24 24">
        <path d="M12 5v14M5 12h14" />
      </symbol>
      <symbol id="i-megaphone" viewBox="0 0 24 24">
        <path
          d="M3 11v2a2 2 0 0 0 2 2h3l9 4V5L8 9H5a2 2 0 0 0-2 2ZM8 15l1 5h3"
        />
        <path d="M21 9v6" />
      </symbol>
      <symbol id="i-chevron" viewBox="0 0 24 24">
        <path d="m9 18 6-6-6-6" />
      </symbol>
      <symbol id="i-upload" viewBox="0 0 24 24">
        <path d="M12 16V4m0 0L7 9m5-5 5 5M4 16v4h16v-4" />
      </symbol>
      <symbol id="i-close" viewBox="0 0 24 24">
        <path d="m6 6 12 12M18 6 6 18" />
      </symbol>
      <symbol id="i-camera" viewBox="0 0 24 24">
        <path d="M4 7h3l2-3h6l2 3h3v13H4z" />
        <circle cx="12" cy="13" r="4" />
      </symbol>
      <symbol id="i-check" viewBox="0 0 24 24">
        <path d="m5 12 4 4L19 6" />
      </symbol>
      <symbol id="i-edit" viewBox="0 0 24 24">
        <path d="m4 20 4.5-1 10-10a2.1 2.1 0 0 0-3-3l-10 10L4 20Z" />
        <path d="m14 7 3 3" />
      </symbol>
      <symbol id="i-logout" viewBox="0 0 24 24">
        <path d="M10 5H5v14h5M14 8l4 4-4 4M8 12h10" />
      </symbol>
    </svg>
    <div class="loading-mask" role="status" aria-label="กำลังโหลด">
      <div class="loading-card">
        <span class="skeleton"></span><span class="skeleton"></span
        ><span class="skeleton"></span>
      </div>
    </div>
    <div class="app-shell">
      <aside class="sidebar" id="sidebar">
        <div class="brand">
          <div class="brand-mark">BC</div>
          <div><strong>Building Care</strong><span>ศูนย์บริการอาคาร</span></div>
        </div>
        <p class="nav-label">เมนูบริการ</p>
        <nav class="nav-list" aria-label="เมนูหลัก">
          <button type="button" class="nav-item active" data-page="dashboard">
            <span class="nav-dot"></span>ภาพรวม
          </button>
          <button type="button" class="nav-item" data-page="lost">
            <span class="nav-dot"></span>ของหาย–ของได้คืน
          </button>
          <button type="button" class="nav-item" data-page="repair">
            <span class="nav-dot"></span>แจ้งซ่อม
          </button>
          <button type="button" class="nav-item" data-page="clean">
            <span class="nav-dot"></span>แจ้งทำความสะอาด
          </button>
        </nav>
        <div class="sidebar-note">
          <strong>ไม่ต้องเข้าสู่ระบบ</strong
          >ผู้ใช้งานสามารถส่งเรื่องได้โดยไม่ต้องมีบัญชี
          และติดตามสถานะด้วยรหัสคำร้อง + อีเมล
        </div>
      </aside>
      <button
        type="button"
        class="sidebar-backdrop"
        id="sidebarBackdrop"
        aria-label="ปิดเมนู"
      ></button>

      <main>
        <div class="pull-indicator">↓ ดึงลงเพื่อรีเฟรช</div>
        <div class="topbar">
          <button
            type="button"
            class="mobile-menu"
            id="menuButton"
            aria-label="เปิดเมนู"
          >
            <svg class="icon"><use href="#i-menu" /></svg>
          </button>
          <div></div>
          <div class="date-chip">
            อาคาร วิทยาศาสตร์คอมพิวเตอร์ (CS) · เปิดบริการ 08:00–18:00
          </div>
        </div>

        <PublicDashboardPage />

        <PublicLostPage />

        <PublicRepairPage />

        <PublicCleanPage />
      </main>
      <nav class="bottom-nav" aria-label="เมนูด้านล่าง">
        <button
          type="button"
          class="active"
          data-go="dashboard"
          data-bottom-page="dashboard"
        >
          <span class="nav-glyph"
            ><svg class="icon"><use href="#i-home" /></svg></span
          ><span>หน้าหลัก</span>
        </button>
        <button type="button" data-go="repair" data-bottom-page="repair">
          <span class="nav-glyph"
            ><svg class="icon"><use href="#i-tools" /></svg></span
          ><span>แจ้งซ่อม</span>
        </button>
        <button type="button" data-go="clean" data-bottom-page="clean">
          <span class="nav-glyph"
            ><svg class="icon"><use href="#i-broom" /></svg></span
          ><span>แจ้งทำความสะอาด</span>
        </button>
        <button
          type="button"
          data-go="lost"
          data-lost-tab="report-lost"
          data-bottom-page="lost"
        >
          <span class="nav-glyph"
            ><svg class="icon"><use href="#i-box" /></svg></span
          ><span>แจ้งของหาย</span>
        </button>
        <button type="button" data-scroll-track>
          <span class="nav-glyph"
            ><svg class="icon"><use href="#i-history" /></svg></span
          ><span>ติดตามสถานะงาน</span>
        </button>
      </nav>









      <div
        class="toast-message"
        id="toastMessage"
        role="status"
        aria-live="polite"
      ></div>
      <div class="offline-banner" role="status">
        ขณะนี้ออฟไลน์ · คำขอจะถูกส่งเมื่อเชื่อมต่ออีกครั้ง
      </div>
    </div>
    <PublicLostFoundModals />
    <PublicCommonModals />
  </div>
</template>

<style src="../styles/views/index.css"></style>
