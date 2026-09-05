<script setup>
import CommonModals from "./CommonModals.vue";
import JobModals from "./JobModals.vue";
import MyWorkHistoryPage from "./MyWorkHistoryPage.vue";
import OverviewPage from "./OverviewPage.vue";
import RepairWorkQueuePage from "./RepairWorkQueuePage.vue";
</script>

<template>
  <OverviewPage />
  <RepairWorkQueuePage />
  <MyWorkHistoryPage />
  <JobModals />
  <CommonModals />
</template>
