<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import {
  fetchAdminClerkAnnouncements,
  fetchAdminClerkOverview,
} from "../../../services/adminClerkOverviewApi.js";

const dateFrom = ref("");
const dateTo = ref("");
const announcementType = ref("");
const overview = ref(null);
const loading = ref(true);
const errorMessage = ref("");
const errorStatus = ref(null);
const detailOpen = ref(false);
const detailMetric = ref("total");
const detailLoading = ref(false);
const detailError = ref("");
const detailErrorStatus = ref(null);
const detailItems = ref([]);
const detailTotal = ref(0);
const selectedRequestId = ref(null);
const appliedFilters = ref({ dateFrom: "", dateTo: "", announcementType: "" });
const dialogClose = ref(null);
let overviewRequest = 0;
let detailRequest = 0;
let lastTrigger = null;

const filtersDirty = computed(() =>
  dateFrom.value !== appliedFilters.value.dateFrom ||
  dateTo.value !== appliedFilters.value.dateTo ||
  announcementType.value !== appliedFilters.value.announcementType,
);
const dateError = computed(() =>
  dateFrom.value && dateTo.value && dateFrom.value > dateTo.value
    ? "วันเริ่มต้นต้องไม่เกินวันสิ้นสุด"
    : "",
);
const filters = () => ({
  dateFrom: dateFrom.value,
  dateTo: dateTo.value,
  announcementType: announcementType.value,
});
const summary = computed(() => overview.value?.summary);
const hasAppliedFilters = computed(() => Boolean(
  appliedFilters.value.dateFrom || appliedFilters.value.dateTo || appliedFilters.value.announcementType,
));
const decided = computed(() => (summary.value?.approved || 0) + (summary.value?.rejected || 0));
const rate = (count) => decided.value ? `${Math.round(count / decided.value * 100)}%` : "—";
const formatHours = (hours) => hours === null || hours === undefined
  ? "—"
  : hours < 24 ? `${Math.round(hours * 10) / 10} ชม.` : `${Math.round(hours / 24 * 10) / 10} วัน`;
const typeLabel = (type) => type === "found" ? "ของที่พบ" : "ประกาศของหาย";
const statusLabel = (status) => ({
  pending: "รอตรวจสอบ",
  approved: "อนุมัติ",
  rejected: "ไม่อนุมัติ",
  claimed: "รับคืนแล้ว",
  closed: "ปิดรายการ",
})[status] || status;
const metricLabels = {
  total: "รายการทั้งหมด",
  approved: "อนุมัติแล้ว",
  rejected: "ไม่อนุมัติ",
  pending_review: "รอตรวจสอบ",
};

async function loadOverview() {
  if (dateError.value) return;
  const request = ++overviewRequest;
  loading.value = true;
  errorMessage.value = "";
  errorStatus.value = null;
  overview.value = null;
  try {
    const result = await fetchAdminClerkOverview(appliedFilters.value);
    if (!result?.summary || !result?.by_announcement_type) throw new Error("Invalid overview response");
    if (request === overviewRequest) overview.value = result;
  } catch (error) {
    if (request !== overviewRequest) return;
    errorStatus.value = error.status || null;
    errorMessage.value = error.status === 401
      ? "เซสชันหมดอายุ กรุณาเข้าสู่ระบบอีกครั้ง"
      : "ไม่สามารถโหลดภาพรวมงานอนุมัติได้ กรุณาลองใหม่";
  } finally {
    if (request === overviewRequest) loading.value = false;
  }
}

function applyFilters() {
  if (dateError.value) return;
  closeDetail();
  appliedFilters.value = filters();
  loadOverview();
}
function clearFilters() {
  dateFrom.value = "";
  dateTo.value = "";
  announcementType.value = "";
  applyFilters();
}
async function openDetail(metric, trigger) {
  lastTrigger = trigger;
  detailMetric.value = metric;
  detailOpen.value = true;
  detailLoading.value = true;
  detailError.value = "";
  detailErrorStatus.value = null;
  detailItems.value = [];
  detailTotal.value = 0;
  selectedRequestId.value = null;
  const request = ++detailRequest;
  await nextTick();
  dialogClose.value?.focus();
  try {
    const result = await fetchAdminClerkAnnouncements(metric, appliedFilters.value);
    if (request !== detailRequest) return;
    detailItems.value = result.announcements || [];
    detailTotal.value = result.total || 0;
  } catch (error) {
    if (request !== detailRequest) return;
    detailErrorStatus.value = error.status || null;
    detailError.value = error.status === 401
      ? "เซสชันหมดอายุ กรุณาเข้าสู่ระบบอีกครั้ง"
      : "ไม่สามารถโหลดรายการได้ กรุณาลองใหม่";
  } finally {
    if (request === detailRequest) detailLoading.value = false;
  }
}
function toggleRequest(item) {
  selectedRequestId.value = selectedRequestId.value === item.id ? null : item.id;
}
function closeDetail() {
  detailRequest += 1;
  detailOpen.value = false;
  if (lastTrigger?.isConnected) lastTrigger.focus();
}
function onKeydown(event) {
  if (event.key === "Escape" && detailOpen.value) closeDetail();
}
onMounted(() => {
  window.addEventListener("keydown", onKeydown);
  window.addEventListener("clerk-approvals:refresh", loadOverview);
  loadOverview();
});
onBeforeUnmount(() => {
  overviewRequest += 1;
  detailRequest += 1;
  window.removeEventListener("keydown", onKeydown);
  window.removeEventListener("clerk-approvals:refresh", loadOverview);
});
</script>

