# Deployment บนเซิร์ฟเวอร์ที่ยังไม่ทราบข้อจำกัด

เอกสารนี้อธิบายชุดรัน production ที่เพิ่มเข้ามา โดยยังต้องตรวจเครือข่ายและทรัพยากรจากเครื่องภาควิชาจริง ไม่ได้หมายความว่า deploy บนเครื่องนั้นแล้ว

## Configuration และลำดับความสำคัญ

Backend อ่านค่าโดยเรียงลำดับความสำคัญจากสูงไปต่ำ: environment ของ process → `Backend/.env` → `.env` ที่ root → ค่าเริ่มต้นใน Settings ตำแหน่ง default อ้างอิงจากไฟล์ `config.py` จึงไม่เปลี่ยนตาม working directory

กำหนด `BSMS_ENV_FILE=/absolute/path/to/backend.env` เพื่อเลือกอ่านเพียงไฟล์นั้น หรือ `BSMS_ENV_FILE=` เพื่อปิด dotenv แล้วใช้ process environment ทั้งหมด ตัวแปรที่ไม่ใช่ของ backend ใน dotenv เช่น `POSTGRES_*` และ `VITE_*` ถูกละเลยผ่าน `extra="ignore"`; ต้องตรวจชื่อที่สะกดเอง เพราะชื่อที่สะกดผิดจะถูกละเลยเช่นกัน `STAFF_LOGIN_URL` ไม่มีผลต่อ invitation

`STAFF_ACTIVATION_URL` ว่างจะคำนวณจาก `PUBLIC_BASE_URL` + `/staff/setup-password` หาก frontend อยู่คนละ path ให้กำหนด URL เต็มเอง Production ปฏิเสธ JWT key เริ่มต้น/สั้นกว่า 32 ตัวอักษร และ frontend URL ที่เป็น localhost แต่ยังต้องจัด HTTPS ที่ reverse proxy ของภาควิชา

`.env.production.example` เป็นตัวอย่าง ไม่มี credentials จริง ห้ามนำไฟล์ตัวอย่างไปใช้งานทั้งชุดโดยไม่กรอกค่า ห้าม commit `.env.production` และอย่าใส่ความลับในตัวแปร `VITE_*` เพราะ browser อ่านได้

## Docker

1. คัดลอก `.env.production.example` เป็น `.env.production` แล้วตั้ง `POSTGRES_PASSWORD`, `JWT_SECRET_KEY`, `PUBLIC_BASE_URL`, `BACKEND_CORS_ORIGINS` และ SMTP/R2 ตามสิทธิ์ที่มี ควรใช้รหัสผ่านฐานข้อมูลที่เป็นตัวอักษร/ตัวเลขเพื่อหลีกเลี่ยงปัญหา URL encoding ใน Compose หรือแก้การสร้าง DATABASE_URL ให้ encode รหัสผ่านตามต้องการ
2. ตรวจ configuration แบบไม่พิมพ์ secrets: `docker compose --env-file .env.production -f compose.production.yaml config --quiet`
3. Build ก่อนเปิดบริการ: `docker compose --env-file .env.production -f compose.production.yaml build`
4. เริ่ม database/backend: `docker compose --env-file .env.production -f compose.production.yaml up -d database backend` คำสั่งเริ่ม backend จะ validate settings → รัน Alembic migration → เริ่ม Uvicorn หนึ่ง worker ไม่ใช้ reload
5. Migration เดิมสร้าง admin ด้วยรหัสผ่าน development ที่เป็นสาธารณะ ต้องเปลี่ยน credentials ของบัญชีนี้ด้วยกระบวนการดูแลฐานข้อมูลของโครงการก่อนเปิดให้บุคคลอื่นใช้งาน ห้ามใช้ `Admin@1234` ใน production
6. ตรวจบริการ: `docker compose --env-file .env.production -f compose.production.yaml exec backend python scripts/check_services.py`
7. เริ่ม frontend หลังจัดบัญชี admin: `docker compose --env-file .env.production -f compose.production.yaml up -d frontend` ให้ผู้ดูแลตั้ง HTTPS reverse proxy ไป `127.0.0.1:8080`

