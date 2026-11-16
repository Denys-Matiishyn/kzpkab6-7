"""Порівняння словникової моделі ЛР № 6 з об'єктною моделлю ЛР № 7."""

from datetime import date, timedelta
from pathlib import Path

import pytest
from legacy_v6 import analysis as legacy_analysis
from legacy_v6 import loader as legacy_loader
from legacy_v6 import reporting as legacy_reporting
from legacy_v6.errors import DataError as LegacyDataError

from kzp_lab06.analysis import build_report
from kzp_lab06.errors import DataError
from kzp_lab06.loader import load_records
from kzp_lab06.reporting import format_report

FILES = ["input.csv", "input-lab07.csv", "empty.csv"]


def old_report(path: Path, reference_date: date) -> str:
    """Звіт словникової моделі попередньої роботи."""
    records = legacy_loader.load_records(path)
    return legacy_reporting.format_report(legacy_analysis.build_report(records, reference_date))


def new_report(path: Path, reference_date: date) -> str:
    """Звіт об'єктної моделі."""
    return format_report(build_report(load_records(path), reference_date))


@pytest.mark.parametrize("name", FILES)
def test_reports_are_identical_for_every_day(data_dir: Path, name: str) -> None:
    """Обидві моделі дають однаковий звіт для кожної дати від 2025-12-25 до 2026-01-15."""
    start = date(2025, 12, 25)
    for offset in range(22):
        day = start + timedelta(days=offset)
        assert new_report(data_dir / name, day) == old_report(data_dir / name, day), day


def test_report_matches_report_committed_in_lab06(data_dir: Path) -> None:
    """Звіт об'єктної моделі збігається зі звітом, збереженим у ЛР № 6."""
    expected = (data_dir.parent / "reports" / "summary.txt").read_text(encoding="utf-8")
    assert new_report(data_dir / "input.csv", date(2026, 1, 3)) == expected


def test_records_hold_the_same_values(data_dir: Path) -> None:
    """Об'єкти містять ті самі значення, що й словники попередньої моделі."""
    for name in FILES:
        old = legacy_loader.load_records(data_dir / name)
        new = [booking.as_dict() for booking in load_records(data_dir / name)]
        assert new == old


@pytest.mark.parametrize(
    "row",
    [
        "abc,Anna Bell,2026-01-04,2026-01-06,150",
        "0,Anna Bell,2026-01-04,2026-01-06,150",
        "101,   ,2026-01-04,2026-01-06,150",
        "101,Anna Bell,2026-01-06,2026-01-06,150",
        "101,Anna Bell,2026-01-04,2026-01-06,-1",
        "101,Anna Bell,2026-01-04,2026-01-06,nan",
        "101,Anna Bell,2026-01-04,2026-01-06",
    ],
)
def test_error_messages_are_unchanged(tmp_path: Path, row: str) -> None:
    """Для помилкових рядків обидві моделі дають однакове повідомлення."""
    path = tmp_path / "input.csv"
    path.write_text("room,guest,check_in,check_out,rate\n" + row + "\n", encoding="utf-8")
    with pytest.raises(LegacyDataError) as old:
        legacy_loader.load_records(path)
    with pytest.raises(DataError) as new:
        load_records(path)
    assert str(new.value) == str(old.value)


def test_duplicated_row_gives_equal_objects(data_dir: Path) -> None:
    """У наборі ЛР № 7 рядки 3 і 7 однакові, тому їхні об'єкти рівні."""
    bookings = load_records(data_dir / "input-lab07.csv")
    assert bookings[1] == bookings[5]
    assert bookings[1] is not bookings[5]
    assert bookings.count(bookings[1]) == 2


def test_lab07_data_has_both_subtypes_and_rate_boundary(data_dir: Path) -> None:
    """Набір ЛР № 7 містить обидва підтипи, межу 999.99/1000.00 і нульовий тариф."""
    bookings = load_records(data_dir / "input-lab07.csv")
    tiers = {(booking.rate, booking.tier) for booking in bookings}
    assert (999.99, "Standard") in tiers
    assert (1000.0, "Premium") in tiers
    assert (0.0, "Standard") in tiers
