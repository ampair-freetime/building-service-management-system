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
| `compose.production.yaml` | มีแล้ว แยก Production พร้อม Nginx stage, Healthchecks, Restart Policy, Log Rotation และ Network/Volume แยก |
| `.env.production.example` | มีแล้ว รวมตัวแปร Settings และ Frontend พร้อม Placeholder; ต้องแทนค่าก่อนใช้งานจริง |
| `.env.production` | สร้างจากไฟล์ตัวอย่างบนเซิร์ฟเวอร์เท่านั้น `chmod 600` ห้าม commit (ถูก ignore ด้วย `.env.*`) |
| `Frontend/nginx.conf` | ควรมี cache `/assets/` 1 ปี + `index.html` no-cache, gzip, security headers, `limit_req` สำหรับ login และ guest POST, `real_ip` เมื่ออยู่หลัง proxy |

### การใช้ไฟล์ Environment สำหรับ Production

`.env.production.example` เป็นไฟล์ตัวอย่างที่ commit ได้ ส่วน `.env.production` ในเครื่อง Local
มีเฉพาะ Placeholder และถูก Git ignore พร้อมสิทธิ์ `600` ยังใช้เปิดบริการจริงไม่ได้
แทนค่าที่ขึ้นต้น `REPLACE_*` ทั้งหมดก่อนใช้งาน โดยไม่คัดลอก Secret จาก Development

- ตั้ง `PUBLIC_BASE_URL` เป็นโดเมน HTTPS จริง และ `BACKEND_CORS_ORIGINS` เป็น JSON list
  ของ origin ที่อนุญาต (ไม่มี path); URL activation/reset ที่ว่างจะคำนวณจาก Public URL
- สร้าง JWT และ Image Secret แยกกัน เช่นใช้ `openssl rand -hex 32` ทีละค่า
  เก็บผ่านช่องทางส่วนตัว ไม่ใส่ใน Git, Log หรือ `VITE_*`; Placeholder สั้นจะถูก validator ปฏิเสธ
- ตั้ง PostgreSQL credentials และ `DATABASE_URL` ให้ตรงกัน โดย URL ใช้ driver `postgresql+asyncpg`
  และ URL-encode รหัสผ่านที่มีอักขระพิเศษ; Host `database:5432` ใช้ภายใน Docker เท่านั้น
  การรันนอก Docker ต้องใช้ Host/Port ที่เข้าถึงได้จริง การเปลี่ยน Env ไม่เปลี่ยนรหัส DB เดิม
- ตั้ง R2 account/token/bucket และ SMTP credentials ตามบริการจริง; ใช้ 587 + STARTTLS
  หรือ 465 + SSL โดยไม่เปิดทั้งสองแบบพร้อมกัน ตั้ง `MAIL_FROM` เป็นผู้ส่งที่ได้รับอนุญาต
- `FORWARDED_ALLOW_IPS` เป็นค่าของ Uvicorn ให้ตั้งตาม trusted proxy จริงในขั้นตอน Compose
  ไม่กำหนด `*` โดยไม่มีการจำกัดทางเข้าของ Backend
- Initial Admin credentials ไม่อยู่ในไฟล์นี้ ส่งให้ Bootstrap ครั้งเดียวตามคู่มือ Initial Admin

Backend ไม่เลือก `.env.production` เอง การรันนอก Docker ให้กำหนด Environment ของ Process
เป็น `BSMS_ENV_FILE=/absolute/path/to/.env.production` เพื่อไม่อ่าน Root `.env` และ `Backend/.env`
Environment ที่ส่งเข้า Process มีลำดับเหนือไฟล์ จึงต้องตรวจว่าไม่มีค่า Development ค้างอยู่

ใช้ `--env-file .env.production` สำหรับ interpolation; `compose.production.yaml` ส่งตัวแปร
Backend ผ่าน `environment` อย่างชัดเจน พร้อม `BSMS_ENV_FILE: ""`
เพื่อปิดการอ่าน dotenv ใน Container; `--env-file` อย่างเดียวไม่ได้ส่งทุกตัวแปรเข้า Container
อย่าใช้ Compose Development เปิด Production: ไฟล์ปัจจุบันยังมี reload, bind mount และ migration อัตโนมัติ

