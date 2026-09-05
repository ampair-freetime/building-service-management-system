<script setup>
import CommonModals from "./CommonModals.vue";
import ClerkCenterPage from "./ClerkCenterPage.vue";
import LostAndFoundManagementPage from "./LostAndFoundManagementPage.vue";
import LostAndFoundModals from "./LostAndFoundModals.vue";
import FoundItemDetailModal from "./FoundItemDetailModal.vue";
import MyWorkHistoryPage from "./MyWorkHistoryPage.vue";
import OverviewPage from "./OverviewPage.vue";
</script>

<template>
  <OverviewPage />
  <ClerkCenterPage />
  <LostAndFoundManagementPage />
  <MyWorkHistoryPage />
  <LostAndFoundModals />
  <FoundItemDetailModal />
  <CommonModals />
</template>
