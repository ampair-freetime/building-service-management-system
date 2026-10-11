"""อีเมลยืนยันรับเรื่องพร้อมรหัสติดตาม ที่ส่งหลัง guest ส่งคำร้อง 5 ประเภท."""

import asyncio
from datetime import UTC, datetime
from io import BytesIO
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi.testclient import TestClient
from PIL import Image as PillowImage
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.dependencies import provide_object_storage, provide_optional_object_storage
from app.core.config import settings
from app.models.enums import LostStatus
from app.models.location import Location
from app.models.lost_found import LostItem
from app.models.service_request import ServiceRequest
from app.services import guest_email
from app.services.guest_email import SubmissionReceipt, build_submission_email, tracking_link
from app.services.invitation_email import EmailDeliveryError
from app.services.object_storage import StorageOperationError, StoredObject

Context = tuple[TestClient, async_sessionmaker[AsyncSession]]


class FakeStorage:
    def __init__(self) -> None:
        self.fail_put = False

    async def put(self, *, object_key: str, data: bytes, content_type: str) -> StoredObject:
        if self.fail_put:
            raise StorageOperationError("simulated R2 failure")
        return StoredObject(object_key=object_key, bucket_name="test-images", etag="etag")

    async def delete(self, object_key: str) -> None:
        return None

    def create_download_url(self, object_key: str) -> str:
        return f"https://signed.example/{object_key}"


class SentMail:
    """แทน send_email ใน guest_email; TestClient รัน background task เสร็จก่อน post() คืนค่า."""

    def __init__(self) -> None:
        self.messages: list[dict[str, str]] = []
        self.fail = False

    async def __call__(self, *, recipient: str, subject: str, body: str) -> None:
        if self.fail:
            raise EmailDeliveryError("simulated SMTP failure")
        self.messages.append({"recipient": recipient, "subject": subject, "body": body})


@pytest.fixture
def mail(monkeypatch: pytest.MonkeyPatch) -> SentMail:
    sent = SentMail()
    # ต้อง patch ชื่อในโมดูล guest_email เพราะ Python ผูกชื่อ send_email ไว้ตอน import
    monkeypatch.setattr(guest_email, "send_email", sent)
    return sent


@pytest.fixture
def storage(test_context: Context) -> FakeStorage:
    client, factory = test_context
    fake = FakeStorage()
    client.app.dependency_overrides[provide_object_storage] = lambda: fake
    client.app.dependency_overrides[provide_optional_object_storage] = lambda: fake

    async def seed() -> None:
        async with factory() as session:
            session.add(Location(id=1, floor="2", area="ห้อง 201", qr_token="active"))
            await session.commit()

    asyncio.run(seed())
    yield fake
    client.app.dependency_overrides.pop(provide_object_storage, None)
    client.app.dependency_overrides.pop(provide_optional_object_storage, None)


def service_form(**changes: str) -> dict[str, str]:
    values = {
        "title": "พื้นเปียก",
        "description": "ข้างลิฟต์ตัวซ้าย",
        "priority": "urgent",
        "reporter_email": "GUEST@EXAMPLE.COM",
        "location_id": "1",
    }
    values.update(changes)
    return values


def item_form(**changes: str) -> dict[str, str]:
    values = {
        "item_category": "กุญแจ",
        "item_name": "กุญแจพร้อมพวงสีแดง",
        "description": "พบหน้าห้องสมุด",
        "event_datetime": "2025-01-15T11:00:00",
        "location_detail": "อาคารหอสมุด ชั้น 1",
        "reporter_email": "GUEST@EXAMPLE.COM",
    }
    values.update(changes)
    return values


def make_png() -> bytes:
    output = BytesIO()
    PillowImage.new("RGB", (32, 24), color="blue").save(output, format="PNG")
    return output.getvalue()


def approve_item(factory: async_sessionmaker[AsyncSession], item_code: str) -> None:
    async def update() -> None:
        async with factory() as session:
            item = await session.scalar(select(LostItem).where(LostItem.item_code == item_code))
            item.status = LostStatus.APPROVED
            await session.commit()

    asyncio.run(update())


def count_rows(factory: async_sessionmaker[AsyncSession], model) -> int:
    async def read() -> int:
        async with factory() as session:
            return await session.scalar(select(func.count()).select_from(model))

    return asyncio.run(read())


