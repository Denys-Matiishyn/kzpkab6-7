# kzp-lab06: звіт про бронювання готелю (Python)

Лабораторна робота № 6 з курсу «Кросплатформні засоби програмування», варіант 14 «Готель».
Пакет читає CSV-файл бронювань, перетворює текстові поля на типізовані значення, обчислює показники й записує детермінований текстовий звіт.

## Структура

```text
src/kzp_lab06/
├── __init__.py    # публічний мінімальний API
├── errors.py      # DataError
├── loader.py      # читання CSV і перетворення полів
├── analysis.py    # обчислення над записами
├── reporting.py   # формування й запис звіту
└── cli.py         # аргументи командного рядка та коди завершення
tests/             # pytest
data/              # input.csv, empty.csv, broken.csv
reports/summary.txt  # приклад очікуваного звіту
tools/measure_memory.py  # порівняння списку й генератора
```

`loader` не друкує звіт, `analysis` не відкриває файли, `reporting` не читає CSV.

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
.venv-wheel\Scripts\python -m pip install --no-deps dist\kzp_lab06-6.0.0-py3-none-any.whl
.venv-wheel\Scripts\python -m kzp_lab06.cli data\input.csv reports\wheel-summary.txt
```

У macOS та Ubuntu замість `.venv-wheel\Scripts\python` використовується `.venv-wheel/bin/python`.

## Потокова обробка (завдання із зірочкою)

`loader.iter_records` є генератором, а `analysis.stream_summary` рахує показники за один прохід. Порівняння зі списком:

```text
python tools/measure_memory.py 200000
```

## CI

GitHub Actions (`.github/workflows/python.yml`) на Ubuntu, Windows і macOS запускає `pytest`, `ruff check`, `ruff format --check`, збирає wheel, встановлює його в чисте середовище, перевіряє успішний і помилковий запуск CLI та публікує wheel як артефакт.

**Автор:** Денис Матіїшин, група КІ-303
