<template>
<section class="page active" id="page-dashboard">
          <div class="hero">
            <article class="hero-main">
              <div class="eyebrow" id="heroEyebrow">งานทั้งหมดของอาคาร</div>
              <h2 id="heroTitle">
                เห็นภาพรวม ตัดสินใจเร็ว และส่งงานถึงคนที่รับผิดชอบ
              </h2>
              <p id="heroText">
                ติดตามงานแจ้งซ่อม งานทำความสะอาด และของหาย–ของได้คืนจากจุดเดียว
              </p>
              <div class="hero-actions">
                <button class="primary" id="heroPrimary" type="button">
                  ดูงานเร่งด่วน
                </button>
              </div>
            </article>
            <aside class="hero-side">
              <h3>สถานะคิวปัจจุบัน</h3>
              <div class="pulse">
                <div class="pulse-ring">
                  <strong id="completion">68%</strong>
                </div>
                <div class="pulse-copy">
                  <strong id="pulseHeadline">17 จาก 25 งาน</strong
                  ><span id="pulseSub">มีผู้รับผิดชอบแล้ว</span>
                </div>
              </div>
              <div class="badge progress" id="shiftBadge">
                กะปัจจุบัน · 08:00–17:00
              </div>
            </aside>
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
