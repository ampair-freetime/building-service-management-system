import argparse
import asyncio
import re

import pytest
from sqlalchemy import func, select

from app.models.location import Location
from scripts import seed_locations as location_seed


def test_normalize_base_url() -> None:
    assert (
        location_seed.normalize_base_url(" https://example.com/app/ ") == "https://example.com/app"
    )
    with pytest.raises(argparse.ArgumentTypeError):
        location_seed.normalize_base_url("javascript:alert(1)")


def test_seed_locations_is_idempotent_and_preserves_tokens(
    test_context, monkeypatch, capsys
) -> None:
    _, factory = test_context
    locations = [
        {"floor": "1", "area": "ห้อง 101"},
        {"floor": None, "area": "โถง"},
    ]
    monkeypatch.setattr(location_seed, "AsyncSessionLocal", factory)
    monkeypatch.setattr(location_seed, "LOCATIONS", locations)

    first = asyncio.run(location_seed.seed_locations("https://frontend.example/app"))
    first_tokens = {location.id: location.qr_token for location in first}
    first_output = capsys.readouterr().out

    second = asyncio.run(location_seed.seed_locations("https://frontend.example/app"))
    second_tokens = {location.id: location.qr_token for location in second}
    second_output = capsys.readouterr().out

    assert first_tokens == second_tokens
    assert len(first_tokens) == 2
    assert all(re.fullmatch(r"[A-Za-z0-9_-]{32}", token) for token in first_tokens.values())
    assert first_output.count("https://frontend.example/app/cleaning?token=") == 2
    assert second_output.count("https://frontend.example/app/cleaning?token=") == 2

    async def count_locations() -> int:
        async with factory() as session:
            return await session.scalar(select(func.count()).select_from(Location))

    assert asyncio.run(count_locations()) == 2
