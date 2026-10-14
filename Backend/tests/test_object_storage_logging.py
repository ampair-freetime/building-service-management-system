"""R2 failures must leave a reason in the logs, without credentials."""

import asyncio
import logging

import pytest
from botocore.exceptions import ClientError, EndpointConnectionError

from app.core.config import Settings
from app.services.object_storage import ObjectStorage, StorageOperationError


def _storage() -> ObjectStorage:
    return ObjectStorage(
        Settings(
            r2_account_id="account",
            r2_access_key_id="key-id",
            r2_secret_access_key="very-secret-value",
            r2_bucket_name="bucket",
        )
    )


@pytest.mark.parametrize(
    ("error", "reason"),
    [
        (
            ClientError({"Error": {"Code": "AccessDenied", "Message": "x"}}, "PutObject"),
            "ClientError AccessDenied",
        ),
        (EndpointConnectionError(endpoint_url="https://r2.invalid"), "EndpointConnectionError"),
    ],
)
def test_upload_failure_is_logged(monkeypatch, caplog, error, reason):
    storage = _storage()

    def fail(**_):
        raise error

    monkeypatch.setattr(storage._client, "put_object", fail)
    with (
        caplog.at_level(logging.WARNING, logger="app.services.object_storage"),
        pytest.raises(StorageOperationError),
    ):
        asyncio.run(storage.put(object_key="k", data=b"x", content_type="image/webp"))
    assert f"R2 upload failed: {reason}" in caplog.text
    assert "very-secret-value" not in caplog.text
