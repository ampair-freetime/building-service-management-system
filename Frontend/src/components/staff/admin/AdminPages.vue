<script setup>
import AdminModals from "./AdminModals.vue";
import AllWorkQueuePage from "./AllWorkQueuePage.vue";
import AnnouncementsPage from "./AnnouncementsPage.vue";
import CommonModals from "./CommonModals.vue";
import JobModals from "./JobModals.vue";
import LostAndFoundManagementPage from "./LostAndFoundManagementPage.vue";
import LostAndFoundModals from "./LostAndFoundModals.vue";
import OverviewPage from "./OverviewPage.vue";
import RoomQrPage from "./RoomQrPage.vue";
import StaffAccountsPage from "./StaffAccountsPage.vue";
import StaffWorkOverviewPage from "./StaffWorkOverviewPage.vue";
import SystemHistoryPage from "./SystemHistoryPage.vue";
</script>

<template>
  <OverviewPage />
  <AllWorkQueuePage />
  <LostAndFoundManagementPage />
  <StaffWorkOverviewPage />
  <StaffAccountsPage />
  <SystemHistoryPage />
  <RoomQrPage />
  <AnnouncementsPage />
  <JobModals />
  <LostAndFoundModals />
  <AdminModals />
  <CommonModals />
</template>
