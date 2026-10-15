"""กฎสถานะของคำขอรับของคืนที่อยู่ใน services/claim_lifecycle.py (ทดสอบผ่าน HTTP API)."""

import pytest
from test_lost_found_clerk import (
    _claim,
    _clerk_headers,
    _item_status,
    _seed_claim,
    _seed_item,
)

from app.models.enums import ClaimStatus, LostStatus, LostType, ReturnStatus
from app.services.claim_lifecycle import allowed_actions

BASE = "/api/v1/lost-found/ownership-requests"


@pytest.fixture
def sent_emails(monkeypatch):
    emails = []

    async def fake_email(**kwargs):
        emails.append(kwargs)

    monkeypatch.setattr("app.services.claim_notifications.send_email", fake_email)
    return emails


def _approved_claim(client, session_factory, headers):
    item_id = _seed_item(session_factory, report_type=LostType.FOUND, status=LostStatus.APPROVED)
    claim_id = _seed_claim(session_factory, item_id, email="owner@example.com")
    assert client.post(f"{BASE}/{claim_id}/approve", headers=headers).status_code == 200
    return item_id, claim_id


@pytest.mark.parametrize(
    "status, expected",
    [
        (ClaimStatus.PENDING, {"approve", "request_additional_info", "reject"}),
        (ClaimStatus.ADDITIONAL_INFO_REQUIRED, {"approve", "request_additional_info", "reject"}),
        (ClaimStatus.APPROVED, {"schedule_pickup", "update_return_status", "release"}),
        (ClaimStatus.SCHEDULED, {"schedule_pickup", "update_return_status", "release"}),
        (ClaimStatus.REJECTED, set()),
        (ClaimStatus.COMPLETED, set()),
    ],
)
def test_allowed_actions_table(status, expected):
    assert set(allowed_actions(status)) == expected


def test_responses_carry_allowed_actions(test_context, sent_emails):
    client, session_factory = test_context
    headers = _clerk_headers(client, session_factory)
    item_id = _seed_item(session_factory, report_type=LostType.FOUND, status=LostStatus.APPROVED)
    claim_id = _seed_claim(session_factory, item_id, email="owner@example.com")

    detail = client.get(f"{BASE}/{claim_id}", headers=headers).json()
    assert "approve" in detail["allowed_actions"]

    approved = client.post(f"{BASE}/{claim_id}/approve", headers=headers).json()
    assert set(approved["allowed_actions"]) == {"schedule_pickup", "update_return_status", "release"}


def test_unknown_claim_is_404_and_wrong_status_is_409(test_context, sent_emails):
    client, session_factory = test_context
    headers = _clerk_headers(client, session_factory)
    _, claim_id = _approved_claim(client, session_factory, headers)

    missing = "00000000-0000-0000-0000-000000000000"
    assert client.post(f"{BASE}/{missing}/approve", headers=headers).status_code == 404
    # อนุมัติแล้ว: approve / ขอข้อมูลเพิ่ม / ปฏิเสธซ้ำ ต้องได้ 409 เหมือนกันทุกคำสั่ง
    assert client.post(f"{BASE}/{claim_id}/approve", headers=headers).status_code == 409
    assert (
        client.post(
            f"{BASE}/{claim_id}/request-additional-info",
            headers=headers,
            json={"message": "more"},
        ).status_code
        == 409
    )
    assert (
        client.post(f"{BASE}/{claim_id}/reject", headers=headers, json={"reason": "x"}).status_code
        == 409
    )


def test_request_additional_info_emails_claimant_with_tracking_link(test_context, sent_emails):
    client, session_factory = test_context
    headers = _clerk_headers(client, session_factory)
    item_id = _seed_item(session_factory, report_type=LostType.FOUND, status=LostStatus.APPROVED)
    claim_id = _seed_claim(session_factory, item_id, email="owner@example.com")

    response = client.post(
        f"{BASE}/{claim_id}/request-additional-info",
        headers=headers,
        json={"message": "กรุณาส่งรูปใบเสร็จ"},
    )

    assert response.status_code == 200
    assert len(sent_emails) == 1
    email = sent_emails[0]
    assert email["recipient"] == "owner@example.com"
    assert "กรุณาส่งรูปใบเสร็จ" in email["body"]
    claim_code = _claim(session_factory, claim_id).claim_code
    assert f"track={claim_code}" in email["body"]


def test_release_reopens_claimed_item_for_other_claimants(test_context, sent_emails):
    client, session_factory = test_context
    headers = _clerk_headers(client, session_factory)
    item_id, claim_id = _approved_claim(client, session_factory, headers)
    assert _item_status(session_factory, item_id) == LostStatus.CLAIMED

    response = client.post(
        f"{BASE}/{claim_id}/release", headers=headers, json={"reason": "ไม่มารับตามนัด"}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert response.json()["email_sent"] is True
    assert _claim(session_factory, claim_id).review_note == "ไม่มารับตามนัด"
    # ของกลับไปแสดงบนหน้า guest และมีคนอื่นยื่นคำขอใหม่ได้
    assert _item_status(session_factory, item_id) == LostStatus.APPROVED
    assert "ไม่มารับตามนัด" in sent_emails[-1]["body"]
    # release ซ้ำไม่ได้ เพราะคำขอไม่ได้อยู่ในสถานะอนุมัติแล้ว
    again = client.post(f"{BASE}/{claim_id}/release", headers=headers, json={"reason": "x"})
    assert again.status_code == 409


def test_release_is_refused_for_pending_and_completed_claims(test_context, sent_emails):
    client, session_factory = test_context
    headers = _clerk_headers(client, session_factory)
    item_id = _seed_item(session_factory, report_type=LostType.FOUND, status=LostStatus.APPROVED)
    pending_id = _seed_claim(session_factory, item_id, email="pending@example.com")
    assert (
        client.post(f"{BASE}/{pending_id}/release", headers=headers, json={"reason": "x"}).status_code
        == 409
    )

    _, claim_id = _approved_claim(client, session_factory, headers)
    returned = client.patch(
        f"{BASE}/{claim_id}/return-status",
        headers=headers,
        json={"return_status": ReturnStatus.RETURNED.value},
    )
    assert returned.status_code == 200
    assert (
        client.post(f"{BASE}/{claim_id}/release", headers=headers, json={"reason": "x"}).status_code
        == 409
    )
