"""Формування тексту звіту та безпечний запис його у файл. Модуль не читає CSV."""

import os
from pathlib import Path
from types import TracebackType
from typing import TextIO

from .models import Booking, ReportSummary


def _stay_period(booking: Booking) -> str:
    """Форматує період проживання як «заїзд..виїзд»."""
    return f"{booking.check_in.isoformat()}..{booking.check_out.isoformat()}"


def format_report(summary: ReportSummary) -> str:
    """Форматує підсумок у детермінований текстовий звіт.

    Формат збігається зі звітом попередньої роботи: ті самі рядки й той самий порядок.
    """
    occupancy = summary.occupancy
    lines = [
        "Звіт про бронювання готелю",
        f"Дата відбору: {summary.reference_date.isoformat()}",
        f"Записів: {summary.count}",
        f"Активні бронювання на дату: {len(summary.active)}",
    ]
    lines.extend(f"  {booking}" for booking in summary.active)

    lines.append(
        f"Завантаження номерів: {occupancy.occupied} з {occupancy.total} ({occupancy.percent:.2f}%)"
    )

    lines.append("Кількість бронювань за тарифом:")
    for rate, count in summary.count_by_rate:
        lines.append(f"  {rate:.2f}: {count}")

    lines.append(f"Гості без повторів: {len(summary.guests)}")
    lines.extend(f"  {guest}" for guest in summary.guests)

    longest = summary.longest_stay
    if longest is None:
        lines.append("Найдовше проживання: немає даних")
    else:
        lines.append(
            f"Найдовше проживання: {longest.guest}, номер {longest.room},"
            f" ночей: {longest.nights} ({_stay_period(longest)})"
        )

    lines.append(f"Сумарна кількість ночей: {summary.total_nights}")
    lines.append(f"Сумарна вартість: {summary.total_cost:.2f}")
    return "\n".join(lines) + "\n"


class ReportWriter:
    """Контекстний менеджер для безпечного запису звіту.

    Текст пишеться в тимчасовий файл поруч із цільовим. Після успішного виходу з блоку
    тимчасовий файл атомарно замінює цільовий. Якщо в блоці виник виняток, тимчасовий
    файл закривається й видаляється, а цільовий лишається без змін; виняток не
    поглинається.
    """

    def __init__(self, path: Path) -> None:
        """Запам'ятовує шлях звіту; файл відкривається у ``__enter__``."""
        self.path = path
        self._temporary = path.with_name(f".{path.name}.tmp")
        self._stream: TextIO | None = None

    @property
    def closed(self) -> bool:
        """True, якщо файл ще не відкрито або вже закрито."""
        return self._stream is None or self._stream.closed

    def __enter__(self) -> TextIO:
        """Створює каталог і відкриває тимчасовий файл UTF-8 з роздільником LF."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._stream = self._temporary.open("w", encoding="utf-8", newline="\n")
        return self._stream

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        """Закриває файл; після успіху замінює звіт, після винятку прибирає тимчасовий файл."""
        assert self._stream is not None
        self._stream.close()
        if exc_type is None:
            os.replace(self._temporary, self.path)
        else:
            self._temporary.unlink(missing_ok=True)
        # False: виняток із блоку передається далі, а не маскується.
        return False


def write_report(path: Path, text: str) -> None:
    """Записує звіт у файл UTF-8 через контекстний менеджер ReportWriter."""
    with ReportWriter(path) as target:
        target.write(text)