def submit(client: TestClient, factory, kind: str) -> tuple[str, str]:
    """ส่งคำร้องหนึ่งประเภท แล้วคืน (รหัสที่ต้องอยู่ในอีเมล, อีเมลผู้รับที่ normalize แล้ว)."""
    if kind == "cleaning":
        response = client.post("/api/v1/guest/cleaning-requests", data=service_form())
        assert response.status_code == 201, response.text
        return response.json()["request_code"], "guest@example.com"
    if kind == "repair":
        response = client.post("/api/v1/guest/repair-requests", data=service_form())
        assert response.status_code == 201, response.text
        return response.json()["request_code"], "guest@example.com"
    if kind in ("lost", "found"):
        form = item_form()
        if kind == "found":
            form["private_verification_detail"] = "มีลูกกุญแจสามดอก"
        response = client.post(f"/api/v1/guest/{kind}-items", data=form)
        assert response.status_code == 201, response.text
        return response.json()["item_code"], "guest@example.com"
    # claim: ต้องมีประกาศพบของที่อนุมัติแล้วก่อน
    found = client.post(
        "/api/v1/guest/found-items",
        data=item_form(private_verification_detail="x", reporter_email="finder@example.com"),
    )
    item_code = found.json()["item_code"]
    approve_item(factory, item_code)
    response = client.post(
        f"/api/v1/guest/found-items/{item_code}/claims",
        json={
            "claimant_name": "สมชาย ใจดี",
            "claimant_email": "Owner@Example.COM",
            "proof_detail": "พวงกุญแจมีหมายเลข 1042 สลักด้านหลัง",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["claim_code"], "owner@example.com"


@pytest.mark.parametrize("kind", ["cleaning", "repair", "lost", "found", "claim"])
def test_each_submission_emails_its_tracking_code(
    test_context: Context, storage: FakeStorage, mail: SentMail, kind: str
) -> None:
    client, factory = test_context
    code, recipient = submit(client, factory, kind)

    receipts = [m for m in mail.messages if m["recipient"] == recipient]
    assert len(receipts) == 1
    assert code in receipts[0]["subject"]
    assert code in receipts[0]["body"]
    assert tracking_link(code) in receipts[0]["body"]


def test_service_request_email_names_the_location_from_the_locations_table(
    test_context: Context, storage: FakeStorage, mail: SentMail
) -> None:
    client, factory = test_context
    submit(client, factory, "repair")

    assert "ห้อง 201" in mail.messages[0]["body"]


def test_email_never_contains_text_the_guest_typed(
    test_context: Context, storage: FakeStorage, mail: SentMail
) -> None:
    client, _ = test_context
    response = client.post(
        "/api/v1/guest/repair-requests",
        data=service_form(
            title="คลิก http://evil.example/login",
            description="ยืนยันบัญชีที่ http://evil.example",
        ),
    )

    assert response.status_code == 201
    assert "evil.example" not in mail.messages[0]["subject"]
    assert "evil.example" not in mail.messages[0]["body"]


def test_tracking_link_carries_the_code_but_not_the_email(
    test_context: Context, storage: FakeStorage, mail: SentMail
) -> None:
    client, factory = test_context
    code, _ = submit(client, factory, "cleaning")

    link = next(line for line in mail.messages[0]["body"].splitlines() if "?track=" in line)
    url = link.split(": ", 1)[1]
    assert parse_qs(urlsplit(url).query) == {"track": [code]}
    assert "@" not in url


def test_rejected_form_sends_no_email(
    test_context: Context, storage: FakeStorage, mail: SentMail
) -> None:
    client, _ = test_context
    response = client.post("/api/v1/guest/repair-requests", data=service_form(title=""))

    assert response.status_code == 422
    assert mail.messages == []


def test_storage_failure_sends_no_email_for_the_unsaved_request(
    test_context: Context, storage: FakeStorage, mail: SentMail
) -> None:
    client, factory = test_context
    storage.fail_put = True
    response = client.post(
        "/api/v1/guest/lost-items",
        data=item_form(),
        files={"image": ("a.png", make_png(), "image/png")},
    )

    assert response.status_code == 502
    assert count_rows(factory, LostItem) == 0
    assert mail.messages == []


def test_smtp_failure_keeps_the_request_and_still_returns_201(
    test_context: Context, storage: FakeStorage, mail: SentMail
) -> None:
    client, factory = test_context
    mail.fail = True
    response = client.post("/api/v1/guest/repair-requests", data=service_form())

    assert response.status_code == 201
    assert count_rows(factory, ServiceRequest) == 1


def test_recipient_limit_skips_email_but_keeps_accepting_requests(
    test_context: Context, storage: FakeStorage, mail: SentMail, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, factory = test_context
    # limiter ถูกสร้างตอนใช้ครั้งแรกจากค่า settings และแต่ละ test ได้ app ใหม่
    monkeypatch.setattr(settings, "guest_email_per_recipient_limit", 2)

    statuses = [
        client.post(
            "/api/v1/guest/repair-requests", data=service_form(reporter_email=email)
        ).status_code
        for email in ("guest@example.com", "GUEST@example.com", "Guest@Example.com")
    ]
    other = client.post(
        "/api/v1/guest/repair-requests", data=service_form(reporter_email="other@example.com")
    )

    assert statuses == [201, 201, 201]
    assert other.status_code == 201
    assert count_rows(factory, ServiceRequest) == 4
    assert [m["recipient"] for m in mail.messages] == [
        "guest@example.com",
        "guest@example.com",
        "other@example.com",
    ]


def test_receipt_time_is_shown_in_bangkok_time() -> None:
    receipt = SubmissionReceipt(
        kind="repair",
        code="RPR-20261011-1A2B3C4D",
        created_at=datetime(2026, 10, 11, 7, 5, tzinfo=UTC),
    )

    subject, body = build_submission_email(receipt)

    assert subject == "ได้รับเรื่องแจ้งซ่อมแล้ว · RPR-20261011-1A2B3C4D"
    assert "เวลาที่รับเรื่อง: 11/10/2026 14:05 น." in body


def test_claim_receipt_mentions_the_found_item_it_refers_to() -> None:
    receipt = SubmissionReceipt(
        kind="claim",
        code="CLM-20261011-AAAA1111",
        created_at=datetime(2026, 10, 11, tzinfo=UTC),
        related_code="FOUND-20261010-BBBB2222",
    )

    _, body = build_submission_email(receipt)

    assert "รหัสประกาศที่ขอรับคืน: FOUND-20261010-BBBB2222" in body