Vite ที่รันจาก `Frontend/` ไม่อ่าน dotenv ที่ Root อัตโนมัติ Production Dockerfile รับ
`VITE_API_BASE_URL` ผ่าน build arg ซึ่ง default เป็น `/api/v1` อยู่แล้ว ส่วน Compose Production กำหนด
`frontend.build.args.VITE_API_BASE_URL=/api/v1` ไว้โดยตรง การเปลี่ยน runtime environment ของ Nginx ไม่เปลี่ยนเว็บที่ Build แล้ว
สำหรับ Build Local (ไม่มีการ Deploy):

```bash
cd Frontend
VITE_API_BASE_URL=/api/v1 npm run build
```

`VITE_CLEANING_REQUEST_URL` และ `VITE_REPAIR_REQUEST_URL` เป็น override ที่โค้ดรองรับ
แต่เว้นว่างไว้เพื่อให้ใช้ API Base URL เดียวกัน; ไม่จำเป็นต้องเพิ่ม Docker build args สำหรับสองตัวนี้
อย่าแก้ fallback Development ใน Frontend เพื่อเปิด Production เพราะ Build Environment รองรับแล้ว

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
| `FORWARDED_ALLOW_IPS` | IP/network ของ trusted proxy | ค่าเริ่มต้น `127.0.0.1` ยังไม่ trust Nginx Container; ต้องกำหนดหลังทราบเครือข่าย |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `MAIL_FROM` | ตามผู้ให้บริการ | 587 + `SMTP_USE_STARTTLS=true` หรือ 465 + `SMTP_USE_SSL=true` |
| `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME` | จาก Cloudflare | ไม่ตั้ง = แนบรูปไม่ได้ |
| `VITE_API_BASE_URL` | `/api/v1` | เป็น build arg ของ frontend เปลี่ยนแล้วต้อง build ใหม่ ห้ามใส่ความลับใน `VITE_*` |
| `MAX_IMAGE_UPLOAD_BYTES` × `MAX_GUEST_IMAGES` | `10485760` × `5` | ผลคูณ + overhead ต้องน้อยกว่า `client_max_body_size` (60m) ใน `Frontend/nginx.conf` |

### Compose Production: Network, Volume และการตรวจสอบ

ใช้ไฟล์ Production เพียงไฟล์เดียว ไม่ merge กับ `compose.yaml` เพราะอาจติดพอร์ต,
bind mount และคำสั่ง Development มาด้วย Project default คือ `cs-building-care-production`
ตั้ง `PRODUCTION_PROJECT_NAME` ได้แต่ควรใช้ค่าเดิมทุกครั้ง

- `database`: PostgreSQL 16 ไม่มี Host Port; Network `data` เป็น internal
  เก็บข้อมูลใน Named Volume `cs_building_care_production_postgres_data`
- `backend`: Network `data` สำหรับ DB และ `app` สำหรับ Nginx/การออกไป SMTP และ R2
  ไม่มี Host Port ใช้ Launcher เดิมหนึ่ง Worker ไม่ reload และไม่ migrate ตอน start
- `frontend`: Nginx Production Stage ฟัง 8080; อยู่เฉพาะ `app` และ publish ที่
  `FRONTEND_BIND_ADDRESS:FRONTEND_PORT` (default `127.0.0.1:8080`)
  หาก Proxy อยู่คนละเครื่อง ต้องกำหนด IP ที่เข้าถึงได้และ Firewall หลังทราบโครงสร้างจริง
- ไม่มีการกำหนด Subnet หรือ bind mount source code; ทุก Service มี restart `unless-stopped`
  และ json-file Log Rotation 10 MB x 5 ไฟล์

`POSTGRES_VOLUME_NAME` ระบุชื่อ Volume จริงแยกจาก Development และคงเดิมแม้เปลี่ยน Project
ไม่ย้ายข้อมูลหรือใช้ Volume เดิมอัตโนมัติ ผู้ดูแลต้องตรวจและสำรองก่อนเลือก Volume ที่มีข้อมูล
ชื่อผิดอาจทำให้เปิดฐานข้อมูลว่างคนละชุด ห้ามใช้ `down -v` หรือ prune volume ที่มีข้อมูล

