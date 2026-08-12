import { createRouter, createWebHistory } from "vue-router";

import HomeView from "../views/index.vue";
import StaffLogin from "../views/staff-login.vue";
import StaffDashboard from "../views/staff-dashboard.vue";

const routes = [

  // ผู้ใช้งานทั่วไป -> ไม่ต้อง Login
  {
    path: "/user",
    name: "user",
    component: HomeView,
  },

  // เจ้าหน้าที่ -> Login
  {
    path: "/staff-login",
    name: "staff-login",
    component: StaffLogin,
  },

  // Dashboard เจ้าหน้าที่
  {
    path: "/staff-dashboard",
    name: "staff-dashboard",
    component: StaffDashboard,
  },
  
  {
    path: "/admin-dashboard",
    name: "admin-dashboard",
    component: StaffDashboard,
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

router.beforeEach((to) => {
  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('access_token')

    if (!token) {
      return '/staff-login'
    }
  }
})

export default router;
