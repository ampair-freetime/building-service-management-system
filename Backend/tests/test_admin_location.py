"""ทดสอบ Admin location และวงจรชีวิตของ QR."""

import asyncio
from io import BytesIO
from urllib.parse import quote
from zipfile import ZipFile

import pytest
from conftest import seed_staff
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.location import Location
from app.schemas.admin_location import normalize_floor
from app.services import admin_location
from app.services.admin_location import build_qr_url


def admin_headers(client: TestClient, factory: async_sessionmaker[AsyncSession]) -> dict[str, str]:
    seed_staff(
        factory,
        email="admin@example.com",
        password="admin-password",
        role="admin",
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": "admin@example.com", "password": "admin-password"},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def create_location(client: TestClient, headers: dict[str, str], **changes) -> dict:
    payload = {"floor": "1", "area": "ห้อง 101", **changes}
    response = client.post("/api/v1/admin/locations", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_generate_and_guest_scan(test_context) -> None:
    client, factory = test_context
    headers = admin_headers(client, factory)
    location = create_location(client, headers)
    assert location["qr_token"] is None
    assert location["qr_url"] is None
    assert location["label"] == "ชั้น 1 ห้อง 101"
    assert location["is_active"] is True

    guest = client.get("/api/v1/guest/cleaning-requests/locations")
    assert [item["id"] for item in guest.json()] == [location["id"]]
    assert "qr_token" not in guest.json()[0]

    path = f"/api/v1/admin/locations/{location['id']}"
    first = client.post(f"{path}/qr/generate", headers=headers)
    second = client.post(f"{path}/qr/generate", headers=headers)
    assert first.status_code == second.status_code == 200
    token = first.json()["qr_token"]
    assert len(token) >= 20
    assert second.json()["qr_token"] == token
    assert first.json()["qr_url"].endswith(f"/user?token={token}")
    assert client.get(f"{path}/qr", headers=headers).status_code == 200

    scanned = client.get(f"/api/v1/guest/cleaning-requests/locations/by-qr/{token}")
    assert scanned.status_code == 200
    assert scanned.json()["id"] == location["id"]
    assert "qr_token" not in scanned.json()


def test_qr_image_bundle_and_regeneration(test_context) -> None:
    client, factory = test_context
    headers = admin_headers(client, factory)
    one = create_location(client, headers)
    two = create_location(client, headers, area="ห้อง 102")
    one_path = f"/api/v1/admin/locations/{one['id']}"
    two_path = f"/api/v1/admin/locations/{two['id']}"
    old_token = client.post(f"{one_path}/qr/generate", headers=headers).json()["qr_token"]
    other_token = client.post(f"{two_path}/qr/generate", headers=headers).json()["qr_token"]
    assert old_token != other_token

    png = client.get(f"{one_path}/qr", headers=headers)
    assert png.status_code == 200
    assert png.headers["content-type"] == "image/png"
    assert png.content.startswith(b"\x89PNG\r\n\x1a\n")
    assert "attachment" in png.headers["content-disposition"]
    assert png.headers["cache-control"] == "no-store"

    svg = client.get(f"{one_path}/qr?format=svg&download=false", headers=headers)
    assert svg.status_code == 200
    assert svg.headers["content-type"] == "image/svg+xml"
    assert b"<svg" in svg.content
    assert "inline" in svg.headers["content-disposition"]
    assert client.get(f"{one_path}/qr?format=gif", headers=headers).status_code == 422

    bundle = client.get(
        "/api/v1/admin/locations/qr-bundle",
        headers=headers,
        params=[("ids", one["id"]), ("ids", two["id"])],
    )
    assert bundle.status_code == 200
    assert bundle.headers["content-type"] == "application/zip"
    with ZipFile(BytesIO(bundle.content)) as archive:
        assert set(archive.namelist()) == {
            f"location-{one['id']}-qr.png",
            f"location-{two['id']}-qr.png",
        }
        assert all(archive.read(name).startswith(b"\x89PNG") for name in archive.namelist())

    changed = client.post(f"{one_path}/qr/regenerate", headers=headers)
    assert changed.status_code == 200
    new_token = changed.json()["qr_token"]
    assert new_token != old_token
    assert (
        client.get(f"/api/v1/guest/cleaning-requests/locations/by-qr/{old_token}").status_code
        == 404
    )
    assert (
        client.get(f"/api/v1/guest/cleaning-requests/locations/by-qr/{new_token}").status_code
        == 200
    )


def test_duplicate_and_update_validation(test_context) -> None:
    client, factory = test_context
    headers = admin_headers(client, factory)
    one = create_location(client, headers, floor=None, area="โถง")
    duplicate = client.post(
        "/api/v1/admin/locations",
        headers=headers,
        json={"floor": "", "area": "  โถง  "},
    )
    assert duplicate.status_code == 409

    create_location(client, headers, floor="2", area="ห้อง 201")
    spaced_duplicate = client.post(
        "/api/v1/admin/locations",
        headers=headers,
        json={"floor": "2", "area": "  ห้อง   201 "},
    )
    assert spaced_duplicate.status_code == 409
    listing = client.get("/api/v1/admin/locations", headers=headers)
    assert len(listing.json()) == 2

    second = create_location(client, headers, floor="2", area="ห้อง 202")
    second_path = f"/api/v1/admin/locations/{second['id']}"
    assert (
        client.patch(second_path, headers=headers, json={"floor": None, "area": "โถง"}).status_code
        == 409
    )
    for invalid in ({"area": None}, {"area": "   "}, {"area": "x" * 101}):
        assert client.patch(second_path, headers=headers, json=invalid).status_code == 422
    assert (
        client.post("/api/v1/admin/locations", headers=headers, json={"area": "   "}).status_code
        == 422
    )

    updated = client.patch(second_path, headers=headers, json={"floor": None})
    assert updated.status_code == 200
    assert updated.json()["floor"] is None
    assert updated.json()["area"] == "ห้อง 202"
    assert client.get(f"/api/v1/admin/locations/{one['id']}", headers=headers).status_code == 200


def test_blank_floor_create_starts_without_qr(test_context) -> None:
    client, factory = test_context
    headers = admin_headers(client, factory)
    location = create_location(client, headers, floor="", area="  โถง  ")
    assert location["floor"] is None
    assert location["area"] == "โถง"
    assert location["qr_token"] is None and location["qr_url"] is None


def test_bulk_create_endpoint_is_removed(test_context) -> None:
    client, factory = test_context
    headers = admin_headers(client, factory)
    response = client.post(
        "/api/v1/admin/locations/bulk",
        headers=headers,
        json={"locations": [{"floor": "1", "area": "ห้อง 101"}]},
    )
    assert response.status_code in {404, 405}
    assert client.get("/api/v1/admin/locations", headers=headers).json() == []


def test_inactive_missing_and_ungenerated_qr(test_context) -> None:
    client, factory = test_context
    headers = admin_headers(client, factory)
    location = create_location(client, headers)
    path = f"/api/v1/admin/locations/{location['id']}"
    assert client.get(f"{path}/qr", headers=headers).status_code == 409
    assert (
        client.get(
            "/api/v1/admin/locations/qr-bundle", headers=headers, params={"ids": location["id"]}
        ).status_code
        == 409
    )
    not_generated = client.post(f"{path}/qr/regenerate", headers=headers)
    assert not_generated.status_code == 409
    assert not_generated.json()["detail"] == "QR has not been generated for this location"
    assert (
        client.post("/api/v1/admin/locations/999/qr/generate", headers=headers).status_code == 404
    )

    token = client.post(f"{path}/qr/generate", headers=headers).json()["qr_token"]
    disabled = client.patch(f"{path}/status", headers=headers, json={"is_active": False})
    assert disabled.status_code == 200
    assert client.get("/api/v1/admin/locations", headers=headers).json() == []
    assert (
        len(client.get("/api/v1/admin/locations?include_inactive=true", headers=headers).json())
        == 1
    )
    assert client.get(f"{path}/qr", headers=headers).status_code == 409
    assert client.post(f"{path}/qr/generate", headers=headers).status_code == 409
    assert client.post(f"{path}/qr/regenerate", headers=headers).status_code == 409
    assert client.get(f"/api/v1/guest/cleaning-requests/locations/by-qr/{token}").status_code == 404
    restored = client.patch(f"{path}/status", headers=headers, json={"is_active": True})
    assert restored.status_code == 200
    assert restored.json()["qr_token"] == token


def test_admin_authorization_and_qr_url_escaping(test_context) -> None:
    client, factory = test_context
    seed_staff(
        factory,
        email="tech@example.com",
        password="tech-password",
        role="technician",
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": "tech@example.com", "password": "tech-password"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.get("/api/v1/admin/locations").status_code == 401
    assert (
        client.post(
            "/api/v1/admin/locations", headers=headers, json={"area": "ห้อง 101"}
        ).status_code
        == 403
    )
    assert (
        client.get(
            "/api/v1/admin/locations/qr-bundle", headers=headers, params={"ids": 1}
        ).status_code
        == 403
    )
    assert build_qr_url("a/b +?", "https://example.com/app/") == (
        "https://example.com/app/user?token=" + quote("a/b +?", safe="")
    )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, None),
        ("", None),
        ("   ", None),
        ("1", "1"),
        ("01", "1"),
        (" 1 ", "1"),
        ("ชั้น 1", "1"),
        ("ชั้น1", "1"),
        ("ชั้น   01", "1"),
        ("Floor 2", "2"),
        ("fl.2", "2"),
        ("0", "0"),
        ("b1", "B1"),
        ("ชั้น B1", "B1"),
        ("ชั้นใต้ดิน", "ใต้ดิน"),
        ("๑", "1"),
        ("Flat", "FLAT"),
    ],
)
def test_normalize_floor(raw, expected) -> None:
    assert normalize_floor(raw) == expected


