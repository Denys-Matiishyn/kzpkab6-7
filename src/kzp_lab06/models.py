"""Об'єктна модель бронювань: базовий клас, підтипи, протокол і незмінні підсумки.

Модуль не читає файли й не форматує звіт. Перевірки значень виконуються у властивостях,
тому некоректний об'єкт неможливо створити.
"""

import math
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Protocol


class Priced(Protocol):
    """Протокол об'єктів, для яких можна обчислити ціну проживання.

    Функції аналізу залежать лише від цього протоколу, а не від конкретних класів.
    """

    @property
    def nights(self) -> int:
        """Кількість ночей."""
        ...

    @property
    def tier(self) -> str:
        """Назва рівня обслуговування."""
        ...

    def total_price(self) -> float:
        """Ціна проживання з надбавкою рівня."""
        ...


CENT = Decimal("0.01")


def money(amount: Decimal) -> float:
    """Округлює суму до копійки за правилом «половина вгору»."""
    return float(amount.quantize(CENT, rounding=ROUND_HALF_UP))


class Booking:
    """Бронювання номера готелю.

    Спільний стан і перевірки зберігаються тут, а формулу ціни задають підтипи.
    """

    # __slots__ фіксує набір полів і зменшує пам'ять на кожен об'єкт.
    __slots__ = ("_room", "_guest", "_check_in", "_check_out", "_rate")

    #: Назва рівня обслуговування; перевизначається в підтипах.
    TIER = "Booking"
    #: Частка надбавки до базової вартості; перевизначається в підтипах.
    SURCHARGE = "0"

    def __init__(self, room: int, guest: str, check_in: date, check_out: date, rate: float) -> None:
        """Створює бронювання й перевіряє всі поля через властивості."""
        self.room = room
        self.guest = guest
        if not isinstance(check_in, date) or not isinstance(check_out, date):
            raise TypeError("поля check_in і check_out мають бути датами")
        if check_out <= check_in:
            raise ValueError("поле check_out має бути пізніше за check_in")
        # Дати не мають setter-а: період бронювання не змінюється після створення.
        self._check_in = check_in
        self._check_out = check_out
        self.rate = rate

    # ---------- властивості ----------

    @property
    def room(self) -> int:
        """Номер кімнати."""
        return self._room

    @room.setter
    def room(self, value: int) -> None:
        """Встановлює номер кімнати: ціле число, більше за нуль."""
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("поле room має бути цілим числом")
        if value <= 0:
            raise ValueError("поле room має бути більшим за нуль")
        # Запис у внутрішнє поле: self.room = value викликав би setter рекурсивно.
        self._room = value

    @property
    def guest(self) -> str:
        """Ім'я гостя без зайвих пробілів."""
        return self._guest

    @guest.setter
    def guest(self, value: str) -> None:
        """Встановлює ім'я гостя; зайві пробіли прибираються, порожнє ім'я відхиляється."""
        if not isinstance(value, str):
            raise TypeError("поле guest має бути текстом")
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("поле guest порожнє")
        self._guest = normalized

    @property
    def rate(self) -> float:
        """Тариф за ніч."""
        return self._rate

    @rate.setter
    def rate(self, value: float) -> None:
        """Встановлює тариф: скінченне число, не менше за нуль."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("поле rate має бути числом")
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("поле rate має бути скінченним числом")
        if number < 0:
            raise ValueError("поле rate не може бути від'ємним")
        self._rate = number

    @property
    def check_in(self) -> date:
        """Дата заїзду (лише читання)."""
        return self._check_in

    @property
    def check_out(self) -> date:
        """Дата виїзду (лише читання)."""
        return self._check_out

    @property
    def nights(self) -> int:
        """Кількість ночей, обчислена з дат."""
        return (self._check_out - self._check_in).days

    @property
    def cost(self) -> float:
        """Базова вартість без надбавки: ночі × тариф."""
        return self.nights * self._rate

    @property
    def tier(self) -> str:
        """Назва рівня обслуговування."""
        return self.TIER

    @property
    def sort_key(self) -> tuple[int, date, str]:
        """Ключ стабільного впорядкування: номер, заїзд, гість."""
        return (self._room, self._check_in, self._guest)

    # ---------- поведінка ----------

    def total_price(self) -> float:
        """Повертає ціну проживання з надбавкою, округлену до копійки.

        Формула належить підтипу; базовий клас лише оголошує операцію.
        """
        raise NotImplementedError("total_price() реалізують підтипи")

    def _base_amount(self) -> Decimal:
        """Базова вартість як Decimal, щоб уникнути похибок двійкових дробів."""
        return Decimal(repr(self._rate)) * self.nights

    def is_active(self, reference_date: date) -> bool:
        """Перевіряє, що бронювання активне на дату: заїзд <= дата < виїзд."""
        return self._check_in <= reference_date < self._check_out

    def as_dict(self) -> dict[str, Any]:
        """Повертає запис у форматі словникової моделі попередньої роботи."""
        return {
            "room": self._room,
            "guest": self._guest,
            "check_in": self._check_in,
            "check_out": self._check_out,
            "rate": self._rate,
            "nights": self.nights,
            "cost": self.cost,
        }

    # ---------- спеціальні методи ----------

    def __str__(self) -> str:
        """Коротке подання для читача."""
        return (
            f"{self._room} | {self._guest} | "
            f"{self._check_in.isoformat()}..{self._check_out.isoformat()}"
        )

    def __repr__(self) -> str:
        """Діагностичне подання, з якого видно клас і всі поля."""
        return (
            f"{type(self).__name__}(room={self._room!r}, guest={self._guest!r}, "
            f"check_in={self._check_in!r}, check_out={self._check_out!r}, rate={self._rate!r})"
        )

    def __eq__(self, other: object) -> bool:
        """Порівнює бронювання за класом і всіма полями."""
        if not isinstance(other, Booking):
            return NotImplemented
        # Різні підтипи мають різну ціну, тому з однаковими полями вони не рівні.
        return type(self) is type(other) and self._fields() == other._fields()

    # Об'єкт змінюваний (є setter-и), тому він не може бути ключем словника чи елементом
    # множини: інакше після зміни поля його не вдалося б знайти.
    __hash__ = None  # type: ignore[assignment]

    def _fields(self) -> tuple[int, str, date, date, float]:
        """Повертає значення полів для порівняння."""
        return (self._room, self._guest, self._check_in, self._check_out, self._rate)


class StandardBooking(Booking):
    """Стандартне бронювання: надбавка 5 % до базової вартості."""

    __slots__ = ()
    TIER = "Standard"
    SURCHARGE = "0.05"

    def total_price(self) -> float:
        """Базова вартість плюс 5 %, округлена до копійки."""
        return money(self._base_amount() * (1 + Decimal(self.SURCHARGE)))


class PremiumBooking(Booking):
    """Преміальне бронювання: надбавка 15 % і фіксований збір за кожну ніч."""

    __slots__ = ()
    TIER = "Premium"
    SURCHARGE = "0.15"
    #: Фіксований збір за ніч (обслуговування номера).
    NIGHTLY_FEE = "50.00"

    def total_price(self) -> float:
        """Базова вартість плюс 15 % і 50.00 за кожну ніч, округлена до копійки."""
        amount = self._base_amount() * (1 + Decimal(self.SURCHARGE))
        return money(amount + Decimal(self.NIGHTLY_FEE) * self.nights)


#: Тариф, починаючи з якого бронювання вважається преміальним.
PREMIUM_RATE = 1000.0


def create_booking(room: int, guest: str, check_in: date, check_out: date, rate: float) -> Booking:
    """Створює підтип за тарифом: від PREMIUM_RATE — PremiumBooking, інакше StandardBooking.

    Це єдине місце, де вибирається конкретний клас.
    """
    kind = PremiumBooking if rate >= PREMIUM_RATE else StandardBooking
    return kind(room, guest, check_in, check_out, rate)


@dataclass(frozen=True)
class Occupancy:
    """Незмінне завантаження номерів на дату."""

    occupied: int
    total: int

    @property
    def percent(self) -> float:
        """Частка зайнятих номерів у відсотках; 0.0, якщо номерів немає."""
        return 100.0 * self.occupied / self.total if self.total else 0.0


@dataclass(frozen=True)
class ReportSummary:
    """Незмінний підсумок усіх показників звіту.

    Колекції зберігаються як кортежі, щоб підсумок не можна було змінити ззовні.
    """

    reference_date: date
    count: int
    active: tuple[Booking, ...]
    occupancy: Occupancy
    count_by_rate: tuple[tuple[float, int], ...]
    guests: tuple[str, ...]
    longest_stay: Booking | None
    total_nights: int
    total_cost: float
