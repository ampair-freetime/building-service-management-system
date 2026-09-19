"""สร้างสถานที่เริ่มต้นพร้อม QR token และพิมพ์ URL สำหรับทำป้าย QR."""

import argparse
import asyncio
import os
import secrets
import sys
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit

from sqlalchemy import select

# ทำให้เรียก `python Backend/scripts/seed_locations.py` จาก repository root ได้
backend_root = Path(__file__).resolve().parents[1]
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))
original_working_directory = Path.cwd()
try:
    os.chdir(backend_root)
    from app.db.session import AsyncSessionLocal
    from app.models.location import Location
finally:
    os.chdir(original_working_directory)

LOCATIONS = [
    {
        "floor": "1",
        "area": "ห้อง 101",
    },
]


def normalize_base_url(value: str) -> str:
    """รับเฉพาะ HTTP(S) URL และตัด path slash ท้ายก่อนต่อหน้า cleaning."""
    parts = urlsplit(value.strip())
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        raise argparse.ArgumentTypeError("--base-url ต้องเป็น HTTP(S) URL ที่สมบูรณ์")
    return urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip("/"), "", ""))


async def seed_locations(base_url: str) -> list[Location]:
    """เพิ่มเฉพาะสถานที่ที่ยังไม่มี โดยรักษา token เดิมเมื่อรันซ้ำ."""
    async with AsyncSessionLocal() as session:
        for values in LOCATIONS:
            location = await session.scalar(select(Location).filter_by(**values))
            if location is None:
                session.add(Location(**values, qr_token=secrets.token_urlsafe(24)))
        await session.commit()
        result = await session.scalars(
            select(Location)
            .where(Location.is_active.is_(True))
            .order_by(Location.floor, Location.area, Location.id)
        )
        locations = list(result)

    for location in locations:
        label = f"ชั้น {location.floor} {location.area}" if location.floor else location.area
        url = f"{base_url}/cleaning?token={quote(location.qr_token, safe='')}"
        print(f"{location.id}\t{label}\t{url}")
    return locations


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, type=normalize_base_url)
    arguments = parser.parse_args()
    asyncio.run(seed_locations(arguments.base_url))


if __name__ == "__main__":
    main()