Compose กำหนด API prefix และ Frontend build arg เป็น `/api/v1` ให้ตรง Nginx/Routes เดิม
การเปลี่ยนค่า prefix ใน dotenv อย่างเดียวจะไม่เปลี่ยน Compose Production นี้

Compose ประกอบ `DATABASE_URL` จาก `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
เพื่อใช้ credentials ชุดเดียวกับ Service database และเชื่อม `database:5432`
ค่า `DATABASE_URL` ใน dotenv ใช้สำหรับรัน Backend นอก Compose เท่านั้น
สำหรับ Compose นี้ให้ใช้ชื่อ DB/user แบบ URL-safe และรหัสผ่าน random hex เพื่อไม่ให้ URL แตก
Environment ไม่เปลี่ยน credentials ใน Volume ที่ initialize แล้ว ต้องเปลี่ยนผ่านขั้นตอน DB แยก

Healthchecks: DB ใช้ TCP `pg_isready`, Backend เรียก `/health`, Frontend ตรวจ HTTP หน้าแรก
`depends_on` รอ Healthcheck ตามลำดับ แต่ไม่รับประกัน schema/credentials/R2/SMTP พร้อมทั้งหมด
Docker restart policy ไม่ restart Container เพียงเพราะสถานะ unhealthy ต้องมีการติดตามและผู้ดูแล

ตรวจ YAML แบบไม่เริ่ม Container และไม่พิมพ์ Secret:

```bash
docker compose --env-file .env.production.example -f compose.production.yaml config --quiet
docker compose --env-file .env.production -f compose.production.yaml config --quiet
```

คำสั่ง `config` ผ่านไม่แปลว่า Placeholder ใช้งานได้จริง Backend จะปฏิเสธ Secret Placeholder
ก่อนเปิดบริการ หลีกเลี่ยงการพิมพ์ `config` แบบเต็มด้วยค่าจริง เพราะจะแสดง Secret
Environment ของ shell มีลำดับเหนือ `--env-file`; ตรวจว่าค่าที่ส่งเข้า Compose เป็นชุด Production

Initial Admin ไม่อยู่ใน environment ปกติของ Service และไม่ถูกรันตอน start
หลัง Migration สำหรับฐานข้อมูลใหม่ ใช้ one-off Backend ตามคู่มือ Initial Admin เช่น
mount โฟลเดอร์ Secret ที่เตรียมไว้และส่งเฉพาะ path (ตัวอย่างสำหรับผู้ดูแล ยังไม่ได้รัน):

```bash
docker compose --env-file .env.production -f compose.production.yaml run --rm --no-deps \
  -v /srv/cs-building-care-secrets:/run/bootstrap-secrets:ro \
  -e INITIAL_ADMIN_EMAIL_FILE=/run/bootstrap-secrets/email \
  -e INITIAL_ADMIN_FULL_NAME_FILE=/run/bootstrap-secrets/name \
  -e INITIAL_ADMIN_PASSWORD_FILE=/run/bootstrap-secrets/password \
  backend python scripts/create_initial_admin.py
