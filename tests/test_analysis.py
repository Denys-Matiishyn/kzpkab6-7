"""Тести обчислень над записами."""

from datetime import date
from typing import Any

import pytest
from conftest import REFERENCE_DATE, make_record

from kzp_lab06.models import Booking, Occupancy
from kzp_lab06.analysis import (
    active_on,
    build_report,
    count_by_rate,
    longest_stay,
    make_summary,
    occupancy,
    preview,
    stream_summary,
    unique_guests,
)


def test_active_on_selects_bookings_covering_date(records: list[Booking]) -> None:
    """На контрольну дату активні чотири бронювання, упорядковані за номером."""
    active = active_on(records, REFERENCE_DATE)
    assert [(record.room, record.guest) for record in active] == [
        (101, "Doe, John"),
        (205, "Diana Prince"),
        (210, "Sarah Connor"),
        (404, "Doe, John"),
    ]


def test_active_on_boundaries() -> None:
    """День заїзду й остання ніч активні, день виїзду вже ні."""
    stay = [make_record(101, "A", "2026-01-01", "2026-01-04", 1.0)]
    assert active_on(stay, date(2025, 12, 31)) == []
    assert active_on(stay, date(2026, 1, 1)) == stay
    assert active_on(stay, date(2026, 1, 3)) == stay
    assert active_on(stay, date(2026, 1, 4)) == []


def test_active_on_can_be_empty(records: list[Booking]) -> None:
    """Дата поза всіма проживаннями дає порожній результат відбору."""
    assert active_on(records, date(2026, 2, 1)) == []


def test_count_by_rate_groups_and_sorts(records: list[Booking]) -> None:
    """Словник рахує бронювання за тарифом, ключі йдуть за зростанням."""
    counts = count_by_rate(records)
    assert counts == {0.0: 1, 150.0: 2, 200.0: 1, 220.5: 1, 1000.0: 1, 2000.0: 1}
    assert list(counts) == sorted(counts)
    assert sum(counts.values()) == len(records)


def test_unique_guests_removes_duplicates(records: list[Booking]) -> None:
    """Гість із двома бронюваннями входить до множини один раз."""
    guests = unique_guests(records)
    assert isinstance(guests, set)
    assert guests == {
        "Anna Bell",
        "Clark Kent",
        "Dexter Morgan",
        "Diana Prince",
        "Doe, John",
        "Sarah Connor",
    }


def test_occupancy_counts_distinct_rooms(records: list[Booking]) -> None:
    """Завантаження рахується за різними номерами, а не за бронюваннями."""
    result = occupancy(records, REFERENCE_DATE)
    assert result.occupied == 4
    assert result.total == 6
    assert result.percent == pytest.approx(66.6667, abs=0.001)


def test_occupancy_same_room_twice_counts_once() -> None:
    """Два активні бронювання одного номера дають один зайнятий номер."""
    same_room = [
        make_record(101, "A", "2026-01-01", "2026-01-05", 1.0),
        make_record(101, "B", "2026-01-02", "2026-01-04", 1.0),
    ]
    assert occupancy(same_room, REFERENCE_DATE) == Occupancy(occupied=1, total=1)


def test_longest_stay(records: list[Booking]) -> None:
    """Найдовше проживання має найбільшу кількість ночей."""
    longest = longest_stay(records)
    assert longest is not None
    assert (longest.guest, longest.nights) == ("Sarah Connor", 10)


def test_longest_stay_tie_prefers_smaller_room() -> None:
    """За однакової тривалості вибирається менший номер кімнати."""
    tied = [
        make_record(404, "B", "2026-01-01", "2026-01-08", 1.0),
        make_record(205, "A", "2026-01-03", "2026-01-10", 1.0),
    ]
    longest = longest_stay(tied)
    assert longest is not None
    assert longest.room == 205


def test_make_summary_accepts_args_default_and_kwargs(records: list[Booking]) -> None:
    """Позиційні метрики підсумовуються, а іменовані аргументи задають підписи."""
    result = make_summary(records, "nights", "cost", nights="Ночей", cost="Вартість")
    assert result == {"count": 7, "Ночей": 35.0, "Вартість": 21293.5}


def test_make_summary_without_metrics_returns_count(records: list[Booking]) -> None:
    """Без метрик повертається лише кількість записів."""
    assert make_summary(records) == {"count": 7}


def test_make_summary_minimum_nights_filters(records: list[Booking]) -> None:
    """Параметр minimum_nights відбирає довші проживання; межа входить у відбір."""
    assert make_summary(records, "nights", minimum_nights=7) == {"count": 3, "nights": 24.0}
    assert make_summary(records, "nights", minimum_nights=10) == {"count": 1, "nights": 10.0}


