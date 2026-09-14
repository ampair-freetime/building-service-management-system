<script setup>
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
          </div>
        </section>
</template>
