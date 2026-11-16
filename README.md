git status
git checkout -b lab-07-oop# kzp-lab06: звіт про бронювання готелю (Python)

Лабораторні роботи № 6 і № 7 з курсу «Кросплатформні засоби програмування», варіант 14 «Готель».
Пакет читає CSV-файл бронювань, перетворює рядки на об'єкти `StandardBooking` і `PremiumBooking`, обчислює показники й записує детермінований текстовий звіт.

* ЛР № 6 (тег `v6.0.0`): записи — словники, обробка функціями.
* ЛР № 7 (тег `v7.0.0`): записи — об'єкти з `@property`, підтипи зі спільною операцією `total_price()`, `@dataclass(frozen=True)` для підсумку. Формат CSV і текст звіту не змінилися.

## Об'єктна модель (ЛР № 7)

| Клас | Призначення |
| :-- | :-- |
| `Booking` | базовий клас: `__slots__`, властивості `room`, `guest`, `rate` із setter-перевіркою; `check_in`, `check_out`, `nights`, `cost`, `sort_key` лише для читання; `__str__`, `__repr__`, `__eq__` |
| `StandardBooking` | `total_price() = cost × 1.05` (надбавка 5 %) |
| `PremiumBooking` | `total_price() = cost × 1.15 + 50 × nights` (15 % і 50 грн за ніч) |
| `create_booking` | обирає підтип: тариф від 1000.00 включно → Premium, інакше Standard |
| `Priced` | `Protocol`: властивості `nights`, `tier`, метод `total_price()` |
| `Occupancy`, `ReportSummary` | `@dataclass(frozen=True)`: завантаження номерів і підсумок звіту |
| `ReportWriter` | контекстний менеджер: пише у тимчасовий файл і замінює звіт лише після успіху |

Ціни округлюються до копійки (`Decimal`, `ROUND_HALF_UP`).

## Структура

```text
src/kzp_lab06/
├── __init__.py    # публічний мінімальний API
├── errors.py      # DataError
├── models.py      # Booking, підтипи, Priced, dataclass-підсумки
├── loader.py      # читання CSV і перетворення рядка на об'єкт
├── analysis.py    # обчислення над об'єктами через спільний протокол
├── reporting.py   # формування звіту, ReportWriter
└── cli.py         # аргументи командного рядка та коди завершення
tests/             # pytest
tests/legacy_v6/   # незмінна словникова модель ЛР № 6 для порівняння звітів
data/              # input.csv (контрольний), input-lab07.csv, empty.csv, broken.csv
reports/summary.txt  # приклад очікуваного звіту
tools/measure_memory.py  # пам'ять: словники проти об'єктів, список проти генератора
```

`models` не читає файли, `loader` не будує звіт, `analysis` не відкриває файли й не перевіряє конкретний підтип, `reporting` не читає CSV.

## Формат CSV

Кодування UTF-8, заголовок обов'язковий, порядок стовпців довільний:

```text
room,guest,check_in,check_out,rate
101,"Doe, John",2026-01-01,2026-01-04,150.00
```

| Поле | Тип після перетворення | Правило |
| :-- | :-- | :-- |
| `room` | `int` | більше нуля |
| `guest` | `str` | не порожнє; зайві пробіли прибираються |
| `check_in` | `date` | ISO `YYYY-MM-DD` |
| `check_out` | `date` | ISO `YYYY-MM-DD`, пізніше за `check_in` |
| `rate` | `float` | скінченне, не від'ємне; нуль дозволено |

Похідні поля запису: `nights` (кількість ночей) і `cost` (`nights × rate`).
Файл лише із заголовком є коректним порожнім входом. Файл без заголовка відхиляється.

## Показники звіту (варіант 14)

* **Відбір:** бронювання, активні на `reference_date`: `check_in <= дата < check_out`. Типова дата `2026-01-03`.
* **Словник:** кількість бронювань за тарифом `rate`.
* **Множина:** гості без повторів.
* **Звіт:** завантаження номерів (зайняті номери з усіх номерів файла) і найдовше проживання.

## Встановлення

Потрібен Python 3.11 або новіший.

```text
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS, Ubuntu
python -m pip install -e ".[dev]"
```

Якщо PowerShell забороняє активацію, запускайте `.venv\Scripts\python.exe` і `.venv\Scripts\ruff.exe` напряму.

## Запуск

```text
python -m kzp_lab06.cli data/input.csv reports/summary.txt
kzp-lab06 data/input.csv reports/summary.txt
kzp-lab06 data/input.csv reports/february.txt --reference-date 2026-02-01
kzp-lab06 data/input.csv reports/summary.txt --details
```

`--details` додатково друкує в консоль ціну з надбавками за рівнями (файл звіту не змінюється):

```text
Ціна з надбавками за рівнями:
  Premium: 20150.00
  Standard: 4508.18
Разом: 24658.18
```

| Код завершення | Значення |
| :-- | :-- |
| 0 | звіт записано |
| 2 | помилка вхідних даних (повідомлення в stderr) або хибні аргументи |
| 3 | звіт не вдалося записати |

Приклад помилки:

```text
> python -m kzp_lab06.cli data/broken.csv reports/x.txt
Помилка даних: Рядок 3: поле rate має бути числом
```

## Приклад звіту

```text
Звіт про бронювання готелю
Дата відбору: 2026-01-03
Записів: 7
Активні бронювання на дату: 4
  101 | Doe, John | 2026-01-01..2026-01-04
  205 | Diana Prince | 2026-01-03..2026-01-10
  210 | Sarah Connor | 2026-01-01..2026-01-11
  404 | Doe, John | 2026-01-02..2026-01-07
Завантаження номерів: 4 з 6 (66.67%)
Кількість бронювань за тарифом:
  0.00: 1
  150.00: 2
  200.00: 1
  220.50: 1
  1000.00: 1
  2000.00: 1
Гості без повторів: 6
  Anna Bell
  Clark Kent
  Dexter Morgan
  Diana Prince
  Doe, John
  Sarah Connor
Найдовше проживання: Sarah Connor, номер 210, ночей: 10 (2026-01-01..2026-01-11)
Сумарна кількість ночей: 35
Сумарна вартість: 21293.50
```

## Перевірки

```text
python -m pytest
ruff check .
ruff format --check .
python -m build
```

Встановлення wheel у чисте середовище без dev-залежностей:

```text
python -m venv .venv-wheel
.venv-wheel\Scripts\python -m pip install --no-deps dist\kzp_lab06-7.0.0-py3-none-any.whl
.venv-wheel\Scripts\python -m kzp_lab06.cli data\input.csv reports\wheel-summary.txt
```

У macOS та Ubuntu замість `.venv-wheel\Scripts\python` використовується `.venv-wheel/bin/python`.

## Потокова обробка та пам'ять

`loader.iter_records` є генератором, а `analysis.stream_summary` рахує показники за один прохід. Скрипт порівнює пам'ять словникової й об'єктної моделей, а також списку й генератора:

```text
python tools/measure_memory.py 200000
```

## CI

GitHub Actions (`.github/workflows/python.yml`) на Ubuntu, Windows і macOS запускає `pytest`, `ruff check`, `ruff format --check`, збирає wheel, встановлює його в чисте середовище, перевіряє успішний і помилковий запуск CLI та публікує wheel як артефакт.

**Автор:** Денис Матіїшин, група КІ-303
