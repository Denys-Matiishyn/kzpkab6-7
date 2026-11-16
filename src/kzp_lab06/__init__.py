"""Звіт про бронювання готелю з CSV-файла (лабораторна робота № 6, варіант 14)."""

from .analysis import build_report, make_summary
from .errors import DataError
from .loader import load_records
from .reporting import format_report, write_report

__all__ = [
    "DataError",
    "build_report",
    "format_report",
    "load_records",
    "make_summary",
    "write_report",
]

__version__ = "6.0.0"
