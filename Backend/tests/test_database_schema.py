from sqlalchemy import CheckConstraint

from app.db.base import Base

EXPECTED_TABLES = {
    "staff",
    "locations",
    "service_categories",
    "service_requests",
    "request_history",
    "images",
    "lost_items",
    "lost_item_history",
    "lost_claims",
    "notifications",
}


def test_database_metadata_contains_service_management_tables() -> None:
    assert EXPECTED_TABLES == set(Base.metadata.tables)


def test_image_has_exactly_one_parent_constraint() -> None:
    image_table = Base.metadata.tables["images"]
    check_names = {
        constraint.name
        for constraint in image_table.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert "image_parent_check" in check_names


def test_lost_claim_and_history_reference_lost_items() -> None:
    claim = Base.metadata.tables["lost_claims"]
    history = Base.metadata.tables["lost_item_history"]

    claim_fk = next(iter(claim.c.found_item_id.foreign_keys))
    history_fk = next(iter(history.c.lost_item_id.foreign_keys))

    assert claim_fk.target_fullname == "lost_items.id"
    assert history_fk.target_fullname == "lost_items.id"