def test_make_summary_empty_selection_gives_zero(records: list[Booking]) -> None:
    """Якщо всі записи відсіяно, відома метрика дорівнює 0.0."""
    assert make_summary(records, "cost", minimum_nights=100) == {"count": 0, "cost": 0.0}
    assert make_summary([], "cost", "nights") == {"count": 0, "cost": 0.0, "nights": 0.0}


def test_make_summary_rejects_unknown_metric_and_label(records: list[Booking]) -> None:
    """Невідома метрика або зайвий підпис не маскуються неповним результатом."""
    with pytest.raises(ValueError, match="Невідома метрика: guest"):
        make_summary(records, "guest")
    with pytest.raises(ValueError, match="Невідома метрика: price"):
        make_summary([], "price")
    with pytest.raises(ValueError, match="Підпис для невибраної метрики: cost"):
        make_summary(records, "nights", cost="Вартість")


def test_build_report_collects_all_values(records: list[Booking]) -> None:
    """Підсумок містить усі показники звіту без форматування."""
    summary = build_report(records, REFERENCE_DATE)
    assert summary.count == 7
    assert len(summary.active) == 4
    assert summary.occupancy.occupied == 4
    assert summary.total_nights == 35
    assert summary.total_cost == pytest.approx(21293.5)
    assert len(summary.guests) == 6


def test_empty_input_gives_empty_results() -> None:
    """Порожній набір дає порожні колекції та нулі без винятків."""
    assert active_on([], REFERENCE_DATE) == []
    assert count_by_rate([]) == {}
    assert unique_guests([]) == set()
    assert occupancy([], REFERENCE_DATE) == Occupancy(occupied=0, total=0)
    assert occupancy([], REFERENCE_DATE).percent == 0.0
    assert longest_stay([]) is None
    summary = build_report([], REFERENCE_DATE)
    assert (summary.count, summary.total_nights, summary.total_cost) == (0, 0, 0.0)


def test_single_record() -> None:
    """Один запис є і найдовшим проживанням, і єдиним номером."""
    one = [make_record(101, "A", "2026-01-01", "2026-01-04", 100.0)]
    summary = build_report(one, REFERENCE_DATE)
    assert summary.longest_stay == one[0]
    assert summary.occupancy == Occupancy(occupied=1, total=1)
    assert summary.occupancy.percent == 100.0
    assert summary.count_by_rate == ((100.0, 1),)


def test_analysis_does_not_change_records(records: list[Booking]) -> None:
    """Функції аналізу не змінюють вхідний список і записи."""
    snapshot = [record.as_dict() for record in records]
    build_report(records, REFERENCE_DATE)
    make_summary(records, "cost", minimum_nights=3)
    assert [record.as_dict() for record in records] == snapshot


def test_preview_takes_first_items_only() -> None:
    """preview читає з ітератора лише потрібну кількість записів."""
    consumed: list[int] = []

    def numbered() -> Any:
        for number in range(1, 100):
            consumed.append(number)
            yield make_record(number, "A", "2026-01-01", "2026-01-02", 1.0)

    assert [record.room for record in preview(numbered(), limit=2)] == [1, 2]
    assert consumed == [1, 2]
    assert preview(iter([]), limit=5) == []
    with pytest.raises(ValueError, match="limit"):
        preview(iter([]), limit=-1)


def test_stream_summary_matches_list_based_report(records: list[Booking]) -> None:
    """Потокова обробка генератора дає ті самі показники, що й обробка списку."""
    expected = build_report(records, REFERENCE_DATE)
    streamed = stream_summary((record for record in records), REFERENCE_DATE)
    assert streamed["count"] == expected.count
    assert streamed["active_rooms"] == expected.occupancy.occupied
    assert streamed["total_rooms"] == expected.occupancy.total
    assert streamed["count_by_rate"] == dict(expected.count_by_rate)
    assert streamed["guest_count"] == len(expected.guests)
    assert streamed["longest_stay"] == expected.longest_stay
    assert streamed["total_nights"] == expected.total_nights
    assert streamed["total_cost"] == pytest.approx(expected.total_cost)


def test_stream_summary_of_empty_iterator() -> None:
    """Порожній ітератор дає нулі й відсутнє найдовше проживання."""
    streamed = stream_summary(iter([]), REFERENCE_DATE)
    assert streamed["count"] == 0
    assert streamed["longest_stay"] is None
    assert streamed["count_by_rate"] == {}
