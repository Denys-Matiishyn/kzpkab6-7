"""Читання CSV-файла бронювань і перетворення текстових полів на типізовані значення."""

import csv
import math
from collections.abc import Iterator
from datetime import date
from pathlib import Path
from typing import Any

from .errors import DataError

Record = dict[str, Any]

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


def parse_row(row: dict[str, str], row_number: int) -> Record:
    """Перетворює один рядок CSV на запис із типізованими значеннями.

    Запис містить поля ``room`` (int), ``guest`` (str), ``check_in`` і ``check_out`` (date),
    ``rate`` (float) та похідні ``nights`` (int) і ``cost`` (float).
    """
    # DictReader кладе зайві значення під ключ None, а відсутні заповнює значенням None.
    if None in row:
        raise DataError(f"Рядок {row_number}: забагато значень")
    absent = [field for field in REQUIRED_FIELDS if row.get(field) is None]
    if absent:
        raise DataError(f"Рядок {row_number}: немає значення поля {absent[0]}")

    room = _parse_int(row, "room", row_number)
    # Зайві пробіли прибираються, щоб «Anna  Bell» і «Anna Bell» були одним гостем.
    guest = " ".join(row["guest"].split())
    check_in = _parse_date(row, "check_in", row_number)
    check_out = _parse_date(row, "check_out", row_number)
    rate = _parse_float(row, "rate", row_number)

    if room <= 0:
        raise DataError(f"Рядок {row_number}: поле room має бути більшим за нуль")
    if not guest:
        raise DataError(f"Рядок {row_number}: поле guest порожнє")
    if check_out <= check_in:
        raise DataError(f"Рядок {row_number}: поле check_out має бути пізніше за check_in")
    # float() приймає тексти "nan" та "inf"; для тарифу вони не мають змісту.
    if not math.isfinite(rate):
        raise DataError(f"Рядок {row_number}: поле rate має бути скінченним числом")
    if rate < 0:
        raise DataError(f"Рядок {row_number}: поле rate не може бути від'ємним")

    nights = (check_out - check_in).days
    return {
        "room": room,
        "guest": guest,
        "check_in": check_in,
        "check_out": check_out,
        "rate": rate,
        "nights": nights,
        "cost": nights * rate,
    }


def iter_records(path: Path) -> Iterator[Record]:
    """Читає CSV потоково й повертає записи по одному.

    Генератор не тримає весь файл у пам'яті, тому підходить для великих файлів.
    Файл відкривається під час першого звернення до генератора.
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


def load_records(path: Path) -> list[Record]:
    """Читає CSV-файл і повертає список записів у порядку файла.

    Файл лише із заголовком дає порожній список. Файл без заголовка, з іншим заголовком
    або з некоректним рядком спричиняє ``DataError``.
    """
    return list(iter_records(path))
