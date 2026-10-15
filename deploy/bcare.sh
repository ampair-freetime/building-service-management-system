#!/usr/bin/env bash
# คำสั่งเดียวสำหรับติดตั้งและดูแล CS Building Care บนเซิร์ฟเวอร์ (ใช้ compose.production.yaml)
#
#   ./deploy/bcare.sh install         ติดตั้งครั้งแรก (รันซ้ำได้ ขั้นที่ทำแล้วจะข้าม)
#   ./deploy/bcare.sh update          backup → git pull → build → migrate → start
#   ./deploy/bcare.sh status          สถานะ container + ตรวจ SMTP/R2 + /health
#   ./deploy/bcare.sh backup          สำรองฐานข้อมูล (เก็บ 14 วัน)
#   ./deploy/bcare.sh restore FILE    กู้คืนฐานข้อมูลจากไฟล์ .dump
#   ./deploy/bcare.sh https DOMAIN    ตั้ง Nginx บนเครื่อง + ใบรับรอง Let's Encrypt (ใช้ sudo)
#   ./deploy/bcare.sh logs [service]  ดู log แบบ realtime
#
# ค่าที่ปรับได้ผ่าน environment: BACKUP_DIR (ค่าเริ่มต้น /srv/backups), BACKUP_KEEP_DAYS (14)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
BACKUP_DIR="${BACKUP_DIR:-/srv/backups}"
BACKUP_KEEP_DAYS="${BACKUP_KEEP_DAYS:-14}"

say() { printf '\n==> %s\n' "$*"; }
die() { printf '\n[หยุด] %s\n' "$*" >&2; exit 1; }
dc() { docker compose "$@"; }  # .env มี COMPOSE_FILE=compose.production.yaml

require_docker() {
  command -v docker >/dev/null || die "ไม่พบ docker — ติดตั้ง Docker Engine ก่อน (README หัวข้อ 2)"
  docker compose version >/dev/null 2>&1 || die "ไม่พบ docker compose plugin v2"
  docker info >/dev/null 2>&1 || die "user นี้สั่ง docker ไม่ได้ — เพิ่มเข้ากลุ่ม docker แล้ว login ใหม่"
}

random_secret() {
  if command -v openssl >/dev/null; then openssl rand -hex 32
  else head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n'; fi
}

# สร้าง .env จากตัวอย่าง และเติมรหัสลับ 3 ค่าให้อัตโนมัติ เหลือให้คนกรอกแค่ค่าที่มาจากภายนอก
prepare_env() {
  if [[ ! -f .env ]]; then
    (umask 077; cp .env.production.example .env)
    sed -i \
      -e "s/^POSTGRES_PASSWORD=REPLACE_DB_PASSWORD$/POSTGRES_PASSWORD=$(random_secret)/" \
      -e "s/^JWT_SECRET_KEY=REPLACE_JWT_SECRET$/JWT_SECRET_KEY=$(random_secret)/" \
      -e "s/^IMAGE_URL_SECRET=REPLACE_IMAGE_SECRET$/IMAGE_URL_SECRET=$(random_secret)/" \
      .env
    say "สร้าง .env แล้ว (รหัสลับของฐานข้อมูล/JWT/รูปภาพ สุ่มให้แล้ว)"
  fi
  chmod 600 .env
  local missing
  missing="$(grep -nE '^[A-Z0-9_]+=.*REPLACE_' .env || true)"
  if [[ -n "$missing" ]]; then
    printf '\nกรอกค่าเหล่านี้ใน .env ให้ครบ (เช่น nano .env) แล้วรันคำสั่งเดิมอีกครั้ง:\n%s\n' "$missing"
    exit 1
  fi
  dc config --quiet || die ".env หรือ compose.production.yaml ไม่ถูกต้อง (ดูข้อความด้านบน)"
}

migrate() {
  say "อัปเดตโครงสร้างฐานข้อมูล"
  dc up -d --wait database
  dc run --rm backend alembic upgrade head
}

start_and_check() {
  say "เริ่มระบบ"
  dc up -d --wait
  check
}

