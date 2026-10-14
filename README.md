# CS Building Care

ระบบแจ้งซ่อม แจ้งทำความสะอาด และของหาย/ของที่พบ สำหรับอาคาร

- **ผู้ใช้ทั่วไป (guest)** สแกน QR ในห้อง → แจ้งเรื่อง → ติดตามสถานะด้วยรหัสที่ได้ทางอีเมล ไม่ต้องมีบัญชี
- **เจ้าหน้าที่** (แม่บ้าน, ช่าง, เจ้าหน้าที่ของหาย) รับงานและปิดงานในหน้า staff
- **Admin** จัดการบัญชีเจ้าหน้าที่ สถานที่ และ QR code

เทคโนโลยี: FastAPI + PostgreSQL 16 + Vue 3 รันทั้งหมดด้วย Docker Compose
รูปภาพเก็บใน Cloudflare R2 และส่งอีเมลผ่าน SMTP

| ต้องการ | ไปที่ |
| --- | --- |
| ลองระบบบนเครื่องตัวเอง | [1. ลองใช้บนเครื่องตัวเอง](#1-ลองใช้บนเครื่องตัวเอง) |
| ติดตั้งบนเซิร์ฟเวอร์จริง | [2. ติดตั้ง Production](#2-ติดตั้ง-production) |
| เพิ่มเจ้าหน้าที่ / สถานที่ / QR | [3. ใช้งานประจำวันของ Admin](#3-ใช้งานประจำวันของ-admin) |
| Backup, อัปเดต, ดู log | [4. ดูแลระบบ](#4-ดูแลระบบ) |
| มีปัญหา | [5. แก้ปัญหาที่พบบ่อย](#5-แก้ปัญหาที่พบบ่อย) |

---

## 1. ลองใช้บนเครื่องตัวเอง

ต้องมี Docker Desktop หรือ Docker Engine + Compose v2.24 ขึ้นไป

```bash
git clone https://github.com/ampair-freetime/building-service-management-system.git
cd building-service-management-system
docker compose up --build
```

ครั้งแรกใช้เวลา build ประมาณ 5–10 นาที (ขึ้นกับความเร็วอินเทอร์เน็ต) ครั้งต่อไปเร็วขึ้นมาก

| หน้า | URL |
| --- | --- |
| เว็บ (guest) | http://localhost:5173/user |
| เข้าสู่ระบบเจ้าหน้าที่ | http://localhost:5173/staff-login |
| API docs | http://localhost:8000/docs |

บัญชี admin สำหรับทดลอง (มีเฉพาะ development): `admin@example.com` / `Admin@1234`

**ทดลองเชิญเจ้าหน้าที่โดยไม่ต้องมีอีเมลจริง:** สร้างไฟล์ `.env` ที่ root ของโปรเจกต์ ใส่

```dotenv
SMTP_HOST=mailpit
SMTP_PORT=1025
SMTP_USE_STARTTLS=false
```

แล้วรัน `docker compose --profile mail up -d` อีเมลทุกฉบับจะไปอยู่ที่ http://localhost:8025

ไม่ได้ตั้ง R2 ก็ใช้งานได้ แต่จะแนบรูปไม่ได้ (ระบบตอบว่า "ระบบจัดเก็บรูปภาพยังไม่ได้ตั้งค่า")

---

## 2. ติดตั้ง Production

```text
ผู้ใช้ ──HTTPS──► Nginx บนเครื่อง (TLS)  ──► frontend container :8080 (หน้าเว็บ + ส่ง /api ต่อ)
                 deploy/nginx/building-care.conf          │
                                                          ▼
                       Cloudflare R2, SMTP ◄── backend container ──► PostgreSQL (Docker volume)
```

### 2.1 สิ่งที่ต้องเตรียม

| รายการ | รายละเอียด |
| --- | --- |
| เซิร์ฟเวอร์ | Ubuntu 22.04/24.04, 2 vCPU, RAM 2–4 GB, ดิสก์ 20 GB ขึ้นไป |
| โดเมน | DNS ชี้มาที่เครื่องแล้ว เช่น `care.example.ac.th` |
| เครือข่าย | เปิดรับ 80/443 จากอินเทอร์เน็ต (guest ใช้มือถือ 4G), ออกไป 443 และพอร์ต SMTP ได้ |
| Cloudflare R2 (**บังคับ**) | bucket แบบ private + API token สิทธิ์ *Object Read & Write* เฉพาะ bucket นั้น |
| SMTP (**บังคับ**) | ใช้ส่งคำเชิญเจ้าหน้าที่ ลิงก์รีเซ็ตรหัสผ่าน และรหัสติดตามให้ guest เช่น Gmail + App Password |

ติดตั้งโปรแกรม:

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER          # จากนั้น logout แล้ว login ใหม่
sudo apt install -y git nginx certbot python3-certbot-nginx
sudo ufw allow OpenSSH && sudo ufw allow 'Nginx Full' && sudo ufw enable
```

### 2.2 ดาวน์โหลดโค้ด

```bash
sudo mkdir -p /srv/building-care && sudo chown $USER /srv/building-care
git clone https://github.com/ampair-freetime/building-service-management-system.git /srv/building-care
cd /srv/building-care
```

**ทุกคำสั่งหลังจากนี้รันในโฟลเดอร์ `/srv/building-care`**

### 2.3 ตั้งค่า `.env`

```bash
cp .env.production.example .env
chmod 600 .env
openssl rand -hex 32     # รัน 3 ครั้ง ได้ค่าสำหรับ POSTGRES_PASSWORD, JWT_SECRET_KEY, IMAGE_URL_SECRET
nano .env
```

แก้ทุกค่าที่ขึ้นต้นด้วย `REPLACE_`:

| ตัวแปร | ใส่อะไร |
| --- | --- |
| `PUBLIC_BASE_URL` | `https://care.example.ac.th` — ฝังอยู่ใน QR และลิงก์อีเมล **ตั้งให้ถูกก่อนพิมพ์ QR** |
| `BACKEND_CORS_ORIGINS` | `["https://care.example.ac.th"]` |
| `POSTGRES_PASSWORD`, `JWT_SECRET_KEY`, `IMAGE_URL_SECRET` | ค่าจาก `openssl rand -hex 32` คนละค่ากัน |
| `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME` | จาก Cloudflare |
| `SMTP_HOST`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `MAIL_FROM` | จากผู้ให้บริการอีเมล (Gmail: `smtp.gmail.com`, port 587) |

ค่าอื่นใช้ค่าเริ่มต้นได้ ไฟล์ `.env` นี้มี `COMPOSE_FILE=compose.production.yaml`
คำสั่ง `docker compose` บนเครื่องนี้จึงใช้ชุด production เสมอ

> ห้าม commit `.env` และห้ามใส่ความลับในตัวแปร `VITE_*` (ค่าเหล่านั้นไปอยู่ในเบราว์เซอร์)

### 2.4 Build, สร้างฐานข้อมูล และสร้าง admin คนแรก

```bash
docker compose build                                   # ครั้งแรกประมาณ 5–10 นาที
docker compose up -d --wait database
docker compose run --rm backend alembic upgrade head   # สร้างตารางในฐานข้อมูล
docker compose run --rm backend python scripts/create_initial_admin.py
```

คำสั่งสุดท้ายจะถาม อีเมล ชื่อ และรหัสผ่านของ admin คนแรก
(รหัสผ่าน 8 ตัวขึ้นไป มีตัวพิมพ์ใหญ่ ตัวพิมพ์เล็ก ตัวเลข และสัญลักษณ์)
รายละเอียดและวิธีแบบอัตโนมัติอยู่ใน [Backend/scripts/INITIAL_ADMIN.md](Backend/scripts/INITIAL_ADMIN.md)

### 2.5 เปิดระบบและตรวจ

```bash
docker compose up -d --wait
docker compose exec backend python scripts/check_services.py   # ต้องได้ SMTP และ R2 เป็น OK
curl -fsS http://127.0.0.1:8080/health                          # ต้องได้ {"status":"ok"}
```

### 2.6 เปิด HTTPS

```bash
sudo cp deploy/nginx/building-care.conf /etc/nginx/sites-available/building-care
sudo nano /etc/nginx/sites-available/building-care        # เปลี่ยน server_name เป็นโดเมนจริง
sudo ln -s /etc/nginx/sites-available/building-care /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d care.example.ac.th
```

### 2.7 ทดสอบก่อนเปิดให้ใช้จริง

1. Login เป็น admin ที่ `https://<โดเมน>/staff-login`
2. เพิ่มสถานที่ 1 ห้อง → Generate QR → ตรวจว่า URL ใน QR เป็นโดเมนจริง
3. เชิญเจ้าหน้าที่ 1 คน → ตรวจว่าอีเมลถึง และเปิดลิงก์ตั้งรหัสผ่านจากมือถือได้
4. ใช้มือถือ (4G) สแกน QR → แจ้งซ่อมพร้อมรูป → ได้อีเมลรหัสติดตาม
5. เจ้าหน้าที่รับงานและปิดงาน → guest เห็นสถานะเปลี่ยน

---

## 3. ใช้งานประจำวันของ Admin

ทำทุกอย่างผ่านหน้าเว็บ admin ได้ ยกเว้นงานที่ระบุว่าเป็นคำสั่งบนเซิร์ฟเวอร์

| งาน | วิธี |
| --- | --- |
| เพิ่มเจ้าหน้าที่ | หน้า admin → บัญชีเจ้าหน้าที่ → ใส่อีเมล ชื่อ และหน้าที่ ระบบส่งลิงก์ตั้งรหัสผ่าน (ใช้ได้ครั้งเดียว อายุ 24 ชม.) |
| ลิงก์หมดอายุ / อีเมลไม่ถึง | กด "ส่งคำเชิญอีกครั้ง" หรือรันบนเซิร์ฟเวอร์ `docker compose exec backend python scripts/invitation_link.py --email <อีเมล>` เพื่อให้แสดงลิงก์บนจอแล้วส่งให้เจ้าหน้าที่เอง |
| ระงับ / เปิดบัญชีคืน | หน้า admin → บัญชีเจ้าหน้าที่ บัญชีที่ถูกระงับใช้งานไม่ได้ทันที |
| เปลี่ยนหน้าที่ (role) | ยังเปลี่ยนตรง ๆ ไม่ได้: ลบบัญชีแล้วเชิญใหม่ด้วยอีเมลเดิม (ประวัติงานเดิมยังอยู่) |
| เพิ่มสถานที่ + QR | หน้า admin → ห้อง/QR → เพิ่ม → Generate QR → ดาวน์โหลด PNG หรือ ZIP หลายห้อง |
| ปิดห้องชั่วคราว | ปิดใช้งานสถานที่ การสแกน QR ของห้องนั้นจะใช้ไม่ได้ แต่คำร้องเดิมยังอยู่ |
| QR หลุด / ถูกคัดลอก | ยังไม่มีปุ่มในหน้าเว็บ: API `POST /api/v1/admin/locations/{id}/qr/regenerate` (token ของ admin) สร้าง QR ใหม่และทำให้ QR เดิมใช้ไม่ได้ทันที |
| ลืมรหัสผ่าน | กด "ลืมรหัสผ่าน" ที่หน้า login ระบบส่งลิงก์ทางอีเมล (อายุ 30 นาที) |

Login ผิดเกิน 5 ครั้งใน 15 นาที (หรือจาก IP เดียวกันเกิน 20 ครั้ง) จะถูกพักการ login 15 นาที

---

## 4. ดูแลระบบ

| งาน | คำสั่ง |
| --- | --- |
| ดูสถานะ | `docker compose ps` |
| ดู log | `docker compose logs -f backend` (หรือ `frontend`, `database`) |
| ตรวจว่าระบบทำงาน | `curl -fsS https://<โดเมน>/health` — ใช้กับบริการ uptime monitor ได้ (ตอบผิดเมื่อ backend ล่ม) |
| ตรวจ SMTP / R2 | `docker compose exec backend python scripts/check_services.py` |
| Restart | `docker compose restart` (ข้อมูลไม่หาย) |
| หยุด / เริ่ม | `docker compose stop` / `docker compose up -d --wait` |

> **ห้ามใช้ `docker compose down -v`** เพราะ `-v` ลบ volume ของฐานข้อมูลทิ้ง

### Backup ทุกวัน

```bash
mkdir -p /srv/backups
(umask 077; docker compose exec -T database \
  sh -c 'pg_dump -U "$POSTGRES_USER" -Fc "$POSTGRES_DB"' > /srv/backups/bsms-$(date +%F).dump)
```

ไฟล์ backup มี hash รหัสผ่านของเจ้าหน้าที่ เก็บไว้ 14 วัน และคัดลอกออกนอกเครื่อง
รูปภาพอยู่ใน R2 ไม่อยู่ในไฟล์นี้

### Restore

```bash
docker compose stop backend frontend
docker compose exec -T database sh -c \
  'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists' < /srv/backups/bsms-YYYY-MM-DD.dump
docker compose up -d --wait
```

ควรซ้อม restore ลงฐานข้อมูลทดสอบเดือนละครั้ง

### อัปเดตเป็นเวอร์ชันใหม่

```bash
# 1) backup ก่อนเสมอ (ด้านบน)
git pull
docker compose build
docker compose run --rm backend alembic upgrade head
docker compose up -d --wait
```

ถ้าเวอร์ชันใหม่มีปัญหา: `git checkout <commit เดิม>` → build → restore backup ที่ทำไว้ก่อนอัปเดต

---

## 5. แก้ปัญหาที่พบบ่อย

| อาการ | สาเหตุและวิธีแก้ |
| --- | --- |
| `backend` ไม่ healthy | ดู `docker compose logs backend` มักเป็น secret สั้นกว่า 32 ตัว หรือ URL ยังเป็น `localhost` / `REPLACE_` |
| `required variable ... is missing a value` | ยังไม่ได้ใส่ค่านั้นใน `.env` |
| `Pool overlaps with other one on this host` | เครือข่าย Docker ชนกับของเดิม เปลี่ยน `APP_SUBNET` ใน `.env` เป็นช่วงอื่น เช่น `172.30.90.0/24` |
| เชิญเจ้าหน้าที่แล้วอีเมลไม่ถึง | รัน `check_services.py`; ระหว่างแก้ SMTP ใช้ `scripts/invitation_link.py --email ...` (หัวข้อ 3) |
| สร้าง admin คนแรกขึ้น `owned by uid ...` | ใช้วิธีไฟล์ secret แต่ลืม `--user "$(id -u):$(id -g)"` ดู [INITIAL_ADMIN.md](Backend/scripts/INITIAL_ADMIN.md) |
| แนบรูปแล้วขึ้น "ไม่สามารถบันทึกรูปภาพได้" | ดู `docker compose logs backend`: `R2 upload failed: ClientError AccessDenied` = token ไม่มีสิทธิ์ bucket, `NoSuchBucket` = ชื่อ bucket ผิด, `SSLError` / `EndpointConnectionError` = `R2_ACCOUNT_ID` ผิดหรือเครื่องออกเน็ตไป R2 ไม่ได้ |
| อัปโหลดรูปได้ 413 | ไฟล์ใหญ่เกิน `client_max_body_size` ของ Nginx บนเครื่อง (`deploy/nginx/building-care.conf`) |
| Login ได้ 429 | login ผิดหลายครั้ง รอ 15 นาที (ปรับได้ด้วย `LOGIN_*` ใน `.env`) |
| log ของ backend เห็น IP เดียวกันทุกคำขอ | Nginx บนเครื่องต้องส่ง `X-Forwarded-For` (ไฟล์ใน `deploy/` ทำให้แล้ว) ถ้ามี proxy ของหน่วยงานอยู่หน้าอีกชั้น ต้องตั้ง `set_real_ip_from` ให้ proxy นั้นใน Nginx บนเครื่อง |
| แก้ `.env` แล้วไม่มีผล | ต้องสร้าง container ใหม่: `docker compose up -d --wait` (ค่า `VITE_*` ต้อง `docker compose build` ใหม่) |

---

## 6. ค่าตั้งค่าที่ควรรู้

ค่าทั้งหมดพร้อมคำอธิบายอยู่ใน [`.env.production.example`](.env.production.example)

| ตัวแปร | ค่าเริ่มต้น | หมายเหตุ |
| --- | --- | --- |
| `JWT_SECRET_KEY` | — | เปลี่ยนแล้วทุกคนถูก logout |
| `IMAGE_URL_SECRET` | — | เปลี่ยนแล้วลิงก์รูปเดิมทั้งหมดใช้ไม่ได้ |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | อายุการ login (8 ชม.) |
| `INVITATION_TOKEN_EXPIRE_HOURS` | `24` | อายุลิงก์เชิญเจ้าหน้าที่ |
| `LOGIN_ACCOUNT_FAILURE_LIMIT` / `LOGIN_IP_FAILURE_LIMIT` | `5` / `20` | จำนวน login ผิดก่อนถูกพัก ภายใน `LOGIN_FAILURE_WINDOW_SECONDS` (900) |
| `MAX_IMAGE_UPLOAD_BYTES` × `MAX_GUEST_IMAGES` | 10 MB × 5 | ต้องไม่เกิน `client_max_body_size 60m` ของ Nginx ทั้งสองชั้น |
| `DEFAULT_CUSTODY_LOCATION` | `ห้องธุรการ ชั้น 1` | จุดฝากของที่พบที่แสดงให้ guest |
| `APP_SUBNET` | `172.30.80.0/24` | เครือข่ายภายใน Docker ที่ใช้ระบุ IP จริงของผู้ใช้ |
| `FRONTEND_BIND_ADDRESS:FRONTEND_PORT` | `127.0.0.1:8080` | ให้เฉพาะ Nginx บนเครื่องเข้าถึง |

ข้อจำกัดที่ตั้งใจไว้: backend รัน 1 worker (ตัวนับ rate limit อยู่ในหน่วยความจำ)
รับคำขอพร้อมกันได้ 16 รายการ เกินจากนั้นตอบ 503

---

## 7. สำหรับนักพัฒนา

```bash
cd Backend
uv run --extra dev pytest        # tests ทั้งหมด (pytest อยู่ใน extra "dev")
uv run --extra dev ruff check .
```

| โฟลเดอร์ | เนื้อหา |
| --- | --- |
| `Backend/app` | FastAPI: `api/` endpoints, `services/` business logic, `models/` ตาราง |
| `Backend/migrations` | Alembic migrations (dev รันให้เองตอน start, production รันด้วยมือ) |
| `Backend/scripts` | `create_initial_admin.py`, `invitation_link.py`, `check_services.py`, `seed_locations.py` |
| `Frontend/src` | Vue 3 + Vite |
| `compose.yaml` | development (hot reload, port 5173/8000) **ห้ามใช้บนเซิร์ฟเวอร์** |
| `compose.production.yaml` | production |
| `deploy/nginx` | config ของ Nginx บนเครื่อง (HTTPS) |
