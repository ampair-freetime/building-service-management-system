<script setup>
<<<<<<< HEAD
import LocationCombobox from "../LocationCombobox.vue";

const floorSuggestions = ["ชั้น 1", "ชั้น 2", "ชั้น 3"];
const roomSuggestions = [
  "ห้องน้ำ",
  "โถงทางเดิน",
  "พื้นที่ส่วนกลาง",
  "CSB201",
  "CSB307",
  "CSB209",
];
=======
import { computed, onMounted, ref } from "vue";

import {
  createCleaningRequest,
  listCleaningLocations,
  resolveCleaningLocation,
} from "../../../services/api";

const locations = ref([]);
const locationId = ref("");
const qrLocation = ref(null);
const qrMessage = ref("");
const loadingLocations = ref(true);
const submitting = ref(false);
const errorMessage = ref("");
const createdRequest = ref(null);
const formElement = ref(null);

const qrLocationLabel = computed(() => formatLocation(qrLocation.value));

function formatLocation(location) {
  if (!location) return "";
  return [
    location.building,
    location.floor ? `ชั้น ${location.floor}` : "",
    location.room ? `ห้อง ${location.room}` : "",
    location.area_type,
  ].filter(Boolean).join(" ");
}

async function loadLocations() {
  loadingLocations.value = true;
  errorMessage.value = "";
  try {
    locations.value = await listCleaningLocations();
    const token = new URLSearchParams(window.location.search).get("token");
    if (!token) return;
    const resolved = await resolveCleaningLocation(token);
    if (resolved) {
      qrLocation.value = resolved;
      locationId.value = String(resolved.id);
    } else {
      qrMessage.value = "QR ไม่ถูกต้องหรือสถานที่ปิดใช้งาน กรุณาเลือกสถานที่";
    }
  } catch (error) {
    errorMessage.value = error.message || "ไม่สามารถโหลดสถานที่ได้";
  } finally {
    loadingLocations.value = false;
  }
}

function chooseAnotherLocation() {
  qrLocation.value = null;
  document.getElementById("cleanLocation")?.focus();
}

async function submitCleaning(event) {
  const form = event.currentTarget;
  if (submitting.value || !form.reportValidity()) return;
  submitting.value = true;
  errorMessage.value = "";
  createdRequest.value = null;
  try {
    const formData = new FormData(form);
    const image = formData.get("image");
    if (!image || !image.name) formData.delete("image");
    const response = await createCleaningRequest(formData);
    createdRequest.value = response;
    form.reset();
    locationId.value = qrLocation.value ? String(qrLocation.value.id) : "";
    form.querySelector(".remove-image")?.click();
  } catch (error) {
    errorMessage.value = error.message || "ไม่สามารถส่งคำขอทำความสะอาดได้";
  } finally {
    submitting.value = false;
  }
}

onMounted(loadLocations);
>>>>>>> 77d1c05 (feat(cleaning): add guest QR request flow)
</script>

<template>
  <section class="page" id="clean" data-theme="clean">
    <header class="page-header clean-page-header">
      <svg class="clean-illustration" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <use href="#i-broom" />
      </svg>
      <div><div class="eyebrow">Cleaning request</div><h2>แจ้งทำความสะอาด</h2></div>
    </header>
    <div class="work-layout single-form-layout">
      <form ref="formElement" class="form-panel" @submit.prevent="submitCleaning">
        <h3>ขอทำความสะอาดพื้นที่</h3>

        <div v-if="qrLocation" class="clean-feedback success" role="status">
          สถานที่จาก QR: {{ qrLocationLabel }}
          <button type="button" @click="chooseAnotherLocation">เปลี่ยน</button>
        </div>
        <p v-else-if="qrMessage" class="clean-feedback error" role="status">{{ qrMessage }}</p>

        <div class="field">
          <label for="cleanLocation">สถานที่</label>
          <select id="cleanLocation" v-model="locationId" name="location_id" required :disabled="loadingLocations">
            <option value="">{{ loadingLocations ? "กำลังโหลดสถานที่..." : "เลือกสถานที่" }}</option>
            <option v-for="location in locations" :key="location.id" :value="String(location.id)">
              {{ formatLocation(location) }}
            </option>
          </select>
        </div>
        <div class="field">
          <label for="cleanTitle">ปัญหาที่พบ</label>
          <input id="cleanTitle" name="title" type="text" required maxlength="200" placeholder="เช่น ขยะสะสม คราบหกเลอะ" />
        </div>
        <div class="field">
          <label for="cleanPriority">ความเร่งด่วน</label>
          <select id="cleanPriority" name="priority">
            <option value="normal">ปกติ</option>
            <option value="urgent">เร่งด่วน</option>
          </select>
        </div>
        <div class="field">
          <label for="cleanDescription">รายละเอียด (ถ้ามี)</label>
          <textarea id="cleanDescription" name="description" maxlength="255" placeholder="บอกลักษณะพื้นที่ที่ต้องการให้ดูแล"></textarea>
        </div>
        <div class="field">
          <label>รูปภาพพื้นที่ (ถ้ามี)</label>
          <div class="upload-field">
            <label class="upload-trigger">
              <input type="file" name="image" class="image-input" accept="image/jpeg,image/png,image/webp" data-max-size="5242880" data-error-id="cleanImageError" />
              <span class="upload-icon">＋</span>
              <span class="upload-copy"><strong>เลือกรูปภาพ</strong><small>JPG, PNG หรือ WebP ไม่เกิน 5 MB</small></span>
            </label>
            <div class="image-preview">
              <img alt="ตัวอย่างรูปที่แนบ" /><span class="image-file-name"></span>
              <button type="button" class="remove-image">ลบ</button>
            </div>