ไฟล์ production เป็น standalone ใช้ `-f compose.production.yaml` เพียงไฟล์เดียว ไม่ merge กับ development compose มีสาม container: PostgreSQL, backend, static frontend ไม่มี Mailpit/dev server/source bind mounts ฐานข้อมูลใช้ named volume; backend/database ไม่ publish port ออก host

Frontend build ใช้ `VITE_API_BASE_URL=/api/v1` เพื่อให้ browser เรียกโดเมนเดียวกับเว็บ Nginx ส่ง `/api/...` ต่อไป backend และเก็บ path เดิมไว้ ส่วน `/staff/setup-password` และ Vue routes อื่นใช้ SPA fallback ไป index.html การเปลี่ยน `VITE_API_BASE_URL` ต้อง build frontend ใหม่

Frontend ผูก host port ที่ loopback โดย default และยังไม่ได้ terminate TLS เอง หากภาควิชาใช้ network/reverse proxy แบบอื่น ให้ปรับ `FRONTEND_BIND_ADDRESS`, port และการเข้าถึงตามที่ผู้ดูแลอนุญาต เปลี่ยนชื่อไฟล์ env ด้วย `BSMS_COMPOSE_ENV_FILE` และใช้ไฟล์เดียวกันใน `--env-file` เพื่อให้ interpolation และ backend env_file สอดคล้องกัน

## ไม่มี Docker

ต้องมี Python 3.11+, PostgreSQL ที่เชื่อมต่อได้ และสิทธิ์รัน process ต่อเนื่องผ่าน supervisor ของภาควิชา ให้ติดตั้ง Python packages ตอนเตรียมเครื่องหรือเตรียม wheel ที่ตรงกับ OS/architecture จากเครื่องอื่น

1. ใน `Backend`: `python3 -m venv .venv` แล้ว `.venv/bin/python -m pip install .`
2. กรอก `.env.production` โดยตั้ง `DATABASE_URL` เป็น PostgreSQL URL ของเครื่องจริง เช่นรูปแบบ `postgresql+asyncpg://USER:PASSWORD@HOST:5432/DB` ใช้ค่าจริงเฉพาะในไฟล์ส่วนตัว
3. กำหนด `BSMS_ENV_FILE` เป็น absolute path ของไฟล์นั้น แล้วใช้ `.venv/bin/python scripts/start_server.py --host 127.0.0.1 --port 8000 --migrate` ครั้งที่ต้อง apply migration ครั้งถัดไปเอา `--migrate` ออกได้
4. จัด credentials admin ก่อนเปิดให้ผู้ใช้เข้าถึง
5. รัน `.venv/bin/python scripts/check_services.py` ภายใต้ environment เดียวกับ process แอป
6. Build frontend จากเครื่องพัฒนา: ใน `Frontend` ใช้ `npm ci` แล้ว `VITE_API_BASE_URL=/api/v1 npm run build` ส่งเฉพาะ `dist` ไปเซิร์ฟเวอร์ ซึ่งไม่ต้องรัน Node.js ตลอดเวลา
7. ให้ผู้ดูแลปรับ `nginx.native.conf.example` ตามตำแหน่ง dist และ reverse proxy จริง รวม SPA fallback และ route `/api/`

การใช้ `--migrate` เปลี่ยน schema ฐานข้อมูล ต้องสำรองข้อมูลและตรวจ migration ก่อนใช้กับฐานข้อมูลเดิม คำสั่งนี้ไม่ได้ถูกรันกับฐานข้อมูลจริงระหว่างการเตรียมชุด deployment

## SMTP และทางเลือกภายหลัง

- STARTTLS: โดยทั่วไปใช้ port 587, `SMTP_USE_STARTTLS=true`, `SMTP_USE_SSL=false`
- Implicit TLS: โดยทั่วไปใช้ port 465, `SMTP_USE_SSL=true`, `SMTP_USE_STARTTLS=false`
- Mailpit/relay ภายในที่อนุญาต plaintext: ตั้ง TLS ทั้งสองค่าเป็น false ตามนโยบายผู้ดูแล ห้ามส่งรหัสผ่านผ่าน plaintext ไปอินเทอร์เน็ต
- Username/password ต้องตั้งคู่กัน; relay ที่ไม่ต้อง authentication ให้เว้นทั้งสองค่า
- ไม่ตั้ง host จะสร้างบัญชีได้ แต่ `email_sent=false`; Admin ใช้ resend เมื่อพร้อม

