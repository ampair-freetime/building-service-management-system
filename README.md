# คู่มือติดตั้งระบบ CS Building Care

ระบบเว็บแจ้งซ่อม แจ้งทำความสะอาด และของหาย/ของที่พบ ภายในอาคาร

- **ผู้ใช้ทั่วไป** สแกน QR ที่ติดในห้อง แล้วแจ้งเรื่องพร้อมรูปได้เลย ไม่ต้องสมัครสมาชิก
- **เจ้าหน้าที่** (แม่บ้าน ช่าง ธุรการ) รับงานและปิดงานผ่านเว็บ
- **ผู้ดูแลระบบ (admin)** เพิ่มเจ้าหน้าที่ เพิ่มห้อง และสร้าง QR

คู่มือนี้เขียนให้ทำตามได้โดยไม่ต้องเขียนโปรแกรม ทุกอย่างทำผ่านคำสั่งเดียวคือ `./deploy/bcare.sh`

---

## 📋 ส่วนที่ 1 — เตรียมของก่อนเริ่ม

ต้องมี:

- เครื่องเซิร์ฟเวอร์ Linux 64-bit (แนะนำ Ubuntu 22.04 / 24.04), 2 CPU, RAM 4 GB, พื้นที่ว่าง 20 GB และสิทธิ์ `sudo`
- ชื่อโดเมน เช่น `care.cs.science.cmu.ac.th` — **ใช้ทำลิงก์ใน QR เปลี่ยนภายหลังไม่ได้ถ้าพิมพ์ QR ไปแล้ว**
- ที่เก็บรูปภาพ Cloudflare R2 (ทำตามข้อ 1.1)
- บัญชีอีเมลสำหรับส่งเมลอัตโนมัติ (ทำตามข้อ 1.2)
- อีเมลและชื่อของผู้ดูแลระบบคนแรก

> 🔒 ค่าที่ได้จากข้อ 1.1 และ 1.2 เป็นความลับ ถ้าจดไว้ใน Notepad ให้ลบไฟล์ทิ้งหลังติดตั้งเสร็จ

### 1.1 สร้างที่เก็บรูปภาพ Cloudflare R2 (ฟรี 10 GB)

ผลลัพธ์ที่ต้องได้ 4 ค่า: **Account ID**, **Bucket Name**, **Access Key ID**, **Secret Access Key**

