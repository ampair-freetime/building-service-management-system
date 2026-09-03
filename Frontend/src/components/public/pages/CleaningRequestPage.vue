<template>
<section class="page" id="clean" data-theme="clean">
          <header class="page-header">
            <div>
              <div class="eyebrow">Cleaning request</div>
              <h2>แจ้งทำความสะอาด</h2>
            </div>
            <p>
              ระบุพื้นที่และลักษณะงาน
              เพื่อให้เจ้าหน้าที่เตรียมอุปกรณ์และเข้าดำเนินการได้ตรงจุด
            </p>
          </header>
          <div class="work-layout single-form-layout">
            <form class="form-panel" data-submit-type="แจ้งทำความสะอาด">
              <h3>ขอทำความสะอาดพื้นที่</h3>
              <div class="field">
                <label>ประเภทพื้นที่</label
                ><select required>
                  <option value="">เลือกพื้นที่</option>
                  <option>ห้องเรียน</option>
                  <option>ห้องน้ำ</option>
                  <option>โถงทางเดิน</option>
                  <option>พื้นที่ส่วนกลาง</option>
                </select>
              </div>
              <div class="field">
                <label>สถานที่</label
                ><input
                  type="text"
                  required
                  placeholder="อาคาร / ชั้น / ห้อง"
                />
              </div>
              <div class="field">
                <label>ประเภทงาน</label
                ><select required>
                  <option>ทำความสะอาดทั่วไป</option>
                  <option>คราบหกเลอะ</option>
                  <option>ขยะสะสม</option>
                  <option>เหตุเร่งด่วน</option>
                </select>
              </div>
              <div class="field">
                <label>รายละเอียด</label
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