`send_invitation_email(recipient, staff_identifier, activation_link)` เป็นขอบเขตเปลี่ยน transport ส่วน `invitations.py` รับผิดชอบ token/DB/audit ถ้าเปิดได้เฉพาะ HTTPS 443 ให้เลือก Email API ที่ภาควิชาอนุญาต แล้วเพิ่ม adapter ภายในขอบเขตนี้ งานรอบนี้ยังไม่ได้ผูกผู้ให้บริการ HTTPS หรือสมัครบัญชีภายนอก

ไม่มี automatic SMTP retry เพื่อหลีกเลี่ยงอีเมลซ้ำเมื่อไม่แน่ใจว่าผู้ให้บริการรับไปแล้ว การ resend จาก Admin สร้าง invitation ใหม่และยกเลิก token เก่า `email_sent=true` หมายถึง SMTP รับฝากส่ง ไม่ใช่หลักฐานว่าถึง inbox

## R2, timeout และ RAM

R2 default: connect timeout 5 วินาที, read timeout 15 วินาที, standard retry รวมไม่เกิน 2 attempts (ครั้งแรก + retry 1 ครั้ง) ปรับด้วย `R2_CONNECT_TIMEOUT_SECONDS`, `R2_READ_TIMEOUT_SECONDS`, `R2_TOTAL_MAX_ATTEMPTS` ค่าพวกนี้ไม่ได้เป็น deadline รวมของ request; หลายรูป, retry, network phases และ cleanup ทำให้เวลารวมมากกว่า timeout แต่ละค่าได้

รูป default ไม่เกิน 5 MiB/ไฟล์, 5 ไฟล์/คำร้อง, 8 ล้านพิกเซล และแปลงภาพพร้อมกัน 1 งานต่อ worker เพดาน pixel ลด decoded buffer แบบ RGBA เหลือประมาณ 32 MB ต่อภาพ แต่ Pillow มีสำเนาและ buffer เพิ่ม จึงไม่ใช่เพดาน RAM รวมของ process

AnyIO CapacityLimiter คุมช่วงอ่าน bytes/decode/encode; งานหนักอยู่ใน thread เพื่อให้ event loop รับ HTTP อื่นต่อได้ หาก request ถูกยกเลิก ระบบรอ thread ที่เริ่มไว้ให้จบก่อนคืน token เพราะ Python หยุด thread กลางงานไม่ได้ รูป compressed ที่เตรียมแล้ว, multipart temporary files, DB pool และ request ที่รอใช้ RAM/disk เพิ่ม จึงยังต้องวัดบนเซิร์ฟเวอร์จริง

Uvicorn เริ่มหนึ่ง workerและจำกัด concurrency 16 (`--limit-concurrency` ปรับได้) เมื่อเต็มจะตอบ 503 แทนการรับงานเพิ่มไม่จำกัด หากเพิ่ม workers เพดาน image concurrency จะเพิ่มตามจำนวน process ด้วย Nginx จำกัด body รวม 30 MiB ให้สอดคล้องกับ 5 รูป × 5 MiB และ multipart overhead หากเปลี่ยน file limits ต้องปรับ proxy ด้วย

Flow upload ยังเป็น browser → backend ตรวจ/แปลงรูป → R2 → DB เก็บ metadata และเก็บกวาด object เมื่อ transaction ล้มเหลว การใช้ R2 ลดพื้นที่เก็บถาวรในเซิร์ฟเวอร์ แต่ไม่ได้ย้ายงานแปลงรูปออกไป

## ติดตามคำร้องเมื่อรูปไม่พร้อม

Cleaning tracking ใช้ optional storage และอ่านคำร้อง/ตรวจอีเมลก่อน รูปแบบ response เพิ่ม `completion_photos_status`:

- `none`: ไม่มีรูปหลังทำงาน `completion_photos=[]`
- `available`: สร้าง signed URLs ได้และคืนรายการรูป
- `unavailable`: มี metadata รูป แต่ไม่มี storage config หรือสร้าง signed URL ไม่ได้ คืนข้อมูลคำร้องพร้อมรายการรูปว่าง Frontend แสดงข้อความให้รีเฟรชภายหลัง

