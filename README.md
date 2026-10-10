# Building Service Management System

ระบบแจ้งซ่อม แจ้งทำความสะอาด และของหาย/ของที่พบ — Backend: FastAPI + PostgreSQL, Frontend: Vue 3 (Vite)

## เริ่มใช้งาน

สำหรับ production และเซิร์ฟเวอร์ภาควิชา ดู [คู่มือ deployment](deploy/README.md) และ `.env.production.example` ชุดเริ่มใช้งานด้านล่างเป็น development

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
