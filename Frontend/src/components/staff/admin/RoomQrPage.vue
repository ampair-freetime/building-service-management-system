<template>
<section class="page" id="page-qr">
          <div class="section-title">
            <div>
              <div class="eyebrow">Room identity system</div>
              <h2>สร้าง QR ประจำห้อง</h2>
              <p>
                QR แต่ละห้องพาผู้ใช้ไปยังหน้ารายงานที่เติมชื่ออาคาร ชั้น
                และห้องให้อัตโนมัติ
              </p>
            </div>
          </div>
          <section class="qr-launch">
            <div>
              <h3>จัดการ QR ประจำห้อง</h3>
              <p class="compact-card-copy">
                สร้าง QR ใหม่หรือจัดการรายการห้องโดยไม่แสดงฟอร์มยาวค้างในหน้า
              </p>
            </div>
            <div class="row-actions">
              <button class="primary" id="openQrModal" type="button">
                สร้าง QR</button
              ><button class="secondary" id="bulkQr" type="button">
                สร้างหลายห้อง</button
              ><button class="secondary" id="printQr" type="button">
                พิมพ์ QR
              </button>
            </div>
          </section>
          <div class="qr-layout compact">
            <section class="qr-preview">
              <div class="qr-card">
                <div>
                  <div class="qr-code" id="qrCode">
                    <div class="qr-fallback"></div>
                  </div>
                  <h3 id="qrRoomName">CSB-307</h3>
                  <p id="qrUrlText">
                    https://building-care.example/report?room=CSB-307
                  </p>
                  <button class="secondary" id="downloadQr" type="button">
                    ดาวน์โหลด PNG
                  </button>
                </div>
              </div>
              <div class="room-list" id="roomList"></div>
            </section>
          </div>
        </section>
</template>
