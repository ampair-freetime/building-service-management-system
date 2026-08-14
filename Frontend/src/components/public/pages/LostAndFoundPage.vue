<template>
<section class="page" id="lost" data-theme="lost">
          <header class="page-header">
            <div>
              <div class="eyebrow">Lost &amp; found</div>
              <h2>ของหายและของที่พบ</h2>
            </div>
            <p>
              ค้นหาประกาศที่มีอยู่ก่อน หากยังไม่พบจึงสร้างประกาศใหม่
              เพื่อช่วยลดรายการซ้ำและเพิ่มโอกาสได้ของคืน
            </p>
          </header>
          <div class="lost-hub">
            <section class="lost-search-panel">
              <div class="eyebrow">ค้นหาก่อนแจ้ง</div>
              <h3>มีใครพบของของคุณแล้วหรือยัง?</h3>
              <p>ค้นหาจากชื่อสิ่งของ สี สถานที่ หรือรายละเอียดที่จำได้</p>
              <div class="search-row">
                <input
                  type="text"
                  id="lostSearch"
                  placeholder="เช่น กระเป๋าสีดำ, บัตรนักศึกษา, อาคาร 3"
                /><button type="button" id="lostSearchButton">
                  ค้นหาประกาศ
                </button>
              </div>
            </section>

            <div class="lost-actions-grid">
              <button
                type="button"
                class="lost-action-card"
                data-open-lost-view="report-lost"
              >
                <span class="action-symbol"
                  ><svg class="icon"><use href="#i-search" /></svg></span
                ><strong>แจ้งของหาย</strong
                ><span>ระบุสิ่งของ จุดที่หาย และลักษณะเฉพาะ</span>
              </button>
              <button
                type="button"
                class="lost-action-card"
                data-open-lost-view="report-found"
              >
                <span class="action-symbol"
                  ><svg class="icon"><use href="#i-box" /></svg></span
                ><strong>แจ้งพบของ</strong><span>ระบุสิ่งของและจุดรับฝาก</span>
              </button>
              <button
                type="button"
                class="lost-action-card"
                data-open-lost-view="browse"
              >
                <span class="action-symbol"
                  ><svg class="icon"><use href="#i-history" /></svg></span
                ><strong>ดูประกาศทั้งหมด</strong
                ><span>ดูรายการตามหาและรายการที่พบแล้ว</span>
              </button>
            </div>

            <div
              class="lost-tabs"
              role="tablist"
              aria-label="เมนูของหายและของที่พบ"
            >
              <button
                type="button"
                class="lost-tab active"
                data-lost-view="browse"
              >
                ประกาศทั้งหมด
              </button>
              <button
                type="button"
                class="lost-tab"
                data-lost-view="report-lost"
              >
                แจ้งของหาย
              </button>
              <button
                type="button"
                class="lost-tab"
                data-lost-view="report-found"
              >
                แจ้งพบของ
              </button>
            </div>

            <div class="lost-view active" id="lost-view-browse">
              <section class="lost-board">
                <div class="board-head">
                  <div>
                    <h3>ประกาศล่าสุด</h3>
                    <p id="resultSummary">
                      แสดงรายการที่กำลังตามหาและของที่พบแล้ว
                    </p>
                  </div>
                </div>
                <div class="filter-row">
                  <button
                    type="button"
                    class="filter-chip active"
                    data-filter="all"
                  >
                    ทั้งหมด</button
                  ><button type="button" class="filter-chip" data-filter="lost">
                    กำลังตามหา</button
                  ><button
                    type="button"
                    class="filter-chip"
                    data-filter="found"
                  >
                    พบของแล้ว
                  </button>
                </div>
                <div class="post-grid" id="postGrid">
                  <article
                    class="post-card"
                    data-kind="lost"
                    data-search="กระเป๋าผ้าสีดำ อาคาร csb ชั้น 3 พวงกุญแจแมว"
                  >
                    <div class="post-image">
                      <svg class="icon"><use href="#i-search" /></svg>
                    </div>
                    <div class="post-body">
                      <div class="post-meta">
                        <span class="post-type lost">กำลังตามหา</span
                        ><span class="post-date">29 ก.ค. 2569</span>
                      </div>
                      <h4>กระเป๋าผ้าสีดำ</h4>
                      <p>หายบริเวณอาคาร CSB ชั้น 3 มีพวงกุญแจรูปแมว</p>
                      <button type="button" class="post-detail-button">
                        ดูรายละเอียด
                      </button>
                    </div>
                  </article>
                  <article
                    class="post-card"
                    data-kind="found"
                    data-search="บัตรนักศึกษา โรงอาหารกลาง เคาน์เตอร์ประชาสัมพันธ์"
                  >
                    <div class="post-image">
                      <svg class="icon"><use href="#i-box" /></svg>
                    </div>
                    <div class="post-body">
                      <div class="post-meta">
                        <span class="post-type found">พบของแล้ว</span
                        ><span class="post-date">29 ก.ค. 2569</span>
                      </div>
                      <h4>บัตรนักศึกษา</h4>
                      <p>พบที่โรงอาหารกลาง ฝากไว้ที่เคาน์เตอร์ประชาสัมพันธ์</p>
                      <button type="button" class="claim-button">
                        นี่อาจเป็นของฉัน
                      </button>
                    </div>
                  </article>
                  <article
                    class="post-card"
                    data-kind="found"
                    data-search="กุญแจ พวงกุญแจสีแดง อาคาร 2 บันได"
                  >
                    <div class="post-image">
                      <svg class="icon"><use href="#i-box" /></svg>
                    </div>
                    <div class="post-body">
                      <div class="post-meta">
                        <span class="post-type found">พบของแล้ว</span
                        ><span class="post-date">28 ก.ค. 2569</span>
                      </div>
                      <h4>กุญแจพร้อมพวงกุญแจ</h4>
                      <p>พบบริเวณบันไดอาคาร 2 พวงกุญแจสีแดง</p>
                      <button type="button" class="claim-button">
                        นี่อาจเป็นของฉัน
                      </button>
                    </div>
                  </article>
                  <article
                    class="post-card"
                    data-kind="lost"
                    data-search="ร่มพับสีดำ ห้อง b201"
                  >
                    <div class="post-image">
                      <svg class="icon"><use href="#i-search" /></svg>
                    </div>
                    <div class="post-body">
                      <div class="post-meta">
                        <span class="post-type lost">กำลังตามหา</span
                        ><span class="post-date">28 ก.ค. 2569</span>
                      </div>
                      <h4>ร่มพับสีดำ</h4>
                      <p>พบเห็นครั้งสุดท้ายหน้าห้อง B201</p>
                      <button type="button" class="post-detail-button">
                        ดูรายละเอียด
                      </button>
                    </div>
                  </article>
                  <article
                    class="post-card"
                    data-kind="found"
                    data-search="หูฟังไร้สาย สีขาว ห้องสมุด ชั้น 2"
                  >
                    <div class="post-image">
                      <svg class="icon"><use href="#i-box" /></svg>
                    </div>
                    <div class="post-body">
                      <div class="post-meta">
                        <span class="post-type found">พบของแล้ว</span
                        ><span class="post-date">27 ก.ค. 2569</span>
                      </div>
                      <h4>หูฟังไร้สายสีขาว</h4>
                      <p>พบบริเวณโต๊ะอ่านหนังสือ ห้องสมุดชั้น 2</p>
                      <button type="button" class="claim-button">
                        นี่อาจเป็นของฉัน
                      </button>
                    </div>
                  </article>
                  <article
                    class="post-card"
                    data-kind="lost"
                    data-search="กระบอกน้ำ สีเขียว ห้อง c104"
                  >
                    <div class="post-image">
                      <svg class="icon"><use href="#i-search" /></svg>
                    </div>
                    <div class="post-body">
                      <div class="post-meta">
                        <span class="post-type lost">กำลังตามหา</span
                        ><span class="post-date">27 ก.ค. 2569</span>
                      </div>
                      <h4>กระบอกน้ำสีเขียว</h4>
                      <p>คาดว่าลืมไว้ในห้อง C104 ช่วงบ่าย</p>
                      <button type="button" class="post-detail-button">
                        ดูรายละเอียด
                      </button>
                    </div>
                  </article>
                </div>
              </section>
            </div>

            <div class="lost-view" id="lost-view-report-lost">
              <div class="two-form-layout">
                <form class="form-panel" data-submit-type="แจ้งของหาย">
                  <h3>แจ้งของหาย</h3>
                  <div class="field">
                    <label>ประเภทสิ่งของ</label
                    ><select required>
                      <option value="">เลือกประเภท</option>
                      <option>กระเป๋า</option>
                      <option>บัตรหรือเอกสาร</option>
                      <option>อุปกรณ์อิเล็กทรอนิกส์</option>
                      <option>กุญแจ</option>
                      <option>อื่น ๆ</option>
                    </select>
                  </div>
                  <div class="field">
                    <label>ชื่อสิ่งของ</label
                    ><input
                      type="text"
                      required
                      placeholder="เช่น กระเป๋าผ้าสีดำ"
                    />
                  </div>
                  <div class="field">
                    <label>วันที่และเวลาที่คาดว่าทำหาย</label
                    ><input type="datetime-local" required />
                  </div>
                  <div class="field">
                    <label>สถานที่คาดว่าทำหาย</label
                    ><input
                      type="text"
                      required
                      placeholder="อาคาร / ชั้น / ห้อง"
                    />
                  </div>
                  <div class="field">
                    <label>ลักษณะเฉพาะ</label
                    ><textarea
                      required
                      placeholder="สี ยี่ห้อ รอยตำหนิ หรือพวงกุญแจที่ติดอยู่"
                    ></textarea>
                  </div>
                  <div class="field">
                    <label>รูปภาพสิ่งของ (ถ้ามี)</label>
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
                    เผยแพร่ประกาศตามหา
                  </button>
                </form>
                <div class="list-panel">
                  <h3>ก่อนเผยแพร่</h3>
                  <div class="privacy-note">
                    อย่าใส่ข้อมูลสำคัญทั้งหมดในประกาศสาธารณะ
                    ควรเก็บรายละเอียดบางอย่างไว้ใช้ตรวจสอบผู้ที่อ้างว่าเป็นเจ้าของ
                  </div>
                  <div class="ticket-list">
                    <div class="ticket">
                      <div>
                        <strong>ค้นหาประกาศก่อน</strong
                        ><small>อาจมีคนประกาศพบสิ่งของไว้แล้ว</small>
                      </div>
                      <span class="status">แนะนำ</span>
                    </div>
                    <div class="ticket">
                      <div>
                        <strong>ระบุลักษณะให้ชัด</strong
                        ><small>สี ยี่ห้อ จุดสังเกต และบริเวณที่หาย</small>
                      </div>
                      <span class="status">สำคัญ</span>
                    </div>
                    <div class="ticket">
                      <div>
                        <strong>เก็บรหัสติดตาม</strong
                        ><small>ใช้ตรวจสอบสถานะหรือปิดประกาศภายหลัง</small>
                      </div>
                      <span class="status">จำเป็น</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="lost-view" id="lost-view-report-found">
              <div class="two-form-layout">
                <form class="form-panel" data-submit-type="แจ้งพบของ">
                  <h3>แจ้งพบของ</h3>
                  <div class="field">
                    <label>ประเภทสิ่งของ</label
                    ><select required>
                      <option value="">เลือกประเภท</option>
                      <option>กระเป๋า</option>
                      <option>บัตรหรือเอกสาร</option>
                      <option>อุปกรณ์อิเล็กทรอนิกส์</option>
                      <option>กุญแจ</option>
                      <option>อื่น ๆ</option>
                    </select>
                  </div>
                  <div class="field">
                    <label>ชื่อสิ่งของ</label
                    ><input
                      type="text"
                      required
                      placeholder="เช่น กุญแจพร้อมพวงกุญแจสีแดง"
                    />
                  </div>
                  <div class="field">
                    <label>วันที่และเวลาที่พบ</label
                    ><input type="datetime-local" required />
                  </div>
                  <div class="field">
                    <label>สถานที่พบ</label
                    ><input
                      type="text"
                      required
                      placeholder="อาคาร / ชั้น / ห้อง"
                    />
                  </div>
                  <div class="field">
                    <label>นำของไปฝากไว้ที่ใด</label
                    ><input
                      type="text"
                      required
                      placeholder="เช่น ห้องประชาสัมพันธ์ชั้น 1"
                    />
                  </div>
                  <div class="field">
                    <label>รายละเอียดทั่วไป</label
                    ><textarea
                      placeholder="อธิบายเฉพาะข้อมูลที่เปิดเผยต่อสาธารณะได้"
                    ></textarea>
                  </div>
                  <div class="field">
                    <label>รูปภาพของที่พบ</label>
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
                    <label>รายละเอียดลับสำหรับยืนยันเจ้าของ</label
                    ><textarea
                      required
                      placeholder="เช่น ของภายใน ตำหนิ หรือข้อมูลที่ไม่ควรแสดงสาธารณะ"
                    ></textarea>
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
                    เผยแพร่ประกาศพบของ
                  </button>
                </form>
                <div class="list-panel">
                  <h3>การปกป้องเจ้าของสิ่งของ</h3>
                  <div class="privacy-note">
                    เลขบัตร ชื่อเต็ม จำนวนเงิน
                    หรือรายละเอียดสำคัญไม่ควรแสดงต่อสาธารณะ
                    ให้เจ้าหน้าที่ใช้ข้อมูลเหล่านี้ตรวจสอบก่อนคืนของ
                  </div>
                  <div class="ticket-list">
                    <div class="ticket">
                      <div>
                        <strong>ฝากไว้ในจุดที่ปลอดภัย</strong
                        ><small
                          >ระบุห้องหรือเคาน์เตอร์ที่ผู้ใช้ติดต่อรับได้</small
                        >
                      </div>
                      <span class="status">แนะนำ</span>
                    </div>
                    <div class="ticket">
                      <div>
                        <strong>อย่าเปิดเผยข้อมูลทั้งหมด</strong
                        ><small
                          >เก็บรายละเอียดบางอย่างไว้ยืนยันเจ้าของจริง</small
                        >
                      </div>
                      <span class="status">สำคัญ</span>
                    </div>
                    <div class="ticket">
                      <div>
                        <strong>ให้ Staff ตรวจคำขอรับ</strong
                        ><small>ลดความเสี่ยงจากการแอบอ้างเป็นเจ้าของ</small>
                      </div>
                      <span class="status">ปลอดภัย</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
</template>
