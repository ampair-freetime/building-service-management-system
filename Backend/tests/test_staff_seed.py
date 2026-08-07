from importlib import import_module

from app.core.security import verify_password


def test_initial_staff_seed_uses_expected_development_password() -> None:
    seed = import_module("migrations.versions.20260807_0002_seed_initial_staff")

    assert seed.INITIAL_ADMIN_EMPLOYEE_CODE == "ADMIN001"
    assert seed.INITIAL_ADMIN_EMAIL == "admin@example.com"
    assert verify_password("Admin@1234", seed.INITIAL_ADMIN_PASSWORD_HASH)
    assert not verify_password("wrong-password", seed.INITIAL_ADMIN_PASSWORD_HASH)
