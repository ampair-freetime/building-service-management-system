"""แปลง URL เป็นรูป QR ในหน่วยความจำ."""

from io import BytesIO
from typing import Literal

import segno


def render_qr(data: str, fmt: Literal["png", "svg"]) -> tuple[bytes, str]:
    qr = segno.make(data, error="q", micro=False)
    buffer = BytesIO()
    qr.save(buffer, kind=fmt, scale=10, border=4)
    media_type = "image/png" if fmt == "png" else "image/svg+xml"
    return buffer.getvalue(), media_type
