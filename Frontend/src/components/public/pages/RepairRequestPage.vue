<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRepairSubmission } from "../../../composables/useRepairSubmission.js";
import {
  listRepairLocations,
  resolveRepairLocationByQr,
  uploadRepairRequest,
} from "../../../services/repairRequests.js";
import { mockServiceLocations } from "../../../services/mockServiceLocations.js";
import LocationCombobox from "../LocationCombobox.vue";

const priorityValues = {
  "งานซ่อมทั่วไป": "normal",
  "เหตุเร่งด่วน": "urgent",
};
const { isSubmitting, status, message, submit, markChanged } = useRepairSubmission(
  uploadRepairRequest,
);

async function submitRepair(event) {
  if (isSubmitting.value) return;
  const form = event.currentTarget;
  if (!form.checkValidity()) return;
  if (!selectedLocation.value) {
    locationError.value = "ยังระบุสถานที่จริงไม่ได้ กรุณาตรวจสอบชั้นและห้อง/สถานที่";
    return;
  }

  const payload = new FormData(form);
  payload.set("location_id", String(selectedLocation.value.id));
  payload.set("priority", priorityValues[selectedWorkType.value] || "");
  payload.delete("image");
  photos.value.forEach(({ file }) => payload.append("image", file));
  await submit(payload, (result) => {
    const recipientEmail = payload.get("reporter_email") || "";
    const submittedLocation = formatLocation(selectedLocation.value);
    const keptFloor = selectedFloor.value;
    const keptArea = selectedArea.value;
    form.reset();
    window.setTimeout(() => {
      selectedFloor.value = keptFloor;
      void nextTick().then(() => { selectedArea.value = keptArea; });
    }, 0);
    form.dispatchEvent(new CustomEvent("repair-request-confirmed", {
      bubbles: true,
      detail: {
        ...result,
        recipientEmail,
        location: submittedLocation,
        problem: payload.get("title") || "",
      },
    }));
  }, (error) => {
    if (error.status === 422 && error.message.includes("สถานที่")) {
      selectedFloor.value = "";
      selectedArea.value = "";
      qrLocation.value = null;
      qrMessage.value = "สถานที่นี้ไม่เปิดใช้งานแล้ว กรุณาเลือกสถานที่ใหม่";
      void loadLocations();
    }
  });
}

const locations = ref([]);
const selectedFloor = ref("");
const selectedArea = ref("");
const qrLocation = ref(null);
const qrMessage = ref("");
const qrRetry = ref(false);
const locationLoadError = ref("");
const selectedWorkType = ref("");
const locationError = ref("");
const photoInput = ref(null);
const photos = ref([]);
const photoErrors = ref([]);
const MAX_PHOTOS = 5;
const MAX_PHOTO_BYTES = 5 * 1024 * 1024;
const allowedTypes = ["image/jpeg", "image/png", "image/webp"];

function syncPhotoFiles() {
  if (!photoInput.value) return;
  const transfer = new DataTransfer();
  photos.value.forEach(({ file }) => transfer.items.add(file));
  photoInput.value.files = transfer.files;
}

function addPhotos(event) {
  const errors = [];
  for (const file of Array.from(event.target.files)) {
    if (!allowedTypes.includes(file.type)) {
      errors.push(`${file.name}: รองรับเฉพาะ JPG, PNG หรือ WebP`);
    } else if (file.size === 0) {
      errors.push(`${file.name}: ไฟล์ว่างเปล่า กรุณาเลือกไฟล์ใหม่`);
    } else if (file.size > MAX_PHOTO_BYTES) {
      errors.push(`${file.name}: ขนาดเกิน 5 MB`);
    } else if (photos.value.some(({ file: existing }) =>
      existing.name === file.name &&
      existing.size === file.size &&
      existing.type === file.type &&
      existing.lastModified === file.lastModified)) {
      errors.push(`${file.name}: รูปนี้ถูกแนบแล้ว`);
    } else if (photos.value.length >= MAX_PHOTOS) {
      errors.push(`${file.name}: แนบได้สูงสุด ${MAX_PHOTOS} รูป`);
    } else {
      photos.value.push({ file, url: URL.createObjectURL(file) });
    }
  }
  photoErrors.value = errors;
  syncPhotoFiles();
}

function removePhoto(index) {
  markChanged();
  URL.revokeObjectURL(photos.value[index].url);
  photos.value.splice(index, 1);
  photoErrors.value = [];
  syncPhotoFiles();
  photoInput.value?.focus();
}

function clearPhotos() {
  photos.value.forEach(({ url }) => URL.revokeObjectURL(url));
  photos.value = [];
  photoErrors.value = [];
}

onBeforeUnmount(clearPhotos);

const floorOptions = computed(() => [...new Set([
  ...mockServiceLocations.map((location) => location.floor || "ไม่ระบุชั้น"),
  ...(qrLocation.value ? [qrLocation.value.floor || "ไม่ระบุชั้น"] : []),
])].map((floor) => floor === "ไม่ระบุชั้น" ? floor : `ชั้น ${floor}`));
const areaOptions = computed(() => [...new Set([
  ...mockServiceLocations,
  ...(qrLocation.value ? [qrLocation.value] : []),
].filter((location) => (location.floor || "ไม่ระบุชั้น") === selectedFloor.value.replace(/^ชั้น /, ""))
  .map((location) => location.area))]);
