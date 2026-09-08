# ARCHITECTURE.md — โครงสร้างระบบ Building Service Management

เอกสารนี้ตอบคำถาม 2 ข้อที่เจอบ่อยที่สุดตอนจะเขียนโค้ดใหม่:

> **1. "โค้ดนี้ต้องไปเขียนไว้ไฟล์ไหน?"** → ดู [ส่วนที่ 3](#3-ตารางตัดสินใจ-ฉันจะเขียน-x-ต้องแตะไฟล์ไหน)
> **2. "ข้อมูลที่ต้องใช้ ดึงมาจากไหน?"** → ดู [ส่วนที่ 4](#4-ดึงข้อมูลจากไหน--dependency-injection)

ถ้าอยากเห็นภาพรวมก่อน อ่าน [ส่วนที่ 1-2](#1-ภาพรวม-30-วินาที) แล้วค่อยกลับมาที่ 2 ข้อข้างบน

---

## 1. ภาพรวม 30 วินาที

ระบบนี้เป็น **web application แบบแยกส่วนหน้า-ส่วนหลัง (decoupled frontend/backend)**
คือ frontend กับ backend เป็นคนละโปรแกรม คุยกันผ่าน HTTP + JSON เท่านั้น

```
┌──────────────┐   HTTP + JSON   ┌──────────────┐   SQL    ┌────────────┐
│   Frontend   │ ──────────────▶ │   Backend    │ ───────▶ │ PostgreSQL │
│  Vue 3 + Vite│ ◀────────────── │   FastAPI    │ ◀─────── │     16     │
│  port 5173   │                 │  port 8000   │          │  port 5432 │
└──────────────┘                 └──────┬───────┘          └────────────┘
                                        │ S3 API
                                        ▼
                                 ┌──────────────┐
                                 │ Cloudflare R2│  เก็บไฟล์รูปภาพ
                                 └──────────────┘
```

| ส่วน | เทคโนโลยี | หน้าที่ |
|---|---|---|
| **Frontend** | Vue 3, Vite | หน้าจอที่ผู้ใช้เห็น ไม่มี business logic สำคัญ |
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy 2.0 (async) | กฎธุรกิจทั้งหมด ตรวจสิทธิ์ ตรวจข้อมูล |
| **Database** | PostgreSQL 16 | เก็บข้อมูลถาวร |
| **Object Storage** | Cloudflare R2 (S3-compatible) | เก็บไฟล์รูป ไม่เก็บใน DB |
| **Migration** | Alembic | จัดการการเปลี่ยนโครงสร้างตาราง |
| **Test** | pytest + SQLite (ในหน่วยความจำชั่วคราว) | เทสต์โดยไม่ต้องมี PostgreSQL |

⚠️ **กฎข้อแรกที่ต้องจำ:** รูปภาพ**ไม่**เก็บลงฐานข้อมูล ฐานข้อมูลเก็บแค่ *ที่อยู่ของไฟล์*
(`object_key`) ส่วนตัวไฟล์จริงอยู่ใน R2 และเวลาจะให้ผู้ใช้ดูรูป backend จะสร้าง
**presigned URL** (ลิงก์ที่มีลายเซ็นและหมดอายุใน 15 นาที) ให้ ไม่ได้เปิด bucket เป็นสาธารณะ

---

## 2. หลักการเดียวที่ต้องเข้าใจ: Layered Architecture

โปรเจกต์นี้แบ่งโค้ดเป็น **ชั้น (layer)** แต่ละชั้นมีหน้าที่เดียว และ
**ชั้นบนเรียกชั้นล่างได้ทางเดียว ห้ามย้อนกลับ**

```
       ┌──────────────────────────────────────────────────────┐
   1   │  endpoints/     "แปลง HTTP ↔ Python"                  │
       │  รู้จัก: status code, HTTPException, query/path param  │
       │  ไม่รู้จัก: SQL, การ query ฐานข้อมูล                    │
       └───────────────────────┬──────────────────────────────┘
                               │ เรียก
       ┌───────────────────────▼──────────────────────────────┐
   2   │  services/      "กฎธุรกิจทั้งหมดอยู่ที่นี่"              │
       │  รู้จัก: SQLAlchemy, เงื่อนไขทางธุรกิจ                  │
       │  ไม่รู้จัก: HTTP, status code, FastAPI                 │
       └───────────────────────┬──────────────────────────────┘
                               │ ใช้
       ┌───────────────────────▼──────────────────────────────┐
   3   │  models/        "หน้าตาของตารางในฐานข้อมูล"            │
       │  รู้จัก: คอลัมน์, ความสัมพันธ์ระหว่างตาราง               │
       │  ไม่รู้จัก: ทุกอย่างข้างบน                              │
       └──────────────────────────────────────────────────────┘

       ┌──────────────────────────────────────────────────────┐
   *   │  schemas/       "รูปทรงข้อมูลเข้า-ออก API"              │
       │  ชั้น 1 และ 2 ใช้ร่วมกัน แต่ไม่ผูกกับ models             │
       └──────────────────────────────────────────────────────┘
```

### ทำไมต้องแบ่งแบบนี้

**เหตุผลที่ 1 — เทสต์ง่าย** service ไม่รู้จัก HTTP จึงเรียกจากเทสต์ตรง ๆ ได้
ไม่ต้องจำลอง request ทั้งอัน

**เหตุผลที่ 2 — ใช้ซ้ำได้** ถ้าวันหนึ่งอยากเรียก logic เดียวกันจาก background job
หรือ command line ก็เรียก service ได้เลย ไม่ติด HTTP มาด้วย

**เหตุผลที่ 3 — รู้ทันทีว่าบั๊กอยู่ชั้นไหน** ตอบ 422 → ปัญหาที่ schema,
ตอบ 404 ทั้งที่ข้อมูลมี → ปัญหาที่ service, INSERT ไม่ลง → ปัญหาที่ model

### ตัวอย่างที่เห็นได้จริงในโค้ดนี้

`services/lost_found.py` นิยาม exception ของตัวเองแทนที่จะ `raise HTTPException`:

```python
class PublicItemNotFoundError(LookupError):
    """ไม่พบประกาศ public ที่ตรงกับประเภทและรหัส."""
```

แล้ว `endpoints/lost_item.py` เป็นคนแปลงเป็น HTTP:

```python
except PublicItemNotFoundError as exc:
    raise HTTPException(status_code=404, detail=str(exc)) from exc
```

นี่คือหลัก **separation of concerns** (แยกความรับผิดชอบ) — service สนใจแค่ว่า
"หาไม่เจอ" ส่วนการตัดสินว่า "หาไม่เจอ = 404" เป็นเรื่องของโลก HTTP

### ⛔ สิ่งที่ห้ามทำเด็ดขาด

| ห้าม | เพราะ |
|---|---|
| `from fastapi import HTTPException` ใน `services/` | ผูก business logic เข้ากับ HTTP |
| เขียน `select(...)` ใน `endpoints/` | logic กระจัดกระจาย เทสต์ยาก ใช้ซ้ำไม่ได้ |
| `services/` import จาก `endpoints/` | เกิด **circular import** (สองไฟล์ import กันไปมาจน Python พัง) |
| ส่ง SQLAlchemy model ออกไปเป็น response ตรง ๆ | ฟิลด์ลับหลุด — ดูหัวข้อ [7.1](#71-ป้องกันข้อมูลลับด้วยรูปทรงของ-schema) |

---

## 3. ตารางตัดสินใจ: "ฉันจะเขียน X ต้องแตะไฟล์ไหน"

> **หลักการเรียงลำดับ: เขียนจากชั้นในออกชั้นนอก** (model → schema → service → endpoint)
> เพราะแต่ละชั้นต้องพึ่งชั้นที่อยู่ล่างกว่า ถ้าเขียนสลับลำดับจะเขียนไปแก้ไปไม่จบ

### 3.1 เพิ่ม endpoint ใหม่ในโมดูลที่มีอยู่แล้ว

*ตัวอย่าง: เพิ่ม `POST /guest/found-items/{item_code}/claims`*

| ลำดับ | ไฟล์ | ทำอะไร |
|---|---|---|
| 1 | `app/schemas/<โมดูล>.py` | สร้างคลาส request/response |
| 2 | `app/services/<โมดูล>.py` | เขียน business logic + exception ของตัวเอง |
| 3 | `app/api/v1/endpoints/<โมดูล>.py` | เพิ่ม `@router.<method>` แล้วเรียก service |
| 4 | `tests/test_<โมดูล>.py` | เขียนเทสต์ |

✅ **ไม่ต้องแตะ `router.py`** ถ้า path ใหม่อยู่ใต้ prefix เดิม

### 3.2 เพิ่มโมดูลใหม่ทั้งก้อน

*ตัวอย่าง: เพิ่มระบบ `/api/v1/guest/locations`*

| ลำดับ | ไฟล์ | ทำอะไร |
|---|---|---|
| 1 | `app/schemas/<ใหม่>.py` | สร้างไฟล์ schema ใหม่ |
| 2 | `app/services/<ใหม่>.py` | สร้างไฟล์ service ใหม่ |
| 3 | `app/api/v1/endpoints/<ใหม่>.py` | สร้างไฟล์ endpoint ใหม่ + `router = APIRouter()` |
| 4 | `app/api/v1/router.py` | ⚠️ **ต้องแตะ** — `import` แล้ว `include_router(..., prefix=...)` |
| 5 | `tests/test_<ใหม่>.py` | เขียนเทสต์ |

### 3.3 เพิ่ม/แก้ฟิลด์ใน response ที่มีอยู่

| ลำดับ | ไฟล์ | ทำอะไร |
|---|---|---|
| 1 | `app/schemas/<โมดูล>.py` | เพิ่มฟิลด์ในคลาส response |
| 2 | `app/services/<โมดูล>.py` | หาจุดที่ประกอบ response แล้วส่งค่าใหม่เข้าไป |

> 💡 ถ้าลืมขั้นที่ 2 Pydantic จะ error ทันทีว่าฟิลด์ขาด — ถือเป็นเรื่องดี เพราะพลาดไม่ได้เงียบ ๆ

### 3.4 เพิ่มตารางใหม่ หรือเพิ่มคอลัมน์ในตารางเดิม

| ลำดับ | ไฟล์ / คำสั่ง | ทำอะไร |
|---|---|---|
| 1 | `app/models/<โมดูล>.py` | เพิ่มคลาส/คอลัมน์ + `relationship()` ถ้ามี FK |
| 2 | `app/models/__init__.py` | ⚠️ **ถ้าเป็นคลาสใหม่ ต้อง import ที่นี่ด้วย** ไม่งั้น Alembic มองไม่เห็น |
| 3 | `alembic revision --autogenerate -m "..."` | ให้ Alembic เทียบ model กับ DB แล้วสร้างไฟล์ migration |
| 4 | `migrations/versions/<ไฟล์ใหม่>.py` | **อ่านและแก้ให้ถูก** — autogenerate ไม่เคยถูก 100% |
| 5 | `alembic upgrade head` | รัน migration จริง |

⚠️ **ขั้นที่ 2 คือกับดักที่พลาดกันบ่อยที่สุด** — `migrations/env.py` มีบรรทัด
`import app.models` แล้วใช้ `Base.metadata` เป็นตัวเปรียบเทียบ ถ้าคลาสใหม่ไม่ถูก import
เข้า `app/models/__init__.py` มันจะไม่อยู่ใน `Base.metadata` และ Alembic จะ
**สร้าง migration ว่างเปล่าให้โดยไม่แจ้ง error อะไรเลย**

### 3.5 อื่น ๆ

| อยากทำอะไร | ไปที่ไฟล์ |
|---|---|
| เพิ่มค่า config / ตัวแปร environment | `app/core/config.py` แล้วอัปเดต `.env.example` |
| เพิ่มกฎตรวจสิทธิ์แบบใหม่ (เช่น `HousekeeperStaff`) | `app/api/dependencies.py` |
| รับไฟล์อัปโหลดจากฟอร์ม | `app/api/v1/forms.py` + `app/services/images.py` |
| แก้เรื่อง JWT / การแฮชรหัสผ่าน | `app/core/security.py` |
| แก้เรื่องการเชื่อม R2 | `app/services/object_storage.py` |
| เพิ่ม enum ใหม่ (สถานะ, บทบาท) | `app/models/enums.py` |

---

## 4. "ดึงข้อมูลจากไหน" — Dependency Injection

นี่คือส่วนที่งงบ่อยที่สุด **คำตอบคือ: ไม่ต้องไปหาเอง ให้ประกาศว่าต้องการอะไร แล้ว
FastAPI จะหามาให้**

กลไกนี้เรียกว่า **Dependency Injection (DI)** แปลว่า "ฉีดสิ่งที่ต้องพึ่งพาเข้ามาให้"
แทนที่ฟังก์ชันจะไปสร้าง/หาของที่ต้องใช้เอง มันแค่**บอกชนิดของสิ่งที่ต้องการไว้ใน
พารามิเตอร์** แล้วมีคนอื่นจัดหามาให้

### 4.1 ตารางสรุป: อยากได้อะไร เขียนว่าอะไร

| อยากได้ | เขียนแบบนี้ในพารามิเตอร์ของ endpoint | import จาก |
|---|---|---|
| **Database session** | `session: DbSession` | `app.api.dependencies` |
| **R2 client** | `storage: ObjectStorageClient` | `app.api.dependencies` |
| **พนักงานที่ล็อกอินอยู่** | `current_staff: CurrentStaff` | `app.api.dependencies` |
| **บังคับว่าต้องเป็น admin** | `_: AdminStaff` | `app.api.dependencies` |
| **บังคับว่าต้องเป็น clerk** | `_: ClerkStaff` | `app.api.dependencies` |
| **ค่าจาก path** เช่น `/{item_code}` | `item_code: str` (ชื่อตรงกับใน path) | — |
| **ค่าจาก query string** `?limit=20` | `limit: Annotated[int, Query(ge=1, le=100)] = 20` | `fastapi` |
| **JSON body** | `payload: MySchema` | `app.schemas.<โมดูล>` |
| **multipart form + ไฟล์** | `payload: Annotated[X, Depends(parse_...)]` | `app.api.v1.forms` |
| **ไฟล์อัปโหลด** | `image: Annotated[UploadFile \| None, File()] = None` | `fastapi` |
| **ค่า config** | `from app.core.config import settings` (import ตรง ไม่ใช่ DI) | `app.core.config` |

### 4.2 ตัวอย่างจริงจากโค้ด

```python
@router.get("/{item_code}", response_model=GuestItemPublicResponse)
async def read_lost_item(
    item_code: str,                                        # ← จาก path
    session: DbSession,                                    # ← DI: database
    storage: ObjectStorageClient,                          # ← DI: R2
    reporter_email: Annotated[EmailStr | None, Query()] = None,  # ← จาก query string
) -> GuestItemPublicResponse:
```

**ไม่มีบรรทัดไหนเลยที่ต้องเขียน `create_engine()` หรือ `boto3.client()` เอง**
เพราะทุกอย่างถูกจัดหามาผ่าน type annotation

### 4.3 เบื้องหลัง: `DbSession` มาจากไหน

```
app/core/config.py        settings.database_url  (อ่านจาก .env)
        ↓
app/db/session.py         engine = create_async_engine(...)
                          AsyncSessionLocal = async_sessionmaker(...)
                          async def get_db_session():  ← เปิด session แล้ว yield
        ↓
app/api/dependencies.py   DbSession = Annotated[AsyncSession, Depends(get_db_session)]
        ↓
endpoint                  session: DbSession
```

`get_db_session()` ใช้ `yield` ไม่ใช่ `return` เพราะ FastAPI จะ:
1. เปิด session ก่อนเข้า endpoint
2. ส่งเข้าไปให้ endpoint ใช้
3. **ปิด session ให้อัตโนมัติหลัง response ถูกส่งกลับ ไม่ว่าจะสำเร็จหรือ error**

> 💡 **1 request = 1 session** เสมอ ทุก service ที่ถูกเรียกใน request เดียวกัน
> ใช้ session ตัวเดียวกัน ดังนั้น `await session.commit()` ครั้งเดียวจะบันทึกทุกอย่าง
> ที่เพิ่มไว้พร้อมกัน (เป็น **transaction** เดียว = สำเร็จทั้งหมดหรือไม่สำเร็จเลย)

### 4.4 การตรวจสิทธิ์ทำงานอย่างไร

```
CurrentStaff  ─── ตรวจ Bearer token → decode JWT → โหลด Staff จาก DB → เช็ค status ACTIVE
    ↓
AdminStaff    ─── ทำทุกอย่างข้างบน + เช็ค role == ADMIN  ไม่ใช่ → 403
ClerkStaff    ─── ทำทุกอย่างข้างบน + เช็ค role == CLERK  ไม่ใช่ → 403
```

⚠️ **จุดออกแบบสำคัญ:** ระบบ**ไม่เชื่อ `role` ที่อยู่ใน JWT** แต่โหลดข้อมูลจริงจาก
ฐานข้อมูลใหม่ทุกครั้ง เพราะถ้า admin ลดสิทธิ์หรือระงับบัญชีใครไปแล้ว token เก่า
ที่ยังไม่หมดอายุจะต้องใช้ไม่ได้ทันที

**endpoint ฝั่ง guest ไม่ใส่ dependency พวกนี้เลย** เพราะ guest ไม่มีบัญชี ไม่ต้อง login

---

## 5. เดินตาม request จริงหนึ่งครั้ง

ตัวอย่าง: guest แจ้งพบของพร้อมแนบรูป
`POST /api/v1/guest/found-items` (multipart form)

```
 ①  main.py
     app = create_application()
     └─ include_router(api_router, prefix="/api/v1")     ← ต่อ "/api/v1" ข้างหน้า

 ②  api/v1/router.py
     include_router(found_item.router, prefix="/guest/found-items")
     → path เต็มกลายเป็น /api/v1/guest/found-items

 ③  api/v1/endpoints/found_item.py :: add_found_item()
     รับ: payload (ผ่าน Depends), session, storage, image
     ยังไม่ทำ logic อะไร แค่รับของแล้วส่งต่อ

 ④  api/v1/forms.py :: parse_guest_found_item_form()
     multipart form ส่งมาเป็น key-value ธรรมดา Pydantic อ่านตรง ๆ ไม่ได้
     ไฟล์นี้จึงรับทีละช่องด้วย Form() แล้วประกอบเป็น schema
     ⚠️ ถ้าตรวจไม่ผ่าน → ตอบ 422 ตั้งแต่ตรงนี้ ไม่เข้า service เลย

 ⑤  schemas/lost_found_item.py :: GuestFoundItemCreate
     ตรวจกฎ: อีเมลถูกรูปแบบไหม, event_datetime เป็นอนาคตหรือเปล่า,
     normalize ข้อความ (ตัดช่องว่างเกิน, อีเมลเป็นตัวพิมพ์เล็ก)

 ⑥  services/lost_found.py :: create_guest_item()      ← business logic อยู่ตรงนี้ทั้งหมด
     ├─ ตรวจว่า location_id มีจริงและเปิดใช้งานอยู่
     ├─ สร้าง item_code เช่น FOUND-20260907-A1B2C3D4
     ├─ services/images.py :: prepare_guest_image()
     │     ตรวจ magic bytes (ดูไบต์ต้นไฟล์ว่าเป็นรูปจริงไหม ไม่เชื่อนามสกุล)
     │     กันไฟล์ระเบิด (decompression bomb) → แปลงเป็น WebP → EXIF หายไปเอง
     ├─ services/object_storage.py :: put()   อัปโหลดขึ้น R2
     ├─ session.add(LostItem)  +  LostItemHistory  +  Image
     └─ await session.commit()     ← ทั้ง 3 ตารางลงพร้อมกันใน transaction เดียว

 ⑦  models/lost_found.py
     SQLAlchemy แปลง object เป็น SQL INSERT แล้วยิงเข้า PostgreSQL

 ⑧  ย้อนกลับขึ้นไป
     service คืน GuestItemCreatedResponse
     → FastAPI แปลงเป็น JSON ตาม response_model
     → HTTP 201 Created
```

### ⚠️ ถ้าพังกลางทางจะเป็นอย่างไร

```
อัปโหลดรูปขึ้น R2 สำเร็จแล้ว → แต่ commit ลง DB ไม่ผ่าน
        ↓
    rollback ฐานข้อมูล  +  ลบไฟล์ที่เพิ่งอัปขึ้น R2 ทิ้ง
        ↓
    ไม่เหลือไฟล์กำพร้า (orphaned object) ค้างใน R2
```

นี่คือสิ่งที่บล็อก `try/except` ใน `create_guest_item()` ทำอยู่ — ต้องดูแล 2 ระบบ
(DB + R2) ที่ไม่มี transaction ร่วมกัน ให้สอดคล้องกันด้วยมือ

---

## 6. แผนที่ไฟล์ทั้งหมด

### 6.1 Backend

```
Backend/
├── app/
│   ├── main.py                     ⭐ จุดเริ่มต้นของโปรแกรม
│   │                                  สร้าง FastAPI app, ตั้ง CORS, ต่อ router
│   │
│   ├── core/                       ── เครื่องมือพื้นฐานที่ทุกส่วนใช้ร่วมกัน
│   │   ├── config.py               ⭐ ค่าตั้งค่าทั้งหมด อ่านจาก .env
│   │   │                              ใช้: from app.core.config import settings
│   │   └── security.py                แฮชรหัสผ่าน (Argon2) + สร้าง/ถอด JWT
│   │
│   ├── db/                         ── การเชื่อมต่อฐานข้อมูล
│   │   ├── base.py                    คลาส Base ที่ทุก model สืบทอด
│   │   └── session.py              ⭐ engine + get_db_session() (ต้นทางของ DbSession)
│   │
│   ├── models/                     ── ชั้น 3: หน้าตาตารางในฐานข้อมูล
│   │   ├── __init__.py             ⚠️ ต้อง import ทุก model ที่นี่ ไม่งั้น Alembic มองไม่เห็น
│   │   ├── enums.py                ⭐ enum ทุกตัว: LostStatus, ClaimStatus, StaffRole, ...
│   │   ├── staff.py                   ตาราง staff (พนักงาน)
│   │   ├── staff_account.py           แค่ alias ชื่อเก่า StaffAccount = Staff
│   │   ├── lost_found.py           ⭐ LostItem, LostItemHistory, LostClaim
│   │   ├── service_request.py         งานซ่อม/ทำความสะอาด (คนละโมดูล)
│   │   ├── location.py                สถานที่ + qr_token
│   │   ├── image.py                   metadata ของรูป (ไม่ใช่ตัวไฟล์)
│   │   └── notification.py            แจ้งเตือนของ staff
│   │
│   ├── schemas/                    ── รูปทรงข้อมูลเข้า-ออก API (Pydantic)
│   │   ├── lost_found_item.py      🟢 guest: ของหาย/ของพบ
│   │   ├── lost_found_clerk.py     🔵 staff: ตรวจสอบประกาศ
│   │   ├── staff.py                   บัญชีพนักงาน (StaffResponse ไม่มี password_hash)
│   │   └── auth.py                    login request/response
│   │
│   ├── services/                   ── ชั้น 2: business logic ทั้งหมด
│   │   ├── lost_found.py           🟢 ⭐ guest: สร้างประกาศ, list, อ่านรายชิ้น, ติดตาม
│   │   ├── lost_found_clerk.py     🔵 staff: ดูรายการรอตรวจ
│   │   ├── images.py                  ตรวจ + แปลงรูปเป็น WebP + กันไฟล์อันตราย
│   │   ├── object_storage.py          คุยกับ R2: put / delete / สร้าง presigned URL
│   │   ├── staff.py                   CRUD บัญชีพนักงาน
│   │   └── auth.py                    ตรวจ username/password
│   │
│   └── api/
│       ├── dependencies.py         ⭐ DbSession, ObjectStorageClient,
│       │                              CurrentStaff, AdminStaff, ClerkStaff
│       └── v1/
│           ├── router.py           ⭐ รวม endpoint ทุกตัว + กำหนด prefix
│           ├── forms.py               แปลง multipart form → schema
│           └── endpoints/          ── ชั้น 1: แปลง HTTP ↔ Python
│               ├── lost_item.py    🟢 /guest/lost-items
│               ├── found_item.py   🟢 /guest/found-items
│               ├── lost_found_clerk.py 🔵 /lost-found (staff)
│               ├── staff.py        🔵 /staff (admin)
│               └── auth.py         🔵 /auth
│
├── migrations/                     ── Alembic
│   ├── env.py                         ตั้งค่า Alembic ให้ใช้ async engine + Base.metadata
│   └── versions/                   ⭐ ไฟล์ migration เรียงตามเวลา
│       ├── 20260806_0001_create_staff_accounts.py
│       ├── 20260807_0002_seed_initial_staff.py
│       ├── 20260812_0003_add_service_management_schema.py   ← lost_items, lost_claims อยู่นี่
│       └── 20260815_0004_add_r2_image_metadata.py
│
├── tests/
│   ├── conftest.py                 ⭐ fixture ที่ทุกเทสต์ใช้ร่วมกัน
│   ├── test_guest_lost_found.py    🟢
│   ├── test_lost_found_clerk.py    🔵
│   ├── test_auth.py
│   ├── test_staff_seed.py
│   └── test_database_schema.py
│
├── pyproject.toml                     dependencies + ตั้งค่า pytest/ruff
├── alembic.ini                        ตั้งค่า Alembic
└── Dockerfile
```

🟢 = ขอบเขตงาน guest backend  🔵 = ฝั่ง staff  ⭐ = ไฟล์ที่ควรอ่านก่อนเป็นอันดับแรก

### 6.2 Frontend (อ่านผ่าน ๆ พอ)

```
Frontend/src/
├── main.js                    จุดเริ่มต้นของ Vue
├── router/index.js            กำหนดว่า URL ไหนแสดงหน้าไหน
├── services/api.js            ⭐ จุดเดียวที่ควรเรียก backend (ตอนนี้มีแค่ getHealth())
├── views/                     หน้าจอหลัก 3 หน้า
│   ├── PublicServicePortal.vue    หน้าสำหรับ guest
│   ├── staff-login.vue
│   └── staff-dashboard.vue
├── view-logic/                logic ของแต่ละหน้า แยกออกจาก template
│   ├── usePublicServicePortal.js  ⭐ logic ฝั่ง guest รวมทั้ง filterPosts()
│   └── useStaffDashboard.js
├── components/
│   ├── public/pages/          หน้าย่อยฝั่ง guest (LostAndFoundPage.vue ฯลฯ)
│   └── staff/<role>/          หน้าย่อยแยกตามบทบาทพนักงาน
└── styles/                    CSS
```

⚠️ **สถานะปัจจุบัน:** `api.js` มีแค่ `getHealth()` — หน้า guest ยัง**ไม่ได้ต่อ API จริง**
ข้อมูลที่เห็นบนหน้าจอเป็นการ์ดที่เขียนค้างไว้ใน template

### 6.3 ไฟล์ที่ root

```
├── compose.yaml            ⭐ นิยาม 3 service: database, backend, frontend
│                              backend รัน "alembic upgrade head" ให้อัตโนมัติตอนเริ่ม
├── .env / .env.example        ค่าลับ (รหัสผ่าน DB, JWT secret, R2 credentials)
├── AGENTS.md                  กติกาการทำงานร่วมกับ AI assistant
├── PLANNING.md                แผนงาน Search + Claim
├── ARCHITECTURE.md            ไฟล์นี้
└── README.md
```

---

## 7. รูปแบบที่ใช้ซ้ำทั้งโปรเจกต์ (จำไว้แล้วเขียนโค้ดใหม่ได้เร็วขึ้นมาก)

### 7.1 ป้องกันข้อมูลลับด้วย "รูปทรงของ schema"

`LostItem` มีฟิลด์ลับ `private_verification_detail` และ `reporter_email`
แต่ `GuestItemPublicResponse` **ไม่มีฟิลด์เหล่านี้อยู่เลยตั้งแต่แรก**

```python
# ✅ ถูก — schema กำหนดว่าอะไรออกได้ ต้องเขียนชื่อฟิลด์เองทีละตัว
return GuestItemPublicResponse(
    id=item.id,
    item_code=item.item_code,
    ...
)

# ❌ ผิด — โยน model เข้าไปทั้งก้อน วันหนึ่งมีคนเพิ่มฟิลด์ลับใหม่แล้วหลุดทันที
return GuestItemPublicResponse.model_validate(item)
```

**ทำไมวิธีแรกปลอดภัยกว่า:** ถ้าใช้วิธี "คืนทุกอย่างแล้วลบตัวที่ไม่อยากให้เห็น"
วันหนึ่งมีคนเพิ่มคอลัมน์ลับใหม่เข้า model แล้วลืมไปเพิ่มในรายการที่ต้องลบ ข้อมูลก็หลุด
แต่วิธีแรก **ฟิลด์ใหม่จะไม่หลุดเอง** เพราะต้องไปเขียนชื่อมันใน schema ก่อน

> ข้อยกเว้น: `StaffResponse` และ schema ฝั่ง clerk ใช้ `ConfigDict(from_attributes=True)`
> ได้ เพราะเป็น API ที่ต้อง login แล้วและ schema ระบุฟิลด์ไว้ครบถ้วนแล้ว

### 7.2 normalize ข้อมูลตั้งแต่ขาเข้า

ทุก schema ที่รับอีเมลจะแปลงเป็นตัวพิมพ์เล็กด้วย `field_validator`:

```python
@field_validator("reporter_email")
@classmethod
def normalize_email(cls, value: EmailStr) -> str:
    return str(value).strip().lower()
```

⚠️ **ผลที่ตามมาที่ต้องจำ:** ข้อมูลใน DB เป็นตัวพิมพ์เล็กเสมอ
ดังนั้น**เวลาค้นหาต้อง `.lower()` ก่อนเทียบด้วย** ไม่งั้นคนกรอก `A@B.com` จะหาไม่เจอ
เช่นเดียวกับ `item_code` ที่เก็บเป็นตัวพิมพ์ใหญ่ → ต้อง `.strip().upper()` ก่อนค้น

### 7.3 exception ของตัวเอง แทน HTTPException ใน service

```python
# services/  →  นิยาม exception เอง
class LocationNotFoundError(ValueError): ...
class PublicItemNotFoundError(LookupError): ...
class ItemPersistenceError(RuntimeError): ...

# endpoints/  →  แปลงเป็น HTTP
except LocationNotFoundError as exc:
    raise HTTPException(status_code=422, detail=str(exc)) from exc
```

> 💡 `from exc` ทำให้ traceback แสดง "สาเหตุเดิม" ด้วย ตอน debug จะเห็นว่าพังมาจากไหนจริง ๆ

### 7.4 ข้อความ error ที่ไม่บอกความจริงมากเกินไป

```python
# ✅ ตอบเหมือนกันทั้งกรณี "ไม่มีรหัสนี้" และ "มีแต่อีเมลไม่ตรง"
raise PublicItemNotFoundError("ไม่พบประกาศนี้")
```

ถ้าแยกข้อความ คนร้ายจะใช้ความต่างนั้นไล่เดาว่าอีเมลไหนเป็นผู้แจ้งประกาศไหน
เรียกว่า **information leak ผ่าน error message** — `endpoints/auth.py` ก็ใช้หลักเดียวกัน
(ไม่บอกว่า "ไม่มีบัญชีนี้" หรือ "รหัสผ่านผิด" แต่บอกรวม ๆ ว่า "identifier or password ผิด")

### 7.5 หลีกเลี่ยง N+1 query

```python
# ❌ ผิด: 1 + N ครั้ง — โหลด 20 ประกาศ = ยิง DB 21 ครั้ง
for item in items:
    images = await session.scalars(select(Image).where(Image.lost_item_id == item.id))

# ✅ ถูก: 2 ครั้งเสมอ ไม่ว่ามีกี่รายการ
image_map = await _load_image_map(session, [item.id for item in items])
```

ดูตัวอย่างจริงที่ `_load_image_map()` ใน `services/lost_found.py`

### 7.6 เทสต์ทำงานอย่างไร

`tests/conftest.py` มี fixture ชื่อ `test_context` ที่:

1. สร้างไฟล์ SQLite ชั่วคราวใน `tmp_path` (หายไปเองหลังเทสต์จบ)
2. สร้างตารางทั้งหมดจาก `Base.metadata` — **ไม่ได้รัน Alembic**
3. ใช้ `dependency_overrides` **สลับ `get_db_session` ให้ชี้ไปที่ SQLite แทน PostgreSQL**

```python
application.dependency_overrides[get_db_session] = override_db_session
```

นี่คือพลังของ DI — สลับของจริงเป็นของปลอมได้โดยไม่ต้องแก้โค้ด production เลยสักบรรทัด
เทสต์ที่ต้องใช้ R2 ก็สลับเป็น `FakeObjectStorage` ด้วยวิธีเดียวกัน

⚠️ **ข้อควรระวัง 2 ข้อ:**
- SQLite **ไม่บังคับ foreign key** ถ้าไม่เปิด `PRAGMA foreign_keys=ON` (ตอนนี้ยังไม่เปิด)
  → บั๊กเรื่องลำดับการ INSERT จะไม่โผล่ในเทสต์ แต่ไปโผล่บน PostgreSQL จริง
- เทสต์สร้างตารางจาก model โดยตรง **ไม่ผ่าน migration** → ถ้า migration เขียนผิด
  เทสต์จะยังเขียวอยู่ ต้องรันจริงด้วย `docker compose up` เพื่อยืนยัน

---

## 8. Checklist เวลาจะเพิ่มฟีเจอร์ใหม่

```
□ 1. ฟีเจอร์นี้เป็นของ guest หรือ staff?
        guest → ไม่ใส่ dependency ตรวจสิทธิ์
        staff → ใส่ CurrentStaff / AdminStaff / ClerkStaff

□ 2. ต้องเพิ่ม/แก้ตารางไหม?
        ใช่  → models/ → models/__init__.py → alembic revision → แก้ migration → upgrade
        ไม่  → ข้ามไปข้อ 3

□ 3. ข้อมูลเข้า-ออกหน้าตาอย่างไร?  → เขียน schema ก่อน
        ⚠️ ตรวจว่าไม่มีฟิลด์ลับหลุดออกไป

□ 4. กฎธุรกิจคืออะไร?  → เขียน service
        ⚠️ ห้าม import HTTPException
        ⚠️ นิยาม exception ของตัวเอง

□ 5. ต่อ endpoint  → เรียก service แล้วแปลง exception เป็น HTTP status

□ 6. path ใหม่อยู่ใต้ prefix เดิมไหม?
        ใช่  → ไม่ต้องแตะ router.py
        ไม่  → เพิ่ม include_router() ใน router.py

□ 7. เขียนเทสต์ แล้วรัน .venv/bin/python -m pytest tests/ -q

□ 8. ตรวจว่าข้อมูลลับไม่หลุด — assert ในเทสต์ว่าฟิลด์ลับไม่อยู่ใน response
```

---

## 9. คำสั่งที่ใช้บ่อย

```bash
# ── รันทั้งระบบ (จาก root ของโปรเจกต์) ──
docker compose up                 # database + backend + frontend
                                  # backend รัน alembic upgrade head ให้เอง
# เปิด http://localhost:8000/docs   ← OpenAPI docs ลองยิง endpoint ได้เลย
# เปิด http://localhost:5173        ← หน้าเว็บ

# ── เทสต์ (จากโฟลเดอร์ Backend) ──
cd Backend
.venv/bin/python -m pytest tests/ -q                       # ทั้งหมด
.venv/bin/python -m pytest tests/test_guest_lost_found.py -v  # เฉพาะไฟล์
.venv/bin/python -m pytest tests/ -k "tracking" -v          # เฉพาะเทสต์ที่ชื่อมีคำนี้

# ── Migration ──
.venv/bin/alembic revision --autogenerate -m "add something"  # สร้างไฟล์ใหม่
.venv/bin/alembic upgrade head       # รัน migration ที่ยังไม่ได้รัน
.venv/bin/alembic downgrade -1       # ย้อนกลับ 1 ขั้น
.venv/bin/alembic current            # ดูว่าตอนนี้อยู่ migration ไหน

# ── ตรวจคุณภาพโค้ด ──
.venv/bin/ruff check app tests       # หาปัญหา
.venv/bin/ruff format app tests      # จัดรูปแบบ (line-length = 100)
```

---

## 10. อ่านต่อ

| ต้องการ | อ่านที่ |
|---|---|
| แผนงาน Search และ Claim ที่กำลังจะทำ | `PLANNING.md` |
| กติกาการทำงานร่วมกับ AI assistant | `AGENTS.md` |
| วิธีติดตั้งและรันครั้งแรก | `README.md` |
| API มี endpoint อะไรบ้าง (อัปเดตเองอัตโนมัติ) | `http://localhost:8000/docs` |

### เริ่มอ่านโค้ดตรงไหนดี — ลำดับที่แนะนำ

1. `app/main.py` — สั้นมาก เห็นภาพรวมว่าแอปประกอบขึ้นมาอย่างไร
2. `app/api/v1/router.py` — เห็นว่ามี endpoint กลุ่มไหนบ้าง
3. `app/models/enums.py` — เห็นสถานะและบทบาททั้งหมดในระบบ
4. `app/models/lost_found.py` — เห็นโครงข้อมูลของโมดูลหลัก
5. `app/api/v1/endpoints/lost_item.py` → `app/services/lost_found.py`
   — **เดินตาม flow เต็ม ๆ หนึ่งรอบ** จาก HTTP ลงไปถึง SQL
6. `tests/test_guest_lost_found.py` — เห็นว่าระบบควรทำงานอย่างไรจากมุมของคนใช้
