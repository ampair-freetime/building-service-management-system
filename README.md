# CS Building Care — Deployment Guide

ระบบแจ้งซ่อม แจ้งทำความสะอาด และของหาย/ของที่พบ (FastAPI + PostgreSQL + Vue 3)
คู่มือนี้สำหรับผู้ที่ได้รับ repository จาก GitHub และต้องการติดตั้งบนเซิร์ฟเวอร์จริง

```text
ผู้ใช้ (มือถือ/คอม)
   │ HTTPS 443
   ▼
Nginx บนเครื่อง (TLS, certbot)      deploy/nginx/building-care.conf
   │ http://127.0.0.1:8080
   ▼
frontend container (Nginx)         เสิร์ฟหน้าเว็บ + ส่ง /api/ ต่อ
   │ http://backend:8000
   ▼
backend container (FastAPI)  ──►  Cloudflare R2 (รูปภาพ), SMTP (อีเมล)
   │
   ▼
database container (PostgreSQL)    เก็บข้อมูลใน Docker volume
```

## 1. สิ่งที่ต้องเตรียม

| รายการ | รายละเอียด |
| --- | --- |
| เซิร์ฟเวอร์ | Ubuntu 22.04/24.04, 2 vCPU, RAM 4 GB, ดิสก์ 40 GB |
| Network | เปิด inbound 80/443 จากอินเทอร์เน็ต (guest สแกน QR ผ่าน 4G), outbound 443 และ 587 |
| โดเมน | DNS ชี้มาที่ IP ของเครื่องแล้ว เช่น `care.example.ac.th` |
| Cloudflare R2 | bucket แบบ private + API token สิทธิ์ **Object Read & Write** เฉพาะ bucket นั้น |
| SMTP | เช่น Gmail: เปิด 2-Step Verification → App passwords → ได้รหัส 16 ตัว |

ติดตั้งโปรแกรมบนเครื่อง:

```bash
curl -fsSL https://get.docker.com | sudo sh    # Docker Engine + Compose plugin
sudo usermod -aG docker $USER                   # logout/login ใหม่หลังคำสั่งนี้
sudo apt install -y git nginx certbot python3-certbot-nginx
sudo ufw allow OpenSSH && sudo ufw allow 'Nginx Full' && sudo ufw enable
docker compose version                          # ต้อง ≥ 2.24
```

## 2. ดาวน์โหลดโค้ด

```bash
sudo mkdir -p /srv/building-care && sudo chown $USER /srv/building-care
git clone https://github.com/ampair-freetime/building-service-management-system.git /srv/building-care
cd /srv/building-care
```

คำสั่งทุกคำสั่งหลังจากนี้ให้รันในโฟลเดอร์ `/srv/building-care`

## 3. ตั้งค่า `.env`

```bash
cp .env.production.example .env
chmod 600 .env
openssl rand -hex 32    # รัน 3 ครั้ง ได้ 3 ค่าสำหรับ POSTGRES_PASSWORD, JWT_SECRET_KEY, IMAGE_URL_SECRET
nano .env
```

| ตัวแปร | ใส่อะไร |
| --- | --- |
| `PUBLIC_BASE_URL` | `https://<โดเมน>` — ค่านี้ถูกฝังใน QR **ต้องถูกต้องก่อนพิมพ์ป้าย QR** |
| `BACKEND_CORS_ORIGINS` | `["https://<โดเมน>"]` |
| `POSTGRES_PASSWORD`, `JWT_SECRET_KEY`, `IMAGE_URL_SECRET` | ค่าสุ่มจาก `openssl` คนละค่า |
| `SMTP_*`, `MAIL_FROM` | ค่าจากผู้ให้บริการอีเมล (port 465 ให้ตั้ง `SMTP_USE_SSL=true`, `SMTP_USE_STARTTLS=false`) |
| `R2_*` | ค่าจาก Cloudflare |

