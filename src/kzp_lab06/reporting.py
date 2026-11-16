"""Формування тексту звіту та запис його у файл. Модуль не читає CSV."""

from pathlib import Path
from typing import Any


def _stay_period(record: dict[str, Any]) -> str:
    """Форматує період проживання як «заїзд..виїзд»."""
    return f"{record['check_in'].isoformat()}..{record['check_out'].isoformat()}"


def format_report(summary: dict[str, Any]) -> str:
    """Форматує показники у детермінований текстовий звіт.

    Рядки йдуть у фіксованому порядку, списки відсортовано, числа мають два знаки після
    крапки, тому однакові дані завжди дають однаковий текст.
    """
    occupancy = summary["occupancy"]
    lines = [
        "Звіт про бронювання готелю",
        f"Дата відбору: {summary['reference_date'].isoformat()}",
        f"Записів: {summary['count']}",
        f"Активні бронювання на дату: {len(summary['active'])}",
    ]
    for record in summary["active"]:
        lines.append(f"  {record['room']} | {record['guest']} | {_stay_period(record)}")

    lines.append(
        f"Завантаження номерів: {occupancy['occupied']} з {occupancy['total']}"
        f" ({occupancy['percent']:.2f}%)"
    )

    lines.append("Кількість бронювань за тарифом:")
    for rate, count in sorted(summary["count_by_rate"].items()):
        lines.append(f"  {rate:.2f}: {count}")

    lines.append(f"Гості без повторів: {len(summary['guests'])}")
    for guest in sorted(summary["guests"]):
        lines.append(f"  {guest}")

    longest = summary["longest_stay"]
    if longest is None:
        lines.append("Найдовше проживання: немає даних")
    else:
        lines.append(
            f"Найдовше проживання: {longest['guest']}, номер {longest['room']},"
            f" ночей: {longest['nights']} ({_stay_period(longest)})"
        )

    lines.append(f"Сумарна кількість ночей: {summary['total_nights']}")
    lines.append(f"Сумарна вартість: {summary['total_cost']:.2f}")
    return "\n".join(lines) + "\n"


def write_report(path: Path, text: str) -> None:
    """Створює каталог і записує звіт у файл UTF-8 з роздільником рядків LF."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # with гарантує закриття файла навіть у разі помилки запису.
    with path.open("w", encoding="utf-8", newline="\n") as target:
        target.write(text)
