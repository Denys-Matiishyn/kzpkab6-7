"""Тести читання CSV і перетворення полів."""

from datetime import date
from pathlib import Path

import pytest

from kzp_lab06.models import Booking
from kzp_lab06.errors import DataError
from kzp_lab06.loader import iter_records, load_records, parse_row

HEADER = "room,guest,check_in,check_out,rate\n"


def write_csv(tmp_path: Path, text: str) -> Path:
    """Записує текст у тимчасовий CSV-файл UTF-8."""
    path = tmp_path / "input.csv"
    path.write_text(text, encoding="utf-8", newline="")
    return path


def test_load_control_file(data_dir: Path, records: list[Booking]) -> None:
    """Контрольний файл дає сім типізованих записів у порядку файла."""
    assert load_records(data_dir / "input.csv") == records


def test_fields_are_converted_to_types(tmp_path: Path) -> None:
    """Текстові поля стають int, date і float, а похідні поля обчислюються."""
    path = write_csv(tmp_path, HEADER + " 101 ,Anna Bell,2026-01-04,2026-01-06, 150.50 \n")
    record = load_records(path)[0]
    assert record.as_dict() == {
        "room": 101,
        "guest": "Anna Bell",
        "check_in": date(2026, 1, 4),
        "check_out": date(2026, 1, 6),
        "rate": 150.5,
        "nights": 2,
        "cost": 301.0,
    }
    assert isinstance(record.room, int)
    assert isinstance(record.rate, float)


def test_guest_name_is_normalized(tmp_path: Path) -> None:
    """Зайві пробіли в імені прибираються."""
    path = write_csv(tmp_path, HEADER + "101,  Anna   Bell ,2026-01-04,2026-01-06,150\n")
    assert load_records(path)[0].guest == "Anna Bell"


def test_text_with_comma_quotes_and_cyrillic(tmp_path: Path) -> None:
    """Кома й лапки в лапках та кирилиця читаються як одне поле."""
    text = HEADER + '101,"Коваленко, Марія ""Маша""",2026-01-04,2026-01-06,150\n'
    assert load_records(write_csv(tmp_path, text))[0].guest == 'Коваленко, Марія "Маша"'


def test_windows_line_endings_are_accepted(tmp_path: Path) -> None:
    """Файл із роздільниками CRLF дає ті самі записи."""
    text = (HEADER + "101,Anna Bell,2026-01-04,2026-01-06,150\n").replace("\n", "\r\n")
    assert len(load_records(write_csv(tmp_path, text))) == 1


def test_column_order_does_not_matter(tmp_path: Path) -> None:
    """Стовпці знаходяться за назвою, а не за позицією."""
    text = "rate,room,check_out,check_in,guest\n150,101,2026-01-06,2026-01-04,Anna Bell\n"
    record = load_records(write_csv(tmp_path, text))[0]
    assert (record.room, record.rate, record.nights) == (101, 150.0, 2)


def test_header_only_file_gives_empty_list(data_dir: Path) -> None:
    """Файл лише із заголовком є коректним порожнім входом."""
    assert load_records(data_dir / "empty.csv") == []


def test_zero_byte_file_is_rejected(tmp_path: Path) -> None:
    """Файл без заголовка не можна відрізнити від помилки, тому він відхиляється."""
    with pytest.raises(DataError, match="немає рядка заголовка"):
        load_records(write_csv(tmp_path, ""))


def test_missing_column_is_named(tmp_path: Path) -> None:
    """Відсутній стовпець називається в повідомленні."""
    text = "room,guest,check_in,check_out\n101,Anna Bell,2026-01-04,2026-01-06\n"
    with pytest.raises(DataError, match="немає стовпців: rate"):
        load_records(write_csv(tmp_path, text))


def test_extra_column_is_named(tmp_path: Path) -> None:
    """Зайвий стовпець називається в повідомленні."""
    text = "room,guest,check_in,check_out,rate,note\n101,A,2026-01-04,2026-01-06,1,x\n"
    with pytest.raises(DataError, match="зайві стовпці: note"):
        load_records(write_csv(tmp_path, text))


def test_duplicated_column_is_rejected(tmp_path: Path) -> None:
    """Повтор назви стовпця відхиляється."""
    text = "room,guest,check_in,check_out,rate,rate\n101,A,2026-01-04,2026-01-06,1,2\n"
    with pytest.raises(DataError, match="повторюються"):
        load_records(write_csv(tmp_path, text))


def test_missing_value_in_row_is_reported(tmp_path: Path) -> None:
    """Коротший рядок дає помилку з номером рядка й назвою поля."""
    text = HEADER + "101,Anna Bell,2026-01-04,2026-01-06,150\n205,Diana Prince,2026-01-03\n"
    with pytest.raises(DataError, match="Рядок 3: немає значення поля check_out"):
        load_records(write_csv(tmp_path, text))


