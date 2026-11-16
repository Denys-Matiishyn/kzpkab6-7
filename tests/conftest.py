"""Спільні дані для тестів."""

from datetime import date
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REFERENCE_DATE = date(2026, 1, 3)


def make_record(
    room: int, guest: str, check_in: str, check_out: str, rate: float
) -> dict[str, Any]:
    """Створює типізований запис так, як це робить loader."""
    start = date.fromisoformat(check_in)
    end = date.fromisoformat(check_out)
    nights = (end - start).days
    return {
        "room": room,
        "guest": guest,
        "check_in": start,
        "check_out": end,
        "rate": rate,
        "nights": nights,
        "cost": nights * rate,
    }


@pytest.fixture
def records() -> list[dict[str, Any]]:
    """Сім записів контрольного набору data/input.csv."""
    return [
        make_record(101, "Doe, John", "2026-01-01", "2026-01-04", 150.0),
        make_record(101, "Anna Bell", "2026-01-04", "2026-01-06", 150.0),
        make_record(205, "Diana Prince", "2026-01-03", "2026-01-10", 220.5),
        make_record(210, "Sarah Connor", "2026-01-01", "2026-01-11", 200.0),
        make_record(301, "Dexter Morgan", "2025-12-27", "2026-01-03", 1000.0),
        make_record(404, "Doe, John", "2026-01-02", "2026-01-07", 2000.0),
        make_record(102, "Clark Kent", "2026-01-05", "2026-01-06", 0.0),
    ]


@pytest.fixture
def data_dir() -> Path:
    """Каталог із прикладами CSV."""
    return PROJECT_ROOT / "data"
