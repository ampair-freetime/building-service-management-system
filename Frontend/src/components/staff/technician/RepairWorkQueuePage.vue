<template>
<section class="page" id="page-jobs">
          <div class="section-title">
            <div>
              <div class="eyebrow">Shared work queue</div>
              <h2 id="jobsTitle">ศูนย์รับงานรวม</h2>
              <p id="jobsSubtitle">
                Staff ทุกคนใน Role เห็นงานใหม่ร่วมกัน และกดรับงานก่อนอัปเดตสถานะ
              </p>
            </div>
            <div class="toolbar">
              <input
                class="field-compact search"
                id="jobSearch"
                placeholder="ค้นหาเลขงาน ห้อง หรือรายละเอียด"
              />
              <select
                class="field-compact"
                id="categoryFilter"
                aria-label="กรองประเภทงานที่ผู้ใช้เลือก"
              ></select>
              <select class="field-compact" id="jobStatusFilter">
                <option value="all">ทุกสถานะ</option>
                <option value="รอรับงาน">รอรับงาน</option>
                <option value="รับงานแล้ว">รับงานแล้ว</option>
                <option value="กำลังดำเนินการ">กำลังดำเนินการ</option>
                <option value="รอข้อมูลเพิ่มเติม">รอข้อมูลเพิ่มเติม</option>
                <option value="เสร็จสิ้น">เสร็จสิ้น</option>
                <option value="ยกเลิก">ยกเลิก</option>
                <option value="คืนเข้าคิวกลาง">คืนเข้าคิวกลาง</option>
              </select>
            </div>
          </div>


          <div class="job-list" id="jobList"></div>
        </section>
</template>