```

ไฟล์ต้องเป็นของ user ที่รันใน Container และไม่มีสิทธิ์ group/other ตาม Bootstrap validator
Backend Image ปัจจุบันรันเป็น root จึงต้องวางแผน ownership ให้ตรง และจำกัดสิทธิ์เข้าถึง Docker
ถอน Secret mount เมื่อเสร็จ; ไม่เก็บ credentials นี้ใน environment ของ Backend ที่รันปกติ

Nginx เดิมส่ง `/api/` ไป `backend:8000` โดยรักษา path และรองรับ Vue Router fallback แล้ว
ยังไม่แก้ HTTPS หรือ forwarded headers ในขั้นตอนนี้ ก่อนเปิดจริงต้องกำหนด trusted proxy/IP
และตรวจ scheme/IP ผู้ใช้ผ่าน Proxy ภาควิชา การเปลี่ยน Backend Container อาจต้อง recreate Frontend
เพื่อให้ Nginx resolve IP ของ upstream ใหม่

### ขั้นตอน deploy

ทุกคำสั่ง `docker compose` ด้านล่างย่อจาก `docker compose --env-file .env.production -f compose.production.yaml`

1. **เตรียมเครื่อง** — สร้าง user `deploy` (ไม่ใช้ root) + SSH key, `ufw allow 22,80,443`, timezone `Asia/Bangkok`, ติดตั้ง Docker แล้ว `usermod -aG docker deploy`
2. **ดึงโค้ด** — `git clone` ไป `/srv/building-care` แล้ว checkout tag ที่จะปล่อย
3. **ตั้งค่า** — `cp .env.production.example .env.production`, `chmod 600 .env.production` แล้วกรอกค่าตามตารางด้านบน
4. **ตรวจ config** — `docker compose config --quiet` (ไม่พิมพ์ secret)
5. **Build + Migration ที่ควบคุมได้** — `docker compose build` แล้ว `docker compose up -d --wait database`
   หลัง Backup และตรวจฐานข้อมูลเป้าหมาย รัน `docker compose run --rm --no-deps backend alembic upgrade head`
   ต้องสำเร็จก่อนเริ่ม Backend; คำสั่งนี้เขียนฐานข้อมูลและต้องรันโดยผู้ดูแลเท่านั้น
   จากนั้น `docker compose up -d --wait backend` และตรวจ Uvicorn started
6. **บัญชี admin** — ตั้ง `ENVIRONMENT=production` ก่อน migration ครั้งแรกเพื่อไม่สร้างบัญชี Development
   แล้วใช้คำสั่ง Bootstrap แยกตาม [คู่มือ Initial Admin](Backend/scripts/INITIAL_ADMIN.md) ก่อนเปิดบริการ
   ฐานข้อมูลเดิมที่มี Admin จะไม่ถูกเปลี่ยนบัญชีหรือรหัสผ่านโดย Bootstrap
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

1. Backup ฐานข้อมูลก่อนทุกครั้ง และตรวจ migration ใหม่; Production ไม่รัน migration ตอน start
2. เลือก tag ใหม่ → `docker compose build` → ทำ migration แบบควบคุมตามขั้นตอนด้านบน
   ถ้า schema ไม่เข้ากับแอปเดิม ให้หยุดรับผู้ใช้/หยุด frontend และ backend ก่อน migration
   จากนั้น `docker compose up -d --wait`
3. ตรวจ log และ smoke test สั้น ๆ
4. ถ้าต้องย้อน: checkout tag เดิม → build → ถ้า migration ใหม่แก้ schema ให้ restore จาก backup ข้อ 1
   (ปลอดภัยกว่า `alembic downgrade` ที่ยังไม่เคยทดสอบ)

### ข้อควรรู้

- Rate limiter ของ forgot-password และอีเมล guest เก็บใน memory ของ process ถูกต้องเมื่อรัน 1 worker
  (`scripts/start_server.py`) เท่านั้น ถ้าเพิ่ม worker ต้องย้ายไปเก็บที่ DB หรือ Redis
- Uvicorn จำกัด concurrency 16 (`--limit-concurrency`) เมื่อเต็มจะตอบ 503
- `check_services.py` ตรวจการเชื่อมต่อ SMTP/R2 เท่านั้น ไม่ส่งอีเมลจริงและไม่อัปโหลดไฟล์

การตรวจ Compose รอบนี้ผ่าน `config --quiet` ด้วยทั้งไฟล์ตัวอย่างและ Local Placeholder
ตรวจโครงสร้างพอร์ต, Network, Volume, Environment และ Build Arguments โดยไม่เริ่ม Container
Docker build check ยังไม่ผ่านการตรวจจริงเพราะเครื่องมือไม่มีสิทธิ์เข้าถึง Docker daemon
จึงต้อง Build และ smoke test บน Staging ที่แยกจากข้อมูลจริงก่อน Deploy
