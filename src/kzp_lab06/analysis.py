"""Обчислення над об'єктами бронювань. Модуль не читає й не записує файли.

Функції не перевіряють конкретний підтип: вони викликають властивості й методи,
спільні для всіх бронювань (протокол ``Priced``).
"""

from collections.abc import Iterable
from datetime import date
from itertools import islice
from typing import Any

from .models import Booking, Occupancy, Priced, ReportSummary

NUMERIC_METRICS = ("cost", "nights", "rate", "total_price")


def active_on(bookings: Iterable[Booking], reference_date: date) -> list[Booking]:
    """Відбирає бронювання, активні на задану дату, у порядку номера кімнати й заїзду."""
    selected = [booking for booking in bookings if booking.is_active(reference_date)]
    return sorted(selected, key=lambda booking: booking.sort_key)


def count_by_rate(bookings: Iterable[Booking]) -> dict[float, int]:
    """Рахує бронювання за тарифом; ключі словника йдуть за зростанням тарифу."""
    counts: dict[float, int] = {}
    for booking in bookings:
        counts[booking.rate] = counts.get(booking.rate, 0) + 1
    return {rate: counts[rate] for rate in sorted(counts)}


def unique_guests(bookings: Iterable[Booking]) -> set[str]:
    """Повертає множину гостей без повторів."""
    return {booking.guest for booking in bookings}


def occupancy(bookings: list[Booking], reference_date: date) -> Occupancy:
    """Обчислює завантаження номерів на дату.

    Усіма номерами готелю вважаються різні номери з файла.
    """
    rooms = {booking.room for booking in bookings}
    occupied = {booking.room for booking in bookings if booking.is_active(reference_date)}
    return Occupancy(occupied=len(occupied), total=len(rooms))


def longest_stay(bookings: Iterable[Booking]) -> Booking | None:
    """Повертає найдовше проживання або None для порожнього набору.

    За однакової тривалості вибирається менший номер кімнати, далі раніший заїзд.
    """
    return min(
        bookings,
        key=lambda booking: (-booking.nights, booking.room, booking.check_in),
        default=None,
    )


def _metric_value(booking: Booking, metric: str) -> float:
    """Повертає значення метрики: властивість або результат методу без аргументів."""
    value = getattr(booking, metric)
    return float(value() if callable(value) else value)


def make_summary(
    bookings: list[Booking],
    *metrics: str,
    minimum_nights: int = 1,
    **labels: str,
) -> dict[str, Any]:
    """Обчислює суми вибраних метрик для проживань не коротших за мінімум.

    ``metrics`` — назви числових властивостей або методів (``cost``, ``nights``, ``rate``,
    ``total_price``), ``labels`` задає підписи результатів. Невідома метрика або підпис для
    невибраної метрики спричиняє ``ValueError``. Якщо жоден запис не пройшов відбір,
    суми дорівнюють 0.0.
    """
    unknown = [metric for metric in metrics if metric not in NUMERIC_METRICS]
    if unknown:
        raise ValueError(f"Невідома метрика: {unknown[0]}")
    stray = sorted(set(labels) - set(metrics))
    if stray:
        raise ValueError(f"Підпис для невибраної метрики: {stray[0]}")

    selected = [booking for booking in bookings if booking.nights >= minimum_nights]
    result: dict[str, Any] = {"count": len(selected)}
    for metric in metrics:
        result[labels.get(metric, metric)] = float(
            sum(_metric_value(booking, metric) for booking in selected)
        )
    return result


def total_revenue(items: Iterable[Priced]) -> float:
    """Сумарна ціна проживань з надбавками; працює з будь-яким об'єктом протоколу Priced."""
    return sum(item.total_price() for item in items)


def revenue_by_tier(items: Iterable[Priced]) -> dict[str, float]:
    """Сумарна ціна за рівнями обслуговування; ключі за алфавітом.

    Функція не перевіряє класи: назву рівня й формулу ціни надає сам об'єкт.
    """
    totals: dict[str, float] = {}
    for item in items:
        totals[item.tier] = totals.get(item.tier, 0.0) + item.total_price()
    return {tier: totals[tier] for tier in sorted(totals)}


def most_expensive(items: Iterable[Priced]) -> Priced | None:
    """Повертає об'єкт із найбільшою ціною або None для порожнього входу."""
    return max(items, key=lambda item: item.total_price(), default=None)


def build_report(bookings: list[Booking], reference_date: date) -> ReportSummary:
    """Збирає всі показники звіту в незмінний підсумок без форматування тексту."""
    totals = make_summary(bookings, "nights", "cost")
    return ReportSummary(
        reference_date=reference_date,
        count=len(bookings),
        active=tuple(active_on(bookings, reference_date)),
        occupancy=occupancy(bookings, reference_date),
        count_by_rate=tuple(count_by_rate(bookings).items()),
        guests=tuple(sorted(unique_guests(bookings))),
        longest_stay=longest_stay(bookings),
        total_nights=int(totals["nights"]),
        total_cost=totals["cost"],
    )


def preview(bookings: Iterable[Booking], limit: int = 3) -> list[Booking]:
    """Повертає перші ``limit`` об'єктів, не читаючи решту ітератора."""
    if limit < 0:
        raise ValueError("limit не може бути від'ємним")
    return list(islice(bookings, limit))


def stream_summary(bookings: Iterable[Booking], reference_date: date) -> dict[str, Any]:
    """Обчислює показники за один прохід, не зберігаючи об'єкти в пам'яті."""
    count = 0
    total_nights = 0
    total_cost = 0.0
    rooms: set[int] = set()
    occupied: set[int] = set()
    guests: set[str] = set()
    counts: dict[float, int] = {}
    longest: Booking | None = None

    for booking in bookings:
        count += 1
        total_nights += booking.nights
        total_cost += booking.cost
        rooms.add(booking.room)
        guests.add(booking.guest)
        counts[booking.rate] = counts.get(booking.rate, 0) + 1
        if booking.is_active(reference_date):
            occupied.add(booking.room)
        longest = longest_stay([booking] if longest is None else [longest, booking])

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
