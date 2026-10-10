"""Run migration against a temporary PostgreSQL table, never application rows."""

import importlib
import os
import subprocess
from io import StringIO

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations


def test_claim_code_migration_backfills_and_downgrades():
    container = os.environ.get("TEST_POSTGRES_CONTAINER")
    if not container:
        pytest.skip("Set TEST_POSTGRES_CONTAINER to test against a local PostgreSQL container")
    migration = importlib.import_module("migrations.versions.20261008_0021_claim_tracking")

    def sql_for(action):
        output = StringIO()
        migration.op = Operations(
            MigrationContext.configure(
                dialect_name="postgresql",
                opts={
                    "as_sql": True,
                    "output_buffer": output,
                },
            )
        )
        action()
        return output.getvalue()

    sql = (
        """
    BEGIN;
    CREATE TEMP TABLE lost_claims (
        id uuid PRIMARY KEY, created_at timestamptz NOT NULL, status text,
        review_note text
    );
    SET LOCAL search_path TO pg_temp;
    INSERT INTO lost_claims VALUES
      ('12345678-0000-4000-8000-000000000001', '2026-10-07 18:00:00+00', 'additional_info_required', 'Describe proof'),
      ('12345678-0000-4000-8000-000000000002', '2026-10-07 18:00:00+00', 'approved', 'Internal note');
    """
        + sql_for(migration.upgrade)
        + """
    DO $$ BEGIN
      IF (SELECT count(DISTINCT claim_code) FROM lost_claims) <> 2 THEN
        RAISE EXCEPTION 'Backfill must be unique'; END IF;
      IF EXISTS (SELECT 1 FROM lost_claims WHERE claim_code NOT LIKE 'CLM-20261008-12345678%') THEN
        RAISE EXCEPTION 'Wrong Bangkok date'; END IF;
      IF EXISTS (SELECT 1 FROM lost_claims WHERE status='approved' AND staff_message IS NOT NULL) THEN
        RAISE EXCEPTION 'Internal note leaked'; END IF;
      IF NOT EXISTS (SELECT 1 FROM lost_claims WHERE staff_message='Describe proof') THEN
        RAISE EXCEPTION 'Missing guest message'; END IF;
      BEGIN
        UPDATE lost_claims SET claim_code = NULL;
        RAISE EXCEPTION 'NULL code allowed';
      EXCEPTION WHEN not_null_violation THEN NULL; END;
      BEGIN
        UPDATE lost_claims SET claim_code = 'duplicate';
        RAISE EXCEPTION 'Duplicate code allowed';
      EXCEPTION WHEN unique_violation THEN NULL; END;
    END $$;
    """
        + sql_for(migration.downgrade)
        + """
    DO $$ BEGIN
      IF (SELECT count(*) FROM lost_claims) <> 2 THEN
        RAISE EXCEPTION 'Downgrade lost rows'; END IF;
    END $$;
    ROLLBACK;
    """
    )
    result = subprocess.run(
        [
            "docker",
            "exec",
            "-i",
            container,
            "sh",
            "-c",
            'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"',
        ],
        input=sql,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
