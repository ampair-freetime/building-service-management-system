# คู่มือการติดตั้งและบริหารจัดการระบบ CS Building Care

**เวอร์ชัน:** 1.0.0
**วันที่ส่งมอบ:** ตุลาคม 2026

| ต้องการ | ไปที่ |
| --- | --- |
| เตรียมของก่อนติดตั้ง | [2. สิ่งที่ต้องจัดเตรียมล่วงหน้า](#2-สิ่งที่ต้องจัดเตรียมล่วงหน้า-prerequisites) |
| ติดตั้งบนเซิร์ฟเวอร์จริง | [3. ขั้นตอนการติดตั้งระบบ](#3-ขั้นตอนการติดตั้งระบบ-installation) |
| ตรวจรับงาน | [4. ขั้นตอนการตรวจรับงาน](#4-ขั้นตอนการตรวจรับงาน-verification-checklist) |
| ใช้งานประจำวัน, Backup, อัปเดต | [5. การบริหารจัดการและบำรุงรักษา](#5-การบริหารจัดการและบำรุงรักษา-operations--maintenance) |
| มีปัญหา | [6. การวิเคราะห์และแก้ไขปัญหาเบื้องต้น](#6-การวิเคราะห์และแก้ไขปัญหาเบื้องต้น-troubleshooting) |
| ลองระบบบนเครื่องตัวเอง / นักพัฒนา | [7. ภาคผนวก](#7-ภาคผนวก) |

---

## 1. ข้อมูลระบบโดยสังเขป (System Overview)

ระบบ **CS Building Care** เป็นเว็บแอปพลิเคชันสำหรับบริหารจัดการงาน **แจ้งซ่อม**, **แจ้งทำความสะอาด**
และ **ของหาย/ของที่พบ (Lost & Found)** ภายในอาคาร

- **ผู้ใช้ทั่วไป (Guest):** สแกน QR Code ในห้อง → แจ้งเรื่องพร้อมรูป → ได้รหัสติดตามทางอีเมล ไม่ต้องมีบัญชี
- **เจ้าหน้าที่:** แม่บ้าน (housekeeper), ช่าง (technician), เจ้าหน้าที่ของหาย (clerk) รับงานและปิดงาน
- **ผู้ดูแลระบบ (admin):** จัดการบัญชีเจ้าหน้าที่ สถานที่ และ QR Code

ส่วนประกอบหลัก:

- **Frontend:** Vue 3 (Vite) build เป็นไฟล์ static เสิร์ฟด้วย Nginx ใน container
- **Backend:** FastAPI (Python 3.12) + SQLAlchemy 2.0 / Alembic
- **Database:** PostgreSQL 16 (เก็บใน Docker volume)
- **Object Storage:** Cloudflare R2 (bucket แบบ private; ผู้ใช้เปิดรูปผ่านลิงก์ที่ระบบลงลายเซ็นไว้)
- **Notification Service:** อีเมลผ่าน SMTP (คำเชิญเจ้าหน้าที่, ลิงก์รีเซ็ตรหัสผ่าน, รหัสติดตามของ guest)

```text
ผู้ใช้ ──HTTPS 443──► Nginx บนเครื่อง (TLS / certbot)          deploy/nginx/building-care.conf
                          │ HTTP 127.0.0.1:8080
                          ▼
                    frontend container (Nginx: หน้าเว็บ + ส่ง /api และ /health ต่อ)
                          │ เครือข่าย Docker ภายใน
                          ▼
                    backend container (FastAPI) ──► PostgreSQL container
                          ├──► Cloudflare R2 (รูปภาพ)
                          └──► SMTP (อีเมล)
```

HTTPS สิ้นสุดที่ Nginx บนเครื่อง ภายในเซิร์ฟเวอร์ใช้ HTTP ซึ่งเข้าถึงจากภายนอกไม่ได้

---

## 2. สิ่งที่ต้องจัดเตรียมล่วงหน้า (Prerequisites)

### 2.1 สเปกเซิร์ฟเวอร์ขั้นต่ำ (Hardware Requirements)

- **ระบบปฏิบัติการ:** Ubuntu 22.04 LTS หรือ 24.04 LTS
- **หน่วยประมวลผล (CPU):** 2 vCPU ขึ้นไป
- **หน่วยความจำ (RAM):** 4 GB ขึ้นไป (2 GB ใช้ได้ถ้าเปิด swap)
- **พื้นที่จัดเก็บข้อมูล (Storage):** 20 GB SSD ขึ้นไป (รูปภาพอยู่ใน R2 ไม่กินดิสก์เครื่อง)

### 2.2 ซอฟต์แวร์ที่ต้องติดตั้งบนเซิร์ฟเวอร์

- **Docker Engine** 24.0 ขึ้นไป
- **Docker Compose plugin** v2.24 ขึ้นไป
- **Git**
- **Nginx** และ **Certbot** (สำหรับ HTTPS)

คำสั่งติดตั้งอยู่ใน [ขั้นตอนที่ 1](#ขั้นตอนที่-1-เตรียมเซิร์ฟเวอร์)

### 2.3 ข้อมูลคอนฟิกและบัญชีภายนอก (Credentials Checklist)

เตรียมให้ครบ **ก่อน** เริ่มติดตั้ง ส่วนใหญ่ที่ติดตั้งไม่ผ่านเกิดจากข้อมูลไม่ครบ ไม่ใช่คำสั่งผิด

| รายการ | รายละเอียดที่ต้องเตรียม | สถานะ |
| :--- | :--- | :---: |
| **Domain & DNS** | ชื่อโดเมน (เช่น `care.example.ac.th`) ที่มี A-Record ชี้มายัง IP ของเซิร์ฟเวอร์แล้ว | [ ] |
| **เครือข่าย** | เปิดรับพอร์ต 80/443 จากอินเทอร์เน็ต (guest ใช้มือถือ 4G), ออกไปพอร์ต 443 และ **587** ได้ | [ ] |
| **SSL / HTTPS** | ใช้ Certbot (Let's Encrypt) บนเครื่อง ตามขั้นตอนที่ 7 *หรือ* proxy ของหน่วยงาน/Cloudflare (ดูหมายเหตุในขั้นตอนที่ 7) | [ ] |
| **Cloudflare R2** (บังคับ) | Account ID, Bucket Name, Access Key ID, Secret Access Key — token สิทธิ์ *Object Read & Write* เฉพาะ bucket นี้ | [ ] |
| **SMTP Account** (บังคับ) | Host ที่รองรับ **STARTTLS port 587**, Username, App Password, อีเมลผู้ส่ง (เช่น Gmail: เปิด 2-Step Verification → App passwords) | [ ] |
| **Admin คนแรก** | อีเมลจริงและชื่อ-นามสกุลของผู้ดูแลระบบ | [ ] |

---

## 3. ขั้นตอนการติดตั้งระบบ (Installation)

**ทุกคำสั่งตั้งแต่ขั้นตอนที่ 2 เป็นต้นไป รันในโฟลเดอร์ `/srv/building-care`**

### ขั้นตอนที่ 1: เตรียมเซิร์ฟเวอร์

```bash
curl -fsSL https://get.docker.com | sudo sh            # Docker Engine + Compose plugin
sudo usermod -aG docker $USER                           # จากนั้น logout แล้ว login ใหม่
sudo apt install -y git nginx certbot python3-certbot-nginx
sudo ufw allow OpenSSH && sudo ufw allow 'Nginx Full' && sudo ufw enable
sudo timedatectl set-timezone Asia/Bangkok

docker --version && docker compose version              # Docker ≥ 24.0, Compose ≥ v2.24
```

### ขั้นตอนที่ 2: ดึง Source Code มายังเซิร์ฟเวอร์

```bash
sudo mkdir -p /srv/building-care && sudo chown $USER /srv/building-care
git clone https://github.com/ampair-freetime/building-service-management-system.git /srv/building-care
cd /srv/building-care
```

### ขั้นตอนที่ 3: ตั้งค่า Environment Variables (`.env`)

```bash
cp .env.production.example .env
chmod 600 .env                       # ไฟล์นี้มีรหัสผ่าน ให้เจ้าของอ่านได้คนเดียว
openssl rand -hex 32                 # รัน 3 ครั้ง ได้ 3 ค่าสำหรับ 3 ตัวแปรลับด้านล่าง
nano .env
```

แทนที่ทุกค่าที่ขึ้นต้นด้วย `REPLACE_`:

| ตัวแปร | ค่าที่ต้องใส่ |
| --- | --- |
| `PUBLIC_BASE_URL` | `https://care.example.ac.th` — **HTTPS เท่านั้น** ฝังอยู่ใน QR และลิงก์อีเมล ต้องถูกต้องก่อนพิมพ์ QR |
| `BACKEND_CORS_ORIGINS` | `["https://care.example.ac.th"]` (รูปแบบ JSON list) |
| `POSTGRES_PASSWORD` | ค่าจาก `openssl rand -hex 32` ค่าที่ 1 |
| `JWT_SECRET_KEY` | ค่าจาก `openssl rand -hex 32` ค่าที่ 2 (เปลี่ยนภายหลัง = ทุกคนถูก logout) |
| `IMAGE_URL_SECRET` | ค่าจาก `openssl rand -hex 32` ค่าที่ 3 (เปลี่ยนภายหลัง = ลิงก์รูปเดิมใช้ไม่ได้) |
| `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME` | จาก Cloudflare R2 |
| `SMTP_HOST`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `MAIL_FROM` | จากผู้ให้บริการอีเมล (Gmail: `smtp.gmail.com`, `SMTP_PORT=587`) |

- ระบบส่งอีเมลด้วย **STARTTLS ที่ port 587 เท่านั้น** (เข้ารหัสก่อนส่งรหัสผ่าน SMTP) ผู้ให้บริการที่มีแค่ port 465 ใช้ไม่ได้
- ค่าอื่นใช้ค่าเริ่มต้นได้ ไฟล์นี้มี `COMPOSE_FILE=compose.production.yaml` คำสั่ง `docker compose` บนเครื่องนี้จึงใช้ชุด production เสมอ
- ห้าม commit `.env` และห้ามใส่ความลับในตัวแปร `VITE_*` (ค่าเหล่านั้นไปอยู่ในเบราว์เซอร์)

### ขั้นตอนที่ 4: ตรวจความพร้อมก่อนติดตั้ง (Preflight Check)

```bash
# 1. ต้องไม่มีบรรทัดใดแสดงออกมา (ทุกค่า REPLACE_ ถูกแทนแล้ว)
grep -nE '^[A-Z_]+=.*REPLACE_' .env

# 2. ไฟล์ตั้งค่าถูกต้อง (ต้องไม่มีข้อความ error; คำสั่งนี้ไม่แสดงรหัสผ่าน)
docker compose config --quiet && echo "CONFIG OK"

# 3. โดเมนชี้มาที่เครื่องนี้แล้ว (สองบรรทัดต้องได้ IP เดียวกัน)
getent hosts care.example.ac.th
curl -4 -s https://api.ipify.org; echo

# 4. พอร์ต 8080 ต้องว่าง (ต้องไม่มีบรรทัดใดแสดงออกมา)
sudo ss -ltnp | grep ':8080 '
```

> หากข้อใดไม่ผ่าน ให้แก้ไขก่อนดำเนินการต่อ การเชื่อมต่อ SMTP และ R2 จะตรวจในขั้นตอนที่ 6

### ขั้นตอนที่ 5: Build, เตรียมฐานข้อมูล และสร้างบัญชีผู้ดูแลระบบ

```bash
# 1. Build image (ครั้งแรกประมาณ 5–10 นาที ขึ้นกับความเร็วอินเทอร์เน็ต)
docker compose build

# 2. รันคอนเทนเนอร์ฐานข้อมูล PostgreSQL และรอจนพร้อม
docker compose up -d --wait database

# 3. สร้างตารางในฐานข้อมูล (Database Migration ผ่าน Alembic)
docker compose run --rm backend alembic upgrade head

# 4. สร้างบัญชี admin คนแรกของระบบ
docker compose run --rm backend python scripts/create_initial_admin.py
```

คำสั่งที่ 4 จะถาม **อีเมล**, **ชื่อ-นามสกุล** และ **รหัสผ่าน** (พิมพ์แล้วไม่แสดงบนจอ ต้องพิมพ์ซ้ำ 2 ครั้ง)
รหัสผ่านไม่ถูกเก็บใน shell history

- กฎรหัสผ่าน: 8–128 ตัวอักษร มีตัวพิมพ์ใหญ่ ตัวพิมพ์เล็ก ตัวเลข และสัญลักษณ์อย่างละ 1 ตัว
- สำเร็จจะขึ้น `Initial admin created` — รันซ้ำจะขึ้น `Admin already exists; no changes made` โดยไม่เปลี่ยนอะไร
- **ห้ามใส่รหัสผ่านในคำสั่งด้วย `-e INITIAL_ADMIN_PASSWORD=...`** เพราะจะค้างอยู่ใน shell history
  ถ้าต้องติดตั้งแบบอัตโนมัติ (ไม่มีคนพิมพ์) ให้ใช้วิธีไฟล์ secret ตาม [Backend/scripts/INITIAL_ADMIN.md](Backend/scripts/INITIAL_ADMIN.md)

### ขั้นตอนที่ 6: เริ่มการทำงานของระบบทั้งหมดและตรวจบริการภายนอก

```bash
docker compose up -d --wait
docker compose exec backend python scripts/check_services.py
curl -fsS http://127.0.0.1:8080/health; echo
```

ผลที่ต้องได้:

```text
SMTP: CONNECTIVITY_OK (no email sent)
R2: BUCKET_ACCESS_OK (upload/delete not tested)
{"status":"ok"}
```

ถ้าขึ้น `FAILED` ดู [หัวข้อ 6](#6-การวิเคราะห์และแก้ไขปัญหาเบื้องต้น-troubleshooting)

### ขั้นตอนที่ 7: เปิดใช้งาน HTTPS

ระบบรับการเชื่อมต่อเฉพาะ `127.0.0.1:8080` จึงต้องมี Nginx บนเครื่องรับ HTTPS จากภายนอกแล้วส่งต่อเข้ามา

```bash
sudo cp deploy/nginx/building-care.conf /etc/nginx/sites-available/building-care
sudo sed -i 's/care.example.ac.th/<โดเมนจริง>/' /etc/nginx/sites-available/building-care
sudo ln -s /etc/nginx/sites-available/building-care /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

sudo certbot --nginx -d <โดเมนจริง>          # ขอใบรับรอง + เปลี่ยน HTTP เป็น HTTPS อัตโนมัติ
sudo certbot renew --dry-run                 # ตรวจว่าต่ออายุใบรับรองอัตโนมัติได้
```

> **ถ้าใช้ Cloudflare Proxy (เมฆสีส้ม) หรือ proxy ของหน่วยงานอยู่หน้าเครื่อง:**
> ตั้ง SSL mode ของ Cloudflare เป็น **Full (strict)** และเพิ่มใน `server { }` ของ
> `/etc/nginx/sites-available/building-care` เพื่อให้ระบบเห็น IP จริงของผู้ใช้
> (ไม่เช่นนั้นการจำกัด login ผิดจะนับผู้ใช้ทุกคนเป็น IP ของ proxy):
>
> ```nginx
> # ใส่ทุกช่วง IP จาก https://www.cloudflare.com/ips/ (หรือ IP ของ proxy หน่วยงาน)
> set_real_ip_from 173.245.48.0/20;
> real_ip_header CF-Connecting-IP;      # proxy หน่วยงานใช้ X-Forwarded-For
> ```

---

## 4. ขั้นตอนการตรวจรับงาน (Verification Checklist)

ผู้ติดตั้งหรือผู้ตรวจรับงานทดสอบความสมบูรณ์ของระบบตามขั้นตอนดังนี้

1. **ตรวจสอบสถานะคอนเทนเนอร์:**

   ```bash
   docker compose ps
   ```

   คอนเทนเนอร์ `database`, `backend`, `frontend` ต้องมีสถานะ `Up ... (healthy)` ทั้งหมด

2. **ทดสอบ Health Check Endpoint ผ่านโดเมนจริง:**

   ```bash
   curl -i https://<โดเมนจริง>/health
   ```

   ต้องได้สถานะ `200` และเนื้อหา `{"status":"ok"}` (ถ้า backend หยุดทำงาน endpoint นี้จะตอบ 502/504)

3. **ทดสอบระบบผ่านหน้าเว็บ (End-to-End Acceptance):**
   - [ ] เข้า `https://<โดเมน>/staff-login` ด้วยบัญชี admin จากขั้นตอนที่ 5 ได้
   - [ ] สร้างสถานที่ (Location) ใหม่ → Generate QR → ตรวจว่า URL ใน QR ขึ้นต้นด้วย `https://<โดเมนจริง>` → ดาวน์โหลดไฟล์ QR
   - [ ] เชิญเจ้าหน้าที่ 1 คน → **อีเมลคำเชิญถึงกล่องจดหมาย** → เปิดลิงก์จากมือถือ ตั้งรหัสผ่าน และ login ได้
   - [ ] ใช้มือถือ (เครือข่าย 4G ไม่ใช่ Wi-Fi ภายใน) สแกน QR → เปิดหน้าแจ้งเรื่องได้
   - [ ] ส่งคำร้องแจ้งซ่อม **พร้อมแนบรูป** → สำเร็จ และรูปแสดงในหน้าเจ้าหน้าที่ (รูปถูกเก็บใน R2 แล้ว)
   - [ ] **guest ได้รับอีเมลรหัสติดตาม** ในอีเมลที่กรอกตอนแจ้ง (ระบบส่งอีเมลให้ผู้แจ้ง ไม่ได้ส่งแจ้งเตือนถึง admin)
   - [ ] เจ้าหน้าที่รับงานและปิดงาน → guest ใช้รหัสติดตามแล้วเห็นสถานะเปลี่ยน
   - [ ] กด "ลืมรหัสผ่าน" ที่หน้า login → ได้อีเมลลิงก์ตั้งรหัสผ่านใหม่
   - [ ] กดรีเฟรชหน้า `https://<โดเมน>/staff/setup-password` แล้วต้องไม่ขึ้น 404
   - [ ] ตั้งเวลา Backup อัตโนมัติแล้ว ([หัวข้อ 5.3](#53-การสำรองและกู้คืนฐานข้อมูล-database-backup--restore))

---

## 5. การบริหารจัดการและบำรุงรักษา (Operations & Maintenance)

### 5.1 คำสั่งควบคุมการทำงานพื้นฐาน

```bash
# ตรวจสอบสถานะการทำงาน
docker compose ps

# ดูบันทึกการทำงาน (Logs) ทั้งหมดแบบ Realtime
docker compose logs -f

# ดู Logs เฉพาะส่วน Backend API (100 บรรทัดล่าสุดแล้วติดตามต่อ)
docker compose logs -f --tail 100 backend

# ตรวจการเชื่อมต่อ SMTP และ R2
docker compose exec backend python scripts/check_services.py

# สั่งเริ่มระบบใหม่ทั้งหมด (Restart) — ข้อมูลไม่หาย
docker compose restart

# ปิด / เปิดการทำงานของระบบทั้งหมด — ข้อมูลไม่หาย
docker compose down
docker compose up -d --wait
```

> ⚠️ **ห้ามใช้ `docker compose down -v`** เด็ดขาด เพราะ `-v` ลบ volume ของฐานข้อมูลทิ้งทั้งหมด
>
> หลังแก้ไฟล์ `.env` ต้องสร้าง container ใหม่ด้วย `docker compose up -d --wait` (`restart` ไม่อ่านค่าใหม่)

### 5.2 งานประจำวันของผู้ดูแลระบบ

| งาน | วิธี |
| --- | --- |
| เพิ่มเจ้าหน้าที่ | หน้า admin → บัญชีเจ้าหน้าที่ → ใส่อีเมล ชื่อ และหน้าที่ → ระบบส่งลิงก์ตั้งรหัสผ่าน (ใช้ได้ครั้งเดียว อายุ 24 ชม.) |
| ลิงก์หมดอายุ / อีเมลไม่ถึง | กด "ส่งคำเชิญอีกครั้ง" หรือรันบนเซิร์ฟเวอร์ `docker compose exec backend python scripts/invitation_link.py --email <อีเมล>` เพื่อแสดงลิงก์บนจอแล้วส่งให้เจ้าหน้าที่เอง |
| ระงับ / เปิดบัญชีคืน | หน้า admin → บัญชีเจ้าหน้าที่ บัญชีที่ถูกระงับใช้งานไม่ได้ทันที |
| เปลี่ยนหน้าที่ (role) | ยังเปลี่ยนตรง ๆ ไม่ได้: ลบบัญชีแล้วเชิญใหม่ด้วยอีเมลเดิม (ประวัติงานเดิมยังอยู่) |
| เพิ่มสถานที่ + QR | หน้า admin → ห้อง/QR → เพิ่ม → Generate QR → ดาวน์โหลด PNG หรือ ZIP หลายห้อง |
| ปิดห้องชั่วคราว | ปิดใช้งานสถานที่ การสแกน QR ของห้องนั้นใช้ไม่ได้ แต่คำร้องเดิมยังอยู่ |
| QR หลุด / ถูกคัดลอก | ยังไม่มีปุ่มในหน้าเว็บ: API `POST /api/v1/admin/locations/{id}/qr/regenerate` (token ของ admin) สร้าง QR ใหม่และทำให้ QR เดิมใช้ไม่ได้ทันที |
| ลืมรหัสผ่าน | กด "ลืมรหัสผ่าน" ที่หน้า login ระบบส่งลิงก์ทางอีเมล (อายุ 30 นาที) |

Login ผิดเกิน 5 ครั้งใน 15 นาที (หรือจาก IP เดียวกันเกิน 20 ครั้ง) จะถูกพักการ login 15 นาที

### 5.3 การสำรองและกู้คืนฐานข้อมูล (Database Backup & Restore)

**การสำรองข้อมูล (Backup):**

```bash
mkdir -p /srv/backups
(umask 077; docker compose exec -T database \
  sh -c 'pg_dump -U "$POSTGRES_USER" -Fc "$POSTGRES_DB"' > /srv/backups/bsms-$(date +%F_%H%M).dump)
```

- ไฟล์ `.dump` บีบอัดในตัวแล้ว และมี hash รหัสผ่านของเจ้าหน้าที่ จึงสร้างด้วยสิทธิ์ให้เจ้าของอ่านได้คนเดียว
- รูปภาพอยู่ใน R2 ไม่อยู่ในไฟล์นี้
- คัดลอกไฟล์ backup ออกนอกเครื่องเป็นประจำ

**ตั้งเวลา Backup อัตโนมัติทุกวัน 02:00 และเก็บไว้ 14 วัน** (`crontab -e` ของ user ที่รัน Docker แล้วเพิ่มบรรทัดเดียวนี้):

```cron
0 2 * * * cd /srv/building-care && umask 077 && docker compose exec -T database sh -c 'pg_dump -U "$POSTGRES_USER" -Fc "$POSTGRES_DB"' > /srv/backups/bsms-$(date +\%F).dump && find /srv/backups -name 'bsms-*.dump' -mtime +14 -delete
```

**การกู้คืนข้อมูล (Restore):**

```bash
docker compose stop backend frontend
docker compose exec -T database sh -c \
  'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists' < /srv/backups/bsms-YYYY-MM-DD.dump
docker compose up -d --wait
```

ควรซ้อม restore ลงฐานข้อมูลทดสอบเดือนละครั้ง

### 5.4 การอัปเดตระบบเวอร์ชันใหม่

```bash
cd /srv/building-care
# 1. สำรองข้อมูลก่อนทุกครั้ง (คำสั่ง Backup ในหัวข้อ 5.3)
# 2. ดึงโค้ดใหม่ และ build
git pull
docker compose build
# 3. อัปเดตโครงสร้างฐานข้อมูล (production ไม่ทำให้เองตอนเริ่มระบบ)
docker compose run --rm backend alembic upgrade head
# 4. เริ่มระบบด้วยเวอร์ชันใหม่ แล้วตรวจ
docker compose up -d --wait
curl -fsS https://<โดเมนจริง>/health; echo
```

ถ้าเวอร์ชันใหม่มีปัญหา: `git checkout <commit เดิม>` → `docker compose build` → restore backup ที่ทำไว้ก่อนอัปเดต → `docker compose up -d --wait`

### 5.5 การเฝ้าระวังระบบ

- ตั้งบริการ uptime monitor ภายนอก (เช่น UptimeRobot) ให้ตรวจ `https://<โดเมนจริง>/health` ทุก 5 นาที
- ตรวจพื้นที่ดิสก์ทุกสัปดาห์: `df -h` และ `docker system df`
- ตรวจขนาดรูปใน R2 (free tier 10 GB) จากหน้า Cloudflare dashboard

---

## 6. การวิเคราะห์และแก้ไขปัญหาเบื้องต้น (Troubleshooting)

| ปัญหาที่พบ | สาเหตุที่เป็นไปได้ | แนวทางการแก้ไข |
| :--- | :--- | :--- |
| `required variable ... is missing a value` | ยังไม่ได้ใส่ค่านั้นใน `.env` | ใส่ค่าตามขั้นตอนที่ 3 |
| `backend` ไม่ขึ้นสถานะ healthy | secret สั้นกว่า 32 ตัว, URL ยังเป็น `localhost` หรือ `REPLACE_`, SMTP ไม่ใช่ STARTTLS, ฐานข้อมูลยังไม่ migrate | `docker compose logs backend` ดูบรรทัด error แล้วแก้ `.env` → `docker compose up -d --wait` |
| `Pool overlaps with other one on this host` | เครือข่าย Docker ชนกับเครือข่ายเดิมบนเครื่อง | เปลี่ยน `APP_SUBNET` ใน `.env` เป็นช่วงอื่น เช่น `172.30.90.0/24` |
| เข้าเว็บได้ `502 Bad Gateway` / `504` | Backend ยังเริ่มไม่เสร็จ หรือหยุดทำงาน | `docker compose ps` และ `docker compose logs backend` |
| เข้าโดเมนแล้วเปิดไม่ได้เลย | Nginx บนเครื่องยังไม่ได้ตั้ง, DNS ยังไม่ชี้, firewall ปิด 80/443 | ทำขั้นตอนที่ 7, ตรวจ `sudo nginx -t`, `sudo ufw status` |
| อัปโหลดรูปขึ้น "ไม่สามารถบันทึกรูปภาพได้" | ดู `docker compose logs backend`: `AccessDenied` = token ไม่มีสิทธิ์ bucket, `NoSuchBucket` = ชื่อ bucket ผิด, `SSLError` / `EndpointConnectionError` = Account ID ผิดหรือออกเน็ตไป R2 ไม่ได้ | แก้ค่า `R2_*` ใน `.env` → `docker compose up -d --wait` → `check_services.py` |
| อัปโหลดรูปได้ `413` | ไฟล์ใหญ่เกิน `client_max_body_size` ของ Nginx บนเครื่อง | ตรวจว่า `/etc/nginx/sites-available/building-care` มี `client_max_body_size 60m;` |
| ไม่ได้รับอีเมล | ค่า SMTP ผิด, App Password ถูกยกเลิก, firewall บล็อกพอร์ต 587, server ไม่รองรับ STARTTLS (`check_services.py` ขึ้น `SMTPNotSupportedError`) | `check_services.py`; ระหว่างแก้ใช้ `invitation_link.py --email ...` (หัวข้อ 5.2); ดูในกล่อง Spam ด้วย |
| สร้าง admin คนแรกขึ้น `Invalid ...` | ข้อมูลไม่ผ่านกฎ (ข้อความบอกช่องและกฎ) | อีเมลต้องเป็นโดเมนจริง รหัสผ่านต้องตามกฎในขั้นตอนที่ 5 |
| สร้าง admin ขึ้น `owned by uid ...` | ใช้วิธีไฟล์ secret แต่ลืม `--user` | ดู [INITIAL_ADMIN.md](Backend/scripts/INITIAL_ADMIN.md) |
| Login ได้ `429` | Login ผิดหลายครั้ง | รอ 15 นาที (ปรับได้ด้วย `LOGIN_*` ใน `.env`) |
| Log ของ backend เห็น IP เดียวกันทุกคำขอ | มี proxy อยู่หน้า Nginx บนเครื่องแต่ยังไม่ได้ตั้ง real IP | ดูหมายเหตุ Cloudflare / proxy ในขั้นตอนที่ 7 |
| แก้ `.env` แล้วไม่มีผล | `restart` ไม่อ่านค่าใหม่ | `docker compose up -d --wait` (ค่า `VITE_*` ต้อง `docker compose build` ใหม่) |

---

## 7. ภาคผนวก

### 7.1 ค่าตั้งค่าที่ควรรู้

ค่าทั้งหมดพร้อมคำอธิบายอยู่ใน [`.env.production.example`](.env.production.example)

| ตัวแปร | ค่าเริ่มต้น | หมายเหตุ |
| --- | --- | --- |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | อายุการ login (8 ชม.) |
| `INVITATION_TOKEN_EXPIRE_HOURS` | `24` | อายุลิงก์เชิญเจ้าหน้าที่ |
| `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES` | `30` | อายุลิงก์ตั้งรหัสผ่านใหม่ |
| `LOGIN_ACCOUNT_FAILURE_LIMIT` / `LOGIN_IP_FAILURE_LIMIT` | `5` / `20` | จำนวน login ผิดก่อนถูกพัก ภายใน `LOGIN_FAILURE_WINDOW_SECONDS` (900) |
| `MAX_IMAGE_UPLOAD_BYTES` × `MAX_GUEST_IMAGES` | 10 MB × 5 | ต้องไม่เกิน `client_max_body_size 60m` ของ Nginx ทั้งสองชั้น |
| `DEFAULT_CUSTODY_LOCATION` | `ห้องธุรการ ชั้น 1` | จุดฝากของที่พบที่แสดงให้ guest |
| `APP_SUBNET` | `172.30.80.0/24` | เครือข่ายภายใน Docker ที่ใช้ระบุ IP จริงของผู้ใช้ |
| `FRONTEND_BIND_ADDRESS:FRONTEND_PORT` | `127.0.0.1:8080` | ให้เฉพาะ Nginx บนเครื่องเข้าถึง |

ข้อจำกัดที่ตั้งใจไว้: backend รัน 1 worker (ตัวนับ rate limit อยู่ในหน่วยความจำ)
รับคำขอพร้อมกันได้ 16 รายการ เกินจากนั้นตอบ 503

### 7.2 ลองใช้บนเครื่องตัวเอง (Development)

ต้องมี Docker Desktop หรือ Docker Engine + Compose v2.24 ขึ้นไป **ห้ามใช้ชุดนี้บนเซิร์ฟเวอร์จริง**

```bash
git clone https://github.com/ampair-freetime/building-service-management-system.git
cd building-service-management-system
docker compose up --build
```

| หน้า | URL |
| --- | --- |
| เว็บ (guest) | http://localhost:5173/user |
| เข้าสู่ระบบเจ้าหน้าที่ | http://localhost:5173/staff-login |
| API docs | http://localhost:8000/docs |

- บัญชี admin สำหรับทดลอง (มีเฉพาะ development): `admin@example.com` / `Admin@1234`
- Development ใช้ HTTP ทั้งหมดบนเครื่องตัวเอง และรัน migration ให้เองตอนเริ่ม
- ไม่ได้ตั้ง R2 ก็ใช้งานได้ แต่จะแนบรูปไม่ได้

**ทดลองเชิญเจ้าหน้าที่โดยไม่ต้องมีอีเมลจริง:** สร้างไฟล์ `.env` ที่ root ของโปรเจกต์ ใส่

```dotenv
SMTP_HOST=mailpit
SMTP_PORT=1025
SMTP_USE_STARTTLS=false
```

แล้วรัน `docker compose --profile mail up -d` อีเมลทุกฉบับจะไปอยู่ที่ http://localhost:8025

### 7.3 สำหรับนักพัฒนา

```bash
cd Backend
uv run --extra dev pytest        # tests ทั้งหมด (pytest อยู่ใน extra "dev")
uv run --extra dev ruff check .
```

| โฟลเดอร์ / ไฟล์ | เนื้อหา |
| --- | --- |
| `Backend/app` | FastAPI: `api/` endpoints, `services/` business logic, `models/` ตาราง |
| `Backend/migrations` | Alembic migrations |
| `Backend/scripts` | `create_initial_admin.py`, `invitation_link.py`, `check_services.py`, `seed_locations.py` |
| `Frontend/src` | Vue 3 + Vite |
| `compose.yaml` | development (hot reload, port 5173/8000) |
| `compose.production.yaml` | production |
| `deploy/nginx` | config ของ Nginx บนเครื่อง (HTTPS) |
