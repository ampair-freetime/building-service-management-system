"""Regression tests for cwd-independent settings and production URL validation."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.services.object_storage import ObjectStorage, StorageConfigurationError


def test_shared_dotenv_and_environment_precedence(tmp_path, monkeypatch):
    dotenv = tmp_path / ".env"
    dotenv.write_text(
        "POSTGRES_DB=shared\nVITE_API_BASE_URL=/api/v1\n"
        "PUBLIC_BASE_URL=https://care.example.org\n"
        "SMTP_HOST=relay.example.org\nSMTP_PORT=587\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SMTP_PORT", "2525")
    configuration = Settings(_env_file=dotenv)
    assert configuration.smtp_port == 2525
    assert configuration.staff_activation_url == "https://care.example.org/staff/setup-password"


def test_explicit_dotenv_works_from_another_working_directory(tmp_path):
    dotenv = tmp_path / "backend.env"
    dotenv.write_text("SMTP_HOST=relay.example.org\nPOSTGRES_DB=shared\n", encoding="utf-8")
    environment = {**os.environ, "BSMS_ENV_FILE": str(dotenv)}
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from app.core.config import settings; assert settings.smtp_host == 'relay.example.org'",
        ],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "overrides",
    [
        {"jwt_secret_key": "development-only-change-this-secret"},
        {"image_url_secret": "development-only-change-this-image-secret"},
        {"image_url_secret": "too-short"},
        {"public_base_url": "http://localhost:5173"},
        {"staff_activation_url": "http://127.0.0.1:5173/staff/setup-password"},
        {"backend_cors_origins": ["*"]},
    ],
)
def test_production_rejects_development_configuration(overrides):
    values = {
        "environment": "production",
        "jwt_secret_key": "test-key-" * 8,
        "image_url_secret": "test-image-key-" * 4,
        "public_base_url": "https://care.example.org",
        "backend_cors_origins": ["https://care.example.org"],
        **overrides,
    }
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **values)


@pytest.mark.parametrize(
    "overrides",
    [
        {"smtp_use_ssl": True, "smtp_use_starttls": True},
        {"smtp_username": "user", "smtp_password": None},
        {"r2_total_max_attempts": 0},
        {"max_image_processing_concurrency": 0},
        {"r2_presigned_url_expire_seconds": 604801},
    ],
)
def test_invalid_transport_and_resource_limits_are_rejected(overrides):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **overrides)


def test_storage_configures_bounded_retries_and_timeout(monkeypatch):
    options = {}

    def client(service, **kwargs):
        assert service == "s3"
        options.update(kwargs)
        return object()

    monkeypatch.setattr("app.services.object_storage.boto3.client", client)
    ObjectStorage(
        Settings(
            _env_file=None,
            r2_account_id="test-account",
            r2_access_key_id="test-key",
            r2_secret_access_key="test-secret",
            r2_bucket_name="test-bucket",
            r2_connect_timeout_seconds=3,
            r2_read_timeout_seconds=7,
            r2_total_max_attempts=2,
        )
    )
    configuration = options["config"]
    assert configuration.connect_timeout == 3
    assert configuration.read_timeout == 7
    assert configuration.retries == {"mode": "standard", "total_max_attempts": 2}
    assert options["endpoint_url"] == "https://test-account.r2.cloudflarestorage.com"


def test_missing_storage_configuration_does_not_construct_network_client(monkeypatch):
    def unexpected_client(*args, **kwargs):
        pytest.fail("Missing credentials must fail before constructing a client")

    monkeypatch.setattr("app.services.object_storage.boto3.client", unexpected_client)
    with pytest.raises(StorageConfigurationError):
        ObjectStorage(Settings(_env_file=None))
