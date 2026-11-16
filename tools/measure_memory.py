"""Порівнює пам'ять і час обробки великого CSV списком і генератором.

Запуск: python tools/measure_memory.py [кількість_рядків]
Скрипт створює тимчасовий CSV, обробляє його двома способами та друкує пікову пам'ять
за tracemalloc. Результати залежать від комп'ютера й версії Python.
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


def write_big_csv(path: Path, rows: int) -> None:
    """Записує CSV із заданою кількістю синтетичних бронювань."""
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
                    f"{90 + (index % 12) * 25.5:.2f}",
                ]
            )


def measure(label: str, action) -> dict:
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
    """Створює файл, вимірює обидва підходи та звіряє результати."""
    sys.stdout.reconfigure(encoding="utf-8")
    rows = int(sys.argv[1]) if len(sys.argv) > 1 else 200_000
    with TemporaryDirectory() as temporary:
        path = Path(temporary) / "big.csv"
        write_big_csv(path, rows)
        print(f"Рядків: {rows}, розмір файла: {path.stat().st_size / 1024 / 1024:.2f} МіБ")
        full = measure(
            "Список (load_records)   ",
            lambda: build_report(load_records(path), REFERENCE_DATE),
        )
        streamed = measure(
            "Генератор (iter_records)",
            lambda: stream_summary(iter_records(path), REFERENCE_DATE),
        )
    same = (
        full["count"] == streamed["count"]
        and full["total_nights"] == streamed["total_nights"]
        and full["count_by_rate"] == streamed["count_by_rate"]
        and full["occupancy"]["occupied"] == streamed["active_rooms"]
        and len(full["guests"]) == streamed["guest_count"]
    )
    print(f"Результати збігаються: {same}")
    return 0 if same else 1


if __name__ == "__main__":
    raise SystemExit(main())