1. **สมัคร / เข้าสู่ระบบ Cloudflare** ที่ https://dash.cloudflare.com/sign-up (มีบัญชีแล้วเข้าที่ https://dash.cloudflare.com)
2. **เปิดใช้ R2:** เมนูซ้ายเลือก **R2 Object Storage** (หรือเข้า https://dash.cloudflare.com/?to=/:account/r2/overview)
   - ครั้งแรกระบบจะให้กด **Purchase R2 Plan / Add R2** และผูกบัตรเครดิตหรือ PayPal — ใช้ไม่เกิน 10 GB **ไม่เสียเงิน**
3. **จด Account ID:** อยู่ด้านขวาของหน้า R2 Overview ในกล่อง **Account Details** → กดไอคอนคัดลอกข้าง **Account ID** (ตัวอักษร 32 ตัว)
4. **สร้าง bucket:** กด **Create bucket**
   - **Bucket name:** ตั้งชื่อตัวพิมพ์เล็ก เช่น `cs-building-care` → นี่คือ **Bucket Name**
   - **Location:** Automatic → กด **Create bucket**
   - ⚠️ **ไม่ต้อง**เปิด Public access หรือ r2.dev subdomain (ระบบเปิดรูปให้ผู้ใช้เองอย่างปลอดภัย)
5. **สร้างกุญแจสำหรับระบบ:** กลับไปหน้า R2 Overview → ด้านขวากด **Manage API tokens** (ในกล่อง Account Details) → **Create Account API token**
   - **Token name:** `cs-building-care`
   - **Permissions:** เลือก **Object Read & Write**
   - **Specify bucket(s):** เลือก **Apply to specific buckets only** → เลือก bucket จากข้อ 4
   - **TTL:** Forever → กด **Create Account API Token**
6. **คัดลอก 2 ค่าจากหน้าผลลัพธ์ทันที** (หน้านี้แสดงครั้งเดียว ปิดแล้วดูใหม่ไม่ได้):
   - **Access Key ID** และ **Secret Access Key** ในหัวข้อ "Use the following credentials for S3 clients"
   - ❌ ไม่ใช่ค่า **Token value** และไม่ต้องใช้ค่า Endpoint (ระบบสร้างจาก Account ID เอง)

ถ้าหน้าเว็บ Cloudflare หน้าตาเปลี่ยนไป ดูคู่มือทางการ: [เริ่มใช้ R2](https://developers.cloudflare.com/r2/get-started/) · [สร้าง bucket](https://developers.cloudflare.com/r2/buckets/create-buckets/) · [สร้าง API token](https://developers.cloudflare.com/r2/api/tokens/)

### 1.2 เตรียมบัญชีอีเมลสำหรับส่งเมล (Gmail)

ผลลัพธ์ที่ต้องได้: **อีเมล Gmail** และ **App Password 16 ตัว**

1. **ใช้บัญชี Gmail แยกสำหรับระบบ** (แนะนำ) เช่น `cs.buildingcare@gmail.com` สมัครที่ https://accounts.google.com/signup
2. **เปิดการยืนยันตัวตน 2 ขั้นตอน (2-Step Verification):** เข้า https://myaccount.google.com/signinoptions/twosv → กด **Turn on** แล้วทำตามขั้นตอน (ผูกเบอร์มือถือ)
   — ต้องเปิดข้อนี้ก่อน ไม่อย่างนั้นจะไม่เห็นเมนู App passwords
3. **สร้าง App Password:** เข้า https://myaccount.google.com/apppasswords
   - **App name:** พิมพ์ `CS Building Care` → กด **Create**
   - ระบบแสดงรหัส **16 ตัว** (เช่น `abcd efgh ijkl mnop`) → คัดลอกเก็บไว้ (แสดงครั้งเดียว) ตอนกรอกให้พิมพ์ติดกัน **ไม่มีช่องว่าง**
   - ❌ ห้ามใช้รหัสผ่าน Gmail ปกติ ระบบจะ login ไม่ผ่าน

ค่าที่จะใช้กรอกในขั้นที่ 4:

| ตัวแปร | ค่า |
| --- | --- |
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` (มีให้แล้ว ไม่ต้องแก้) |
| `SMTP_USERNAME` | อีเมล Gmail เต็ม เช่น `cs.buildingcare@gmail.com` |
| `SMTP_PASSWORD` | App Password 16 ตัว (ไม่มีช่องว่าง) |
| `MAIL_FROM` | `"CS Building Care <cs.buildingcare@gmail.com>"` (อีเมลเดียวกับ Username) |

- Gmail ส่งได้ประมาณ **500 ฉบับต่อวัน** พอสำหรับระบบนี้
- ถ้าใช้อีเมลของมหาวิทยาลัย (`@cmu.ac.th`) ผู้ดูแลอาจปิดเมนู App passwords ไว้ — ใช้ Gmail แยกจะง่ายกว่า
- ผู้ให้บริการอื่นต้องรองรับ **STARTTLS พอร์ต 587** · คู่มือ Google: [App passwords](https://support.google.com/accounts/answer/185833)

---

## 🚀 ส่วนที่ 2 — ติดตั้ง (ทำตามทีละขั้น)

คำสั่งทั้งหมดพิมพ์ในหน้าต่าง Terminal ของเครื่องเซิร์ฟเวอร์

### ขั้นที่ 1 — ติดตั้งโปรแกรมที่จำเป็น (ทำครั้งเดียว ถ้ามีแล้วข้ามได้)

```bash
sudo apt update && sudo apt install -y git
curl -fsSL https://get.docker.com | sudo sh && sudo usermod -aG docker $USER
```

เสร็จแล้ว **ออกจากเครื่อง (`exit`) แล้วเข้าเครื่องใหม่อีกครั้ง** ไม่อย่างนั้นขั้นต่อไปจะใช้คำสั่ง `docker` ไม่ได้

### ขั้นที่ 2 — ดาวน์โหลดระบบมาไว้ในเครื่อง

```bash
sudo mkdir -p /srv/building-care && sudo chown $USER /srv/building-care
git clone https://github.com/ampair-freetime/building-service-management-system.git /srv/building-care
cd /srv/building-care
```

> ทุกครั้งที่เข้าเครื่องมาใหม่ ให้พิมพ์ `cd /srv/building-care` ก่อนใช้คำสั่งอื่นเสมอ

### ขั้นที่ 3 — สร้างไฟล์ตั้งค่า

```bash
./deploy/bcare.sh install
```

ระบบจะสร้างไฟล์ชื่อ `.env` แล้ว **หยุด** พร้อมแสดงรายการบรรทัดที่ยังต้องกรอก — **ถูกต้องแล้ว** ไปขั้นที่ 4 ได้เลย

### ขั้นที่ 4 — กรอกข้อมูลในไฟล์ตั้งค่า

```bash
nano .env
```

- เลื่อนด้วยปุ่มลูกศร หรือกด **Ctrl+W** แล้วพิมพ์ `REPLACE_` เพื่อค้นหา
- **ลบค่าเดิมทั้งหมดหลังเครื่องหมาย `=`** แล้วพิมพ์ค่าจริงแทน (อย่าลบแค่คำว่า `REPLACE_`)
- รหัสลับอื่น ๆ ระบบสุ่มใส่ให้แล้ว ไม่ต้องแก้

| บรรทัดเดิม | แก้เป็น (ตัวอย่าง) |
| --- | --- |
| `PUBLIC_BASE_URL=https://REPLACE_DOMAIN.example.org` | `PUBLIC_BASE_URL=https://care.cs.science.cmu.ac.th` |
| `BACKEND_CORS_ORIGINS=["https://REPLACE_DOMAIN.example.org"]` | `BACKEND_CORS_ORIGINS=["https://care.cs.science.cmu.ac.th"]` |
| `R2_ACCOUNT_ID=REPLACE_R2_ACCOUNT_ID` | `R2_ACCOUNT_ID=<Account ID จาก Cloudflare>` |
| `R2_ACCESS_KEY_ID=REPLACE_...` / `R2_SECRET_ACCESS_KEY=REPLACE_...` / `R2_BUCKET_NAME=REPLACE_...` | ค่าจาก Cloudflare R2 ตามชื่อ |
| `SMTP_HOST=REPLACE_SMTP_HOST` | `SMTP_HOST=smtp.gmail.com` |
| `SMTP_USERNAME=REPLACE_SMTP_USERNAME` | `SMTP_USERNAME=building.care@gmail.com` |
| `SMTP_PASSWORD=REPLACE_SMTP_PASSWORD` | `SMTP_PASSWORD=<App Password 16 ตัว>` |
| `MAIL_FROM="CS Building Care <REPLACE_SENDER@example.org>"` | `MAIL_FROM="CS Building Care <building.care@gmail.com>"` |

**ทาง B เท่านั้น (มี proxy):** แก้เพิ่มอีก 2 บรรทัด

| บรรทัดเดิม | แก้เป็น (ตัวอย่าง) | ทำไม |
| --- | --- | --- |
| `FRONTEND_BIND_ADDRESS=127.0.0.1` | `FRONTEND_BIND_ADDRESS=10.10.5.20` (IP ภายในของเครื่องนี้) | ให้ proxy เข้ามาที่เครื่องเราได้ |
| `EDGE_PROXY_CIDR=` | `EDGE_PROXY_CIDR=10.10.1.5/32` (IP ของ proxy ต่อท้ายด้วย `/32`) | รับคำขอเฉพาะจาก proxy (เครื่องอื่นจะได้ 403) และให้ระบบเห็น IP จริงของผู้ใช้ |

บันทึกและออก: กด **Ctrl+O** → **Enter** → **Ctrl+X**

### ขั้นที่ 5 — ติดตั้งระบบ

```bash
./deploy/bcare.sh install
```

- ครั้งแรกใช้เวลา **5–10 นาที** หน้าจอจะขึ้นข้อความยาว ๆ ให้รอจนจบ
- ช่วงท้ายจะถาม **อีเมล ชื่อ และรหัสผ่าน** ของผู้ดูแลระบบคนแรก
  - รหัสผ่านยาว 8 ตัวขึ้นไป ต้องมี **ตัวพิมพ์ใหญ่ ตัวพิมพ์เล็ก ตัวเลข และสัญลักษณ์** อย่างละ 1 ตัว เช่น `Care@2026`
  - ตอนพิมพ์รหัสผ่าน **ตัวอักษรจะไม่ขึ้นบนจอ** เป็นเรื่องปกติ พิมพ์ให้ครบแล้วกด Enter ระบบจะให้พิมพ์ซ้ำอีกครั้ง
- ระบบตั้งการสำรองข้อมูลอัตโนมัติทุกวัน 02:00 น. ให้ด้วย

**ติดตั้งสำเร็จ** เมื่อท้ายจอมี 3 บรรทัดนี้:

```text
SMTP: CONNECTIVITY_OK (no email sent)
R2: BUCKET_ACCESS_OK (upload/delete not tested)
{"status":"ok"}
```

ถ้ามีคำว่า `FAILED` ให้ดู [ส่วนที่ 4](#-ส่วนที่-4--แก้ปัญหาเบื้องต้น) แก้ไฟล์ `.env` แล้วรันขั้นที่ 5 ซ้ำได้เลย (ส่วนที่ทำเสร็จแล้วระบบจะข้ามให้)

### ขั้นที่ 6 — เปิดใช้งาน HTTPS (เลือกทางเดียว)

**ทาง A — ไม่มี proxy:** เครื่องเราทำ HTTPS เอง (ต้องให้ไอทีชี้โดเมนมาที่ IP เครื่องนี้ และเปิดพอร์ต 80 กับ 443 จากอินเทอร์เน็ต)

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
./deploy/bcare.sh https care.cs.science.cmu.ac.th
```

ใส่อีเมลและกดยอมรับเงื่อนไขตามที่ระบบถาม

**ทาง B — มี proxy อยู่แล้ว:** ไม่ต้องรันคำสั่งใด ส่งข้อความนี้ให้ผู้ดูแล proxy

> ขอตั้ง Reverse Proxy ให้โดเมน `care.cs.science.cmu.ac.th` ส่งต่อไปที่ `http://<IP ภายในเครื่อง>:8080`
> - ส่ง header `X-Forwarded-Proto: https` และ `X-Forwarded-For` (IP จริงของผู้ใช้)
> - รับไฟล์อัปโหลดได้ 60 MB (`client_max_body_size 60m`) และ timeout 120 วินาที
> - ไม่ cache เส้นทาง `/api/`

ไม่ต้องขอให้กั้น firewall พอร์ต 8080 เพราะระบบปฏิเสธคำขอที่ไม่ได้มาจาก IP ใน `EDGE_PROXY_CIDR` ให้เอง

### ขั้นที่ 7 — ตรวจว่าใช้งานได้จริง

1. เปิดเบราว์เซอร์ไปที่ `https://<โดเมน>/health` ต้องเห็น `{"status":"ok"}`
2. เปิด `https://<โดเมน>/staff-login` แล้วเข้าสู่ระบบด้วยบัญชี admin จากขั้นที่ 5
3. เพิ่มห้อง → กด Generate QR → ใช้มือถือ **ปิด Wi-Fi ใช้ 4G** สแกน QR แล้วลองแจ้งเรื่องพร้อมรูป
4. เชิญเจ้าหน้าที่ 1 คน → ต้องได้อีเมลคำเชิญ (ดูในกล่อง Spam ด้วย)

ผ่านครบ 4 ข้อ = ติดตั้งเสร็จ 🎉

---

## 🛠️ ส่วนที่ 3 — ดูแลระบบประจำวัน

พิมพ์ `cd /srv/building-care` ก่อนทุกครั้ง

| อยากทำอะไร | พิมพ์คำสั่ง |
| --- | --- |
| เช็คว่าระบบยังทำงานดีไหม | `./deploy/bcare.sh status` |
| ดูข้อผิดพลาดล่าสุด (กด **Ctrl+C** เพื่อออก) | `./deploy/bcare.sh logs backend` |
| สำรองข้อมูลทันที (ปกติระบบทำเองทุกวัน 02:00 น.) | `./deploy/bcare.sh backup` |
| กู้ข้อมูลคืนจากไฟล์สำรอง | `./deploy/bcare.sh restore /srv/backups/<ชื่อไฟล์>.dump` |
| อัปเดตระบบเป็นเวอร์ชันใหม่ (สำรองข้อมูลให้ก่อนอัตโนมัติ) | `./deploy/bcare.sh update` |
| แก้ไฟล์ `.env` แล้วอยากให้ค่าใหม่มีผล | `./deploy/bcare.sh install` |

- ไฟล์สำรองอยู่ที่ `/srv/backups` เก็บย้อนหลัง 14 วัน — **ควรคัดลอกออกไปเก็บนอกเครื่องเป็นประจำ** (รูปภาพเก็บอยู่ใน Cloudflare R2 ไม่ได้อยู่ในไฟล์สำรอง)
- ⚠️ **ห้ามพิมพ์ `docker compose down -v`** คำสั่งนี้ลบข้อมูลทั้งหมดของระบบ

### สิ่งที่ผู้ดูแลระบบทำได้ผ่านหน้าเว็บ

| งาน | วิธี |
| --- | --- |
| เพิ่มเจ้าหน้าที่ | หน้า admin → บัญชีเจ้าหน้าที่ → ใส่อีเมล ชื่อ หน้าที่ → ระบบส่งลิงก์ตั้งรหัสผ่านทางอีเมล (ใช้ได้ครั้งเดียว ภายใน 24 ชม.) |
| เจ้าหน้าที่ไม่ได้รับอีเมลเชิญ | กด "ส่งคำเชิญอีกครั้ง" หรือพิมพ์บนเซิร์ฟเวอร์ `docker compose exec backend python scripts/invitation_link.py --email <อีเมล>` แล้วส่งลิงก์ที่ได้ให้เจ้าหน้าที่เอง |
| ระงับ / เปิดบัญชีเจ้าหน้าที่ | หน้า admin → บัญชีเจ้าหน้าที่ |
| เปลี่ยนหน้าที่ของเจ้าหน้าที่ | ลบบัญชีแล้วเชิญใหม่ด้วยอีเมลเดิม (ประวัติงานยังอยู่) |
| เพิ่มห้อง + QR | หน้า admin → ห้อง/QR → เพิ่ม → Generate QR → ดาวน์โหลดไปพิมพ์ |
| ปิดห้องชั่วคราว | ปิดใช้งานห้อง (สแกน QR ห้องนั้นไม่ได้ แต่งานเดิมยังอยู่) |
| ลืมรหัสผ่าน | กด "ลืมรหัสผ่าน" ที่หน้าเข้าสู่ระบบ (ลิงก์ใช้ได้ 30 นาที) |

ใส่รหัสผ่านผิด 5 ครั้งใน 15 นาที จะถูกพักการเข้าสู่ระบบ 15 นาที

---

## 🆘 ส่วนที่ 4 — แก้ปัญหาเบื้องต้น

ดูข้อผิดพลาดก่อนเสมอด้วย `./deploy/bcare.sh logs backend`

| อาการ | สาเหตุ / วิธีแก้ |
| --- | --- |
| ขั้นที่ 3–5 หยุดพร้อมรายการ `REPLACE_` | ยังกรอก `.env` ไม่ครบ → ทำขั้นที่ 4 ใหม่ |
| `Permission denied` ตอนใช้ `docker` หรือ `user นี้สั่ง docker ไม่ได้` | ยังไม่ได้ออกแล้วเข้าเครื่องใหม่หลังขั้นที่ 1 → `exit` แล้วเข้าเครื่องใหม่ |
| `Permission denied` ตอน `git clone` | ลืมบรรทัด `sudo mkdir ...` ในขั้นที่ 2 |
| `R2: FAILED` | `AccessDenied` = key ไม่มีสิทธิ์, `NoSuchBucket` = ชื่อ bucket ผิด, `SSLError` = Account ID ผิดหรือเครื่องออกอินเทอร์เน็ตไม่ได้ |
| `SMTP: FAILED` | Username / App Password ผิด หรือพอร์ต 587 ถูกปิด → ระหว่างรอแก้ ใช้ `invitation_link.py` (ส่วนที่ 3) |
| เปิดเว็บแล้วขึ้น `502` หรือ `504` | ระบบยังเปิดไม่เสร็จหรือหยุดทำงาน → `./deploy/bcare.sh status` (ทาง B: เช็คว่าตั้ง `FRONTEND_BIND_ADDRESS` แล้ว) |
| ทาง B: เปิดเว็บแล้วขึ้น `403 Forbidden` | `EDGE_PROXY_CIDR` ไม่ตรงกับ IP ที่ proxy ใช้ต่อเข้ามา → พิมพ์ `./deploy/bcare.sh logs frontend` ดูตัวเลข IP ต้นบรรทัดที่ลงท้ายด้วย `403` นั่นคือ IP ที่ proxy ใช้จริง แก้ `EDGE_PROXY_CIDR` ใน `.env` แล้ว `./deploy/bcare.sh install` (ถ้า IP ขึ้นต้นด้วย `172.` แปลว่า proxy อยู่บนเครื่องเดียวกัน **ห้ามใส่ IP นั้น** ให้ใช้ทาง A แทน) |
| `install` หยุดพร้อมข้อความเรื่อง `EDGE_PROXY_CIDR` | ตั้ง `FRONTEND_BIND_ADDRESS` แล้วแต่ยังไม่ใส่ IP ของ proxy → ทำตารางทาง B ในขั้นที่ 4 |
| อัปโหลดรูปแล้วขึ้น `413` | proxy หรือ nginx จำกัดขนาดไฟล์ → ต้องตั้ง `client_max_body_size 60m` |
| `Pool overlaps` หรือ `port is already allocated` | ชนกับโปรแกรมอื่นในเครื่อง → เปลี่ยน `APP_SUBNET` หรือ `FRONTEND_PORT` ใน `.env` |
| สร้าง admin ไม่ผ่าน ขึ้น `Invalid ...` | รหัสผ่านไม่ตรงกฎ หรืออีเมลไม่ใช่โดเมนจริง |
| เข้าสู่ระบบแล้วขึ้น `429` | ใส่รหัสผิดหลายครั้ง → รอ 15 นาที |

---

## 💻 ส่วนที่ 5 — สำหรับนักพัฒนา

```bash
docker compose up --build        # ทดลองบนเครื่องตัวเอง http://localhost:5173 (admin@example.com / Admin@1234) ห้ามใช้บนเซิร์ฟเวอร์จริง
cd Backend && uv run --extra dev pytest
```

ค่าตั้งทั้งหมดพร้อมคำอธิบายอยู่ใน [`.env.production.example`](.env.production.example)
ติดตั้งแบบไม่มีคนพิมพ์ตอบ ดู [INITIAL_ADMIN.md](Backend/scripts/INITIAL_ADMIN.md)
