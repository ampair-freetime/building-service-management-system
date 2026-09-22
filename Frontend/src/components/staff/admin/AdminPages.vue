<script setup>
import AdminModals from "./AdminModals.vue";
import CommonModals from "./CommonModals.vue";
import JobModals from "./JobModals.vue";
import LostAndFoundModals from "./LostAndFoundModals.vue";
import RoomQrPage from "./RoomQrPage.vue";
import StaffAccountsPage from "./StaffAccountsPage.vue";
import StaffWorkOverviewPage from "./StaffWorkOverviewPage.vue";
import SystemHistoryPage from "./SystemHistoryPage.vue";
</script>

<template>
  <StaffWorkOverviewPage />
  <SystemHistoryPage />
  <StaffAccountsPage />
  <RoomQrPage />
  <JobModals />
  <LostAndFoundModals />
  <AdminModals />
  <CommonModals />
</template>