check() {
  say "ตรวจบริการภายนอก (SMTP / R2) และ /health"
  dc exec -T backend python scripts/check_services.py \
    || echo "(ระบบยังทำงานได้ แต่ส่งอีเมล/อัปโหลดรูปไม่ได้ — ดู README หัวข้อแก้ปัญหา)"
  local host port
  host="$(sed -n 's/^FRONTEND_BIND_ADDRESS=//p' .env)"
  port="$(sed -n 's/^FRONTEND_PORT=//p' .env)"
  curl -fsS "http://${host:-127.0.0.1}:${port:-8080}/health" && echo
}

install_backup_cron() {
  local line="0 2 * * * cd $ROOT && ./deploy/bcare.sh backup >/dev/null 2>&1"
  if ! crontab -l 2>/dev/null | grep -Fq "deploy/bcare.sh backup"; then
    (crontab -l 2>/dev/null; echo "$line") | crontab -
    say "ตั้ง backup อัตโนมัติทุกวัน 02:00 แล้ว (crontab -l เพื่อดู)"
  fi
}

cmd_install() {
  require_docker
  prepare_env
  say "Build image (ครั้งแรกใช้เวลาหลายนาที)"
  dc build
  migrate
  say "สร้างบัญชี admin คนแรก (ถ้ามีแล้วจะข้าม)"
  dc run --rm backend python scripts/create_initial_admin.py
  start_and_check
  install_backup_cron
  say "ติดตั้งเสร็จ ขั้นต่อไป: เปิด HTTPS (README ขั้นตอนที่ 3)"
}

cmd_update() {
  require_docker
  prepare_env
  cmd_backup
  say "ดึงโค้ดใหม่"
  git pull --ff-only
  dc build
  migrate
  start_and_check
}

cmd_backup() {
  mkdir -p "$BACKUP_DIR"
  local file
  file="$BACKUP_DIR/bsms-$(date +%F_%H%M).dump"
  # ไฟล์ dump มี hash รหัสผ่านของเจ้าหน้าที่ จึงให้เจ้าของอ่านได้คนเดียว
  (umask 077; dc exec -T database sh -c 'pg_dump -U "$POSTGRES_USER" -Fc "$POSTGRES_DB"' >"$file")
  find "$BACKUP_DIR" -name 'bsms-*.dump' -mtime +"$BACKUP_KEEP_DAYS" -delete
  say "Backup: $file"
}

cmd_restore() {
  local file="${1:-}"
  [[ -f "$file" ]] || die "ระบุไฟล์ backup เช่น ./deploy/bcare.sh restore $BACKUP_DIR/bsms-2026-10-15_0200.dump"
  read -r -p "กู้คืนจาก $file ข้อมูลปัจจุบันจะถูกแทนที่ทั้งหมด พิมพ์ yes เพื่อยืนยัน: " answer
  [[ "$answer" == "yes" ]] || die "ยกเลิก"
  dc stop backend frontend
  dc exec -T database sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists' <"$file"
  start_and_check
}

cmd_https() {
  local domain="${1:-}"
  [[ -n "$domain" ]] || die "ระบุโดเมน เช่น ./deploy/bcare.sh https care.cs.cmu.ac.th"
  command -v nginx >/dev/null || die "ไม่พบ nginx บนเครื่อง (ถ้าภาควิชาทำ HTTPS ให้ ข้ามขั้นนี้ได้ ดู README)"
  command -v certbot >/dev/null || die "ไม่พบ certbot (ติดตั้ง certbot + python3-certbot-nginx)"
  local site=/etc/nginx/conf.d/building-care.conf
  [[ -d /etc/nginx/sites-available ]] && site=/etc/nginx/sites-available/building-care
  sed "s/care.example.ac.th/$domain/" deploy/nginx/building-care.conf | sudo tee "$site" >/dev/null
  if [[ -d /etc/nginx/sites-enabled ]]; then
    sudo ln -sf "$site" /etc/nginx/sites-enabled/building-care
  fi
  sudo nginx -t
  sudo systemctl reload nginx
  sudo certbot --nginx -d "$domain"
  curl -fsS "https://$domain/health" && echo
}

cmd_status() {
  require_docker
  dc ps
  check
}

case "${1:-}" in
  install) cmd_install ;;
  update) cmd_update ;;
  status) cmd_status ;;
  backup) cmd_backup ;;
  restore) shift; cmd_restore "${1:-}" ;;
  https) shift; cmd_https "${1:-}" ;;
  logs) shift; dc logs -f --tail 100 "$@" ;;
  *) sed -n '2,12p' "$0"; exit 1 ;;
esac
