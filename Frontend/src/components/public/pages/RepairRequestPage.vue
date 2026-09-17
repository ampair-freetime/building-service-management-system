<script setup>
import { onBeforeUnmount, ref } from "vue";
import { useRepairSubmission } from "../../../composables/useRepairSubmission.js";
import { uploadRepairRequest } from "../../../services/repairRequests.js";
import LocationCombobox from "../LocationCombobox.vue";

const isDemo = !import.meta.env.VITE_REPAIR_REQUEST_URL;
const { isSubmitting, status, message, submit, markChanged } = useRepairSubmission(
  isDemo ? async () => ({ demo: true }) : uploadRepairRequest,
);

async function submitRepair(event) {
  if (isSubmitting.value) return;
  const form = event.currentTarget;
  if (!form.checkValidity()) return;

  const payload = new FormData(form);
  payload.delete("image");
  photos.value.forEach(({ file }) => payload.append("image", file));
  await submit(payload, (result) => {
    const recipientEmail = payload.get("recipient_email") || "";
    form.reset();
    form.dispatchEvent(new CustomEvent("repair-request-confirmed", {
      bubbles: true,
      detail: {
        ...result,
        recipientEmail,
        location: [payload.get("repair_floor"), payload.get("repair_room")]
          .filter(Boolean)
          .join(" · "),
        problem: payload.get("problem") || "",
      },
    }));
  });
}

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
    } else if (
      !photos.value.some(
        ({ file: existing }) =>
          existing.name === file.name &&
          existing.size === file.size &&
          existing.type === file.type &&
          existing.lastModified === file.lastModified,
      )
    ) {
      if (photos.value.length >= MAX_PHOTOS) {
        errors.push(`${file.name}: แนบได้สูงสุด ${MAX_PHOTOS} รูป`);
      } else {
        photos.value.push({ file, url: URL.createObjectURL(file) });
      }
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

const floorSuggestions = [
  "ชั้น 1",
  "ชั้น 2",
  "ชั้น 3",
];
const roomSuggestions = [
  "ห้องน้ำ",
  "โถงทางเดิน",
  "พื้นที่ส่วนกลาง",
  "CSB201",
  "CSB307",
  "CSB209",
];
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
                  id="repairFloor"
                  name="repair_floor"
                  label="ชั้น"
                  placeholder="เลือกชั้น"
                  :options="floorSuggestions"
                  required
                />
                <LocationCombobox
                  id="repairRoom"
                  name="repair_room"
                  label="ห้อง"
                  placeholder="เลือกห้อง"
                  :options="roomSuggestions"
                  required
                />
              </div>
              <div class="field">
                <label for="repairProblem">ปัญหาที่พบ</label
                ><input
                  id="repairProblem"
                  name="problem"
                  type="text"
                  required
                  placeholder="เช่น เครื่องปรับอากาศไม่ทำงาน ท่อประปารั่ว"
                />
              </div>
              <div class="field">
                <label for="repairType">ประเภทงาน</label
                ><select id="repairType" name="work_type" required>
                  <option>งานซ่อมทั่วไป</option>
                  <option>เหตุเร่งด่วน</option>
                </select>
              </div>
              <div class="field">
                <label for="repairDetails">อธิบายปัญหา (ถ้ามี)</label
                ><textarea
                  id="repairDetails"
                  name="description"
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
                      <small id="repairImageHint">แนบได้สูงสุด {{ MAX_PHOTOS }} รูป JPG, PNG หรือ WebP ไม่เกิน 5 MB ต่อรูป</small>
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
                  name="recipient_email"
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
