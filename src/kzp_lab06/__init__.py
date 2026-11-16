"""Об'єктна обробка бронювань готелю з CSV-файла (лабораторні роботи № 6–7, варіант 14)."""

from .analysis import build_report, make_summary, revenue_by_tier, total_revenue
from .errors import DataError
from .loader import load_records
from .models import (
    Booking,
    Occupancy,
    PremiumBooking,
    Priced,
    ReportSummary,
    StandardBooking,
    create_booking,
)
from .reporting import ReportWriter, format_report, write_report

__all__ = [
    "Booking",
    "DataError",
    "Occupancy",
    "PremiumBooking",
    "Priced",
    "ReportSummary",
    "ReportWriter",
    "StandardBooking",
    "build_report",
    "create_booking",
    "format_report",
    "load_records",
    "make_summary",
    "revenue_by_tier",
    "total_revenue",
    "write_report",
]

__version__ = "7.0.0"
