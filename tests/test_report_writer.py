"""Тести контекстного менеджера ReportWriter."""

from pathlib import Path

import pytest

from kzp_lab06.reporting import ReportWriter, write_report


def test_writer_replaces_file_after_success(tmp_path: Path) -> None:
    """Після успішного блоку звіт записано, файл закрито, тимчасового файла немає."""
    target = tmp_path / "out" / "report.txt"
    writer = ReportWriter(target)
    assert writer.closed
    with writer as stream:
        stream.write("Готово\n")
        assert not writer.closed
    assert writer.closed
    assert target.read_bytes() == "Готово\n".encode()
    assert list(target.parent.iterdir()) == [target]


def test_writer_closes_file_and_keeps_old_report_on_exception(tmp_path: Path) -> None:
    """Виняток у блоці закриває файл, не змінює старий звіт і передається далі."""
    target = tmp_path / "report.txt"
    target.write_text("старий звіт\n", encoding="utf-8")
    writer = ReportWriter(target)
    with pytest.raises(RuntimeError, match="збій"):
        with writer as stream:
            stream.write("частковий текст")
            raise RuntimeError("збій під час формування")
    assert writer.closed
    assert target.read_text(encoding="utf-8") == "старий звіт\n"
    assert list(tmp_path.iterdir()) == [target]


def test_writer_does_not_create_file_on_exception(tmp_path: Path) -> None:
    """Якщо звіту ще не було, після винятку файл не з'являється."""
    target = tmp_path / "report.txt"
    with pytest.raises(ValueError):
        with ReportWriter(target) as stream:
            stream.write("x")
            raise ValueError
    assert not target.exists()


def test_write_report_uses_writer(tmp_path: Path) -> None:
    """write_report записує текст через контекстний менеджер з LF."""
    target = tmp_path / "report.txt"
    write_report(target, "один\nдва\n")
    assert target.read_bytes() == "один\nдва\n".encode()
