"""Обчислення над записами бронювань. Модуль не читає й не записує файли."""

from collections.abc import Iterable
from datetime import date
from itertools import islice
from typing import Any

Record = dict[str, Any]

NUMERIC_METRICS = ("cost", "nights", "rate")


def is_active(record: Record, reference_date: date) -> bool:
    """Перевіряє, що бронювання активне на дату: check_in <= дата < check_out."""
    return record["check_in"] <= reference_date < record["check_out"]


def active_on(records: Iterable[Record], reference_date: date) -> list[Record]:
    """Відбирає бронювання, активні на задану дату, у порядку номера кімнати й заїзду."""
    selected = [record for record in records if is_active(record, reference_date)]
    return sorted(selected, key=lambda record: (record["room"], record["check_in"]))


def count_by_rate(records: Iterable[Record]) -> dict[float, int]:
    """Рахує бронювання за тарифом; ключі словника йдуть за зростанням тарифу."""
    counts: dict[float, int] = {}
    for record in records:
        counts[record["rate"]] = counts.get(record["rate"], 0) + 1
    return {rate: counts[rate] for rate in sorted(counts)}


def unique_guests(records: Iterable[Record]) -> set[str]:
    """Повертає множину гостей без повторів."""
    return {record["guest"] for record in records}


def occupancy(records: list[Record], reference_date: date) -> dict[str, float | int]:
    """Обчислює завантаження номерів на дату.

    Усіма номерами готелю вважаються різні номери з файла. Для порожнього набору
    повертаються нулі.
    """
    rooms = {record["room"] for record in records}
    occupied = {record["room"] for record in records if is_active(record, reference_date)}
    percent = 100.0 * len(occupied) / len(rooms) if rooms else 0.0
    return {"occupied": len(occupied), "total": len(rooms), "percent": percent}


def longest_stay(records: Iterable[Record]) -> Record | None:
    """Повертає найдовше проживання або None для порожнього набору.

    За однакової тривалості вибирається менший номер кімнати, далі раніший заїзд.
    """
    return min(
        records,
        key=lambda record: (-record["nights"], record["room"], record["check_in"]),
        default=None,
    )


def make_summary(
    records: list[Record],
    *metrics: str,
    minimum_nights: int = 1,
    **labels: str,
) -> dict[str, Any]:
    """Обчислює суми вибраних числових метрик для проживань не коротших за мінімум.

    ``metrics`` — назви числових полів (``cost``, ``nights``, ``rate``), ``labels`` задає
    підписи результатів. Невідома метрика або підпис для невибраної метрики спричиняє
    ``ValueError``. Якщо жоден запис не пройшов відбір, суми дорівнюють 0.0.
    """
    unknown = [metric for metric in metrics if metric not in NUMERIC_METRICS]
    if unknown:
        raise ValueError(f"Невідома метрика: {unknown[0]}")
    stray = sorted(set(labels) - set(metrics))
    if stray:
        raise ValueError(f"Підпис для невибраної метрики: {stray[0]}")

    # Відбір виконується один раз, після чого всі метрики використовують selected.
    selected = [record for record in records if record["nights"] >= minimum_nights]
    result: dict[str, Any] = {"count": len(selected)}
    for metric in metrics:
        result[labels.get(metric, metric)] = float(sum(record[metric] for record in selected))
    return result


def build_report(records: list[Record], reference_date: date) -> dict[str, Any]:
    """Збирає всі показники звіту в один словник без форматування тексту."""
    totals = make_summary(records, "nights", "cost")
    return {
        "reference_date": reference_date,
        "count": len(records),
        "active": active_on(records, reference_date),
        "occupancy": occupancy(records, reference_date),
        "count_by_rate": count_by_rate(records),
        "guests": unique_guests(records),
        "longest_stay": longest_stay(records),
        "total_nights": int(totals["nights"]),
        "total_cost": totals["cost"],
    }


def preview(records: Iterable[Record], limit: int = 3) -> list[Record]:
    """Повертає перші ``limit`` записів, не читаючи решту ітератора."""
    if limit < 0:
        raise ValueError("limit не може бути від'ємним")
    return list(islice(records, limit))


def stream_summary(records: Iterable[Record], reference_date: date) -> dict[str, Any]:
    """Обчислює показники за один прохід, не зберігаючи записи в пам'яті.

    Приймає будь-який ітератор, зокрема генератор ``loader.iter_records``. У пам'яті
    лишаються тільки лічильники, множини номерів і гостей та один найдовший запис.
    """
    count = 0
    total_nights = 0
    total_cost = 0.0
    rooms: set[int] = set()
    occupied: set[int] = set()
    guests: set[str] = set()
    counts: dict[float, int] = {}
    longest: Record | None = None

    for record in records:
        count += 1
        total_nights += record["nights"]
        total_cost += record["cost"]
        rooms.add(record["room"])
        guests.add(record["guest"])
        counts[record["rate"]] = counts.get(record["rate"], 0) + 1
        if is_active(record, reference_date):
            occupied.add(record["room"])
        longest = longest_stay([record] if longest is None else [longest, record])

    return {
        "count": count,
        "active_rooms": len(occupied),
        "total_rooms": len(rooms),
        "count_by_rate": {rate: counts[rate] for rate in sorted(counts)},
        "guest_count": len(guests),
        "longest_stay": longest,
        "total_nights": total_nights,
        "total_cost": total_cost,
    }
