# Initial Admin สำหรับ Production

คำสั่งนี้ต้องรันโดยผู้ดูแลเท่านั้น หลังฐานข้อมูลผ่าน Alembic migration จนถึง head แล้ว
Script ไม่รัน migration และไม่ทำงานอัตโนมัติเมื่อเริ่มแอปหรือ Restart Container

## ฐานข้อมูลใหม่

ตั้ง `ENVIRONMENT=production` ก่อน migration ครั้งแรก พร้อม JWT/IMAGE secrets และ URL
ที่ผ่าน Production validator ของระบบ Seed เดิมจะทำงานเฉพาะ `development` เท่านั้น
ไม่ได้เปลี่ยน revision, parent revision หรือ schema ของ migration เดิม
Migration ใหม่ภายหลังไม่สามารถป้องกัน Seed เดิมได้โดยไม่ย้อนลบข้อมูล จึงเพิ่ม guard
เฉพาะใน upgrade ของ Seed เดิม; Alembic จะไม่รันซ้ำกับฐานข้อมูลที่บันทึก revision นี้แล้ว

Bootstrap รับตัวแปรต่อไปนี้จาก Environment ของ Process โดยตรง:

- `INITIAL_ADMIN_EMAIL`
- `INITIAL_ADMIN_FULL_NAME`
- `INITIAL_ADMIN_PASSWORD`

แต่ละตัวใช้ `<ชื่อตัวแปร>_FILE` แทนได้ เช่น `INITIAL_ADMIN_PASSWORD_FILE`
ห้ามกำหนดทั้งค่าตรงและ `_FILE` สำหรับตัวเดียวกัน; ไม่อ่านค่าชุด INITIAL_ADMIN จาก dotenv
โดยอัตโนมัติ เพื่อแยก credentials ที่ใช้ครั้งเดียวออกจากการตั้งค่าของแอป

แนะนำไฟล์ Secret UTF-8 นอก repository และ build context จำกัดสิทธิ์ `chmod 600`
ไฟล์ต้องเป็น regular file ไม่ใช่ symlink เป็นของ user ที่รันคำสั่ง และไม่มีสิทธิ์ group/other
ขนาดไม่เกิน 4096 bytes; newline ท้ายไฟล์จะถูกตัดออก รหัสผ่านไม่ถูก strip ช่องว่าง
เตรียมไฟล์ด้วยระบบ Secret ของผู้ดูแล หลีกเลี่ยงการพิมพ์รหัสผ่านใน command line หรือ shell history

ตัวอย่างบน Linux (ไฟล์ต้องเตรียมไว้แล้ว; ตัวอย่างนี้ไม่มีค่ารหัสผ่าน):

```bash
export INITIAL_ADMIN_EMAIL_FILE=/run/secrets/initial_admin_email
export INITIAL_ADMIN_FULL_NAME_FILE=/run/secrets/initial_admin_name
export INITIAL_ADMIN_PASSWORD_FILE=/run/secrets/initial_admin_password
python scripts/create_initial_admin.py
```

รันจาก `Backend/` ด้วย Python environment ของโปรเจกต์ หรือรันคำสั่งเดียวกันใน Backend
Container โดยส่ง Environment และ mount Secret แบบ read-only เข้าสู่ Process นั้นอย่างชัดเจน
การตั้งตัวแปรบน Host ไม่ทำให้ `docker compose exec` รับค่าไปโดยอัตโนมัติ
Script ใช้ DATABASE_URL และการโหลด Settings เดิม (`BSMS_ENV_FILE` ใช้เลือกไฟล์ได้)
ตรวจสอบฐานข้อมูลเป้าหมายก่อนรันจริง และอย่าเปิด SQL debug logging ขณะ Bootstrap

หลังสำเร็จจะได้ Admin สถานะ active ตั้งรหัสผ่านแล้ว ไม่ต้องผ่านคำเชิญ สามารถ Login ปกติ
ใช้กฎรหัสผ่านเดิมของระบบและแฮช Argon2 จากนั้นถอน Environment/Secret สำหรับ Bootstrap
ออกจากการตั้งค่า deployment และเก็บหรือทำลายไฟล์ตามนโยบายของภาควิชา

## การรันซ้ำและฐานข้อมูลเดิม

- พบ Admin ใด ๆ รวมถึง suspended/deleted: สำเร็จแบบไม่เปลี่ยนข้อมูล (exit 0)
  ไม่ต้องมี credentials สำหรับ Bootstrap และไม่สร้าง Admin เพิ่ม
- พบอีเมลของบัญชีอื่น: หยุด (exit 1) ไม่เปลี่ยน role, status หรือ password
- ข้อมูลไม่ถูกต้อง/เชื่อมต่อไม่ได้: หยุด (exit 1) ไม่พิมพ์รายละเอียดที่อาจมี Secret
- PostgreSQL ใช้ transaction และ table lock ป้องกัน Bootstrap พร้อมกันและ staff writes
  ระหว่างตรวจ/สร้าง; รอ lock ได้ไม่เกิน 10 วินาที ควรรันก่อนเปิดรับผู้ใช้
- ไม่มีการลบ ระงับบัญชี หรือรีเซ็ตรหัสผ่านเดิมโดยอัตโนมัติ

ถ้าฐานข้อมูลเดิมมี Development Admin ต้องสำรองและตรวจสอบบัญชีด้วยผู้ดูแลก่อนเปิดบริการ
ใช้กระบวนการจัดการบัญชี/รหัสผ่านที่มีอยู่เพื่อสร้างหรือปรับบัญชีจริง และตรวจว่ารหัสผ่าน
Development เข้าไม่ได้ Bootstrap นี้ไม่ใช่เครื่องมือกู้บัญชีหรือยกระดับสิทธิ์
อย่า downgrade migration เพื่อเอา Seed ออก เพราะ downgrade เดิมมีคำสั่งลบบัญชี
อย่าลบ volume หรือสร้างฐานข้อมูลใหม่เพื่อแก้ปัญหาบัญชีเดิม

## การทดสอบ

Tests ใช้ SQLite ชั่วคราวและ mock Seed/CLI ไม่มีการรันกับฐานข้อมูลจริง
เส้นทาง lock ของ PostgreSQL ต้องตรวจเพิ่มใน staging PostgreSQL ที่แยกจากข้อมูลจริง
ก่อน Deploy; SQLite รองรับเฉพาะการทดสอบ Script นี้
