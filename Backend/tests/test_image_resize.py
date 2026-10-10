"""Verify uploaded images are downscaled and re-encoded as small WebP files."""

import os
from io import BytesIO

import pytest
from PIL import Image

from app.services import images
from app.services.images import InvalidImageError, _normalize_to_webp

MB = 1024 * 1024


def encode(image, fmt="JPEG", **kwargs):
    data = BytesIO()
    image.save(data, format=fmt, **kwargs)
    return data.getvalue()


def normalize(data, *, max_output_bytes=MB, max_pixels=50_000_000):
    return _normalize_to_webp(data, max_output_bytes, max_pixels, 2048, 78)


def decoded(result):
    return Image.open(BytesIO(result.data))


def test_large_jpeg_is_downscaled_to_max_dimension():
    result = normalize(encode(Image.new("RGB", (8000, 6000), "steelblue")))

    assert result.content_type == "image/webp"
    assert (result.width, result.height) == (2048, 1536)
    assert decoded(result).size == (2048, 1536)
    assert decoded(result).format == "WEBP"


def test_more_than_max_pixels_is_rejected_before_decoding():
    data = encode(Image.new("RGB", (8200, 6200)))

    with pytest.raises(InvalidImageError, match="ความละเอียด"):
        normalize(data)


def test_small_image_is_not_upscaled():
    result = normalize(encode(Image.new("RGB", (800, 600), "white")))

    assert (result.width, result.height) == (800, 600)


def test_exif_rotation_is_applied_before_recording_size():
    image = Image.new("RGB", (4000, 3000))
    exif = image.getexif()
    exif[0x0112] = 6  # Orientation: rotate 90° clockwise

    result = normalize(encode(image, exif=exif))

    assert (result.width, result.height) == (1536, 2048)
    assert "exif" not in decoded(result).info


def test_png_alpha_is_preserved():
    result = normalize(encode(Image.new("RGBA", (3000, 3000), (0, 0, 0, 0)), "PNG"))

    assert (result.width, result.height) == (2048, 2048)
    assert "A" in decoded(result).getbands()


def test_panorama_wider_than_webp_limit_is_accepted_after_resize():
    result = normalize(encode(Image.new("RGB", (20000, 2400), "gray")))

    assert result.width == 2048
    assert result.height == round(2400 * 2048 / 20000)


def test_hard_to_compress_image_lowers_quality_to_fit_output_limit():
    noise = Image.frombytes("RGB", (2048, 2048), os.urandom(2048 * 2048 * 3))
    data = encode(noise, quality=95)

    first_try = BytesIO()
    noise.save(first_try, format="WEBP", quality=78, method=6)
    limit = first_try.tell() - 1

    result = normalize(data, max_output_bytes=limit)

    assert len(result.data) <= limit


def test_output_still_too_large_is_rejected():
    data = encode(Image.new("RGB", (1000, 1000), "red"))

    with pytest.raises(InvalidImageError, match="หลังประมวลผล"):
        normalize(data, max_output_bytes=10)


def test_quality_ladder_never_raises_quality_or_drops_below_50():
    assert images._quality_ladder(78) == [78, 70, 60, 50]
    assert images._quality_ladder(65) == [65, 60, 50]
    assert images._quality_ladder(40) == [40]
