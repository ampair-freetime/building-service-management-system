<script setup>
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { useCleaningSubmission } from "../../../composables/useCleaningSubmission.js";
import { uploadCleaningRequest } from "../../../services/cleaningRequests.js";
import { mockServiceLocations as mockLocations } from "../../../services/mockServiceLocations.js";
import LocationCombobox from "../LocationCombobox.vue";

const priorityValues = {
  "ทำความสะอาดทั่วไป": "normal",
  "เหตุเร่งด่วน": "urgent",
};

const { isSubmitting, status, message, submit, markChanged } = useCleaningSubmission(
  uploadCleaningRequest,
);

async function submitCleaning(event) {
  if (isSubmitting.value) return;
  const form = event.currentTarget;
  if (!form.checkValidity()) return;
  if (!selectedLocation.value) {
    locationError.value = "กรุณาเลือกชั้นและห้องจากรายการ";
    return;
  }
  const payload = new FormData(form);
  payload.set("location_id", String(selectedLocation.value.id));
  payload.set("priority", priorityValues[selectedWorkType.value] || "");
  // Explicitly include only accepted photos; omit the empty file input entry.
  payload.delete("image");
  photos.value.forEach(({ file }) => payload.append("image", file));
  await submit(payload, (result) => {
    const recipientEmail = payload.get("reporter_email") || "";
    const submittedLocation = [selectedFloor.value, selectedRoom.value]
      .filter(Boolean)
      .join(" · ");
    form.reset();
    form.dispatchEvent(new CustomEvent("cleaning-request-confirmed", {
      bubbles: true,
      detail: {
        ...result,
        recipientEmail,
        location: submittedLocation,
        problem: payload.get("title") || "",
      },
    }));
  });
}

const selectedFloor = ref("");
const selectedRoom = ref("");
const selectedWorkType = ref("");
const locationError = ref("");
const photoInput = ref(null);
const photos = ref([]);
const photoErrors = ref([]);
const MAX_PHOTOS = 1;
const MAX_PHOTO_BYTES = 5 * 1024 * 1024;
const allowedTypes = ["image/jpeg", "image/png", "image/webp"];

const floorSuggestions = [...new Set(
  mockLocations.map(({ floor }) => `ชั้น ${floor}`),
)];
const roomSuggestions = computed(() => mockLocations
  .filter(({ floor }) => `ชั้น ${floor}` === selectedFloor.value)
  .map(({ room }) => room));
const selectedLocation = computed(() => mockLocations.find(
  ({ floor, room }) => `ชั้น ${floor}` === selectedFloor.value && room === selectedRoom.value,
));
const workTypeSuggestions = Object.keys(priorityValues);

watch(selectedFloor, () => {
  selectedRoom.value = "";
  locationError.value = "";
});
watch(selectedRoom, () => {
  locationError.value = "";
});

function syncPhotoFiles() {
  const transfer = new DataTransfer();
  photos.value.forEach(({ file }) => transfer.items.add(file));
  photoInput.value.files = transfer.files;
}

