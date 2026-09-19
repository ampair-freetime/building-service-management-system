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
| `clerk` (เจ้าหน้าที่ของหาย) | ตั้งเองตอนสร้าง | `CL001@gmail.com` | `1234567A` | ต้องสร้างเอง ↓ |
| `housekeeper` (แม่บ้าน) | ตั้งเองตอนสร้าง | `CL002@gmail.com` | `1234567A` | ต้องสร้างเอง ↓ |
| `technician` (ช่าง) | — | — | — | ยังไม่มี |

บัญชีที่ "ต้องสร้างเอง" ไม่ได้อยู่ใน seed ให้ login เป็น `ADMIN001` แล้วสร้างผ่าน `POST /api/v1/staff`
(ทำใน http://localhost:8000/docs ได้) รหัสผ่านทั้งหมดนี้เป็นค่าสาธารณะสำหรับ dev ห้ามใช้บน production

## QR code ของสถานที่

แต่ละสถานที่ในตาราง `locations` มี `qr_token` แบบสุ่ม **token ของแต่ละเครื่องจะไม่เหมือนกัน** เพราะสุ่มตอน seed
สร้างสถานที่และพิมพ์ token/URL ด้วย:

```bash
docker compose exec backend python scripts/seed_locations.py --base-url http://localhost:5173
```

ผลลัพธ์แต่ละบรรทัดคือ `id  ชื่อสถานที่  URL` เอา URL ไปทำรูป QR ได้เลย รันซ้ำได้ token เดิมไม่เปลี่ยน
แก้รายการสถานที่ได้ที่ `LOCATIONS` ใน `Backend/scripts/seed_locations.py`

ทดสอบ token:

```bash
curl http://localhost:8000/api/v1/guest/cleaning-requests/locations/by-qr/<qr_token>
curl http://localhost:8000/api/v1/guest/repair-requests/locations/by-qr/<qr_token>
```

token ที่ใช้อยู่ในเครื่อง dev หลัก:

| id | สถานที่ | qr_token |
| --- | --- | --- |
| — | ยังไม่ได้ seed | — |

## Environment (`.env` ที่ root ห้าม commit)

รูปภาพเก็บใน Cloudflare R2 (bucket แบบ private) ถ้าไม่ตั้งค่า การแนบรูปจะใช้ไม่ได้

```dotenv
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET_NAME=building-service-images
JWT_SECRET_KEY=   # production ต้องตั้งเป็นค่าลับของตัวเอง
```

## Tests

```bash
cd Backend
uv run pytest
```
