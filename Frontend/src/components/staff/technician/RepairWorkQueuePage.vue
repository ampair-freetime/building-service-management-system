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
                <option value="รออะไหล่">รออะไหล่</option>
                <option value="เสร็จสิ้น">เสร็จสิ้น</option>
                <option value="ยกเลิก">ยกเลิก</option>
                <option value="คืนเข้าคิวกลาง">คืนเข้าคิวกลาง</option>
              </select>
            </div>
          </div>
          <div class="queue-explainer">
            <div class="queue-explainer-icon">↳</div>
            <div>
              <strong id="queueExplainerTitle"
                >คิวนี้เป็นคิวร่วมของ Role</strong
              >
              <p>
                งานใหม่ยังไม่มีเจ้าของ ทุกคนใน Role สามารถเห็นและกดรับได้
                คนที่รับสำเร็จจะเป็นผู้แก้ไขสถานะงานนั้น
              </p>
            </div>
          </div>
          <div class="board-tabs" id="boardTabs">
            <button class="board-tab active" data-view="unassigned">
              งานรอรับร่วม
            </button>
            <button class="board-tab" data-view="mine">งานของฉัน</button>
            <button class="board-tab" data-view="team">งานของทีม</button>
            <button class="board-tab" data-view="all">ทั้งหมด</button>
          </div>
          <div class="job-list" id="jobList"></div>
        </section>
</template>
