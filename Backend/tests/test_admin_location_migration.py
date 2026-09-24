"""ตรวจ migration ของ locations.qr_token กับข้อมูลเก่าและ rollback."""

import importlib
from uuid import uuid4

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


def test_location_qr_token_nullable_migration_round_trip(tmp_path) -> None:
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'migration.db'}")
    metadata = sa.MetaData()
    locations = sa.Table(
        "locations",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("qr_token", sa.String(255), unique=True, nullable=False),
    )
    metadata.create_all(engine)
    migration = importlib.import_module(
        "migrations.versions.20260923_0010_make_location_qr_token_nullable"
    )

    with engine.begin() as connection:
        connection.execute(locations.insert().values(id=1, qr_token="existing-token"))
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()
        assert next(
            column
            for column in sa.inspect(connection).get_columns("locations")
            if column["name"] == "qr_token"
        )["nullable"]
        connection.execute(
            sa.text("INSERT INTO locations (id, qr_token) VALUES (2, NULL), (3, NULL)")
        )
        migration.downgrade()
        assert not next(
            column
            for column in sa.inspect(connection).get_columns("locations")
            if column["name"] == "qr_token"
        )["nullable"]
        tokens = (
            connection.execute(sa.text("SELECT qr_token FROM locations ORDER BY id"))
            .scalars()
            .all()
        )
        assert tokens[0] == "existing-token"
        assert len(set(tokens)) == 3
        assert all(tokens)
    engine.dispose()


def _floor_migration_table(tmp_path, name: str):
    engine = sa.create_engine(f"sqlite:///{tmp_path / name}")
    metadata = sa.MetaData()
    locations = sa.Table(
        "locations",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("floor", sa.String(30), nullable=True),
        sa.Column("area", sa.String(100), nullable=False),
    )
    metadata.create_all(engine)
    migration = importlib.import_module(
        "migrations.versions.20260924_0011_normalize_location_floor"
    )
    return engine, locations, migration


def test_location_floor_migration_normalizes_and_indexes(tmp_path) -> None:
    engine, locations, migration = _floor_migration_table(tmp_path, "floor.db")
    with engine.begin() as connection:
        connection.execute(
            locations.insert(),
            [
                {"id": 1, "floor": "01", "area": "ห้อง 101"},
                {"id": 2, "floor": "ชั้น 3", "area": "ห้อง 301"},
                {"id": 3, "floor": None, "area": "โถง"},
            ],
        )
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()
        floors = (
            connection.execute(sa.text("SELECT floor FROM locations ORDER BY id")).scalars().all()
        )
        assert floors == ["1", "3", None]
        with pytest.raises(sa.exc.IntegrityError), connection.begin_nested():
            connection.execute(locations.insert().values(id=4, floor=None, area="โถง"))
        migration.downgrade()
        connection.execute(locations.insert().values(id=4, floor=None, area="โถง"))
    engine.dispose()


def test_location_floor_migration_stops_on_duplicates(tmp_path) -> None:
    engine, locations, migration = _floor_migration_table(tmp_path, "floor-duplicate.db")
    with engine.begin() as connection:
        connection.execute(
            locations.insert(),
            [
                {"id": 1, "floor": "1", "area": "ห้อง 101"},
                {"id": 2, "floor": "ชั้น 1", "area": "ห้อง 101"},
            ],
        )
        migration.op = Operations(MigrationContext.configure(connection))
        with pytest.raises(RuntimeError, match="ห้อง 101"):
            migration.upgrade()
    engine.dispose()


def _staff_migration_table(tmp_path, name: str):
    engine = sa.create_engine(f"sqlite:///{tmp_path / name}")
    metadata = sa.MetaData()
    staff = sa.Table(
        "staff",
        metadata,
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("staff_code", sa.String(30), nullable=False),
        sa.Index("ix_staff_staff_code", "staff_code", unique=True),
    )
    metadata.create_all(engine)
    migration = importlib.import_module("migrations.versions.20260924_0012_drop_staff_code")
    return engine, staff, migration


def test_drop_staff_code_migration_round_trip(tmp_path) -> None:
    engine, staff, migration = _staff_migration_table(tmp_path, "staff.db")
    with engine.begin() as connection:
        connection.execute(
            staff.insert(),
            [
                {"id": uuid4(), "email": "Admin@Example.com", "staff_code": "ADMIN001"},
                {"id": uuid4(), "email": "hk@example.com", "staff_code": "HK001"},
            ],
        )
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()
        columns = {column["name"] for column in sa.inspect(connection).get_columns("staff")}
        assert "staff_code" not in columns
        emails = connection.execute(sa.text("SELECT email FROM staff ORDER BY email")).scalars()
        assert list(emails) == ["admin@example.com", "hk@example.com"]

        migration.downgrade()
        codes = connection.execute(sa.text("SELECT staff_code FROM staff")).scalars().all()
        assert len(set(codes)) == 2
        assert all(code.startswith("STAFF-") for code in codes)
    engine.dispose()


def test_drop_staff_code_migration_stops_on_case_duplicate_emails(tmp_path) -> None:
    engine, staff, migration = _staff_migration_table(tmp_path, "staff-duplicate.db")
    with engine.begin() as connection:
        connection.execute(
            staff.insert(),
            [
                {"id": uuid4(), "email": "a@example.com", "staff_code": "A1"},
                {"id": uuid4(), "email": "A@example.com", "staff_code": "A2"},
            ],
        )
        migration.op = Operations(MigrationContext.configure(connection))
        with pytest.raises(RuntimeError, match="a@example.com"):
            migration.upgrade()
    engine.dispose()
