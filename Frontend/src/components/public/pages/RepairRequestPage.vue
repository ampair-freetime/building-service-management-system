<template>
<section class="page" id="repair" data-theme="repair">
          <header class="page-header">
            <div>
              <div class="eyebrow">Repair request</div>
              <h2>แจ้งซ่อม</h2>
            </div>
            <p>
              แจ้งอุปกรณ์หรือพื้นที่ชำรุด
              พร้อมระดับความเร่งด่วนเพื่อให้ทีมช่างจัดลำดับงานได้เหมาะสม
            </p>
          </header>
          <div class="work-layout single-form-layout">
            <form class="form-panel" data-submit-type="แจ้งซ่อม">
              <h3>รายละเอียดปัญหา</h3>
              <div class="field">
                <label>ประเภทอุปกรณ์</label
                ><select required>
                  <option value="">เลือกประเภท</option>
                  <option>ไฟฟ้า</option>
                  <option>ประปา</option>
                  <option>เครื่องปรับอากาศ</option>
                  <option>อุปกรณ์ห้องเรียน</option>
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
                <label>ความเร่งด่วน</label
                ><select required>
                  <option>ทั่วไป</option>
                  <option>เร่งด่วน</option>
                  <option>กระทบความปลอดภัย</option>
                </select>
              </div>
              <div class="field">
                <label>อธิบายปัญหา</label
                ><textarea
                  required
                  placeholder="เกิดอะไรขึ้น และมีผลต่อการใช้งานอย่างไร"
                ></textarea>
              </div>
              <div class="field">
                <label>รูปภาพจุดชำรุด</label>
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
              <button type="submit" class="submit-btn">ส่งคำขอซ่อม</button>
            </form>
          </div>
        </section>
</template>