<<<<<<< HEAD
          </header>
          <div class="work-layout single-form-layout">
            <form class="form-panel" data-submit-type="แจ้งทำความสะอาด">
              <h3>ขอทำความสะอาดพื้นที่</h3>
              <div class="form-row clean-location-row">
                <LocationCombobox
                  id="cleanFloor"
                  name="clean_floor"
                  label="ชั้น"
                  placeholder="เลือกชั้น"
                  :options="floorSuggestions"
                  required
                />
                <LocationCombobox
                  id="cleanRoom"
                  name="clean_room"
                  label="ห้อง"
                  placeholder="เลือกห้อง"
                  :options="roomSuggestions"
                  required
                />
              </div>
              <div class="field">
                <label>ปัญหาที่พบ</label
                ><input
                  type="text"
                  required
                  placeholder="เช่น ขยะสะสม คราบหกเลอะ"
                />
              </div>
              <div class="field">
                <label>ประเภทงาน</label
                ><select required>
                  <option>ทำความสะอาดทั่วไป</option>
                  <option>เหตุเร่งด่วน</option>
                </select>
              </div>
              <div class="field">
                <label>รายละเอียด (ถ้ามี)</label
                ><textarea
                  required
                  placeholder="บอกตำแหน่งและลักษณะพื้นที่ที่ต้องการให้ดูแล"
                ></textarea>
              </div>
              <div class="field">
                <label>รูปภาพพื้นที่</label>
                <div class="upload-field">
                  <label class="upload-trigger"
                    ><input
                      type="file"
                      class="image-input"
                      accept="image/jpeg,image/png,image/webp"
                      data-max-size="5242880"
                    /><span class="upload-icon">＋</span
                    ><span class="upload-copy"
                      ><strong>เลือกรูปภาพ</strong
                      ><small>JPG, PNG หรือ WebP ไม่เกิน 5 MB</small></span
                    ></label
                  >
                  <div class="image-preview">
                    <img
                      src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs="
                      alt="ตัวอย่างรูปที่แนบ"
                    /><span></span
                    ><button type="button" class="remove-image">ลบ</button>
                  </div>
                </div>
              </div>
              <div class="field">
                <label>อีเมลสำหรับติดตามสถานะ</label
                ><input
                  type="email"
                  name="recipient_email"
                  required
                  placeholder="name@example.com"
                  autocomplete="email"
                />
              </div>
              <button type="submit" class="submit-btn">
                ส่งคำขอทำความสะอาด
              </button>
            </form>
=======
            <small id="cleanImageError" class="field-error"></small>
>>>>>>> 77d1c05 (feat(cleaning): add guest QR request flow)
          </div>
        </div>
        <div class="field">
          <label for="cleanEmail">อีเมลสำหรับติดตามสถานะ</label>
          <input id="cleanEmail" type="email" name="reporter_email" required maxlength="255" placeholder="name@example.com" autocomplete="email" />
        </div>
        <p v-if="errorMessage" class="clean-feedback error" role="alert">{{ errorMessage }}</p>
        <div v-if="createdRequest" class="clean-feedback success" role="status">
          รับคำร้องแล้ว รหัสติดตาม: <strong>{{ createdRequest.request_code }}</strong>
        </div>
        <button type="submit" class="submit-btn" :disabled="submitting || loadingLocations">
          {{ submitting ? "กำลังส่งคำขอ..." : "ส่งคำขอทำความสะอาด" }}
        </button>
      </form>
    </div>
  </section>
</template>

<style scoped>
.clean-feedback { margin: 0 0 16px; padding: 12px 14px; border-radius: 12px; }
.clean-feedback.success { background: #ecfdf3; color: #166534; }
.clean-feedback.error { background: #fef2f2; color: #991b1b; }
.clean-feedback button { margin-left: 8px; text-decoration: underline; }
</style>