const selectedLocation = computed(() => {
  const floor = selectedFloor.value.replace(/^ชั้น /, "");
  if (!floor || !selectedArea.value) return null;
  if (qrLocation.value && (qrLocation.value.floor || "ไม่ระบุชั้น") === floor &&
      qrLocation.value.area === selectedArea.value) return qrLocation.value;
  const matches = locations.value.filter((location) =>
    (location.floor || "ไม่ระบุชั้น") === floor && location.area === selectedArea.value);
  return matches.length === 1 ? matches[0] : null;
});
const isQrLocation = computed(() =>
  qrLocation.value !== null &&
  selectedFloor.value.replace(/^ชั้น /, "") === (qrLocation.value.floor || "ไม่ระบุชั้น") &&
  selectedArea.value === qrLocation.value.area,
);
const workTypeSuggestions = Object.keys(priorityValues);

function formatLocation(location) {
  if (!location) return "";
  return location.floor ? `ชั้น ${location.floor} · ${location.area}` : location.area;
}

watch(selectedFloor, () => {
  selectedArea.value = "";
  locationError.value = "";
});
watch(selectedArea, () => { locationError.value = ""; });

async function loadLocations() {
  locationLoadError.value = "";
  try {
    locations.value = await listRepairLocations();
  } catch {
    locationLoadError.value = "โหลดข้อมูลสถานที่จริงไม่สำเร็จ กรุณาลองใหม่ภายหลัง";
  }
}

async function loadQrLocation() {
  const params = new URLSearchParams(window.location.search);
  if (params.get("service") === "clean") return;
  const token = params.get("token")?.trim() ?? "";
  if (!token) return;

  qrMessage.value = "";
  qrRetry.value = false;
  if (token.length > 255) {
    qrMessage.value = "QR นี้ใช้ไม่ได้ กรุณาเลือกสถานที่เอง";
    return;
  }

  try {
    const location = await resolveRepairLocationByQr(token);
    if (!location) {
      qrMessage.value = "QR นี้ใช้ไม่ได้หรือสถานที่ถูกปิด กรุณาเลือกสถานที่เอง";
      return;
    }
    qrLocation.value = location;
    if (!selectedFloor.value && !selectedArea.value) {
      selectedFloor.value = location.floor ? `ชั้น ${location.floor}` : "ไม่ระบุชั้น";
      await nextTick();
      selectedArea.value = location.area;
      await nextTick();
      for (const id of ["repairFloor", "repairArea"]) {
        document.getElementById(id)?.dispatchEvent(new Event("change", { bubbles: true }));
      }
    }
  } catch {
    qrMessage.value = "ตรวจสอบสถานที่จาก QR ไม่สำเร็จ";
    qrRetry.value = true;
  }
}

onMounted(() => {
  void loadLocations();
  void loadQrLocation();
});
</script>