> [!IMPORTANT]
> ห้ามเปลี่ยน secret ทั้ง 3 ค่าหลังเปิดใช้งาน: เปลี่ยน `JWT_SECRET_KEY` = ทุกคนถูก logout,
> เปลี่ยน `IMAGE_URL_SECRET` = ลิงก์รูปเดิมใช้ไม่ได้, เปลี่ยน `POSTGRES_PASSWORD` = backend ต่อฐานข้อมูลไม่ได้
> เก็บสำเนา `.env` ไว้ในที่ปลอดภัยนอกเครื่อง

ไฟล์ `.env` มี `COMPOSE_FILE=compose.production.yaml` อยู่แล้ว ดังนั้นคำสั่ง `docker compose` บนเครื่องนี้
จะใช้ชุด production เสมอ (`compose.yaml` เป็นชุด development ห้ามใช้บนเซิร์ฟเวอร์)

## 4. รันระบบ

```bash
docker compose config --quiet     # ตรวจ config ถ้าขาดค่าที่จำเป็นจะบอกชื่อตัวแปร
docker compose up -d --build      # build และรัน (migration ฐานข้อมูลรันอัตโนมัติ)
docker compose ps                 # database และ backend ต้องเป็น (healthy)
```

ถ้า backend ไม่ healthy ดูสาเหตุด้วย `docker compose logs backend` (ดูหัวข้อ 10)

## 5. สร้าง admin คนแรก

ระบบ production ไม่มีบัญชีตั้งต้น ให้สร้าง admin คนแรกด้วยคำสั่ง:

```bash
docker compose exec backend python scripts/bootstrap_admin.py --email admin@your-org.ac.th --name "ชื่อ นามสกุล"
```

- ระบบจะส่งลิงก์ตั้งรหัสผ่านไปที่อีเมลนั้น (ใช้ได้ครั้งเดียว อายุ 24 ชั่วโมง)
- ถ้าส่งอีเมลไม่ได้ ลิงก์จะแสดงบนหน้าจอแทน ให้เปิดลิงก์นั้นเอง (หลังทำข้อ 7 แล้ว)
- ลิงก์หมดอายุก่อนใช้: รันคำสั่งเดิมด้วยอีเมลเดิมอีกครั้ง
- คำสั่งนี้ใช้ได้จนกว่าจะมี admin ที่ตั้งรหัสผ่านแล้ว จากนั้นให้เพิ่มเจ้าหน้าที่ผ่านหน้า admin

## 6. ตรวจการเชื่อมต่อ SMTP และ R2

```bash
docker compose exec backend python scripts/check_services.py
```

ต้องได้ `SMTP: CONNECTIVITY_OK` และ `R2: BUCKET_ACCESS_OK` ถ้าไม่ผ่านให้แก้ค่าใน `.env` แล้ว
`docker compose up -d` ใหม่

## 7. เปิด HTTPS ด้วย Nginx บนเครื่อง

```bash
sudo cp deploy/nginx/building-care.conf /etc/nginx/sites-available/building-care.conf
sudo sed -i 's/care.example.ac.th/<โดเมน>/' /etc/nginx/sites-available/building-care.conf
sudo ln -s /etc/nginx/sites-available/building-care.conf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d <โดเมน>     # เลือก redirect HTTP → HTTPS
```

certbot ต่ออายุใบรับรองให้อัตโนมัติ ตรวจได้ด้วย `sudo certbot renew --dry-run`

## 8. ตรวจสอบและเริ่มใช้งาน

```bash
curl -I https://<โดเมน>/                                              # 200
curl https://<โดเมน>/api/v1/guest/cleaning-requests/locations          # ได้ JSON
```

