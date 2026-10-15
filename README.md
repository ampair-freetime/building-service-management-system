# CS Building Care

เว็บแจ้งซ่อม แจ้งทำความสะอาด และของหาย/ของที่พบภายในอาคาร
guest สแกน QR ในห้องแล้วแจ้งเรื่องได้โดยไม่ต้องมีบัญชี เจ้าหน้าที่ (แม่บ้าน ช่าง ธุรการ) รับงานและปิดงานผ่านเว็บ

ระบบประกอบด้วย Vue 3 + FastAPI + PostgreSQL 16 รันด้วย Docker Compose เก็บรูปใน Cloudflare R2 และส่งอีเมลผ่าน SMTP

ทุกงานบนเซิร์ฟเวอร์ใช้คำสั่งเดียว: **`./deploy/bcare.sh <งาน>`**

## 1. ติดตั้งทีละขั้น (สำหรับผู้รับมอบระบบ)

**ก่อนเริ่ม ต้องมี:**

- เซิร์ฟเวอร์ Linux 64-bit (2 vCPU, RAM 4 GB, ดิสก์ 20 GB) ที่ภายนอก (มือถือ 4G) เข้าพอร์ต 80/443 ได้ และเครื่องออกอินเทอร์เน็ตพอร์ต 443 และ 587 ได้
- โดเมน เช่น `care.example.ac.th` ที่ชี้มาที่เครื่องแล้ว (ต้องถูกต้องก่อนพิมพ์ QR)
- Cloudflare R2: Account ID, Bucket Name, Access Key ID, Secret Access Key (สิทธิ์ Object Read & Write เฉพาะ bucket)
- บัญชี SMTP ที่ใช้ **STARTTLS พอร์ต 587**: Host, Username, App Password, อีเมลผู้ส่ง (Gmail: เปิด 2-Step Verification → App passwords)

### ขั้นที่ 1 — ติดตั้ง Docker (ข้ามได้ถ้ามีแล้ว)

```bash
curl -fsSL https://get.docker.com | sudo sh && sudo usermod -aG docker $USER
```

แล้ว logout / login ใหม่ 1 ครั้ง (ตัวอย่างนี้สำหรับ Ubuntu)

### ขั้นที่ 2 — ดึงโค้ดมาไว้บนเครื่อง

```bash
git clone https://github.com/ampair-freetime/building-service-management-system.git /srv/building-care
cd /srv/building-care
```

ทุกคำสั่งหลังจากนี้รันในโฟลเดอร์ `/srv/building-care`

### ขั้นที่ 3 — สร้างไฟล์ตั้งค่า

```bash
./deploy/bcare.sh install
```

สคริปต์จะสร้างไฟล์ `.env` สุ่มรหัสลับให้เอง แล้ว **หยุด** พร้อมบอกบรรทัดที่ยังเป็น `REPLACE_` (ถูกต้องตามขั้นตอน)

### ขั้นที่ 4 — กรอกค่าใน `.env`

```bash
nano .env
```

แทนที่ทุกค่าที่ขึ้นต้นด้วย `REPLACE_` แล้วบันทึก (Ctrl+O, Enter, Ctrl+X)

| ตัวแปร | ค่า |
| --- | --- |
| `PUBLIC_BASE_URL` | `https://care.example.ac.th` |
| `BACKEND_CORS_ORIGINS` | `["https://care.example.ac.th"]` |
| `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME` | จาก Cloudflare R2 |
| `SMTP_HOST`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `MAIL_FROM` | จากผู้ให้บริการอีเมล (Gmail: `smtp.gmail.com`) |

### ขั้นที่ 5 — ติดตั้งระบบ

```bash
./deploy/bcare.sh install
```

รอบนี้สคริปต์ทำต่อจนจบ (ครั้งแรก 5–10 นาที): build → สร้างตารางฐานข้อมูล → **ถามอีเมล ชื่อ และรหัสผ่านของ admin คนแรก**
→ เริ่มระบบ → ตรวจ SMTP / R2 → ตั้ง backup อัตโนมัติทุกวัน 02:00

รหัสผ่าน admin: 8–128 ตัว มีตัวพิมพ์ใหญ่ เล็ก ตัวเลข และสัญลักษณ์ (พิมพ์แล้วไม่แสดงบนจอ) ผลที่ต้องได้ท้ายสุด:

```text
SMTP: CONNECTIVITY_OK (no email sent)
R2: BUCKET_ACCESS_OK (upload/delete not tested)
{"status":"ok"}
```

