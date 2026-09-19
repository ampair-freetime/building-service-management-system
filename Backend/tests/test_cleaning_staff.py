import asyncio

from conftest import seed_staff
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.enums import RequestAction, RequestStatus
from app.models.location import Location
from app.models.service_request import RequestHistory, ServiceRequest


def seed_location(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def seed() -> None:
        async with session_factory() as session:
            session.add(
                Location(
                    id=1,
                    floor="2",
                    area="ห้อง 201",
                    qr_token="cleaning-staff-test",
                )
            )
            await session.commit()

    asyncio.run(seed())


def login_staff(
    client: TestClient,
    identifier: str,
    password: str,
) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": identifier,
            "password": password,
        },
    )

    assert response.status_code == 200

    return {
        "Authorization": f"Bearer {response.json()['access_token']}"
    }


def get_request_id(
    session_factory: async_sessionmaker[AsyncSession],
    request_code: str,
):
    async def get_id():
        async with session_factory() as session:
            request = await session.scalar(
                select(ServiceRequest).where(
                    ServiceRequest.request_code == request_code
                )
            )
            assert request is not None
            return request.id

    return asyncio.run(get_id())


def test_housekeeper_can_accept_cleaning_task(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        staff_code="HK001",
        email="housekeeper1@example.com",
        password="password-one",
        role="housekeeper",
        full_name="House Keeper One",
    )

    headers = login_staff(
        client,
        "HK001",
        "password-one",
    )

    created = client.post(
        "/api/v1/guest/cleaning-requests",
        data={
            "title": "พื้นเปียก",
            "description": "ข้างลิฟต์ตัวซ้าย",
            "priority": "urgent",
            "reporter_email": "guest@example.com",
            "location_id": "1",
        },
    )

    assert created.status_code == 201

    request_id = get_request_id(
        session_factory,
        created.json()["request_code"],
    )

    response = client.patch(
        f"/api/v1/cleaning-tasks/{request_id}/accept",
        headers=headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == str(request_id)
    assert body["request_code"] == created.json()["request_code"]
    assert body["status"] == "assigned"

    assert body["assigned_staff"]["staff_code"] == "HK001"
    assert body["assigned_staff"]["full_name"] == "House Keeper One"

    async def verify_database() -> None:
        async with session_factory() as session:
            task = await session.get(ServiceRequest, request_id)

            assert task is not None
            assert task.status == RequestStatus.ASSIGNED
            assert task.assigned_staff_id is not None

            history = await session.scalar(
                select(RequestHistory).where(
                    RequestHistory.request_id == request_id,
                    RequestHistory.action == RequestAction.ACCEPTED,
                )
            )

            assert history is not None
            assert history.old_status == RequestStatus.WAITING
            assert history.new_status == RequestStatus.ASSIGNED
            assert history.target_staff_id == task.assigned_staff_id

    asyncio.run(verify_database())


def test_second_housekeeper_cannot_accept_assigned_cleaning_task(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        staff_code="HK001",
        email="housekeeper1@example.com",
        password="password-one",
        role="housekeeper",
        full_name="House Keeper One",
    )

    seed_staff(
        session_factory,
        staff_code="HK002",
        email="housekeeper2@example.com",
        password="password-two",
        role="housekeeper",
        full_name="House Keeper Two",
    )

    hk1_headers = login_staff(
        client,
        "HK001",
        "password-one",
    )

    hk2_headers = login_staff(
        client,
        "HK002",
        "password-two",
    )

    created = client.post(
        "/api/v1/guest/cleaning-requests",
        data={
            "title": "ถังขยะเต็ม",
            "description": "หน้าห้อง 201",
            "priority": "normal",
            "reporter_email": "guest@example.com",
            "location_id": "1",
        },
    )

    assert created.status_code == 201

    request_id = get_request_id(
        session_factory,
        created.json()["request_code"],
    )

    # HK001 รับงานก่อน
    first = client.patch(
        f"/api/v1/cleaning-tasks/{request_id}/accept",
        headers=hk1_headers,
    )

    assert first.status_code == 200
    assert first.json()["assigned_staff"]["staff_code"] == "HK001"

    # HK002 พยายามรับงานเดียวกัน
    second = client.patch(
        f"/api/v1/cleaning-tasks/{request_id}/accept",
        headers=hk2_headers,
    )

    assert second.status_code == 409
    assert second.json()["detail"] == (
        "Cleaning task has already been assigned"
    )

    # งานต้องยังเป็นของ HK001 และมี ACCEPTED history แค่ครั้งเดียว
    async def verify_database() -> None:
        async with session_factory() as session:
            task = await session.get(ServiceRequest, request_id)

            assert task is not None
            assert task.status == RequestStatus.ASSIGNED

            histories = (
                await session.scalars(
                    select(RequestHistory).where(
                        RequestHistory.request_id == request_id,
                        RequestHistory.action == RequestAction.ACCEPTED,
                    )
                )
            ).all()

            assert len(histories) == 1
            assert histories[0].performed_by == task.assigned_staff_id

    asyncio.run(verify_database())


def test_non_housekeeper_cannot_accept_cleaning_task(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        staff_code="TECH001",
        email="technician@example.com",
        password="correct-password",
        role="technician",
        full_name="Technician One",
    )

    headers = login_staff(
        client,
        "TECH001",
        "correct-password",
    )

    created = client.post(
        "/api/v1/guest/cleaning-requests",
        data={
            "title": "พื้นเปียก",
            "description": "หน้าห้อง 201",
            "priority": "normal",
            "reporter_email": "guest@example.com",
            "location_id": "1",
        },
    )

    assert created.status_code == 201

    request_id = get_request_id(
        session_factory,
        created.json()["request_code"],
    )

    response = client.patch(
        f"/api/v1/cleaning-tasks/{request_id}/accept",
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Housekeeper access required"


def test_housekeeper_cannot_accept_nonexistent_cleaning_task(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    from uuid import uuid4

    client, session_factory = test_context

    seed_staff(
        session_factory,
        staff_code="HK001",
        email="housekeeper@example.com",
        password="correct-password",
        role="housekeeper",
        full_name="House Keeper",
    )

    headers = login_staff(
        client,
        "HK001",
        "correct-password",
    )

    response = client.patch(
        f"/api/v1/cleaning-tasks/{uuid4()}/accept",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Cleaning task not found"


def test_housekeeper_can_update_cleaning_status_in_order(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        staff_code="HK001",
        email="status-housekeeper@example.com",
        password="correct-password",
        role="housekeeper",
        full_name="House Keeper",
    )

    headers = login_staff(
        client,
        "HK001",
        "correct-password",
    )

    created = client.post(
        "/api/v1/guest/cleaning-requests",
        data={
            "title": "ทำความสะอาดพื้น",
            "description": "หน้าห้อง 201",
            "priority": "normal",
            "reporter_email": "guest@example.com",
            "location_id": "1",
        },
    )

    assert created.status_code == 201

    request_id = get_request_id(
        session_factory,
        created.json()["request_code"],
    )

    # ก่อนเปลี่ยนสถานะ Cleaner ต้องรับงานก่อน
    accepted = client.patch(
        f"/api/v1/cleaning-tasks/{request_id}/accept",
        headers=headers,
    )

    assert accepted.status_code == 200
    assert accepted.json()["status"] == "assigned"

    # assigned -> received
    received = client.patch(
        f"/api/v1/cleaning-tasks/{request_id}/status",
        headers=headers,
        json={"status": "received"},
    )

    assert received.status_code == 200
    assert received.json()["status"] == "received"

    # received -> in_progress
    in_progress = client.patch(
        f"/api/v1/cleaning-tasks/{request_id}/status",
        headers=headers,
        json={"status": "in_progress"},
    )

    assert in_progress.status_code == 200
    assert in_progress.json()["status"] == "in_progress"

    # in_progress -> completed
    completed = client.patch(
        f"/api/v1/cleaning-tasks/{request_id}/status",
        headers=headers,
        json={"status": "completed"},
    )

    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"

    # ตรวจสถานะในฐานข้อมูลจริง
    async def verify_database() -> None:
        async with session_factory() as session:
            task = await session.get(ServiceRequest, request_id)

            assert task is not None
            assert task.status == RequestStatus.COMPLETED

    asyncio.run(verify_database())


def test_housekeeper_cannot_skip_cleaning_status(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        staff_code="HK001",
        email="invalid-status-housekeeper@example.com",
        password="correct-password",
        role="housekeeper",
        full_name="House Keeper",
    )

    headers = login_staff(
        client,
        "HK001",
        "correct-password",
    )

    created = client.post(
        "/api/v1/guest/cleaning-requests",
        data={
            "title": "เก็บขยะ",
            "description": "หน้าห้อง 201",
            "priority": "normal",
            "reporter_email": "guest@example.com",
            "location_id": "1",
        },
    )

    assert created.status_code == 201

    request_id = get_request_id(
        session_factory,
        created.json()["request_code"],
    )

    accepted = client.patch(
        f"/api/v1/cleaning-tasks/{request_id}/accept",
        headers=headers,
    )

    assert accepted.status_code == 200
    assert accepted.json()["status"] == "assigned"

    # ห้ามข้าม assigned -> completed
    response = client.patch(
        f"/api/v1/cleaning-tasks/{request_id}/status",
        headers=headers,
        json={"status": "completed"},
    )

    assert response.status_code == 409

    # หลังถูกปฏิเสธ สถานะต้องยังเป็น assigned
    async def verify_database() -> None:
        async with session_factory() as session:
            task = await session.get(ServiceRequest, request_id)

            assert task is not None
            assert task.status == RequestStatus.ASSIGNED

    asyncio.run(verify_database())


def test_guest_can_view_updated_cleaning_status(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context

    seed_location(session_factory)

    seed_staff(
        session_factory,
        staff_code="HK001",
        email="progress-housekeeper@example.com",
        password="correct-password",
        role="housekeeper",
        full_name="House Keeper",
    )

    headers = login_staff(
        client,
        "HK001",
        "correct-password",
    )

    reporter_email = "guest@example.com"

    created = client.post(
        "/api/v1/guest/cleaning-requests",
        data={
            "title": "ทำความสะอาดห้อง",
            "description": "ห้อง 201",
            "priority": "normal",
            "reporter_email": reporter_email,
            "location_id": "1",
        },
    )

    assert created.status_code == 201

    request_code = created.json()["request_code"]
    request_id = get_request_id(session_factory, request_code)

    # Cleaner รับงาน
    accepted = client.patch(
        f"/api/v1/cleaning-tasks/{request_id}/accept",
        headers=headers,
    )
    assert accepted.status_code == 200

    # Cleaner เปลี่ยนเป็น received
    updated = client.patch(
        f"/api/v1/cleaning-tasks/{request_id}/status",
        headers=headers,
        json={"status": "received"},
    )

    assert updated.status_code == 200

    # Guest เข้ามาดูคำร้องของตัวเอง
    tracking = client.get(
        f"/api/v1/guest/cleaning-requests/{request_code}",
        params={"reporter_email": reporter_email},
    )

    assert tracking.status_code == 200
    assert tracking.json()["status"] == "received"

    # Cleaner เปลี่ยนต่อเป็น in_progress
    updated = client.patch(
        f"/api/v1/cleaning-tasks/{request_id}/status",
        headers=headers,
        json={"status": "in_progress"},
    )

    assert updated.status_code == 200

    # Guest ต้องเห็นสถานะล่าสุด
    tracking = client.get(
        f"/api/v1/guest/cleaning-requests/{request_code}",
        params={"reporter_email": reporter_email},
    )

    assert tracking.status_code == 200
    assert tracking.json()["status"] == "in_progress"