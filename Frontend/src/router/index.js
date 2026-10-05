import { createRouter, createWebHistory } from "vue-router";

import PublicServicePortal from "../views/PublicServicePortal.vue";
import StaffLogin from "../views/staff-login.vue";
import StaffPasswordSetup from "../views/staff-password-setup.vue";
import StaffResetPassword from "../views/staff-reset-password.vue";
import StaffDashboard from "../views/staff-dashboard.vue";
import MobileDemo from "../views/MobileDemo.vue";

const routes = [

  // ผู้ใช้งานทั่วไป -> ไม่ต้อง Login
  {
    path: "/user",
    name: "user",
    component: PublicServicePortal,
  },
  {
    path: "/cleaning",
    redirect: (to) => ({ path: "/user", query: { ...to.query, service: "clean" } }),
  },
  {
    path: "/repair",
    redirect: (to) => ({ path: "/user", query: { ...to.query, service: "repair" } }),
  },

  // เจ้าหน้าที่ -> Login
  {
    path: "/staff-login",
    name: "staff-login",
    component: StaffLogin,
  },
  {
    path: "/staff/setup-password",
    name: "staff-password-setup",
    component: StaffPasswordSetup,
  },
  {
    // เปิดจากลิงก์ในอีเมล จึงต้องเข้าได้โดยไม่ต้อง login
    path: "/staff/reset-password",
    name: "staff-reset-password",
    component: StaffResetPassword,
  },

  // Dashboard เจ้าหน้าที่
  {
    path: "/staff-dashboard",
    name: "staff-dashboard",
    component: StaffDashboard,
    meta: { requiresAuth: true },
  },

  {
    path: "/admin-dashboard",
    name: "admin-dashboard",
    component: StaffDashboard,
    meta: { requiresAuth: true },
  },

  // Mobile Demo สำหรับนำเสนอ Client
  {
    path: "/demo",
    name: "mobile-demo",
    component: MobileDemo,
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

router.beforeEach((to) => {
  if (to.meta.requiresAuth) {
    const token = localStorage.getItem("buildingCareAccessToken");

    if (!token) {
      return "/staff-login";
    }
  }
});

export default router;
