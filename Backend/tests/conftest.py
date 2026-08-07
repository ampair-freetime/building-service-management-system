import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.base import Base
from app.db.session import get_db_session
from app.main import create_application
from app.models.staff_account import StaffAccount
from app.schemas.staff import StaffCreate
from app.services.staff import create_staff


@pytest.fixture
def test_context(
    tmp_path: Path,
) -> tuple[TestClient, async_sessionmaker[AsyncSession]]:
    database_path = tmp_path / "test.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{database_path}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def create_schema() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    asyncio.run(create_schema())

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    application = create_application()
    application.dependency_overrides[get_db_session] = override_db_session

    with TestClient(application) as client:
        yield client, session_factory

    application.dependency_overrides.clear()
    asyncio.run(engine.dispose())


def seed_staff(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    employee_code: str,
    email: str,
    password: str,
    role: str,
    full_name: str = "Test Staff",
    is_active: bool = True,
) -> StaffAccount:
    async def seed() -> StaffAccount:
        async with session_factory() as session:
            return await create_staff(
                session,
                StaffCreate(
                    employee_code=employee_code,
                    email=email,
                    full_name=full_name,
                    password=password,
                    role=role,
                    is_active=is_active,
                ),
            )

    return asyncio.run(seed())
