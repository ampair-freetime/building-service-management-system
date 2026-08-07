# Building Service Management System

Starter monorepo for a FastAPI backend and Vue 3 frontend.

## Structure

```text
Backend/
  app/
    db/      Database base class and async session
    api/     FastAPI endpoints
    core/    Application configuration
  tests/     Backend tests
Frontend/    Vue 3 application built with Vite
.codex/      Repository-local development skill
```

## Run locally

Start the API:

```bash
cd Backend
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload
```

Start the web application in another terminal:

```bash
cd Frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173`; the API and its documentation run at
`http://localhost:8000` and `http://localhost:8000/docs`.

Alternatively, run the PostgreSQL database, API, and web application together:

```bash
docker compose up --build
```

PostgreSQL is available to the backend inside the Compose network. Its data is persisted in the
`postgres_data` Docker volume. Development credentials can be overridden
with `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD`.

## Staff login backend / ระบบล็อกอินพนักงาน

This project provides backend-only staff authentication. Staff may sign in with either
their email address or employee code. Passwords are hashed with Argon2, and successful
login returns a JWT bearer token.

ระบบนี้มีเฉพาะ API ฝั่ง backend สำหรับล็อกอินพนักงาน โดยใช้อีเมลหรือรหัสพนักงานก็ได้
รหัสผ่านถูกแฮชด้วย Argon2 และเมื่อล็อกอินสำเร็จจะได้รับ JWT สำหรับยืนยันตัวตน

| Stored role | คำแปลภาษาไทย |
| --- | --- |
| `housekeeper` | แม่บ้าน |
| `technician` | ช่างเทคนิค |
| `coordinator` | ผู้ประสานงาน |
| `admin` | ผู้ดูแลระบบ (แอดมิน) |

Apply the database migrations before first use. This also seeds the development
administrator, so no separate staff-creation CLI command is required:

```bash
cd Backend
alembic upgrade head
```

| Seed field | Development value |
| --- | --- |
| Employee code | `ADMIN001` |
| Email | `admin@example.com` |
| Password | `Admin@1234` |
| Role | `admin` |

The seed stores only an Argon2 password hash in the migration and database. These are
public development credentials; do not use this seeded account in production.

Available endpoints:

| Method and path | Purpose / คำอธิบาย |
| --- | --- |
| `POST /api/v1/auth/login` | Login with email or employee code / ล็อกอิน |
| `GET /api/v1/auth/me` | Read the signed-in staff profile / ดูข้อมูลผู้ใช้ปัจจุบัน |
| `POST /api/v1/staff` | Create a staff account (admin only) / เพิ่มพนักงาน |
| `GET /api/v1/staff` | List staff accounts (admin only) / ดูรายชื่อพนักงาน |

Login request example:

```json
{
  "identifier": "ADMIN001",
  "password": "Admin@1234"
}
```

Set a strong, private `JWT_SECRET_KEY` in production. Never use the development
default for a deployed system.
