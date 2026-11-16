"""Тести формування та запису звіту."""

import random
from pathlib import Path

from conftest import REFERENCE_DATE

from kzp_lab06.models import Booking
from kzp_lab06.analysis import build_report
from kzp_lab06.reporting import format_report, write_report

EMPTY_REPORT = (
    "Звіт про бронювання готелю\n"
    "Дата відбору: 2026-01-03\n"
    "Записів: 0\n"
    "Активні бронювання на дату: 0\n"
    "Завантаження номерів: 0 з 0 (0.00%)\n"
    "Кількість бронювань за тарифом:\n"
    "Гості без повторів: 0\n"
    "Найдовше проживання: немає даних\n"
    "Сумарна кількість ночей: 0\n"
    "Сумарна вартість: 0.00\n"
)


def test_report_matches_committed_example(records: list[Booking], data_dir: Path) -> None:
    """Текст звіту збігається зі збереженим прикладом reports/summary.txt."""
    expected = (data_dir.parent / "reports" / "summary.txt").read_text(encoding="utf-8")
    assert format_report(build_report(records, REFERENCE_DATE)) == expected


def test_report_lines(records: list[Booking]) -> None:
    """Звіт містить показники варіанта з форматуванням до двох знаків."""
    text = format_report(build_report(records, REFERENCE_DATE))
    assert "Активні бронювання на дату: 4\n" in text
    assert "  101 | Doe, John | 2026-01-01..2026-01-04\n" in text
    assert "Завантаження номерів: 4 з 6 (66.67%)\n" in text
    assert "  150.00: 2\n" in text
    assert "Гості без повторів: 6\n" in text
    assert "Найдовше проживання: Sarah Connor, номер 210, ночей: 10" in text
    assert text.endswith("Сумарна вартість: 21293.50\n")


def test_report_does_not_depend_on_input_order(records: list[Booking]) -> None:
    """Перемішані записи дають той самий текст звіту."""
    expected = format_report(build_report(records, REFERENCE_DATE))
    shuffled = list(records)
    random.Random(6).shuffle(shuffled)
    assert shuffled != records
    assert format_report(build_report(shuffled, REFERENCE_DATE)) == expected


def test_empty_report() -> None:
    """Порожній набір дає повний звіт із нулями."""
    assert format_report(build_report([], REFERENCE_DATE)) == EMPTY_REPORT


def test_write_report_creates_directories_and_utf8(tmp_path: Path) -> None:
    """Звіт записується в UTF-8, каталоги створюються."""
    output = tmp_path / "nested" / "dir" / "report.txt"
    write_report(output, "Готово: 100%\n")
    assert output.read_text(encoding="utf-8") == "Готово: 100%\n"
    assert output.read_bytes().startswith("Готово".encode())


def test_write_report_uses_lf_and_overwrites(tmp_path: Path) -> None:
    """Роздільник рядків завжди LF, а старий довший вміст не лишається."""
    output = tmp_path / "report.txt"
    write_report(output, "перший\nдругий\nтретій\n")
    write_report(output, "один\nдва\n")
    assert output.read_bytes() == "один\nдва\n".encode()
