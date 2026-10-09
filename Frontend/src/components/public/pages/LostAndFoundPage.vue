<template>
  <section class="page" id="lost" data-theme="lost">
    <header class="page-header lost-page-header">
      <svg class="lost-illustration" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
        <rect width="20" height="5" x="2" y="3" rx="1" /><path d="M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8" /><path d="M10 12h4" />
      </svg>
      <div>
        <div class="eyebrow">Lost &amp; found</div>
        <h2>แจ้งของหายและพบของ</h2>
      </div>

    </header>
    <div class="lost-hub">
      <section class="lost-search-panel">
        <div class="eyebrow">ค้นหาก่อนแจ้ง</div>
        <h3>มีใครพบของของคุณแล้วหรือยัง?</h3>
        <p>ค้นหาจากชื่อสิ่งของ สี สถานที่ หรือรายละเอียดที่จำได้</p>
        <form id="lostSearchForm" class="search-row" role="search">
          <input
            type="text"
            id="lostSearch"
            placeholder="เช่น กระเป๋าสีดำ, บัตรนักศึกษา, อาคาร 3"
          /><button type="submit" id="lostSearchButton">ค้นหาประกาศ</button>
        </form>
      </section>

      <div class="lost-actions-grid">
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
      </div>

      <div class="lost-tabs" role="tablist" aria-label="เมนูของหายและของที่พบ">
        <button type="button" class="lost-tab active" data-lost-view="browse">
          ประกาศทั้งหมด
        </button>
        <button type="button" class="lost-tab" data-lost-view="report-lost">
          แจ้งของหาย
        </button>
        <button type="button" class="lost-tab" data-lost-view="report-found">
          แจ้งพบของ
        </button>
      </div>

      <div class="lost-view active" id="lost-view-browse">
        <section class="lost-board" id="lostSearchResults">
          <div class="board-head">
            <div>
              <h3>ประกาศล่าสุด</h3>
              <p id="resultSummary">แสดงรายการที่กำลังตามหาและของที่พบแล้ว</p>
            </div>
            <button id="lostRefreshButton" type="button" class="filter-chip">
              รีเฟรชประกาศ
            </button>
          </div>
          <div class="filter-row">
            <button type="button" class="filter-chip active" data-filter="all">
              ทั้งหมด</button
            ><button type="button" class="filter-chip" data-filter="lost">
              กำลังตามหา</button
            ><button type="button" class="filter-chip" data-filter="found">
              พบของแล้ว
            </button>
          </div>
          <div class="post-grid" id="postGrid"></div>
          <nav id="lostPagination" class="filter-row" aria-label="หน้าประกาศ" hidden>
            <button id="lostPreviousPage" class="filter-chip" type="button" disabled>ก่อนหน้า</button>
            <span id="lostPageSummary" aria-live="polite"></span>
            <button id="lostNextPage" class="filter-chip" type="button" disabled>ถัดไป</button>
          </nav>
          <div
            id="noSearchResults"
            class="no-search-results"
            role="status"
            aria-live="polite"
            hidden
          >
            <strong>ไม่พบประกาศที่ตรงกับคำค้น</strong>
            <p>ลองเปลี่ยนคำค้น หรือเลือกประเภท “ทั้งหมด” แล้วค้นหาอีกครั้ง</p>
          </div>
        </section>
      </div>

      <div class="lost-view" id="lost-view-report-lost">
        <div class="two-form-layout single-form-layout">
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
              <p
                id="lostItemCategoryError"
                class="field-error"
                aria-live="polite"
              ></p>
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
              <p
                id="lostItemNameError"
                class="field-error"
                aria-live="polite"
              ></p>
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
              <p
                id="lostItemDateTimeError"
                class="field-error"
                aria-live="polite"
              ></p>
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
              <p
                id="lostItemLocationError"
                class="field-error"
                aria-live="polite"
              ></p>
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
              <p
                id="lostItemDescriptionError"
                class="field-error"
                aria-live="polite"
              ></p>
            </div>
            <div class="field">
              <label>รูปภาพสิ่งของ (ถ้ามี)</label>
              <div class="upload-field">
                <label class="upload-trigger"
                  ><input
                    name="image"
                    type="file"
                    class="image-input"
                    multiple
                    accept="image/jpeg,image/png,image/webp"
                    data-max-size="5242880"
                    data-max-files="5"
                    data-error-id="lostItemPhotoError"
                    aria-describedby="lostItemPhotoError"
                  /><span class="upload-icon">＋</span
                  ><span class="upload-copy"
                    ><strong class="image-upload-action">เลือกรูปภาพ</strong
                    ><small>แนบได้สูงสุด 5 รูป · JPG, PNG หรือ WebP ไม่เกิน 5 MB ต่อรูป</small></span
                  ></label
                >
                <ul class="image-preview-list" aria-label="รูปภาพสิ่งของที่แนบ"></ul>
                <p
                  id="lostItemPhotoError"
                  class="field-error"
                  aria-live="polite"
                ></p>
              </div>
            </div>
            <div class="field">
              <label for="lostItemEmail">อีเมลสำหรับติดตามสถานะ</label
              ><input
                id="lostItemEmail"
                type="email"
                name="reporter_email"
                required
                maxlength="255"
                aria-describedby="lostItemEmailError"
                placeholder="name@example.com"
                autocomplete="email"
              />
              <p
                id="lostItemEmailError"
                class="field-error"
                aria-live="polite"
              ></p>
            </div>
            <button type="submit" class="submit-btn">เผยแพร่ประกาศตามหา</button>
          </form>

        </div>
      </div>

      <div class="lost-view" id="lost-view-report-found">
        <div class="two-form-layout single-form-layout">
          <form
            id="publicFoundForm"
            class="form-panel"
            data-confirmation-mode="lost-found"
            novalidate
          >
            <h3>แจ้งพบของ</h3>
            <p class="found-dropoff-notice">
              กรุณานำของไปฝากไว้ที่บริเวณห้องธุรการ ชั้น 1
            </p>
            <div class="field">
              <label for="publicFoundCategory">ประเภทสิ่งของ</label
              ><select
                id="publicFoundCategory"
                name="item_category"
                required
                aria-describedby="publicFoundCategoryError"
              >
                <option value="">เลือกประเภท</option>
                <option>อุปกรณ์อิเล็กทรอนิกส์</option>
                <option>กระเป๋าและของใช้ส่วนตัว</option>
                <option>บัตรและเอกสาร</option>
                <option>กุญแจ</option>
                <option>เสื้อผ้าและเครื่องแต่งกาย</option>
                <option>อื่น ๆ</option>
              </select>
              <p
                id="publicFoundCategoryError"
                class="field-error"
                aria-live="polite"
              ></p>
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
              <p
                id="publicFoundNameError"
                class="field-error"
                aria-live="polite"
              ></p>
            </div>
            <div class="field">
              <label for="publicFoundDateTime">วันที่และเวลาที่พบ</label
              ><input
                id="publicFoundDateTime"
                name="event_datetime"
                type="datetime-local"
                required
                aria-describedby="publicFoundDateTimeError"
              />
              <p
                id="publicFoundDateTimeError"
                class="field-error"
                aria-live="polite"
              ></p>
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
              <p
                id="publicFoundLocationError"
                class="field-error"
                aria-live="polite"
              ></p>
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
              <p
                id="publicFoundDescriptionError"
                class="field-error"
                aria-live="polite"
              ></p>
            </div>
            <div class="field">
              <label for="publicFoundPhoto"
                >รูปภาพของที่พบ
                <span class="optional-label">(ถ้ามี)</span></label
              >
              <div class="upload-field">
                <label class="upload-trigger"
                  ><input
                    id="publicFoundPhoto"
                    name="image"
                    type="file"
                    class="image-input"
                    multiple
                    accept="image/jpeg,image/png,image/webp"
                    data-max-size="5242880"
                    data-max-files="5"
                    data-error-id="publicFoundPhotoError"
                    aria-describedby="publicFoundPhotoError"
                  /><span class="upload-icon">＋</span
                  ><span class="upload-copy"
                    ><strong class="image-upload-action">เลือกรูปภาพ</strong
                    ><small>แนบได้สูงสุด 5 รูป · JPG, PNG หรือ WebP ไม่เกิน 5 MB ต่อรูป</small></span
                  ></label
                >
                <ul class="image-preview-list" aria-label="รูปภาพของที่พบที่แนบ"></ul>
              </div>
              <p
                id="publicFoundPhotoError"
                class="field-error"
                aria-live="polite"
              ></p>
            </div>
            <div class="field">
              <label for="publicFoundPrivateDetail"
                >รายละเอียดลับสำหรับยืนยันเจ้าของ (ถ้ามี)</label
              ><textarea
                id="publicFoundPrivateDetail"
                name="private_detail"
                required
                minlength="10"
                maxlength="600"
                aria-describedby="publicFoundPrivateDetailError"
                placeholder="เช่น ของภายใน ตำหนิ หรือข้อมูลที่ไม่ควรแสดงสาธารณะ"
              ></textarea>
              <p
                id="publicFoundPrivateDetailError"
                class="field-error"
                aria-live="polite"
              ></p>
            </div>

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
              <p
                id="publicFoundEmailError"
                class="field-error"
                aria-live="polite"
              ></p>
            </div>
            <button type="submit" class="submit-btn">
              ส่งให้เจ้าหน้าที่ตรวจสอบ
            </button>
          </form>

        </div>
      </div>
    </div>
  </section>
</template>
