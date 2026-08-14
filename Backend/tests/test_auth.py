from conftest import seed_staff
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


def test_login_by_email_and_read_current_staff(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context
    seed_staff(
        session_factory,
        staff_code="TECH001",
        email="tech@example.com",
        password="correct-password",
        role="technician",
        full_name="Technical Staff",
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": "TECH@EXAMPLE.COM", "password": "correct-password"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["staff"]["staff_code"] == "TECH001"
    assert body["staff"]["role"] == "technician"
    assert "password" not in body["staff"]
    assert "password_hash" not in body["staff"]

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "tech@example.com"


def test_login_by_staff_code_and_reject_invalid_credentials(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context
    seed_staff(
        session_factory,
        staff_code="HK001",
        email="housekeeper@example.com",
        password="correct-password",
        role="housekeeper",
    )

    successful = client.post(
        "/api/v1/auth/login",
        json={"identifier": "hk001", "password": "correct-password"},
    )
    rejected = client.post(
        "/api/v1/auth/login",
        json={"identifier": "HK001", "password": "wrong-password"},
    )
    missing_token = client.get("/api/v1/auth/me")

    assert successful.status_code == 200
    assert successful.json()["staff"]["role"] == "housekeeper"
    assert rejected.status_code == 401
    assert rejected.json()["detail"] == "Incorrect identifier or password"
    assert missing_token.status_code == 401


def test_suspended_staff_cannot_login(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context
    seed_staff(
        session_factory,
        staff_code="CLERK001",
        email="clerk@example.com",
        password="correct-password",
        role="administrative",
        status="suspended",
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": "CLERK001", "password": "correct-password"},
    )

    assert response.status_code == 401


def test_admin_can_create_and_list_all_staff_roles(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context
    seed_staff(
        session_factory,
        staff_code="ADMIN001",
        email="admin@example.com",
        password="admin-password",
        role="admin",
        full_name="System Admin",
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": "ADMIN001", "password": "admin-password"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    new_staff = [
        ("HK001", "housekeeper@example.com", "House Keeper", "housekeeper"),
        ("TECH001", "technician@example.com", "Technician", "technician"),
        ("ADMINISTRATIVE001", "administrative@example.com", "Administrative Staff", "administrative"),
    ]
    for staff_code, email, full_name, role in new_staff:
        response = client.post(
            "/api/v1/staff",
            headers=headers,
            json={
                "staff_code": staff_code,
                "email": email,
                "full_name": full_name,
                "password": "staff-password",
                "role": role,
            },
        )
        assert response.status_code == 201

    list_response = client.get("/api/v1/staff", headers=headers)
    assert list_response.status_code == 200
    assert {staff["role"] for staff in list_response.json()} == {
        "housekeeper",
        "technician",
        "administrative",
        "admin",
    }

    duplicate = client.post(
        "/api/v1/staff",
        headers=headers,
        json={
            "staff_code": "HK001",
            "email": "another@example.com",
            "full_name": "Duplicate Staff",
            "password": "staff-password",
            "role": "housekeeper",
        },
    )
    assert duplicate.status_code == 409


def test_non_admin_cannot_manage_staff(
    test_context: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = test_context
    seed_staff(
        session_factory,
        staff_code="TECH001",
        email="tech@example.com",
        password="staff-password",
        role="technician",
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": "TECH001", "password": "staff-password"},
    )

    response = client.get(
        "/api/v1/staff",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Administrator access required"