def test_too_many_values_in_row_are_reported(tmp_path: Path) -> None:
    """Кома без лапок у тексті дає зайве значення в рядку."""
    text = HEADER + "101,Doe, John,2026-01-04,2026-01-06,150\n"
    with pytest.raises(DataError, match="Рядок 2: забагато значень"):
        load_records(write_csv(tmp_path, text))


def test_invalid_number_keeps_cause(data_dir: Path) -> None:
    """Хибне число дає DataError з номером рядка, полем і першопричиною."""
    with pytest.raises(DataError, match="Рядок 3: поле rate має бути числом") as caught:
        load_records(data_dir / "broken.csv")
    assert isinstance(caught.value.__cause__, ValueError)


@pytest.mark.parametrize(
    ("row", "message"),
    [
        ("abc,Anna Bell,2026-01-04,2026-01-06,150", "поле room має бути цілим числом"),
        ("10.5,Anna Bell,2026-01-04,2026-01-06,150", "поле room має бути цілим числом"),
        ("0,Anna Bell,2026-01-04,2026-01-06,150", "поле room має бути більшим за нуль"),
        ("101,   ,2026-01-04,2026-01-06,150", "поле guest порожнє"),
        ("101,Anna Bell,04.01.2026,2026-01-06,150", "поле check_in має бути датою"),
        ("101,Anna Bell,2026-01-04,2026-02-30,150", "поле check_out має бути датою"),
        ("101,Anna Bell,2026-01-06,2026-01-06,150", "поле check_out має бути пізніше за check_in"),
        ("101,Anna Bell,2026-01-04,2026-01-06,", "поле rate має бути числом"),
        ("101,Anna Bell,2026-01-04,2026-01-06,-0.01", "поле rate не може бути від'ємним"),
        ("101,Anna Bell,2026-01-04,2026-01-06,nan", "поле rate має бути скінченним числом"),
        ("101,Anna Bell,2026-01-04,2026-01-06,inf", "поле rate має бути скінченним числом"),
    ],
)
def test_invalid_values_are_rejected(tmp_path: Path, row: str, message: str) -> None:
    """Кожне некоректне значення дає помилку з номером рядка та назвою поля."""
    with pytest.raises(DataError, match=f"Рядок 2: {message}"):
        load_records(write_csv(tmp_path, HEADER + row + "\n"))


def test_zero_rate_is_allowed(tmp_path: Path) -> None:
    """Нульовий тариф є граничним допустимим значенням."""
    record = load_records(write_csv(tmp_path, HEADER + "102,Clark Kent,2026-01-05,2026-01-06,0\n"))[
        0
    ]
    assert record.rate == 0.0
    assert record.cost == 0.0


def test_missing_file_keeps_os_error(tmp_path: Path) -> None:
    """Відсутній файл дає DataError з OSError як першопричиною."""
    with pytest.raises(DataError, match="Не вдалося прочитати файл") as caught:
        load_records(tmp_path / "absent.csv")
    assert isinstance(caught.value.__cause__, OSError)


def test_not_utf8_file_is_rejected(tmp_path: Path) -> None:
    """Файл в іншому кодуванні не читається мовчки з «кракозябрами»."""
    path = tmp_path / "cp1251.csv"
    path.write_bytes((HEADER + "101,Марія,2026-01-04,2026-01-06,150\n").encode("cp1251"))
    with pytest.raises(DataError) as caught:
        load_records(path)
    assert isinstance(caught.value.__cause__, UnicodeDecodeError)


def test_unclosed_quote_is_rejected(tmp_path: Path) -> None:
    """Незакриті лапки не дають тихо втратити записи."""
    text = HEADER + '101,"Anna Bell,2026-01-04,2026-01-06,150\n'
    with pytest.raises(DataError):
        load_records(write_csv(tmp_path, text))


def test_parse_row_reports_given_row_number() -> None:
    """parse_row використовує переданий номер рядка."""
    row = {"room": "1", "guest": "A", "check_in": "2026-01-01", "check_out": "x", "rate": "1"}
    with pytest.raises(DataError, match="Рядок 17: поле check_out"):
        parse_row(row, 17)


def test_iter_records_is_lazy(tmp_path: Path) -> None:
    """Генератор повертає коректні записи до того, як дійде до пошкодженого рядка."""
    text = HEADER + "101,Anna Bell,2026-01-04,2026-01-06,150\n205,Diana Prince,x,y,z\n"
    iterator = iter_records(write_csv(tmp_path, text))
    assert next(iterator).guest == "Anna Bell"
    with pytest.raises(DataError, match="Рядок 3"):
        next(iterator)


def test_loading_does_not_change_input_file(data_dir: Path) -> None:
    """Вхідний файл після читання лишається тим самим."""
    path = data_dir / "input.csv"
    before = path.read_bytes()
    load_records(path)
    assert path.read_bytes() == before