def test_normalize_floor_rejects_prefix_only() -> None:
    with pytest.raises(ValueError):
        normalize_floor("ชั้น")


def test_equivalent_floors_are_duplicates(test_context) -> None:
    client, factory = test_context
    headers = admin_headers(client, factory)
    first = create_location(client, headers, floor="ชั้น 01", area="ห้อง 101")
    assert first["floor"] == "1"
    assert first["label"] == "ชั้น 1 ห้อง 101"

    duplicate = client.post(
        "/api/v1/admin/locations", headers=headers, json={"floor": "1", "area": "ห้อง 101"}
    )
    assert duplicate.status_code == 409

    create_location(client, headers, floor="2", area="ห้อง 201")
    no_space_prefix = client.post(
        "/api/v1/admin/locations", headers=headers, json={"floor": "ชั้น2", "area": "ห้อง 201"}
    )
    assert no_space_prefix.status_code == 409

    second = create_location(client, headers, floor="3", area="ห้อง 101")
    moved = client.patch(
        f"/api/v1/admin/locations/{second['id']}", headers=headers, json={"floor": "ชั้น 1"}
    )
    assert moved.status_code == 409
    assert (
        client.post(
            "/api/v1/admin/locations", headers=headers, json={"floor": "ชั้น", "area": "โถง"}
        ).status_code
        == 422
    )
    assert len(client.get("/api/v1/admin/locations", headers=headers).json()) == 3


def test_database_rejects_duplicate_location_with_null_floor(test_context) -> None:
    _, factory = test_context

    async def insert_twice() -> None:
        async with factory() as session:
            session.add_all([Location(floor=None, area="โถง"), Location(floor=None, area="โถง")])
            await session.commit()

    with pytest.raises(IntegrityError):
        asyncio.run(insert_twice())


def test_concurrent_duplicate_returns_conflict(test_context, monkeypatch) -> None:
    client, factory = test_context
    headers = admin_headers(client, factory)
    create_location(client, headers)

    async def never_duplicate(*args, **kwargs) -> bool:
        # จำลองคำขอที่สองซึ่ง SELECT ก่อนคำขอแรก commit จึงไม่เห็นแถวซ้ำ
        return False

    monkeypatch.setattr(admin_location, "_duplicate_exists", never_duplicate)
    response = client.post(
        "/api/v1/admin/locations", headers=headers, json={"floor": "1", "area": "ห้อง 101"}
    )
    assert response.status_code == 409