<template>
<section class="page" id="repair" data-theme="repair">
          <header class="page-header repair-page-header">
            <svg class="repair-illustration" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
              <use href="#i-tools" />
            </svg>
            <div>
              <div class="eyebrow">Repair request</div>
              <h2>แจ้งซ่อม</h2>
            </div>
          </header>
          <div class="work-layout single-form-layout">
            <form class="form-panel" novalidate data-service-validation :aria-busy="isSubmitting" @submit.prevent="submitRepair" @reset="clearPhotos" @input="markChanged" @change="markChanged">
              <fieldset class="repair-fields" :disabled="isSubmitting">
              <h3>รายละเอียดปัญหา</h3>
              <div class="form-row repair-location-row">
                <LocationCombobox
                  v-model="selectedFloor"
                  id="repairFloor"
                  label="ชั้น"
                  placeholder="ชั้น"
                  :options="floorOptions"
                  :allow-custom="false"
                  required
                />
                <LocationCombobox
                  v-model="selectedArea"
                  id="repairArea"
                  label="ห้อง/สถานที่"
                  placeholder="ห้องหรือสถานที่"
                  :options="areaOptions"
                  :allow-custom="false"
                  required
                />
                <input type="hidden" name="location_id" :value="selectedLocation?.id || ''" />
              </div>
              <p v-if="isQrLocation" class="qr-location-message" role="status" aria-live="polite">
                📍 เลือก {{ formatLocation(qrLocation) }} จาก QR แล้ว · เปลี่ยนสถานที่ได้จากรายการ
              </p>
              <p v-if="qrMessage" class="qr-location-message" role="status" aria-live="polite">
                {{ qrMessage }}
                <button v-if="qrRetry" type="button" class="secondary" @click="loadQrLocation">ลองตรวจสอบ QR อีกครั้ง</button>
              </p>
              <p v-if="locationLoadError && !selectedLocation" class="field-error location-load-error" role="alert">
                {{ locationLoadError }}
              </p>
              <p v-if="locationError" class="field-error repair-location-error" aria-live="polite">
                {{ locationError }}
              </p>
              <div class="field">
                <label for="repairProblem">ปัญหาที่พบ</label
                ><input
                  id="repairProblem"
                  name="title"
                  type="text"
                  maxlength="200"
                  autocomplete="on"
                  required
                  placeholder="เช่น เครื่องปรับอากาศไม่ทำงาน ท่อประปารั่ว"
                />
              </div>
              <LocationCombobox
                v-model="selectedWorkType"
                id="repairType"
                label="ประเภทงาน"
                placeholder="เลือกประเภทงาน"
                :options="workTypeSuggestions"
                :allow-custom="false"
                required
              />
              <input
                type="hidden"
                name="priority"
                :value="priorityValues[selectedWorkType] || ''"
              />
              <div class="field">
                <label for="repairDetails">อธิบายปัญหา (ถ้ามี)</label
                ><textarea
                  id="repairDetails"
                  name="description"
                  maxlength="1000"
                  placeholder="เกิดอะไรขึ้น และมีผลต่อการใช้งานอย่างไร"
                ></textarea>
              </div>
              <div class="field">
                <label for="repairImage">รูปภาพจุดชำรุด (ถ้ามี)</label>
                <div class="upload-field">
                  <label class="upload-trigger repair-photo-trigger">
                    <input
                      id="repairImage"
                      ref="photoInput"
                      name="image"
                      type="file"
                      multiple
                      accept="image/jpeg,image/png,image/webp"
                      aria-describedby="repairImageHint repairImageError"
                      @change="addPhotos"
                    />
                    <span class="upload-icon" aria-hidden="true">＋</span>
                    <span class="upload-copy">
                      <strong>{{ photos.length ? "เพิ่มรูปภาพ" : "เลือกรูปภาพ" }}</strong>
                      <small id="repairImageHint">แนบได้สูงสุด {{ MAX_PHOTOS }} รูป · JPG, PNG หรือ WebP ไม่เกิน 5 MB ต่อรูป</small>
                    </span>
                  </label>
                  <ul v-if="photos.length" class="repair-photo-list" aria-label="รูปจุดชำรุดที่แนบ">
                    <li v-for="(photo, index) in photos" :key="photo.url" class="repair-photo-preview">
                      <img :src="photo.url" :alt="`ตัวอย่างรูป ${photo.file.name}`" />
                      <span>{{ photo.file.name }}</span>
                      <button
                        type="button"
                        class="remove-image"
                        :aria-label="`ลบรูป ${photo.file.name}`"
                        @click="removePhoto(index)"
                      >ลบ</button>
                    </li>
                  </ul>
                </div>
              </div>
              <div id="repairImageError" class="field-error repair-photo-errors" aria-live="polite" aria-atomic="true">
                <ul v-if="photoErrors.length">
                  <li v-for="(error, index) in photoErrors" :key="index">{{ error }}</li>
                </ul>
              </div>
              <div class="field">
                <label for="repairEmail">อีเมลสำหรับติดตามสถานะ</label
                ><input
                  id="repairEmail"
                  type="email"
                  name="reporter_email"
                  required
                  placeholder="name@example.com"
                  autocomplete="email"
                />
              </div>
              </fieldset>
              <p
                class="submission-status"
                :class="{ 'image-error': status === 'error' }"
                role="status"
                aria-live="polite"
                aria-atomic="true"
              >{{ message }}</p>
              <button type="submit" class="submit-btn" :disabled="isSubmitting">
                {{ isSubmitting ? "กำลังส่ง…" : status === "error" ? "ลองส่งอีกครั้ง" : "ส่งคำขอซ่อม" }}
              </button>
            </form>
          </div>
        </section>
</template>

<style scoped>
.repair-fields {
  min-width: 0;
  margin: 0;
  padding: 0;
  border: 0;
}

.submit-btn:disabled {
  opacity: 0.65;
  cursor: wait;
}

.repair-photo-trigger {
  position: relative;
  cursor: pointer;
}

.repair-photo-trigger input {
  display: block;
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

.repair-photo-trigger:focus-within {
  outline: 2px solid var(--primary);
  outline-offset: 3px;
}

.repair-photo-list {
  display: grid;
  gap: 10px;
  margin: 10px 0 0;
  padding: 0;
  list-style: none;
}

.repair-photo-preview {
  display: flex;
  align-items: center;
  gap: 10px;
}

.repair-photo-preview img {
  width: 80px;
  height: 80px;
  flex-shrink: 0;
  border-radius: 12px;
  object-fit: cover;
}

.repair-photo-preview span {
  flex: 1;
  min-width: 0;
  overflow-wrap: anywhere;
  font-size: 12px;
}

.repair-photo-preview button {
  flex-shrink: 0;
}

.repair-photo-errors ul {
  margin: 0;
  padding-left: 20px;
  overflow-wrap: anywhere;
}

.submission-status {
  overflow-wrap: anywhere;
}

.image-error {
  display: block;
  margin-top: 6px;
  color: #b91c1c;
}

.submission-status:empty {
  display: none;
}
</style>