ถ้ามีบรรทัด `FAILED` ดู [แก้ปัญหา](#3-แก้ปัญหา) แก้ `.env` แล้วรันขั้นที่ 5 ซ้ำได้เลย (ขั้นที่ทำแล้วจะข้าม)

### ขั้นที่ 6 — เปิด HTTPS

```bash
sudo apt install -y nginx certbot python3-certbot-nginx     # ข้ามได้ถ้ามีแล้ว
./deploy/bcare.sh https care.example.ac.th
```

ถ้าหน่วยงานมี reverse proxy / HTTPS ให้อยู่แล้ว ไม่ต้องทำขั้นนี้: ตั้ง `FRONTEND_BIND_ADDRESS` ใน `.env` เป็น IP ภายในของเครื่อง
แล้วรันขั้นที่ 5 ซ้ำ และให้ proxy ส่งต่อไป `http://<IP>:8080` พร้อม header `X-Forwarded-Proto: https`, `X-Forwarded-For` และรับไฟล์ได้ 60 MB

### ขั้นที่ 7 — ตรวจว่าใช้งานได้

1. เปิด `https://care.example.ac.th/health` ต้องเห็น `{"status":"ok"}`
2. เปิด `https://care.example.ac.th/staff-login` แล้ว login ด้วยบัญชี admin จากขั้นที่ 5
3. เพิ่มสถานที่ → Generate QR → ใช้มือถือ (4G) สแกนแล้วแจ้งเรื่องพร้อมรูปได้

เสร็จแล้ว จากนี้ใช้คำสั่งในหัวข้อถัดไปดูแลระบบ

## 2. ดูแลระบบ

| คำสั่ง | ทำอะไร |
| --- | --- |
| `./deploy/bcare.sh status` | สถานะ container + ตรวจ SMTP / R2 / `/health` |
| `./deploy/bcare.sh logs backend` | ดู log (Ctrl+C ออก) |
| `./deploy/bcare.sh backup` | สำรองฐานข้อมูลไป `/srv/backups` (เก็บ 14 วัน) |
| `./deploy/bcare.sh restore <ไฟล์.dump>` | กู้คืนฐานข้อมูล (ถามยืนยันก่อน) |
| `./deploy/bcare.sh update` | backup → ดึงโค้ดใหม่ → build → อัปเดตฐานข้อมูล → เริ่มระบบ |

- แก้ `.env` แล้วรัน `./deploy/bcare.sh install` ให้ค่าใหม่มีผล
- ⚠️ ห้ามใช้ `docker compose down -v` (ลบฐานข้อมูลทิ้งทั้งหมด)
- คัดลอก `/srv/backups` ออกนอกเครื่องเป็นประจำ รูปภาพอยู่ใน R2 ไม่อยู่ใน backup
- ตั้ง uptime monitor ตรวจ `https://<โดเมน>/health` ทุก 5 นาที

### สิ่งที่ผู้ดูแลระบบสามารถทำได้

| งาน | วิธี |
| --- | --- |
| เพิ่มเจ้าหน้าที่ | หน้า admin → บัญชีเจ้าหน้าที่ → ระบบส่งลิงก์ตั้งรหัสผ่าน (ใช้ครั้งเดียว อายุ 24 ชม.) |
| ลิงก์หมดอายุ / อีเมลไม่ถึง | กด "ส่งคำเชิญอีกครั้ง" หรือ `docker compose exec backend python scripts/invitation_link.py --email <อีเมล>` แล้วส่งลิงก์ให้เอง |
| ระงับ / เปิดบัญชีคืน | หน้า admin → บัญชีเจ้าหน้าที่ |
| เปลี่ยนหน้าที่ (role) | ลบบัญชีแล้วเชิญใหม่ด้วยอีเมลเดิม (ประวัติงานยังอยู่) |
| เพิ่มสถานที่ + QR | หน้า admin → ห้อง/QR → เพิ่ม → Generate QR → ดาวน์โหลด PNG/ZIP |
| ปิดห้องชั่วคราว | ปิดใช้งานสถานที่ (QR ใช้ไม่ได้ คำร้องเดิมยังอยู่) |
| ลืมรหัสผ่าน | "ลืมรหัสผ่าน" ที่หน้า login (ลิงก์อายุ 30 นาที) |

Login ผิดเกิน 5 ครั้งใน 15 นาที (หรือ IP เดียวกันเกิน 20 ครั้ง) จะถูกพัก 15 นาที

## 3. แก้ปัญหา

ดู log ก่อนเสมอ: `./deploy/bcare.sh logs backend`

| อาการ | แก้ |
| --- | --- |
| `install` หยุดพร้อมรายการ `REPLACE_` | กรอก `.env` ให้ครบแล้วรันใหม่ |
| `user นี้สั่ง docker ไม่ได้` | `sudo usermod -aG docker $USER` แล้ว logout/login |
| `R2: FAILED` | `AccessDenied` = token ไม่มีสิทธิ์, `NoSuchBucket` = ชื่อผิด, `SSLError` = Account ID ผิดหรือออกเน็ตไม่ได้ |
| `SMTP: FAILED` | ค่าผิด, App Password ถูกยกเลิก, พอร์ตถูกบล็อก — ระหว่างแก้ใช้ `invitation_link.py` |
| เว็บได้ `502` / `504` | backend ยังไม่พร้อม: `./deploy/bcare.sh status` |
| อัปโหลดได้ `413` | Nginx/proxy หน้าเครื่องต้องตั้ง `client_max_body_size 60m;` |
| `Pool overlaps` / `port is already allocated` | เปลี่ยน `APP_SUBNET` หรือ `FRONTEND_PORT` ใน `.env` |
| Login ได้ `429` | รอ 15 นาที (ปรับด้วย `LOGIN_*` ใน `.env`) |

## 4. สำหรับนักพัฒนา

```bash
docker compose up --build        # http://localhost:5173 (admin@example.com / Admin@1234), ห้ามใช้บนเซิร์ฟเวอร์จริง
cd Backend && uv run --extra dev pytest
```

ค่าตั้งทั้งหมดอยู่ใน [`.env.production.example`](.env.production.example)