1. เปิด `https://<โดเมน>/staff-login` แล้ว login ด้วย admin จากข้อ 5
2. เพิ่มสถานที่ (ชั้น/ห้อง) แล้วกด Generate QR → ดาวน์โหลดไปพิมพ์ติดป้าย
3. เพิ่มเจ้าหน้าที่ (ช่าง, แม่บ้าน, ธุรการ) ระบบจะส่งลิงก์ตั้งรหัสผ่านทางอีเมล
4. ลองสแกน QR ด้วยมือถือผ่าน 4G แล้วส่งเรื่องทดสอบ 1 รายการพร้อมรูป

## 9. Backup ฐานข้อมูล

รูปภาพอยู่ใน R2 ส่วนข้อมูลอื่นทั้งหมดอยู่ใน PostgreSQL ให้ backup ทุกวัน:

```bash
sudo mkdir -p /srv/backups && sudo chown $USER /srv/backups
crontab -e
```

เพิ่มบรรทัดนี้ (backup ตี 2 และเก็บไว้ 14 วัน):

```cron
0 2 * * * cd /srv/building-care && docker compose exec -T database sh -c 'pg_dump -U "$POSTGRES_USER" -Fc "$POSTGRES_DB"' > /srv/backups/bsms-$(date +\%F).dump && find /srv/backups -name 'bsms-*.dump' -mtime +14 -delete
```

ควรคัดลอกไฟล์ใน `/srv/backups` ออกนอกเครื่องด้วย (เช่น `rsync` ไปเครื่องอื่น)

Restore จากไฟล์ backup:

```bash
docker compose stop backend
docker compose exec -T database sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists' \
  < /srv/backups/bsms-YYYY-MM-DD.dump
docker compose start backend
```

## 10. อัปเดตเวอร์ชัน

```bash
cd /srv/building-care
# backup ก่อนทุกครั้ง (คำสั่งเดียวกับใน cron)
git pull                      # หรือ git fetch --tags && git checkout <tag>
docker compose up -d --build  # migration ใหม่รันอัตโนมัติ
docker compose ps
```

ย้อนกลับ: `git checkout <commit/tag เดิม>` แล้ว `docker compose up -d --build`
ถ้าเวอร์ชันใหม่เปลี่ยนโครงสร้างฐานข้อมูลแล้ว ให้ restore backup ที่ทำก่อนอัปเดตด้วย

## 11. แก้ปัญหาที่พบบ่อย

| อาการ | สาเหตุ / วิธีแก้ |
| --- | --- |
| `docker compose` แจ้ง `set XXX in .env` | ยังไม่ได้ใส่ค่าที่จำเป็นใน `.env` |
| backend log: `Production requires ... at least 32 characters` | secret สั้นเกินไป ใช้ `openssl rand -hex 32` |
| backend log: `Production frontend URLs must be ...` | `PUBLIC_BASE_URL`/`BACKEND_CORS_ORIGINS` ต้องเป็น `https://<โดเมน>` ไม่ใช่ localhost |
| backend log: `password authentication failed` | เปลี่ยน `POSTGRES_PASSWORD` หลังสร้างฐานข้อมูลแล้ว ให้ใช้ค่าเดิม |
| อัปโหลดรูปได้ 413 | `client_max_body_size 60m` หายไปจาก config Nginx บนเครื่อง |
| 502 Bad Gateway | container ยังไม่ขึ้น ดู `docker compose ps` และ `docker compose logs backend` |
| ไม่ได้รับอีเมล | รัน `check_services.py` และดูโฟลเดอร์ spam |

คำสั่งที่ใช้บ่อย: `docker compose logs -f backend`, `docker compose restart backend`, `docker compose down`
(ห้ามใช้ `docker compose down -v` เพราะจะลบฐานข้อมูลทั้งหมด)

## สำหรับนักพัฒนา

`docker compose -f compose.yaml up --build` บนเครื่องตัวเองด้วย `.env` จาก `.env.example`
ชุดนี้มีบัญชีทดสอบ `admin@example.com` / `Admin@1234` ซึ่งจะไม่ถูกสร้างเมื่อ `ENVIRONMENT=production`