คำว่า available หมายถึงสร้าง URL ได้ ไม่ได้ตรวจ network ไป R2; signed URL สร้างได้ในเครื่อง จึงยังเป็นไปได้ว่า browser ดาวน์โหลดไม่สำเร็จเพราะ network/token ที่หมดอายุ หากรหัสไม่พบหรืออีเมลไม่ตรงยังตอบ 404 แบบเดียวกัน ไม่มีการลบรูปหรือเปลี่ยนสถานะงานเพราะ storage ไม่พร้อม

## ตรวจจากเครื่องภาควิชาก่อนเปิดใช้งาน

`check_services.py` เชื่อมต่อ SMTP, TLS และ login เท่านั้น ไม่ส่งอีเมล ส่วน R2 ใช้ HEAD bucket ไม่ upload/delete และพิมพ์เพียงประเภทข้อผิดพลาด ไม่พิมพ์ credentials หาก token จำกัดสิทธิ์จน HEAD ใช้ไม่ได้ ต้องตรวจสิทธิ์ object operation เพิ่ม

`GET /health` เป็น liveness: บอกว่าแอปตอบ HTTP ได้ ไม่ได้บอกว่า DB, SMTP หรือ R2 พร้อม

ต้องยืนยันกับผู้ดูแลเรื่อง outbound DNS/HTTPS 443 ไป R2, SMTP port ที่เลือก, domain allowlist/proxy/CA, RAM/CPU/disk, Python/Docker, process supervision และการเข้าถึง PostgreSQL Browser ผู้ใช้ต้องเข้าถึง R2 เพื่อโหลดรูปโดยตรงด้วย

ก่อนเปิดให้ผู้ใช้จริง ให้ส่ง invitation แล้วตรวจ inbox/ลิงก์ตั้งรหัสผ่าน, อัปโหลด–อ่าน–ลบไฟล์ทดสอบใน prefix แยก, ตรวจ rollback และวัด RAM ขณะส่งคำร้องพร้อมกัน การตรวจการเชื่อมต่อจากเครื่องพัฒนาไม่รับรองนโยบาย network ของเครื่องภาควิชา

## รีเซ็ตรหัสผ่านด้วยตนเอง

Staff ขอลิงก์ได้ที่ `POST /api/v1/auth/password-reset-requests` ระบบตอบ 202 ด้วยข้อความเดียวกันทุกกรณี แล้วส่งเมลหลังตอบ (background task) จึงไม่ถือ lock ฐานข้อมูลระหว่างคุยกับ SMTP ลิงก์ชี้ไป `STAFF_PASSWORD_RESET_URL` (ค่าว่าง = `PUBLIC_BASE_URL` + `/staff/reset-password`) อายุตาม `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES`

การจำกัดคำขอมีสองชั้น: ต่อบัญชีด้วย `PASSWORD_RESET_COOLDOWN_SECONDS` (เก็บใน DB) และต่อ IP ด้วย `PASSWORD_RESET_IP_LIMIT` / `PASSWORD_RESET_IP_WINDOW_SECONDS` (เก็บใน memory ของ worker เดียว) ชั้น IP ต้องให้ Uvicorn เชื่อ `X-Forwarded-For` จาก proxy ผ่าน `FORWARDED_ALLOW_IPS` Compose ตั้ง `*` เพราะ backend ไม่ได้ publish port ออก host ถ้ารันแบบไม่มี Docker ให้ตั้งเป็น IP ของ reverse proxy เท่านั้น ไม่เช่นนั้นผู้ใช้ทุกคนจะถูกนับเป็น IP เดียวกัน หรือผู้โจมตีปลอม header ได้

ยืนยันรหัสใหม่สำเร็จแล้วทุก JWT ที่ออกก่อนหน้าจะใช้ไม่ได้ (เทียบ `iat` กับ `staff.password_changed_at`) Migration `20261006_0016` เติมค่า `password_changed_at` ให้บัญชีเดิม: บัญชีที่ activate แล้วใช้เวลาที่ใช้ invitation, บัญชีที่ไม่มี invitation เลย (เช่น admin seed) ใช้ `created_at`, บัญชีที่ยังไม่ activate คงเป็น NULL และขอรีเซ็ตไม่ได้ (ต้องใช้ invitation)
