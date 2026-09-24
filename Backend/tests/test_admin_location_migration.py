"""ตรวจ migration ของ locations.qr_token กับข้อมูลเก่าและ rollback."""

import importlib

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
