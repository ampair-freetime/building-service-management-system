<template>
<section class="page active" id="page-dashboard">
          <div class="section-title">
      <div>
        <div class="eyebrow">Clerk Overview</div>
        <h2>ภาพรวมงาน</h2>
      </div>
      
    </div>
          <div class="metrics" id="metricGrid"></div>
          <section class="panel" style="margin-bottom: 20px">
            <div class="panel-head">
              <div>
                <h3>ดำเนินการด่วน</h3>
                <p>เลือกสิ่งที่ต้องทำต่อจากสถานะงานปัจจุบัน</p>
              </div>
            </div>
            <div class="panel-body">
              <div class="quick-action-grid" id="dashboardQuickActions"></div>
            </div>
          </section>
          <div class="grid-2">
            <section class="panel">
              <div class="panel-head">
                <div>
                  <h3 id="queueTitle">คิวงานรวมที่ควรรับก่อน</h3>
                  <p>งานที่ยังไม่มีผู้รับผิดชอบ เรียงตามความเร่งด่วน</p>
                </div>
                <button class="text-btn" data-go="jobs">
                  เปิดศูนย์รับงาน →
                </button>
              </div>
              <div class="panel-body">
                <div class="queue" id="priorityQueue"></div>
              </div>
            </section>
            <section class="panel">
              <div class="panel-head">
                <div>
                  <h3>กิจกรรมล่าสุด</h3>
                  <p>การเปลี่ยนแปลงใน Role ของคุณ</p>
                </div>
              </div>
              <div class="panel-body">
                <div class="activity" id="activityList"></div>
              </div>
            </section>
          </div>
        </section>
</template>
