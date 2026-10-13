# Building Service Management System

ระบบแจ้งซ่อม แจ้งทำความสะอาด และของหาย/ของที่พบ — Backend: FastAPI + PostgreSQL, Frontend: Vue 3 (Vite)

## เริ่มใช้งาน

ชุดเริ่มใช้งานด้านล่างเป็น development (Vite dev server) สำหรับ production ดูหัวข้อ
[Production deployment](#production-deployment) ซึ่งใช้ Nginx เสิร์ฟไฟล์ที่ build แล้วแทน Vite

```bash
docker compose up --build
```

| บริการ | URL |
| --- | --- |
| Frontend | http://localhost:5173 |
| API | http://localhost:8000 |
| API docs (ดู endpoint ทั้งหมด) | http://localhost:8000/docs |

Backend รัน `alembic upgrade head` ให้เองทุกครั้งที่ container เริ่ม ถ้าเพิ่ม migration ใหม่ให้ restart backend:

```bash
docker compose restart backend
```

## การส่งอีเมล

ตั้งค่า SMTP ใน `.env` ตามผู้ให้บริการที่ใช้งาน: `SMTP_HOST`, `SMTP_PORT`,
`SMTP_USERNAME`, `SMTP_PASSWORD` และ `MAIL_FROM` โดยค่าเริ่มต้นใช้ port 587
พร้อม `SMTP_USE_STARTTLS=true` หากใช้ port 465 ให้ตั้ง `SMTP_USE_SSL=true`
และ `SMTP_USE_STARTTLS=false` ระบบจะส่งอีเมลไปยังผู้รับโดยตรง
หากไม่ตั้ง `SMTP_HOST` ระบบจะตอบ `email_sent=false`
หลังแก้ค่าให้สร้าง backend container ใหม่ด้วย `docker compose up -d backend`

## บัญชีสำหรับ login (development เท่านั้น)

Login ที่ `POST /api/v1/auth/login` ใช้ **อีเมล**

```json
{ "identifier": "admin@example.com", "password": "Admin@1234" }
```

| Role | Email | Password | ที่มา |
| --- | --- | --- | --- |
| `admin` (แอดมิน) | `admin@example.com` | `Admin@1234` | สร้างอัตโนมัติจาก migration |
| `clerk` (เจ้าหน้าที่ของหาย) | อีเมลที่ใช้ได้ | Staff ตั้งเองผ่าน invitation link | Admin สร้างผ่าน API |
| `housekeeper` (แม่บ้าน) | อีเมลที่ใช้ได้ | Staff ตั้งเองผ่าน invitation link | Admin สร้างผ่าน API |
| `technician` (ช่าง) | อีเมลที่ใช้ได้ | Staff ตั้งเองผ่าน invitation link | Admin สร้างผ่าน API |

Admin สร้างบัญชีผ่าน `POST /api/v1/staff` โดยส่ง `email`, `full_name` และ `role`
(ทำใน http://localhost:8000/docs ได้) จากนั้นเปิดอีเมลในกล่องจดหมายของผู้รับ แล้วกด invitation link
เพื่อตั้งรหัสผ่านก่อน login; response มี `email_sent` แต่ไม่คืนรหัสผ่านหรือ token
ลิงก์หมดอายุใน 24 ชั่วโมงตามค่าเริ่มต้น และใช้ได้ครั้งเดียว
หากส่งอีเมลไม่สำเร็จหรือลิงก์หมดอายุ ให้ Admin เรียก
`POST /api/v1/staff/{staff_id}/resend-invitation` เพื่อส่งลิงก์ใหม่สำหรับบัญชีเดิมที่ยังไม่ activate
ลิงก์เก่าจะใช้ไม่ได้หลัง resend และ resend ใช้ไม่ได้กับบัญชีที่ activate แล้ว
รหัสผ่านของบัญชี admin เริ่มต้นเป็นค่าสาธารณะสำหรับ dev ห้ามใช้บน production

## QR code ของสถานที่

Admin เพิ่ม location ทีละรายการผ่าน `POST /api/v1/admin/locations`
ก่อน ห้องใหม่มี `qr_token: null` และ `qr_url: null` จนกว่าจะกด
`POST /api/v1/admin/locations/{id}/qr/generate` การกด Generate ซ้ำคืน token เดิม

จากนั้นใช้ `GET /api/v1/admin/locations/{id}/qr?format=png` เพื่อดาวน์โหลดรูป
หรือ `format=svg&download=false` เพื่อเปิดดู/พิมพ์ ใช้ Bearer token ของ admin กับทุก endpoint นี้
หากต้องดาวน์โหลดหลายห้อง ใช้ `GET /api/v1/admin/locations/qr-bundle?ids=1&ids=2`
ซึ่งคืนไฟล์ ZIP เบราว์เซอร์ที่แสดงรูปผ่าน `<img>` ต้องโหลดรูปแบบ Blob ด้วย header Authorization ก่อน

`PATCH /api/v1/admin/locations/{id}/status` รับ `{"is_active": false}` เพื่อปิดห้อง
การสแกน QR ของห้องที่ปิดจะได้ 404 แต่คำร้องเดิมยังอยู่
`DELETE /api/v1/admin/locations/{id}` ลบสถานที่ที่สร้างผิด ได้ 204 และสร้างชื่อเดิมใหม่ได้
ลบได้เฉพาะสถานที่ที่ยังไม่เคยมีคำร้องหรือรายการของหาย/ของที่พบ ถ้ามีแล้วจะได้ 409 ให้ใช้ปิดใช้งานแทน
`POST /api/v1/admin/locations/{id}/qr/regenerate` สุ่ม token ใหม่ ทำให้ QR เก่าใช้ไม่ได้ทันที

`PUBLIC_BASE_URL` กำหนดต้นทาง URL ที่ฝังใน QR ค่าเริ่มต้นคือ `http://localhost:5173`
ถ้าสแกนด้วยมือถือ ให้ตั้งเป็น IP หรือโดเมนที่มือถือเข้าได้ แล้ว restart backend

Seed script ยังใช้ได้สำหรับห้องเริ่มต้น โดยสร้างห้องและ Generate QR ให้พร้อมใช้ทันที
รันซ้ำแล้ว token เดิมไม่เปลี่ยน:

```bash
docker compose exec backend python scripts/seed_locations.py --base-url http://localhost:5173
```

ผลลัพธ์คือ `id  ชื่อสถานที่  URL` ซึ่งตอนนี้เป็น `/user?token=...`
ฝั่ง guest สแกน token ได้ที่ `/api/v1/guest/cleaning-requests/locations/by-qr/{token}`
หรือ `/api/v1/guest/repair-requests/locations/by-qr/{token}`

## Environment (`.env` ที่ root ห้าม commit)

รูปภาพเก็บใน Cloudflare R2 (bucket แบบ private) ถ้าไม่ตั้งค่า การแนบรูปจะใช้ไม่ได้

```dotenv
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET_NAME=building-service-images
JWT_SECRET_KEY=   # production ต้องตั้งเป็นค่าลับของตัวเอง
PUBLIC_BASE_URL=http://localhost:5173  # เปลี่ยนเป็น IP/โดเมนที่มือถือเข้าได้
```

## Tests

```bash
cd Backend
uv run pytest
```

## Production deployment

### ภาพรวม

Development ใช้ Vite dev server (`npm run dev`) ซึ่งแปลงไฟล์ตอน browser ขอและมี hot reload
ไม่ได้ออกแบบให้รับผู้ใช้จริง Production จึง build frontend เป็นไฟล์ static (`npm run build` → `dist/`)
แล้วให้ Nginx เสิร์ฟไฟล์เหล่านั้นและส่งต่อ `/api/...` ไป backend ผู้ใช้จึงเห็นโดเมนเดียว (same-origin)
ไม่ต้องพึ่ง CORS และลิงก์รูปแบบ relative `/api/v1/images/...` ใช้ได้ทันที

```text
Browser ──HTTPS 443──> Edge TLS (proxy ภาควิชา หรือ host Nginx + certbot)
                          │ HTTP 127.0.0.1:8080
                          v
                 frontend container (Nginx: dist/ + /api proxy)
                          │ docker network ภายใน
                          v
                 backend container (Uvicorn 1 worker) ──> PostgreSQL 16 (named volume)
                          ├──> Cloudflare R2 (S3 API, 443)
                          └──> SMTP (587/465)
```

- `Frontend/Dockerfile` stage `production` ใช้ `nginxinc/nginx-unprivileged` ฟัง port 8080 และคัดลอก `Frontend/nginx.conf`
- backend และ database ห้าม publish port ออก host; frontend bind เฉพาะ `127.0.0.1:8080` ให้ edge proxy เข้าถึงคนเดียว
- `compose.yaml` เป็นของ development เท่านั้น (`--reload`, bind mount, Vite, port 8000 เปิดทุก interface) ห้ามใช้บน production

### สิ่งที่ต้องเตรียมก่อน

| รายการ | ข้อกำหนด |
| --- | --- |
| เครื่อง | ขั้นต่ำ 2 vCPU, RAM 2–4 GB (≤ 2 GB ให้เปิด swap), ดิสก์ 20 GB, Ubuntu 22.04/24.04, Docker Engine + Compose plugin |
| โดเมน | DNS A record ชี้เครื่อง และ HTTPS (ใบรับรองจาก proxy ภาควิชาหรือ certbot) |
| เครือข่าย | inbound 80/443; outbound 443 ไป `*.r2.cloudflarestorage.com`; outbound SMTP 587 หรือ 465 |
| Cloudflare R2 | bucket แบบ private + API token สิทธิ์ Object Read & Write เฉพาะ bucket นั้น |
| SMTP | บัญชีส่งเมล + App Password (Gmail ต้องเปิด 2FA) |

### ไฟล์ที่ต้องมีใน repo

| ไฟล์ | สถานะ / สิ่งที่ต้องมี |
| --- | --- |
| `compose.production.yaml` | ถ้ายังไม่มี กู้ได้จาก `git show c3d9020^:compose.production.yaml` แล้วต้องเพิ่ม `IMAGE_URL_SECRET` (บังคับใน production), `restart: unless-stopped` และ `logging` (`max-size: 10m`, `max-file: 5`) ทุก service; frontend ใช้ `target: production` |
| `.env.production.example` | กู้ได้จาก `git show c3d9020^:.env.production.example` แล้วแก้ `MAX_IMAGE_UPLOAD_BYTES` เป็น `10485760` และเพิ่ม `IMAGE_URL_SECRET`, `IMAGE_REDIRECT_URL_EXPIRE_SECONDS`, `GUEST_EMAIL_*` |
| `.env.production` | สร้างจากไฟล์ตัวอย่างบนเซิร์ฟเวอร์เท่านั้น `chmod 600` ห้าม commit (ถูก ignore ด้วย `.env.*`) |
| `Frontend/nginx.conf` | ควรมี cache `/assets/` 1 ปี + `index.html` no-cache, gzip, security headers, `limit_req` สำหรับ login และ guest POST, `real_ip` เมื่ออยู่หลัง proxy |

### Environment variables สำหรับ production

ค่าที่ไม่ได้ระบุใช้ default เดียวกับ `.env.example` ได้ Backend จะ **ไม่ยอม start** ถ้า `ENVIRONMENT=production`
แต่ secret สั้นกว่า 32 ตัว, ยังเป็นค่า default หรือ URL เป็น localhost

| ตัวแปร | ค่า production | หมายเหตุ |
| --- | --- | --- |
| `ENVIRONMENT` | `production` | เปิด validator และปิด `/docs`, `/redoc` |
| `POSTGRES_DB`, `POSTGRES_USER` | ตั้งเอง | ใช้ประกอบ `DATABASE_URL` ใน compose |
| `POSTGRES_PASSWORD` | `openssl rand -hex 32` | ใช้ hex เพื่อไม่ต้อง URL-encode |
| `JWT_SECRET_KEY` | `openssl rand -hex 32` | เปลี่ยนแล้วทุกคนถูก logout |
| `IMAGE_URL_SECRET` | `openssl rand -hex 32` (คนละค่ากับ JWT) | เปลี่ยนแล้วลิงก์รูปเดิมทั้งหมดใช้ไม่ได้ |
| `PUBLIC_BASE_URL` | `https://<โดเมนจริง>` | ฝังใน QR และลิงก์ในอีเมล ต้องนิ่งก่อนพิมพ์ QR |
| `BACKEND_CORS_ORIGINS` | `["https://<โดเมนจริง>"]` | รูปแบบ JSON list |
| `STAFF_ACTIVATION_URL`, `STAFF_PASSWORD_RESET_URL` | เว้นว่าง | ว่าง = คำนวณจาก `PUBLIC_BASE_URL` |
| `FORWARDED_ALLOW_IPS` | `*` ใน Docker / IP ของ proxy ถ้าไม่ใช้ Docker | ให้ rate limit เห็น IP จริงจาก `X-Forwarded-For` |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `MAIL_FROM` | ตามผู้ให้บริการ | 587 + `SMTP_USE_STARTTLS=true` หรือ 465 + `SMTP_USE_SSL=true` |
| `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME` | จาก Cloudflare | ไม่ตั้ง = แนบรูปไม่ได้ |
| `VITE_API_BASE_URL` | `/api/v1` | เป็น build arg ของ frontend เปลี่ยนแล้วต้อง build ใหม่ ห้ามใส่ความลับใน `VITE_*` |
| `MAX_IMAGE_UPLOAD_BYTES` × `MAX_GUEST_IMAGES` | `10485760` × `5` | ผลคูณ + overhead ต้องน้อยกว่า `client_max_body_size` (60m) ใน `Frontend/nginx.conf` |

### ขั้นตอน deploy

ทุกคำสั่ง `docker compose` ด้านล่างย่อจาก `docker compose --env-file .env.production -f compose.production.yaml`

1. **เตรียมเครื่อง** — สร้าง user `deploy` (ไม่ใช้ root) + SSH key, `ufw allow 22,80,443`, timezone `Asia/Bangkok`, ติดตั้ง Docker แล้ว `usermod -aG docker deploy`
2. **ดึงโค้ด** — `git clone` ไป `/srv/building-care` แล้ว checkout tag ที่จะปล่อย
3. **ตั้งค่า** — `cp .env.production.example .env.production`, `chmod 600 .env.production` แล้วกรอกค่าตามตารางด้านบน
4. **ตรวจ config** — `docker compose config --quiet` (ไม่พิมพ์ secret)
5. **Build + เปิด DB/backend** — `docker compose build` แล้ว `docker compose up -d database backend`
   จากนั้น `docker compose logs -f backend` ต้องเห็น migration ไปถึง head และ Uvicorn started
6. **บัญชี admin** — migration `20260807_0002` สร้าง `admin@example.com` / `Admin@1234` ซึ่งเป็นค่าสาธารณะ
   ต้องสร้าง admin จริงแล้ว suspend บัญชีนี้ก่อนเปิดให้ผู้อื่นเข้าถึง ทดสอบว่า login ด้วย `Admin@1234` ไม่ผ่าน
7. **ตรวจบริการภายนอก** — `docker compose exec backend python scripts/check_services.py` ต้องได้ SMTP และ R2 OK
8. **เปิด frontend** — `docker compose up -d frontend` แล้ว `curl -I http://127.0.0.1:8080/` ต้องได้ 200
9. **HTTPS** — ตั้ง edge proxy ชี้ `127.0.0.1:8080` (certbot หรือ proxy ของภาควิชา) และเปิด HSTS ที่ edge
10. **ข้อมูลเริ่มต้น** — เพิ่ม location → Generate QR → ตรวจว่า URL ใน QR เป็นโดเมนจริง → พิมพ์;
    เชิญ staff แต่ละ role แล้วตรวจว่าอีเมลถึง inbox และลิงก์ตั้งรหัสเปิดจากมือถือได้
11. **Smoke test** — guest (มือถือผ่าน 4G) แจ้งทำความสะอาด/ซ่อมพร้อมรูปและติดตามสถานะ, แม่บ้าน/ช่างรับและปิดงาน,
    clerk อนุมัติของพบ → claim → คืน, admin suspend staff; refresh หน้า `/staff/setup-password` ต้องไม่ 404

### งานดูแลหลังเปิดใช้งาน

| งาน | ความถี่ | วิธี |
| --- | --- | --- |
| Backup PostgreSQL | ทุกวัน | `docker compose exec -T database pg_dump -U <user> -Fc <db> > /srv/backups/bsms-$(date +%F).dump` เก็บ 14 ไฟล์ + คัดลอกออกนอกเครื่อง |
| ซ้อม restore | เดือนละครั้ง | `pg_restore` ลงฐานข้อมูลชั่วคราวแล้วเทียบจำนวนแถว |
| ตรวจขนาดรูปใน R2 | ทุกสัปดาห์ | `SELECT count(*), sum(size_bytes) FROM images WHERE deleted_at IS NULL;` (R2 free tier 10 GB) |
| ตรวจดิสก์ | ทุกสัปดาห์ | `df -h`, `docker system df` |
| Uptime | ทุก 5 นาที | บริการ ping ภายนอกยิง `/health` (liveness เท่านั้น ไม่ได้ตรวจ DB/SMTP/R2) |

### อัปเดตเวอร์ชันและย้อนกลับ

1. Backup ฐานข้อมูลก่อนทุกครั้ง เพราะ backend รัน `alembic upgrade head` เองตอน start
2. `git fetch && git checkout <tag ใหม่>` → `docker compose build` → `docker compose up -d`
3. ตรวจ log และ smoke test สั้น ๆ
4. ถ้าต้องย้อน: checkout tag เดิม → build → ถ้า migration ใหม่แก้ schema ให้ restore จาก backup ข้อ 1
   (ปลอดภัยกว่า `alembic downgrade` ที่ยังไม่เคยทดสอบ)

### ข้อควรรู้

- Rate limiter ของ forgot-password และอีเมล guest เก็บใน memory ของ process ถูกต้องเมื่อรัน 1 worker
  (`scripts/start_server.py`) เท่านั้น ถ้าเพิ่ม worker ต้องย้ายไปเก็บที่ DB หรือ Redis
- Uvicorn จำกัด concurrency 16 (`--limit-concurrency`) เมื่อเต็มจะตอบ 503
- `check_services.py` ตรวจการเชื่อมต่อ SMTP/R2 เท่านั้น ไม่ส่งอีเมลจริงและไม่อัปโหลดไฟล์
