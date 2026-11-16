"""Тести командного рядка та кодів завершення."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from kzp_lab06.cli import EXIT_DATA_ERROR, EXIT_OK, EXIT_OUTPUT_ERROR, main


def test_success_writes_report_and_returns_zero(
    data_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Успішний запуск повертає 0, пише звіт і нічого не друкує в stderr."""
    output = tmp_path / "out" / "summary.txt"
    assert main([str(data_dir / "input.csv"), str(output)]) == EXIT_OK
    expected = (data_dir.parent / "reports" / "summary.txt").read_text(encoding="utf-8")
    assert output.read_text(encoding="utf-8") == expected
    assert capsys.readouterr().err == ""


def test_reference_date_option(data_dir: Path, tmp_path: Path) -> None:
    """Параметр --reference-date змінює відбір; порожній відбір є коректним звітом."""
    output = tmp_path / "summary.txt"
    code = main([str(data_dir / "input.csv"), str(output), "--reference-date", "2026-02-01"])
    assert code == EXIT_OK
    text = output.read_text(encoding="utf-8")
    assert "Дата відбору: 2026-02-01\n" in text
    assert "Активні бронювання на дату: 0\n" in text
    assert "Завантаження номерів: 0 з 6 (0.00%)\n" in text


def test_header_only_input_gives_empty_report(data_dir: Path, tmp_path: Path) -> None:
    """Файл лише із заголовком дає звіт із нулями й код 0."""
    output = tmp_path / "summary.txt"
    assert main([str(data_dir / "empty.csv"), str(output)]) == EXIT_OK
    assert "Записів: 0\n" in output.read_text(encoding="utf-8")


def test_broken_csv_returns_two_and_writes_nothing(
    data_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Пошкоджений CSV дає код 2, пояснення в stderr і не створює звіт."""
    output = tmp_path / "summary.txt"
    assert main([str(data_dir / "broken.csv"), str(output)]) == EXIT_DATA_ERROR
    captured = capsys.readouterr()
    assert captured.err == "Помилка даних: Рядок 3: поле rate має бути числом\n"
    assert captured.out == ""
    assert "Traceback" not in captured.err
    assert not output.exists()


def test_missing_input_returns_two(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Відсутній вхідний файл є помилкою даних."""
    code = main([str(tmp_path / "absent.csv"), str(tmp_path / "summary.txt")])
    assert code == EXIT_DATA_ERROR
    assert "Не вдалося прочитати файл" in capsys.readouterr().err


def test_same_input_and_output_is_rejected(tmp_path: Path, data_dir: Path) -> None:
    """Вхідний файл не можна перезаписати звітом."""
    source = tmp_path / "input.csv"
    source.write_bytes((data_dir / "input.csv").read_bytes())
    before = source.read_bytes()
    assert main([str(source), str(source)]) == EXIT_DATA_ERROR
    assert source.read_bytes() == before


def test_unwritable_output_returns_three(
    data_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Якщо шлях звіту є каталогом, повертається окремий код помилки запису."""
    assert main([str(data_dir / "input.csv"), str(tmp_path)]) == EXIT_OUTPUT_ERROR
    assert "Не вдалося записати звіт" in capsys.readouterr().err


def test_invalid_reference_date_is_usage_error(data_dir: Path, tmp_path: Path) -> None:
    """Хибна дата в аргументі завершує програму з кодом помилки аргументів."""
    with pytest.raises(SystemExit) as caught:
        main(
            [str(data_dir / "input.csv"), str(tmp_path / "s.txt"), "--reference-date", "03.01.2026"]
        )
    assert caught.value.code == 2


def run_python(*arguments: str, src: Path) -> subprocess.CompletedProcess[bytes]:
    """Запускає окремий процес Python із пакетом у PYTHONPATH."""
    env = {**os.environ, "PYTHONPATH": str(src), "PYTHONIOENCODING": "utf-8"}
    return subprocess.run([sys.executable, *arguments], capture_output=True, env=env, check=False)


def test_module_runs_as_script(data_dir: Path, tmp_path: Path) -> None:
    """Команда python -m kzp_lab06.cli працює і повертає коди завершення процесу."""
    src = data_dir.parent / "src"

    good = run_python(
        "-m", "kzp_lab06.cli", str(data_dir / "input.csv"), str(tmp_path / "ok.txt"), src=src
    )
    assert good.returncode == 0
    assert (tmp_path / "ok.txt").exists()

    bad = run_python(
        "-m", "kzp_lab06.cli", str(data_dir / "broken.csv"), str(tmp_path / "bad.txt"), src=src
    )
    assert bad.returncode == 2
    assert "Рядок 3" in bad.stderr.decode("utf-8")
    assert not (tmp_path / "bad.txt").exists()


def test_importing_modules_does_not_run_cli(data_dir: Path) -> None:
    """Імпорт пакета й модуля cli нічого не друкує та не потребує аргументів."""
    result = run_python("-c", "import kzp_lab06, kzp_lab06.cli", src=data_dir.parent / "src")
    assert result.returncode == 0
    assert result.stdout == b""
    assert result.stderr == b""
