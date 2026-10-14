# สร้าง Admin คนแรก (Production)

Production ไม่มีบัญชีตั้งต้น ต้องสร้าง admin คนแรกเองหนึ่งครั้ง หลังรัน migration แล้ว
(ขั้นตอนเต็มอยู่ใน [README](../../README.md))

## วิธีปกติ: พิมพ์ตอบในเทอร์มินัล

```bash
docker compose run --rm backend python scripts/create_initial_admin.py
```

ระบบจะถาม อีเมล, ชื่อ-นามสกุล และรหัสผ่าน (พิมพ์แล้วไม่แสดงบนจอ ต้องพิมพ์ซ้ำ 2 ครั้ง)
รหัสผ่านไม่ถูกเก็บใน shell history หรือไฟล์ใด ๆ

กฎรหัสผ่าน: 8–128 ตัวอักษร มีตัวพิมพ์ใหญ่ ตัวพิมพ์เล็ก ตัวเลข และสัญลักษณ์อย่างละ 1 ตัว
อีเมลต้องเป็นโดเมนจริง (`.test`, `.local`, `.example` ใช้ไม่ได้)

| ผลลัพธ์ | ความหมาย |
| --- | --- |
| `Initial admin created` | สำเร็จ เข้าสู่ระบบที่ `/staff-login` ได้ทันที |
| `Admin already exists; no changes made` | มี admin อยู่แล้ว (รวมบัญชีที่ถูกระงับ/ลบ) ไม่มีอะไรเปลี่ยน |
| `Bootstrap stopped: Invalid ...` | ข้อมูลไม่ผ่าน ข้อความบอกว่าช่องไหนและผิดกฎข้อใด |
| `Bootstrap stopped: Email already belongs ...` | อีเมลนี้เป็นของ staff คนอื่น ไม่มีการเปลี่ยน role ให้ |

รันซ้ำได้อย่างปลอดภัย: ถ้ามี admin แล้วจะไม่สร้างเพิ่มและไม่แตะรหัสผ่านเดิม
เพิ่ม admin หรือ staff คนถัดไปผ่านหน้า admin ของเว็บ

## วิธีอัตโนมัติ: ไฟล์ secret (ไม่มีคนพิมพ์)

สำหรับสคริปต์ deploy ที่ไม่มีเทอร์มินัล ให้เตรียมไฟล์ละ 1 ค่าไว้นอก repository:

```bash
mkdir -p ~/bootstrap && cd ~/bootstrap && umask 077
printf '%s\n' 'admin@your-org.ac.th' > email
printf '%s\n' 'ชื่อ นามสกุล'         > name
nano password                               # ใส่รหัสผ่านบรรทัดเดียว

cd /srv/building-care
docker compose run --rm --user "$(id -u):$(id -g)" \
  -v ~/bootstrap:/run/bootstrap:ro \
  -e INITIAL_ADMIN_EMAIL_FILE=/run/bootstrap/email \
  -e INITIAL_ADMIN_FULL_NAME_FILE=/run/bootstrap/name \
  -e INITIAL_ADMIN_PASSWORD_FILE=/run/bootstrap/password \
  backend python scripts/create_initial_admin.py

rm -rf ~/bootstrap
```

- `--user "$(id -u):$(id -g)"` จำเป็น: script ยอมอ่านเฉพาะไฟล์ที่เป็นของ user เดียวกับ process
  ถ้าลืม จะได้ `... is owned by uid 1000 but this process runs as uid 10001`
- ไฟล์ต้องเป็น regular file (ไม่ใช่ symlink), สิทธิ์ `600`, ไม่เกิน 4096 bytes
- ใช้ `INITIAL_ADMIN_EMAIL` / `INITIAL_ADMIN_FULL_NAME` / `INITIAL_ADMIN_PASSWORD`
  แบบค่าตรงแทนไฟล์ได้ แต่ห้ามตั้งทั้งค่าตรงและ `_FILE` ของตัวเดียวกัน

## สิ่งที่ script ไม่ทำ

- ไม่รัน migration และไม่ทำงานเองตอนเริ่มระบบ
- ไม่รีเซ็ตรหัสผ่าน ไม่ระงับ และไม่ยกระดับสิทธิ์บัญชีเดิม (admin ลืมรหัสผ่าน → ใช้ "ลืมรหัสผ่าน" ที่หน้า login)
- Seed บัญชี `admin@example.com` ของ development ไม่ถูกสร้างเมื่อ `ENVIRONMENT=production`
  ถ้าฐานข้อมูลเคยรันแบบ development มาก่อน ให้ลบหรือระงับบัญชีนั้นก่อนเปิดใช้งานจริง

## การทดสอบ

`tests/test_initial_admin.py` ใช้ SQLite ชั่วคราว ครอบคลุมการสร้าง, รันซ้ำ, ข้อมูลผิด,
ไฟล์ไม่ปลอดภัย, การถามในเทอร์มินัล และการรันพร้อมกัน ส่วน lock ของ PostgreSQL
ตรวจจริงได้เฉพาะบน staging
