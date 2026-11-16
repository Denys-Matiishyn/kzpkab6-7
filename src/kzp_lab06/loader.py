"""Читання CSV-файла бронювань і перетворення рядків на об'єкти моделі."""

import csv
from collections.abc import Iterator
from datetime import date
from pathlib import Path

from .errors import DataError
from .models import Booking, create_booking

REQUIRED_FIELDS = ("room", "guest", "check_in", "check_out", "rate")


def _check_header(fieldnames: list[str] | None) -> None:
    """Перевіряє, що заголовок містить рівно обов'язкові стовпці."""
    if fieldnames is None:
        raise DataError("Файл порожній: немає рядка заголовка")
    missing = sorted(set(REQUIRED_FIELDS) - set(fieldnames))
    extra = sorted(set(fieldnames) - set(REQUIRED_FIELDS))
    if missing:
        raise DataError(f"У заголовку немає стовпців: {', '.join(missing)}")
    if extra:
        raise DataError(f"У заголовку зайві стовпці: {', '.join(extra)}")
    if len(fieldnames) != len(REQUIRED_FIELDS):
        raise DataError("У заголовку повторюються назви стовпців")


def _parse_int(row: dict[str, str], field: str, row_number: int) -> int:
    """Перетворює поле на ціле число та додає до помилки номер рядка й назву поля."""
    try:
        return int(row[field].strip())
    except (AttributeError, KeyError, TypeError, ValueError) as error:
        raise DataError(f"Рядок {row_number}: поле {field} має бути цілим числом") from error


def _parse_float(row: dict[str, str], field: str, row_number: int) -> float:
    """Перетворює поле на дробове число та додає до помилки номер рядка й назву поля."""
    try:
        return float(row[field].strip())
    except (AttributeError, KeyError, TypeError, ValueError) as error:
        raise DataError(f"Рядок {row_number}: поле {field} має бути числом") from error


def _parse_date(row: dict[str, str], field: str, row_number: int) -> date:
    """Перетворює поле на дату у форматі ISO YYYY-MM-DD."""
    try:
        return date.fromisoformat(row[field].strip())
    except (AttributeError, KeyError, TypeError, ValueError) as error:
        raise DataError(
            f"Рядок {row_number}: поле {field} має бути датою у форматі YYYY-MM-DD"
        ) from error


def parse_row(row: dict[str, str], row_number: int) -> Booking:
    """Перетворює один рядок CSV на об'єкт StandardBooking або PremiumBooking.

    Loader перетворює текст на типи, а перевірку значень виконують властивості моделі.
    Помилка моделі доповнюється номером рядка; першопричина зберігається.
    """
    # DictReader кладе зайві значення під ключ None, а відсутні заповнює значенням None.
    if None in row:
        raise DataError(f"Рядок {row_number}: забагато значень")
    absent = [field for field in REQUIRED_FIELDS if row.get(field) is None]
    if absent:
        raise DataError(f"Рядок {row_number}: немає значення поля {absent[0]}")

    room = _parse_int(row, "room", row_number)
    guest = row["guest"]
    check_in = _parse_date(row, "check_in", row_number)
    check_out = _parse_date(row, "check_out", row_number)
    rate = _parse_float(row, "rate", row_number)
    try:
        return create_booking(room, guest, check_in, check_out, rate)
    except (TypeError, ValueError) as error:
        raise DataError(f"Рядок {row_number}: {error}") from error


def iter_records(path: Path) -> Iterator[Booking]:
    """Читає CSV потоково й повертає об'єкти по одному.

    Генератор не тримає весь файл у пам'яті. Файл відкривається під час першого
    звернення до генератора.
    """
    try:
        # newline="" передає керування роздільниками рядків модулю csv.
        with path.open("r", encoding="utf-8", newline="") as source:
            reader = csv.DictReader(source)
            _check_header(reader.fieldnames)
            for row in reader:
                # line_num враховує рядок заголовка й багаторядкові поля в лапках.
                yield parse_row(row, reader.line_num)
    except (OSError, UnicodeDecodeError) as error:
        raise DataError(f"Не вдалося прочитати файл: {path}") from error
    except csv.Error as error:
        raise DataError(f"Пошкоджений CSV: {error}") from error


def load_records(path: Path) -> list[Booking]:
    """Читає CSV-файл і повертає список об'єктів у порядку файла.

    Файл лише із заголовком дає порожній список. Файл без заголовка, з іншим заголовком
    або з некоректним рядком спричиняє ``DataError``.
    """
    return list(iter_records(path))