function addPhotos(event) {
  const errors = [];
  for (const file of Array.from(event.target.files)) {
    if (!allowedTypes.includes(file.type)) {
      errors.push(`${file.name}: ไม่ได้แนบไฟล์ รองรับเฉพาะ JPG, PNG หรือ WebP`);
    } else if (file.size === 0) {
      errors.push(`${file.name}: ไม่ได้แนบไฟล์ เพราะไฟล์ว่างเปล่า กรุณาเลือกไฟล์ใหม่`);
    } else if (file.size > MAX_PHOTO_BYTES) {
      errors.push(`${file.name}: ไม่ได้แนบไฟล์ ขนาดเกิน 5 MB ต่อรูป กรุณาลดขนาดไฟล์`);
    } else {
      clearPhotos();
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
  photoInput.value.focus();
}

function clearPhotos() {
  photos.value.forEach(({ url }) => URL.revokeObjectURL(url));
  photos.value = [];
  photoErrors.value = [];
}

onBeforeUnmount(clearPhotos);
</script>

<template>
<section class="page" id="clean" data-theme="clean">
          <header class="page-header clean-page-header">
            <svg class="clean-illustration" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
              <use href="#i-broom" />
            </svg>
            <div>
              <div class="eyebrow">Cleaning request</div>
              <h2>แจ้งทำความสะอาด</h2>
            </div>
          </header>
          <div class="work-layout single-form-layout">
            <form class="form-panel" novalidate data-service-validation :aria-busy="isSubmitting" @submit.prevent="submitCleaning" @reset="clearPhotos" @input="markChanged" @change="markChanged">
              <fieldset class="clean-fields" :disabled="isSubmitting">
              <h3>ขอทำความสะอาดพื้นที่</h3>
              <div class="form-row clean-location-row">
                <LocationCombobox
                  v-model="selectedFloor"
                  id="cleanFloor"
                  label="ชั้น"
                  placeholder="เลือกชั้น"
                  :options="floorSuggestions"
                  required
                />
                <LocationCombobox
                  v-model="selectedRoom"
                  id="cleanRoom"
                  label="ห้อง"
                  placeholder="เลือกห้อง"
                  :options="roomSuggestions"
                  required
                />
                <input type="hidden" name="location_id" :value="selectedLocation?.id || ''" />
              </div>
              <p v-if="locationError" class="field-error clean-location-error" aria-live="polite">
                {{ locationError }}
              </p>
              <div class="field">
                <label for="cleanProblem">ปัญหาที่พบ</label>
                <input
                  id="cleanProblem"
                  name="title"
                  type="text"
                  maxlength="200"
                  autocomplete="on"
                  required
                  placeholder="เช่น ขยะสะสม น้ำหกบนพื้นหน้าห้อง"
                />
              </div>
              <LocationCombobox
                v-model="selectedWorkType"
                id="cleanType"
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
                <label for="cleanDetails">รายละเอียด (ถ้ามี)</label>
                <textarea
                  id="cleanDetails"
                  name="description"
                  maxlength="255"
                  aria-describedby="cleanDetailsError"
                  placeholder="บอกตำแหน่งและลักษณะพื้นที่ที่ต้องการให้ดูแล"
                ></textarea>
                <p id="cleanDetailsError" class="field-error" aria-live="polite"></p>
              </div>
              <div class="field">
                <label for="cleanImage">รูปภาพพื้นที่ (ถ้ามี)</label>
                <div class="upload-field">
                  <label class="upload-trigger clean-photo-trigger">
                    <input
                      id="cleanImage"
                      ref="photoInput"
                      name="image"
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      aria-describedby="cleanImageHint cleanImageError"
                      @change="addPhotos"
                    />
                    <span class="upload-icon" aria-hidden="true">＋</span>
                    <span class="upload-copy">
                      <strong>{{ photos.length ? "เปลี่ยนรูปภาพ" : "เลือกรูปภาพ" }}</strong>
                      <small id="cleanImageHint">JPG, PNG หรือ WebP ไม่เกิน 5 MB</small>
                    </span>
                  </label>
                  <ul v-if="photos.length" class="clean-photo-list" aria-label="รูปภาพที่แนบ">
                    <li v-for="(photo, index) in photos" :key="photo.url" class="clean-photo-preview">
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
                <div id="cleanImageError" class="field-error" aria-live="polite" aria-atomic="true">
                  <ul v-if="photoErrors.length">
                    <li v-for="(error, index) in photoErrors" :key="index">{{ error }}</li>
                  </ul>
                </div>
              </div>
              <div class="field">
                <label for="cleanEmail">อีเมลสำหรับติดตามสถานะ</label
                ><input
                  id="cleanEmail"
                  type="email"
                  name="reporter_email"
                  required
                  placeholder="name@example.com"
                  autocomplete="email"
                />
              </div>
              </fieldset>
              <p class="submission-status" :class="{ 'image-error': status === 'error' }" role="status" aria-live="polite" aria-atomic="true">{{ message }}</p>
              <button type="submit" class="submit-btn" :disabled="isSubmitting">
                {{ isSubmitting ? "กำลังส่ง…" : status === "error" ? "ลองส่งอีกครั้ง" : "ส่งคำขอทำความสะอาด" }}
              </button>
            </form>
          </div>
        </section>
</template>

<style scoped>
.clean-fields {
  border: 0;
  padding: 0;
  margin: 0;
  min-width: 0;
}

.submit-btn:disabled {
  opacity: 0.65;
  cursor: wait;
}

.submission-status {
  overflow-wrap: anywhere;
}

.clean-photo-trigger {
  position: relative;
  cursor: pointer;
}

.clean-photo-trigger input {
  display: block;
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

.clean-photo-trigger:focus-within {
  outline: 2px solid var(--primary);
  outline-offset: 3px;
}

.clean-photo-list {
  list-style: none;
  padding: 0;
  margin: 10px 0 0;
  display: grid;
  gap: 10px;
}

.clean-photo-preview {
  display: flex;
  align-items: center;
  gap: 10px;
}

.clean-photo-preview img {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 12px;
  flex-shrink: 0;
}

.clean-photo-preview span {
  flex: 1;
  min-width: 0;
  overflow-wrap: anywhere;
  font-size: 12px;
}

.clean-photo-preview button {
  flex-shrink: 0;
}

.image-error {
  display: block;
  margin-top: 6px;
  color: #b91c1c;
}

.image-error ul {
  margin: 0;
  padding-left: 20px;
  overflow-wrap: anywhere;
}

.image-error:empty {
  display: none;
}
</style>
