"""Read-only SMTP and R2 connectivity checks from the deployment host."""

import smtplib
import ssl
import sys
from pathlib import Path

from botocore.exceptions import BotoCoreError, ClientError

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))


def main() -> int:
    from app.core.config import settings
    from app.services.object_storage import ObjectStorage, StorageConfigurationError

    ready = True
    if not settings.smtp_host:
        print("SMTP: NOT_CONFIGURED")
        ready = False
    else:
        try:
            options = {
                "host": settings.smtp_host,
                "port": settings.smtp_port,
                "timeout": settings.smtp_timeout_seconds,
            }
            if settings.smtp_use_ssl:
                connection = smtplib.SMTP_SSL(**options, context=ssl.create_default_context())
            else:
                connection = smtplib.SMTP(**options)
            with connection as client:
                client.ehlo()
                if settings.smtp_use_starttls and not settings.smtp_use_ssl:
                    client.starttls(context=ssl.create_default_context())
                    client.ehlo()
                if settings.smtp_username:
                    client.login(settings.smtp_username, settings.smtp_password or "")
            print("SMTP: CONNECTIVITY_OK (no email sent)")
        except (OSError, smtplib.SMTPException) as exc:
            print(f"SMTP: FAILED ({type(exc).__name__})")
            ready = False

    try:
        storage = ObjectStorage(settings)
        storage._client.head_bucket(Bucket=storage.bucket_name)
        print("R2: BUCKET_ACCESS_OK (upload/delete not tested)")
    except (StorageConfigurationError, BotoCoreError, ClientError) as exc:
        print(f"R2: FAILED ({type(exc).__name__})")
        ready = False
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
