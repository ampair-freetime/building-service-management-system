<script setup>
import AdminPages from "../components/staff/admin/AdminPages.vue";
import ClerkPages from "../components/staff/clerk/ClerkPages.vue";
import HousekeeperPages from "../components/staff/housekeeper/HousekeeperPages.vue";
import TechnicianPages from "../components/staff/technician/TechnicianPages.vue";
import { useStaffDashboard } from "../view-logic/useStaffDashboard.js";

const { activeRole } = useStaffDashboard();
</script>

<template>
  <div
    class="staff-dashboard-page"
    :class="{ 'is-admin': activeRole === 'admin' }"
  >
    <div class="toast" id="toast" role="status" aria-live="polite"></div>
    <svg
      aria-hidden="true"
      width="0"
      height="0"
      style="position: absolute; overflow: hidden"
    >
      <symbol id="i-menu" viewBox="0 0 24 24">
        <path d="M4 7h16M4 12h16M4 17h16" />
      </symbol>
      <symbol id="i-bell" viewBox="0 0 24 24">
        <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M14 21h-4" />
      </symbol>
      <symbol id="i-user" viewBox="0 0 24 24">
        <circle cx="12" cy="8" r="4" />
        <path d="M4 21a8 8 0 0 1 16 0" />
      </symbol>
      <symbol id="i-home" viewBox="0 0 24 24">
        <path d="m3 11 9-8 9 8v9h-6v-6H9v6H3z" />
      </symbol>
      <symbol id="i-list" viewBox="0 0 24 24">
        <path d="M9 6h11M9 12h11M9 18h11M4 6h.01M4 12h.01M4 18h.01" />
      </symbol>
      <symbol id="i-plus" viewBox="0 0 24 24">
        <path d="M12 5v14M5 12h14" />
      </symbol>
      <symbol id="i-history" viewBox="0 0 24 24">
        <path d="M3 12a9 9 0 1 0 3-6.7L3 8M3 3v5h5M12 7v5l3 2" />
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
        <path d="m3 7 9-4 9 4-9 4-9-4ZM3 7l9 4 9-4v10l-9 4-9-4V7Zm9 4v10" />
      </symbol>
      <symbol id="i-qr" viewBox="0 0 24 24">
        <path d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h2v2h-2zM18 14h2v6h-4v-2h-2" />
      </symbol>
      <symbol id="i-close" viewBox="0 0 24 24">
        <path d="m6 6 12 12M18 6 6 18" />
      </symbol>
      <symbol id="i-check" viewBox="0 0 24 24">
        <path d="m5 12 4 4L19 6" />
      </symbol>
      <symbol id="i-upload" viewBox="0 0 24 24">
        <path d="M12 16V4m0 0L7 9m5-5 5 5M4 16v4h16v-4" />
      </symbol>
      <symbol id="i-chevron" viewBox="0 0 24 24">
        <path d="m9 18 6-6-6-6" />
      </symbol>
      <symbol id="i-log-out" viewBox="0 0 24 24">
        <path d="M10 5H5v14h5M14 8l4 4-4 4M8 12h10" />
      </symbol>
      <symbol id="i-trash" viewBox="0 0 24 24">
        <path d="M4 7h16M9 7V4h6v3m3 0-1 13H7L6 7m4 4v5m4-5v5" />
      </symbol>
      <symbol id="i-megaphone" viewBox="0 0 24 24">
        <path
          d="M3 11v2a2 2 0 0 0 2 2h3l9 4V5L8 9H5a2 2 0 0 0-2 2ZM8 15l1 5h3M21 9v6"
        />
      </symbol>
    </svg>
    <div class="loading-mask" aria-label="กำลังโหลด">
      <div class="loading-card">
        <span class="skeleton"></span><span class="skeleton"></span
        ><span class="skeleton"></span>
      </div>
    </div>
    <div class="app">
      <aside class="sidebar" id="sidebar">
        <div class="brand">
          <div class="brand-mark">BC</div>
          <div>
            <strong>CS Building Care</strong><span>Staff operations portal</span>
          </div>
          <button
            type="button"
            class="sidebar-close"
            aria-label="ปิดเมนู"
          >
            <svg class="icon" aria-hidden="true"><use href="#i-close" /></svg>
          </button>
        </div>
        <nav class="nav-list" aria-label="เมนูเจ้าหน้าที่">
          <button
            v-if="activeRole !== 'admin'"
            class="nav-item active"
            data-page="dashboard"
            data-roles="housekeeper,technician,clerk"
          >
            <span class="nav-icon">01</span>ภาพรวมงาน
          </button>
          <button
            class="nav-item"
            data-page="clerk-center"
            data-roles="clerk"
          >
            <span class="nav-icon">02</span>ศูนย์รับงาน
          </button>
          <button
            v-if="activeRole !== 'admin'"
            class="nav-item"
            data-page="jobs"
            data-roles="housekeeper,technician"
          >
            <span class="nav-icon">02</span
            ><span id="jobsNavLabel">ศูนย์รับงานรวม</span>
          </button>
          <button
            v-if="['housekeeper', 'technician'].includes(activeRole)"
            class="nav-item"
            data-page="my-jobs"
            data-roles="housekeeper,technician"
          >
            <span class="nav-icon">03</span>งานของฉัน
          </button>
          <button
            class="nav-item"
            data-page="my-history"
            data-roles="housekeeper,technician,clerk"
          >
            <span class="nav-icon">H</span>ประวัติงานของฉัน
          </button>
          <button class="nav-item" data-page="staff-overview" data-roles="admin">
            <span class="nav-icon">WO</span>ภาพรวมงาน Staff
          </button>
          <button v-if="activeRole === 'clerk'" class="nav-item" data-page="lost" data-roles="clerk">
            <span class="nav-icon">03</span>ของหายและรับฝาก
          </button>
          <button class="nav-item" data-page="history" data-roles="admin">
            <span class="nav-icon">02</span>ของหายและรับฝาก
          </button>
          <button class="nav-item" data-page="staff" data-roles="admin">
            <span class="nav-icon">03</span>บัญชีเจ้าหน้าที่
          </button>
          <button class="nav-item" data-page="qr" data-roles="admin">
            <span class="nav-icon">QR</span>QR ประจำห้อง
          </button>
        </nav>
        <div class="sidebar-foot">
          <button class="logout" id="logoutBtn">ออกจากระบบ</button>
        </div>
      </aside>
      <button
        class="icon-btn menu-toggle sidebar-floating-toggle"
        id="menuToggle"
        type="button"
        aria-label="เปิดเมนู"
        aria-expanded="false"
        aria-controls="sidebar"
      >
        <svg class="icon"><use href="#i-menu" /></svg>
      </button>
      <button
        type="button"
        class="sidebar-backdrop"
        id="sidebarBackdrop"
        aria-label="ปิดเมนู"
      ></button>

      <main>
        <header class="topbar">
          
          <div class="top-actions">
            <span class="ready-pill">พร้อมปฏิบัติงาน</span>
            <div class="notification-wrap">
              <button
                class="icon-btn"
                id="notificationButton"
                aria-label="เปิดการแจ้งเตือน"
                aria-expanded="false"
              >
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  aria-hidden="true"
                >
                  <path
                    d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"
                  ></path>
                  <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                </svg>
                <span
                  class="notification-count"
                  id="notificationCount"
                  aria-live="polite"
                  hidden
                ></span>
              </button>
              <Teleport to="body">
                <section
                  class="notification-panel"
                  id="notificationPanel"
                  aria-label="รายการแจ้งเตือน"
                >
                  <div class="notification-head">
                    <h3 id="notificationTitle">การแจ้งเตือนของแอดมิน</h3>
                    <button id="markAllRead">อ่านทั้งหมดแล้ว</button>
                  </div>
                  <div class="notification-list" id="notificationList"></div>
                </section>
              </Teleport>
            </div>
            <button
              class="header-profile"
              id="profileButton"
              type="button"
              aria-label="เปิดโปรไฟล์"
            >
              <span class="avatar" id="headerAvatar">AD</span
              ><span
                ><strong id="headerName">พิมพ์ชนก</strong
                ><small id="headerRole">แอดมิน</small></span
              >
            </button>
          </div>
        </header>

        <HousekeeperPages v-if="activeRole === 'housekeeper'" />
        <TechnicianPages v-else-if="activeRole === 'technician'" />
        <ClerkPages v-else-if="activeRole === 'clerk'" />
        <AdminPages v-else />
      </main>
    </div>

    <nav
      class="bottom-nav"
      :class="{ 'admin-bottom-nav': activeRole === 'admin' }"
      aria-label="เมนูด้านล่าง"
    >
      <template v-if="activeRole === 'admin'">
        <button type="button" class="active" data-mobile-page="staff-overview">
          <svg class="icon"><use href="#i-home" /></svg><span>ภาพรวม Staff</span>
        </button>
        <button type="button" data-mobile-page="history">
          <svg class="icon"><use href="#i-box" /></svg><span>ของหาย-รับฝาก</span>
        </button>
        <button type="button" data-mobile-page="staff">
          <svg class="icon"><use href="#i-user" /></svg><span>บัญชี Staff</span>
        </button>
        <button type="button" data-mobile-page="qr">
          <svg class="icon"><use href="#i-qr" /></svg><span>QR ห้อง</span>
        </button>
      </template>
      <template v-else>
        <button type="button" class="active" data-mobile-page="dashboard">
          <svg class="icon"><use href="#i-home" /></svg><span>ภาพรวม</span>
        </button>
        <button type="button" data-mobile-page="jobs">
          <svg class="icon"><use href="#i-list" /></svg><span>งาน</span>
        </button>
        <button type="button" id="mobileNotification">
          <svg class="icon"><use href="#i-bell" /></svg><span>แจ้งเตือน</span
          ><span
            class="notification-count"
            id="mobileNotificationCount"
            aria-live="polite"
            hidden
          ></span>
        </button>
        <button type="button" id="mobileProfile">
          <svg class="icon"><use href="#i-user" /></svg><span>โปรไฟล์</span>
        </button>
      </template>
    </nav>
  </div>
</template>

<style src="../styles/views/staff-dashboard.css"></style>
