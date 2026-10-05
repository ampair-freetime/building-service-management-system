"""Verify memory-heavy work stays bounded under concurrency and cancellation."""

import asyncio
import threading
import time
from io import BytesIO

import anyio
from fastapi import UploadFile
from PIL import Image
from starlette.datastructures import Headers

from app.services import images


def upload():
    data = BytesIO()
    Image.new("RGB", (10, 10)).save(data, format="PNG")
    data.seek(0)
    return UploadFile(
        file=data, filename="image.png", headers=Headers({"content-type": "image/png"})
    )


def test_image_normalization_concurrency_is_bounded(monkeypatch):
    normalize = images._normalize_to_webp
    lock = threading.Lock()
    active = peak = 0

    def slow_normalize(*args):
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        try:
            time.sleep(0.02)
            return normalize(*args)
        finally:
            with lock:
                active -= 1

    monkeypatch.setattr(images, "_normalize_to_webp", slow_normalize)

    async def run():
        limiter = anyio.CapacityLimiter(2)
        monkeypatch.setattr(images, "_processing_limiter", lambda: limiter)
        results = await asyncio.gather(*(images.prepare_guest_image(upload()) for _ in range(6)))
        assert all(result.content_type == "image/webp" for result in results)

    asyncio.run(run())
    assert peak == 2
    assert active == 0


def test_cancellation_does_not_release_capacity_while_thread_is_running(monkeypatch):
    started = threading.Event()
    release = threading.Event()
    lock = threading.Lock()
    calls = 0
    normalize = images._normalize_to_webp

    def blocking_normalize(*args):
        nonlocal calls
        with lock:
            calls += 1
            first = calls == 1
        if first:
            started.set()
            assert release.wait(3), "Test must release the first normalization thread"
        return normalize(*args)

    monkeypatch.setattr(images, "_normalize_to_webp", blocking_normalize)

    async def run():
        limiter = anyio.CapacityLimiter(1)
        monkeypatch.setattr(images, "_processing_limiter", lambda: limiter)
        first = asyncio.create_task(images.prepare_guest_image(upload()))
        second = None
        try:
            await asyncio.wait_for(asyncio.to_thread(started.wait), timeout=2)
            first.cancel()
            second = asyncio.create_task(images.prepare_guest_image(upload()))
            await asyncio.sleep(0.05)
            assert calls == 1, "Cancelled request must retain capacity until its thread ends"
        finally:
            release.set()
            results = await asyncio.gather(
                first, *([second] if second else []), return_exceptions=True
            )
        assert isinstance(results[0], asyncio.CancelledError)
        assert calls == 2

    asyncio.run(run())
