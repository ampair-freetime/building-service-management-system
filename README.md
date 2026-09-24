# Building Service Management System

ระบบแจ้งซ่อม แจ้งทำความสะอาด และของหาย/ของที่พบ — Backend: FastAPI + PostgreSQL, Frontend: Vue 3 (Vite)

## เริ่มใช้งาน

```bash
docker compose up --build
```

| บริการ | URL |
| --- | --- |
| Frontend | http://localhost:5173 |
| API | http://localhost:8000 |
| API docs (ดู endpoint ทั้งหมด) | http://localhost:8000/docs |
| Mailpit (อีเมลทดสอบ) | http://localhost:8025 |

Backend รัน `alembic upgrade head` ให้เองทุกครั้งที่ container เริ่ม ถ้าเพิ่ม migration ใหม่ให้ restart backend:

```bash
docker compose restart backend
```

## บัญชีสำหรับ login (development เท่านั้น)

Login ที่ `POST /api/v1/auth/login` ใช้ **รหัสพนักงานหรืออีเมล** ก็ได้

```json
{ "identifier": "ADMIN001", "password": "Admin@1234" }
```

| Role | รหัสพนักงาน | Email | Password | ที่มา |
| --- | --- | --- | --- | --- |
| `admin` (แอดมิน) | `ADMIN001` | `admin@example.com` | `Admin@1234` | สร้างอัตโนมัติจาก migration |
| `clerk` (เจ้าหน้าที่ของหาย) | ตั้งเองตอนสร้าง | อีเมลที่ใช้ได้ | ระบบสุ่มและส่งทางอีเมล | ต้องสร้างเอง ↓ |
| `housekeeper` (แม่บ้าน) | ตั้งเองตอนสร้าง | อีเมลที่ใช้ได้ | ระบบสุ่มและส่งทางอีเมล | ต้องสร้างเอง ↓ |
| `technician` (ช่าง) | ตั้งเองตอนสร้าง | อีเมลที่ใช้ได้ | ระบบสุ่มและส่งทางอีเมล | ต้องสร้างเอง ↓ |

บัญชีที่ "ต้องสร้างเอง" ไม่ได้อยู่ใน seed ให้ login เป็น `ADMIN001` แล้วสร้างผ่าน `POST /api/v1/staff`
(ทำใน http://localhost:8000/docs ได้) ดูรหัสผ่านเริ่มต้นใน Mailpit; response มี `email_sent` แต่ไม่คืนรหัสผ่าน
รหัสผ่านของบัญชี admin เริ่มต้นเป็นค่าสาธารณะสำหรับ dev ห้ามใช้บน production

## QR code ของสถานที่

Admin เพิ่ม location ผ่าน `POST /api/v1/admin/locations` หรือ `POST /api/v1/admin/locations/bulk`
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