<template>
  <section class="clerk-admin-overview" id="clerkApprovalsOverview">
    
    <form class="clerk-admin-filters" @submit.prevent="applyFilters">
      <label>ตั้งแต่วันที่ <input v-model="dateFrom" class="field-compact" type="date" :max="dateTo || undefined" /></label>
      <label>ถึงวันที่ <input v-model="dateTo" class="field-compact" type="date" :min="dateFrom || undefined" /></label>
      <label>ประเภทประกาศ
        <select v-model="announcementType" class="field-compact">
          <option value="">ทุกประเภท</option>
          <option value="found">ของที่พบ</option>
          <option value="lost">ประกาศของหาย</option>
        </select>
      </label>
      <button class="primary" type="submit" :disabled="Boolean(dateError)">แสดงผล</button>
      <button class="secondary" type="button" @click="clearFilters">ล้างตัวกรอง</button>
    </form>
    <p class="clerk-admin-filter-note">ตัวกรองนี้ใช้กับภาพรวมการอนุมัติเท่านั้น · ช่วงวันที่อ้างอิงวันที่ส่งประกาศตามเวลา UTC<span v-if="filtersDirty"> · กด “แสดงผล” เพื่อใช้ตัวกรองที่เลือก</span></p>
    <div v-if="dateError" class="clerk-admin-state clerk-admin-error" role="alert">{{ dateError }}</div>
    <div v-else-if="loading" class="clerk-admin-state" role="status">กำลังโหลดภาพรวมงานอนุมัติ…</div>
    <div v-else-if="errorMessage" class="clerk-admin-state" role="alert">
      {{ errorMessage }} <button v-if="errorStatus !== 401" class="small-btn" type="button" @click="loadOverview">ลองใหม่</button>
    </div>
    <template v-else-if="summary">
      <div v-if="summary.total === 0" class="clerk-admin-state clerk-admin-empty" role="status">
        <strong>{{ hasAppliedFilters ? 'ไม่พบรายการที่ตรงกับตัวกรอง' : 'ยังไม่มีประกาศของหายหรือของที่พบในระบบ' }}</strong>
        <p>{{ hasAppliedFilters ? 'ลองเปลี่ยนช่วงวันที่หรือประเภทประกาศ' : 'สถิติจะปรากฏเมื่อมีรายการส่งเข้าระบบ' }}</p>
        <button v-if="hasAppliedFilters" class="secondary" type="button" @click="clearFilters">ล้างตัวกรอง</button>
      </div>
      <div class="clerk-admin-metrics">
        <button v-for="metric in ['total', 'approved', 'rejected', 'pending_review']" :key="metric"
          class="metric clerk-admin-metric" type="button" @click="openDetail(metric, $event.currentTarget)">
          <span>{{ metricLabels[metric] }}</span>
          <strong>{{ metric === 'pending_review' ? summary.pending_review : summary[metric] }}</strong>
          <small>ดูรายการ →</small>
        </button>
      </div>
      
    </template>
  </section>

  <Teleport to="body">
    <div v-if="detailOpen" class="clerk-admin-overlay" @click.self="closeDetail">
      <section class="clerk-admin-dialog" role="dialog" aria-modal="true" aria-labelledby="clerkAdminDetailTitle">
        <header>
          <div><h3 id="clerkAdminDetailTitle">{{ metricLabels[detailMetric] }}</h3><p>{{ detailLoading ? 'กำลังโหลด…' : detailError ? 'โหลดไม่สำเร็จ' : `${detailTotal} รายการ` }}</p></div>
          <button ref="dialogClose" class="secondary" type="button" aria-label="ปิดรายการ" @click="closeDetail">ปิด</button>
        </header>
        <div v-if="detailLoading" class="clerk-admin-state" role="status">กำลังโหลดรายการ…</div>
        <div v-else-if="detailError" class="clerk-admin-state" role="alert">
          {{ detailError }} <button v-if="detailErrorStatus !== 401" class="small-btn" type="button" @click="openDetail(detailMetric, lastTrigger)">ลองใหม่</button>
        </div>
        <div v-else-if="!detailItems.length" class="clerk-admin-state" role="status">ไม่มีรายการ “{{ metricLabels[detailMetric] }}” ในช่วงที่เลือก</div>
        <div v-else class="clerk-admin-item-list">
          <article v-for="item in detailItems" :key="item.id">
            <div><strong>{{ item.item_code }}</strong><span>{{ typeLabel(item.announcement_type) }} · {{ statusLabel(item.status) }}</span></div>
            <div><time :datetime="item.submission_date">{{ new Date(item.submission_date).toLocaleString('th-TH') }}</time><small v-if="item.pending_review_age_hours !== null">รอ {{ formatHours(item.pending_review_age_hours) }}</small></div>
            <button class="small-btn" type="button" :aria-expanded="selectedRequestId === item.id" @click="toggleRequest(item)">
              {{ selectedRequestId === item.id ? 'ซ่อนข้อมูล' : 'ดูข้อมูลคำขอ' }}
            </button>
            <div v-if="selectedRequestId === item.id" class="clerk-admin-request-details">
              <div><span>รหัสรายการ</span><strong>{{ item.item_code }}</strong></div>
              <div><span>ประเภท</span><strong>{{ typeLabel(item.announcement_type) }}</strong></div>
              <div><span>สถานะ</span><strong>{{ statusLabel(item.status) }}</strong></div>
              <div><span>วันที่ส่ง</span><strong>{{ new Date(item.submission_date).toLocaleString('th-TH') }}</strong></div>
              <div v-if="item.pending_review_age_hours !== null"><span>เวลาที่รอตรวจสอบ</span><strong>{{ formatHours(item.pending_review_age_hours) }}</strong></div>
            </div>
          </article>
        </div>
      </section>
    </div>
  </Teleport>
</template>
