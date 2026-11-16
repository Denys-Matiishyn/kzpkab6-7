"""Тести об'єктної моделі: властивості, спеціальні методи, dataclass, підтипи й протокол."""

import dataclasses
from datetime import date

import pytest

from kzp_lab06.analysis import most_expensive, revenue_by_tier, total_revenue
from kzp_lab06.models import (
    PREMIUM_RATE,
    Booking,
    Occupancy,
    PremiumBooking,
    ReportSummary,
    StandardBooking,
    create_booking,
)

JAN1 = date(2026, 1, 1)
JAN4 = date(2026, 1, 4)


def standard(rate: float = 150.0) -> StandardBooking:
    """Створює стандартне бронювання на три ночі."""
    return StandardBooking(101, "Anna Bell", JAN1, JAN4, rate)


# ---------- @property і setter ----------


def test_properties_return_constructor_values() -> None:
    """Властивості повертають значення, передані в конструктор."""
    booking = standard()
    assert (booking.room, booking.guest, booking.rate) == (101, "Anna Bell", 150.0)
    assert (booking.check_in, booking.check_out, booking.nights) == (JAN1, JAN4, 3)
    assert booking.cost == 450.0


@pytest.mark.parametrize(
    ("value", "expected"),
    [(150.0, 150.0), (0, 0.0), (0.0, 0.0), (0.01, 0.01), (2000, 2000.0)],
)
def test_rate_setter_accepts_valid_and_boundary_values(value: float, expected: float) -> None:
    """Setter приймає коректне, нульове та граничне значення й зберігає float."""
    booking = standard()
    booking.rate = value
    assert booking.rate == expected
    assert isinstance(booking.rate, float)


@pytest.mark.parametrize(
    ("value", "error", "message"),
    [
        (-0.01, ValueError, "не може бути від'ємним"),
        (float("nan"), ValueError, "скінченним числом"),
        (float("inf"), ValueError, "скінченним числом"),
        ("150", TypeError, "має бути числом"),
        (True, TypeError, "має бути числом"),
    ],
)
def test_rate_setter_rejects_invalid_values(value: object, error: type, message: str) -> None:
    """Setter відхиляє помилкове значення й не змінює стан об'єкта."""
    booking = standard()
    with pytest.raises(error, match=message):
        booking.rate = value
    assert booking.rate == 150.0


def test_room_setter() -> None:
    """Номер кімнати: 1 є граничним допустимим значенням, 0 і текст відхиляються."""
    booking = standard()
    booking.room = 1
    assert booking.room == 1
    with pytest.raises(ValueError, match="більшим за нуль"):
        booking.room = 0
    with pytest.raises(TypeError, match="цілим числом"):
        booking.room = "101"
    assert booking.room == 1


def test_guest_setter_normalizes_and_rejects_empty() -> None:
    """Ім'я нормалізується, а порожнє ім'я відхиляється."""
    booking = standard()
    booking.guest = "  Марія   Коваленко "
    assert booking.guest == "Марія Коваленко"
    with pytest.raises(ValueError, match="порожнє"):
        booking.guest = "   "
    assert booking.guest == "Марія Коваленко"


def test_dates_are_read_only_and_checked() -> None:
    """Дати не мають setter-а, а виїзд має бути пізніше за заїзд."""
    booking = standard()
    with pytest.raises(AttributeError):
        booking.check_in = JAN4  # type: ignore[misc]
    with pytest.raises(ValueError, match="пізніше за check_in"):
        StandardBooking(101, "A", JAN4, JAN4, 1.0)
    with pytest.raises(TypeError, match="датами"):
        StandardBooking(101, "A", "2026-01-01", JAN4, 1.0)  # type: ignore[arg-type]


def test_constructor_uses_setters() -> None:
    """Конструктор перевіряє поля тими самими setter-ами."""
    with pytest.raises(ValueError, match="більшим за нуль"):
        StandardBooking(0, "A", JAN1, JAN4, 1.0)
    with pytest.raises(ValueError, match="від'ємним"):
        PremiumBooking(1, "A", JAN1, JAN4, -5.0)


def test_slots_prevent_unknown_attributes() -> None:
    """__slots__ не дає випадково створити нове поле через одруківку."""
    booking = standard()
    with pytest.raises(AttributeError):
        booking.rtae = 10.0  # type: ignore[attr-defined]


# ---------- спеціальні методи ----------


def test_str_and_repr() -> None:
    """__str__ призначений для читача, __repr__ показує клас і всі поля."""
    booking = StandardBooking(101, "Doe, John", JAN1, JAN4, 150.0)
    assert str(booking) == "101 | Doe, John | 2026-01-01..2026-01-04"
    assert repr(booking) == (
        "StandardBooking(room=101, guest='Doe, John', check_in=datetime.date(2026, 1, 1), "
        "check_out=datetime.date(2026, 1, 4), rate=150.0)"
    )


def test_eq_compares_all_fields() -> None:
    """Однакові бронювання рівні, а зміна будь-якого поля робить їх різними."""
    assert standard() == standard()
    assert standard() != standard(rate=151.0)
    assert standard() != StandardBooking(102, "Anna Bell", JAN1, JAN4, 150.0)
    assert standard() != StandardBooking(101, "Anna", JAN1, JAN4, 150.0)
    assert standard() != StandardBooking(101, "Anna Bell", JAN1, date(2026, 1, 5), 150.0)


