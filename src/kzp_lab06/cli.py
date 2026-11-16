"""Командний рядок: аргументи, запуск обробки та перетворення помилок на коди завершення."""

import argparse
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from .analysis import build_report, revenue_by_tier, total_revenue
from .errors import DataError
from .loader import load_records
from .reporting import format_report, write_report

DEFAULT_REFERENCE_DATE = date(2026, 1, 3)

EXIT_OK = 0
EXIT_DATA_ERROR = 2
EXIT_OUTPUT_ERROR = 3


def _print_error(message: str) -> None:
    """Виводить повідомлення в stderr у кодуванні UTF-8."""
    try:
        # Консоль Windows може мати інше кодування, тому UTF-8 задається явно.
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    print(message, file=sys.stderr)


def _print_out(text: str) -> None:
    """Виводить текст у stdout у кодуванні UTF-8."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    print(text, end="")


def _iso_date(text: str) -> date:
    """Перетворює аргумент командного рядка на дату."""
    try:
        return date.fromisoformat(text)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"дата має бути у форматі YYYY-MM-DD: {text}") from error


def build_parser() -> argparse.ArgumentParser:
    """Створює парсер аргументів командного рядка."""
    parser = argparse.ArgumentParser(
        prog="kzp-lab06",
        description="Будує текстовий звіт про бронювання готелю з CSV-файла.",
    )
    parser.add_argument("input_csv", type=Path, help="вхідний CSV-файл у кодуванні UTF-8")
    parser.add_argument("output_report", type=Path, help="файл текстового звіту")
    parser.add_argument(
        "--reference-date",
        type=_iso_date,
        default=DEFAULT_REFERENCE_DATE,
        help=f"дата відбору активних бронювань (типово {DEFAULT_REFERENCE_DATE.isoformat()})",
    )
    parser.add_argument(
        "--details",
        action="store_true",
        help="вивести в консоль ціни з надбавками за рівнями обслуговування",
    )
    return parser


def format_details(records: list) -> str:
    """Форматує ціни з надбавками за рівнями; звіт у файлі від цього не змінюється."""
    lines = ["Ціна з надбавками за рівнями:"]
    for tier, amount in revenue_by_tier(records).items():
        lines.append(f"  {tier}: {amount:.2f}")
    lines.append(f"Разом: {total_revenue(records):.2f}")
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    """Обробляє аргументи, будує та записує звіт.

    Повертає 0 після успіху, 2 для помилки вхідних даних і 3, якщо звіт не вдалося
    записати. Вхідний файл не змінюється.
    """
    args = build_parser().parse_args(argv)
    if args.input_csv.resolve() == args.output_report.resolve():
        _print_error("Помилка даних: вхідний і вихідний файли мають бути різними")
        return EXIT_DATA_ERROR
    try:
        records = load_records(args.input_csv)
        report = format_report(build_report(records, args.reference_date))
    except DataError as error:
        _print_error(f"Помилка даних: {error}")
        return EXIT_DATA_ERROR
    try:
        write_report(args.output_report, report)
    except OSError as error:
        _print_error(f"Не вдалося записати звіт: {args.output_report} ({error})")
        return EXIT_OUTPUT_ERROR
    if args.details:
        _print_out(format_details(records))
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
