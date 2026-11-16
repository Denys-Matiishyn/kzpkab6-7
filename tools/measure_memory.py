"""Порівнює пам'ять словникової та об'єктної моделей, а також списку й генератора.

Запуск: python tools/measure_memory.py [кількість_рядків]
Скрипт створює тимчасовий CSV і друкує пікову пам'ять за tracemalloc:
1) словникова модель ЛР № 6 (list[dict]) проти об'єктної моделі ЛР № 7 (класи з __slots__);
2) повний список об'єктів проти потокової обробки генератором.
Результати залежать від комп'ютера й версії Python.
"""

import csv
import sys
import time
import tracemalloc
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from kzp_lab06.analysis import build_report, stream_summary
from kzp_lab06.loader import iter_records, load_records

REFERENCE_DATE = date(2026, 1, 3)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tests"))

from legacy_v6 import loader as legacy_loader  # noqa: E402


def write_big_csv(path: Path, rows: int) -> None:
    """Записує CSV із заданою кількістю синтетичних бронювань обох підтипів."""
    start = date(2025, 12, 1)
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.writer(target)
        writer.writerow(["room", "guest", "check_in", "check_out", "rate"])
        for index in range(rows):
            check_in = start + timedelta(days=index % 60)
            check_out = check_in + timedelta(days=1 + index % 9)
            writer.writerow(
                [
                    100 + index % 400,
                    f"Guest, {index % 5000}",
                    check_in.isoformat(),
                    check_out.isoformat(),
                    f"{90 + (index % 12) * 95.5:.2f}",
                ]
            )


def measure(label: str, action):
    """Виконує дію та друкує час і пікову пам'ять."""
    tracemalloc.start()
    started = time.perf_counter()
    result = action()
    elapsed = time.perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"{label}: пік пам'яті {peak / 1024 / 1024:8.2f} МіБ, час {elapsed:6.2f} с")
    return result


def main() -> int:
    """Створює файл, вимірює всі підходи та звіряє результати."""
    sys.stdout.reconfigure(encoding="utf-8")
    rows = int(sys.argv[1]) if len(sys.argv) > 1 else 200_000
    with TemporaryDirectory() as temporary:
        path = Path(temporary) / "big.csv"
        write_big_csv(path, rows)
        print(f"Рядків: {rows}, розмір файла: {path.stat().st_size / 1024 / 1024:.2f} МіБ")
        print("1) Модель записів у пам'яті")
        dicts = measure("   Словники ЛР № 6 (list[dict])", lambda: legacy_loader.load_records(path))
        objects = measure("   Об'єкти ЛР № 7 (__slots__)  ", lambda: load_records(path))
        same_data = len(dicts) == len(objects) and all(
            booking.as_dict() == record for booking, record in zip(objects, dicts, strict=True)
        )
        del dicts, objects
        print("2) Повний звіт і потокова обробка")
        full = measure(
            "   Список (load_records)       ",
            lambda: build_report(load_records(path), REFERENCE_DATE),
        )
        streamed = measure(
            "   Генератор (iter_records)    ",
            lambda: stream_summary(iter_records(path), REFERENCE_DATE),
        )
    same = (
        same_data
        and full.count == streamed["count"]
        and full.total_nights == streamed["total_nights"]
        and dict(full.count_by_rate) == streamed["count_by_rate"]
        and full.occupancy.occupied == streamed["active_rooms"]
        and len(full.guests) == streamed["guest_count"]
    )
    print(f"Результати збігаються: {same}")
    return 0 if same else 1


if __name__ == "__main__":
    raise SystemExit(main())