def test_eq_with_other_types_and_subtypes() -> None:
    """__eq__ повертає NotImplemented для чужого типу; різні підтипи не рівні."""
    booking = standard()
    assert booking.__eq__("text") is NotImplemented
    assert booking != "text"
    assert booking != None  # noqa: E711
    assert standard() != PremiumBooking(101, "Anna Bell", JAN1, JAN4, 150.0)


def test_mutable_booking_is_not_hashable() -> None:
    """Змінюваний об'єкт не можна покласти в множину."""
    with pytest.raises(TypeError):
        {standard()}  # noqa: B018


def test_sort_key_orders_by_room_then_check_in() -> None:
    """Ключ впорядкування: номер кімнати, потім дата заїзду, потім гість."""
    late = StandardBooking(101, "B", date(2026, 1, 5), date(2026, 1, 6), 1.0)
    early = StandardBooking(101, "A", JAN1, JAN4, 1.0)
    other = StandardBooking(100, "C", date(2026, 2, 1), date(2026, 2, 2), 1.0)
    assert sorted([late, early, other], key=lambda b: b.sort_key) == [other, early, late]


# ---------- dataclass ----------


def test_summary_dataclass_is_frozen_and_comparable() -> None:
    """Підсумок створюється, порівнюється за полями й не змінюється."""
    first = Occupancy(occupied=4, total=6)
    assert first == Occupancy(4, 6)
    assert first != Occupancy(3, 6)
    assert repr(first) == "Occupancy(occupied=4, total=6)"
    assert first.percent == pytest.approx(66.6667, abs=0.001)
    with pytest.raises(dataclasses.FrozenInstanceError):
        first.occupied = 5  # type: ignore[misc]
    assert {first, Occupancy(4, 6)} == {first}


def test_report_summary_is_frozen() -> None:
    """ReportSummary не дає змінити поле після створення."""
    summary = ReportSummary(JAN1, 0, (), Occupancy(0, 0), (), (), None, 0, 0.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        summary.count = 1  # type: ignore[misc]
    assert Occupancy(0, 0).percent == 0.0


# ---------- підтипи ----------


def test_subtypes_have_different_total_price() -> None:
    """Однакові дані дають різну ціну у різних підтипах."""
    plain = StandardBooking(101, "A", JAN1, JAN4, 1000.0)
    premium = PremiumBooking(101, "A", JAN1, JAN4, 1000.0)
    assert plain.cost == premium.cost == 3000.0
    assert plain.total_price() == 3150.0
    assert premium.total_price() == 3600.0
    assert (plain.tier, premium.tier) == ("Standard", "Premium")


def test_total_price_is_rounded_to_cents() -> None:
    """Ціна округлюється до копійки за правилом «половина вгору»."""
    booking = StandardBooking(205, "A", date(2026, 1, 3), date(2026, 1, 10), 220.5)
    assert booking.cost == 1543.5
    assert booking.total_price() == 1620.68


def test_zero_rate_prices() -> None:
    """Нульовий тариф дає нульову ціну стандартного номера."""
    assert standard(rate=0.0).total_price() == 0.0


def test_base_class_does_not_define_price() -> None:
    """Базовий клас оголошує операцію, але формулу задають підтипи."""
    booking = Booking(101, "A", JAN1, JAN4, 1.0)
    with pytest.raises(NotImplementedError):
        booking.total_price()


def test_factory_chooses_subtype_by_rate_boundary() -> None:
    """Від PREMIUM_RATE включно створюється PremiumBooking, нижче — StandardBooking."""
    assert PREMIUM_RATE == 1000.0
    assert type(create_booking(1, "A", JAN1, JAN4, 999.99)) is StandardBooking
    assert type(create_booking(1, "A", JAN1, JAN4, 1000.0)) is PremiumBooking
    assert type(create_booking(1, "A", JAN1, JAN4, 0.0)) is StandardBooking


# ---------- протокол і duck typing ----------


class GiftCertificate:
    """Сторонній клас без наслідування Booking, що відповідає протоколу Priced."""

    tier = "Gift"
    nights = 1

    def total_price(self) -> float:
        """Повертає фіксовану ціну сертифіката."""
        return 99.5


def test_protocol_functions_work_with_both_subtypes(records: list[Booking]) -> None:
    """Спільні функції працюють з обома підтипами без перевірки класу."""
    assert revenue_by_tier(records) == {"Premium": 20150.0, "Standard": 4508.18}
    assert total_revenue(records) == pytest.approx(24658.18)
    best = most_expensive(records)
    assert best is not None
    assert (best.room, best.total_price()) == (404, 11750.0)


def test_protocol_accepts_unrelated_class(records: list[Booking]) -> None:
    """Duck typing: функції приймають будь-який об'єкт із потрібними методами."""
    items = [*records, GiftCertificate()]
    assert revenue_by_tier(items)["Gift"] == 99.5
    assert total_revenue([GiftCertificate(), GiftCertificate()]) == 199.0


def test_protocol_functions_on_empty_input() -> None:
    """Порожній вхід дає нуль, порожній словник і None."""
    assert total_revenue([]) == 0
    assert revenue_by_tier([]) == {}
    assert most_expensive([]) is None


def test_analysis_has_no_subtype_checks() -> None:
    """У модулі аналізу немає перевірок конкретного підтипу."""
    from pathlib import Path

    source = (Path(__file__).resolve().parent.parent / "src/kzp_lab06/analysis.py").read_text(
        encoding="utf-8"
    )
    assert "isinstance" not in source
    assert "StandardBooking" not in source
    assert "PremiumBooking" not in source
