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
              <button
                type="button"
                class="lost-action-card"
                data-open-lost-view="track"
              >
                <span class="action-symbol"
                  ><svg class="icon"><use href="#i-history" /></svg></span
                ><strong>ติดตามคำร้อง</strong
                ><span>ตรวจสอบสถานะด้วยรหัสติดตาม</span>
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
              <button type="button" class="lost-tab" data-lost-view="track">
                ติดตามคำร้อง
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
                      <button type="button" class="post-detail-button">
                        ดูรายละเอียด
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
                      <button type="button" class="post-detail-button">
                        ดูรายละเอียด
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
                      <button type="button" class="post-detail-button">
                        ดูรายละเอียด
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

            <div class="lost-view" id="lost-view-track">
              <section class="lost-search-panel lost-tracking-panel">
                <div class="eyebrow">Lost &amp; found tracking</div>
                <h3>ติดตามคำร้องของหายและของที่พบ</h3>
                <p>กรอกรหัสติดตามที่ได้รับ โดยไม่ต้องเข้าสู่ระบบ</p>
                <form id="lostFoundTrackingForm" class="tracking-box lost-tracking-box">
                  <div class="field">
                    <label for="lostFoundTrackingCode">รหัสติดตาม</label>
                    <input
                      id="lostFoundTrackingCode"
                      type="text"
                      required
                      placeholder="เช่น CLAIM-4821"
                      autocomplete="off"
                    />
                  </div>
                  <button type="submit" class="primary-btn">ตรวจสอบสถานะ</button>
                </form>
                <div
                  class="tracking-result"
                  id="lostFoundTrackingResult"
                  role="status"
                  aria-live="polite"
                >
                  <div class="tracking-result-head">
                    <div>
                      <small>รหัสติดตาม</small>
                      <strong id="lostFoundTrackingResultCode">–</strong>
                      <p id="lostFoundTrackingResultText" style="margin: 5px 0 0"></p>
                    </div>
                    <span class="status" id="lostFoundTrackingResultStatus"></span>
                  </div>
                  <div id="lostFoundTrackingDetails" class="tracking-request-details" hidden>
                    <div>
                      <small>ประเภทคำร้อง</small>
                      <strong id="lostFoundTrackingRequestType">–</strong>
                    </div>
                    <div>
                      <small>รายการ</small>
                      <strong id="lostFoundTrackingItemName">–</strong>
                    </div>
                    <div>
                      <small>อัปเดตล่าสุด</small>
                      <strong id="lostFoundTrackingUpdatedAt">–</strong>
                    </div>
                  </div>
                </div>
              </section>
            </div>

            <div class="lost-view" id="lost-view-report-lost">
              <div class="two-form-layout">
                <form id="lostItemForm" class="form-panel" novalidate>
                  <h3>แจ้งของหาย</h3>
                  <div class="field">
                    <label for="lostItemCategory">ประเภทสิ่งของ</label
                    ><select
                      id="lostItemCategory"
                      name="item_category"
                      required
                      aria-describedby="lostItemCategoryError"
                    >
                      <option value="">เลือกประเภท</option>
                      <option>กระเป๋า</option>
                      <option>บัตรหรือเอกสาร</option>
                      <option>อุปกรณ์อิเล็กทรอนิกส์</option>
                      <option>กุญแจ</option>
                      <option>อื่น ๆ</option>
                    </select>
                    <p id="lostItemCategoryError" class="field-error" aria-live="polite"></p>
                  </div>
                  <div class="field">
                    <label for="lostItemName">ชื่อสิ่งของ</label
                    ><input
                      id="lostItemName"
                      name="item_name"
                      type="text"
                      required
                      minlength="2"
                      maxlength="200"
                      aria-describedby="lostItemNameError"
                      placeholder="เช่น กระเป๋าผ้าสีดำ"
                    />
                    <p id="lostItemNameError" class="field-error" aria-live="polite"></p>
                  </div>
                  <div class="field">
                    <label for="lostItemDateTime">วันที่และเวลาที่คาดว่าทำหาย</label
                    ><input
                      id="lostItemDateTime"
                      name="event_datetime"
                      type="datetime-local"
                      required
                      aria-describedby="lostItemDateTimeError"
                    />
                    <p id="lostItemDateTimeError" class="field-error" aria-live="polite"></p>
                  </div>
                  <div class="field">
                    <label for="lostItemLocation">สถานที่คาดว่าทำหาย</label
                    ><input
                      id="lostItemLocation"
                      name="location_detail"
                      type="text"
                      required
                      minlength="2"
                      maxlength="255"
                      aria-describedby="lostItemLocationError"
                      placeholder="อาคาร / ชั้น / ห้อง"
                    />
                    <p id="lostItemLocationError" class="field-error" aria-live="polite"></p>
                  </div>
                  <div class="field">
                    <label for="lostItemDescription">ลักษณะเฉพาะ</label
                    ><textarea
                      id="lostItemDescription"
                      name="description"
                      required
                      minlength="10"
                      maxlength="5000"
                      aria-describedby="lostItemDescriptionError"
                      placeholder="สี ยี่ห้อ รอยตำหนิ หรือพวงกุญแจที่ติดอยู่"
                    ></textarea>
                    <p id="lostItemDescriptionError" class="field-error" aria-live="polite"></p>
                  </div>
                  <div class="field">
                    <label>รูปภาพสิ่งของ (ถ้ามี)</label>
                    <div class="upload-field">
                      <label class="upload-trigger"
                        ><input
                          name="image"
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
                    <label for="lostItemEmail">อีเมลสำหรับติดตามสถานะ</label
                    ><input
                      id="lostItemEmail"
                      type="email"
                      name="recipient_email"
                      required
                      maxlength="255"
                      aria-describedby="lostItemEmailError"
                      placeholder="name@example.com"
                      autocomplete="email"
                    />
                    <p id="lostItemEmailError" class="field-error" aria-live="polite"></p>
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
                <form
                  id="publicFoundForm"
                  class="form-panel"
                  data-confirmation-mode="lost-found"
                  novalidate
                >
                  <h3>แจ้งพบของ</h3>
                  <p class="form-helper">กรอกข้อมูลสิ่งของและจุดรับฝาก รายการจะส่งให้เจ้าหน้าที่ตรวจสอบก่อนแสดงในประกาศ</p>
                  <div class="field">
                    <label for="publicFoundCategory">ประเภทสิ่งของ</label
                    ><select id="publicFoundCategory" name="item_category" required aria-describedby="publicFoundCategoryError">
                      <option value="">เลือกประเภท</option>
                      <option>อุปกรณ์อิเล็กทรอนิกส์</option>
                      <option>กระเป๋าและของใช้ส่วนตัว</option>
                      <option>บัตรและเอกสาร</option>
                      <option>กุญแจ</option>
                      <option>เสื้อผ้าและเครื่องแต่งกาย</option>
                      <option>อื่น ๆ</option>
                    </select>
                    <p id="publicFoundCategoryError" class="field-error" aria-live="polite"></p>
                  </div>
                  <div class="field">
                    <label for="publicFoundName">ชื่อสิ่งของ</label
                    ><input
                      id="publicFoundName"
                      name="item_name"
                      type="text"
                      required
                      minlength="2"
                      maxlength="120"
                      aria-describedby="publicFoundNameError"
                      placeholder="เช่น กุญแจพร้อมพวงกุญแจสีแดง"
                    />
                    <p id="publicFoundNameError" class="field-error" aria-live="polite"></p>
                  </div>
                  <div class="public-found-row">
                    <div class="field"><label for="publicFoundDate">วันที่พบ</label><input id="publicFoundDate" name="found_date" type="date" required aria-describedby="publicFoundDateError" /><p id="publicFoundDateError" class="field-error" aria-live="polite"></p></div>
                    <div class="field"><label for="publicFoundTime">เวลาที่พบ</label><input id="publicFoundTime" name="found_time" type="time" required aria-describedby="publicFoundTimeError" /><p id="publicFoundTimeError" class="field-error" aria-live="polite"></p></div>
                  </div>
                  <div class="field">
                    <label for="publicFoundLocation">สถานที่พบ</label
                    ><input
                      id="publicFoundLocation"
                      name="location_detail"
                      type="text"
                      required
                      minlength="2"
                      maxlength="160"
                      aria-describedby="publicFoundLocationError"
                      placeholder="อาคาร / ชั้น / ห้อง"
                    />
                    <p id="publicFoundLocationError" class="field-error" aria-live="polite"></p>
                  </div>
                  <div class="field">
                    <label for="publicFoundCustody">นำของไปฝากไว้ที่ใด</label
                    ><input
                      id="publicFoundCustody"
                      name="custody_location"
                      type="text"
                      required
                      minlength="2"
                      maxlength="160"
                      aria-describedby="publicFoundCustodyError"
                      placeholder="เช่น ห้องประชาสัมพันธ์ชั้น 1"
                    />
                    <p id="publicFoundCustodyError" class="field-error" aria-live="polite"></p>
                  </div>
                  <div class="field">
                    <label for="publicFoundDescription">รายละเอียดทั่วไป</label
                    ><textarea
                      id="publicFoundDescription"
                      name="description"
                      required
                      minlength="10"
                      maxlength="600"
                      aria-describedby="publicFoundDescriptionError"
                      placeholder="อธิบายเฉพาะข้อมูลที่เปิดเผยต่อสาธารณะได้"
                    ></textarea>
                    <p id="publicFoundDescriptionError" class="field-error" aria-live="polite"></p>
                  </div>
                  <div class="field">
                    <label for="publicFoundPhoto">รูปภาพของที่พบ <span class="optional-label">(ไม่บังคับ)</span></label>
                    <div class="upload-field">
                      <label class="upload-trigger"
                        ><input
                          id="publicFoundPhoto"
                          name="image"
                          type="file"
                          class="image-input"
                          accept="image/jpeg,image/png,image/webp"
                          data-max-size="5242880"
                          data-error-id="publicFoundPhotoError"
                          aria-describedby="publicFoundPhotoError"
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
                    <p id="publicFoundPhotoError" class="field-error" aria-live="polite"></p>
                  </div>
                  <div class="field">
                    <label for="publicFoundPrivateDetail">รายละเอียดลับสำหรับยืนยันเจ้าของ</label
                    ><textarea
                      id="publicFoundPrivateDetail"
                      name="private_detail"
                      required
                      minlength="10"
                      maxlength="600"
                      aria-describedby="publicFoundPrivateDetailError"
                      placeholder="เช่น ของภายใน ตำหนิ หรือข้อมูลที่ไม่ควรแสดงสาธารณะ"
                    ></textarea>
                    <p id="publicFoundPrivateDetailError" class="field-error" aria-live="polite"></p>
                  </div>
                  <div class="field"><label for="publicFinderName">ชื่อผู้พบหรือผู้ส่งมอบ <span class="optional-label">(ไม่บังคับ)</span></label><input id="publicFinderName" type="text" maxlength="120" /></div>
                  <div class="field">
                    <label for="publicFoundEmail">อีเมลสำหรับติดตามสถานะ</label
                    ><input
                      id="publicFoundEmail"
                      type="email"
                      name="recipient_email"
                      required
                      maxlength="255"
                      aria-describedby="publicFoundEmailError"
                      placeholder="name@example.com"
                      autocomplete="email"
                    />
                    <p id="publicFoundEmailError" class="field-error" aria-live="polite"></p>
                  </div>
                  <button type="submit" class="submit-btn">
                    ส่งให้เจ้าหน้าที่ตรวจสอบ
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
