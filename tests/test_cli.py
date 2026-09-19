"""Integration tests for habits.cli (spec 001)."""

from datetime import date
from pathlib import Path

import pytest

from habits.cli import main
from habits.storage import load

TODAY = date(2026, 9, 19)


def _run(monkeypatch, tmp_path: Path, argv: list[str], today: date = TODAY) -> int:
    monkeypatch.setenv("HABITS_FILE", str(tmp_path / "habits.json"))
    return main(argv, today=today)


# --- T19: parser and usage errors (E-1, exit 2) ---


def test_rf10_unknown_command_exits_2(monkeypatch, tmp_path, capsys) -> None:
    code = _run(monkeypatch, tmp_path, ["bogus"])
    assert code == 2
    assert capsys.readouterr().err.startswith("Error: uso incorrecto")


def test_rf10_missing_argument_exits_2(monkeypatch, tmp_path, capsys) -> None:
    code = _run(monkeypatch, tmp_path, ["add"])
    assert code == 2
    assert capsys.readouterr().err.startswith("Error: uso incorrecto")


def test_rf10_extra_argument_exits_2(monkeypatch, tmp_path, capsys) -> None:
    code = _run(monkeypatch, tmp_path, ["add", "Leer", "Extra"])
    assert code == 2
    assert capsys.readouterr().err.startswith("Error: uso incorrecto")


# --- T20: data path, "today" and domain errors (E-5, exit 1) ---


def test_rf9_corrupt_file_exits_1_and_is_untouched(monkeypatch, tmp_path, capsys) -> None:
    path = tmp_path / "habits.json"
    path.write_text("{not json", encoding="utf-8")
    original = path.read_bytes()
    code = _run(monkeypatch, tmp_path, ["list"])
    assert code == 1
    err = capsys.readouterr().err
    assert err.startswith("Error: los datos guardados están dañados")
    assert path.read_bytes() == original


def test_rf9_default_path_is_home_habits_json(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("HABITS_FILE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    code = main(["add", "Leer"], today=TODAY)
    assert code == 0
    assert (tmp_path / ".habits.json").is_file()


# --- T21: `add` and `list` ---


def test_rf1_add_creates_habit(monkeypatch, tmp_path, capsys) -> None:
    code = _run(monkeypatch, tmp_path, ["add", "Leer"])
    assert code == 0
    assert capsys.readouterr().out == "Hábito «Leer» creado.\n"


def test_rf1_add_duplicate_exits_1(monkeypatch, tmp_path, capsys) -> None:
    _run(monkeypatch, tmp_path, ["add", "Leer"])
    code = _run(monkeypatch, tmp_path, ["add", "leer"])
    assert code == 1
    assert capsys.readouterr().err == "Error: ya existe un hábito llamado «leer».\n"


def test_rf6_list_empty(monkeypatch, tmp_path, capsys) -> None:
    code = _run(monkeypatch, tmp_path, ["list"])
    assert code == 0
    assert capsys.readouterr().out == "No hay hábitos todavía.\n"


def test_rf6_list_shows_streak_and_done_today(monkeypatch, tmp_path, capsys) -> None:
    _run(monkeypatch, tmp_path, ["add", "Leer"])
    _run(monkeypatch, tmp_path, ["done", "Leer"])
    _run(monkeypatch, tmp_path, ["add", "Correr"])
    capsys.readouterr()
    code = _run(monkeypatch, tmp_path, ["list"])
    assert code == 0
    out = capsys.readouterr().out
    assert out == (
        "[ ] Correr — racha: 0 días\n"
        "[x] Leer — racha: 1 día\n"
    )


# --- T22: `done` and `undo` ---


def test_rf3_done_marks_today(monkeypatch, tmp_path, capsys) -> None:
    _run(monkeypatch, tmp_path, ["add", "Leer"])
    capsys.readouterr()
    code = _run(monkeypatch, tmp_path, ["done", "Leer"])
    assert code == 0
    assert capsys.readouterr().out == "«Leer» marcado el 2026-09-19.\n"


def test_rf3_done_twice_shows_warning_and_exits_0(monkeypatch, tmp_path, capsys) -> None:
    _run(monkeypatch, tmp_path, ["add", "Leer"])
    _run(monkeypatch, tmp_path, ["done", "Leer"])
    capsys.readouterr()
    code = _run(monkeypatch, tmp_path, ["done", "Leer"])
    assert code == 0
    assert capsys.readouterr().out == "«Leer» ya estaba marcado el 2026-09-19.\n"


def test_rf5_undo_unmarks_day(monkeypatch, tmp_path, capsys) -> None:
    _run(monkeypatch, tmp_path, ["add", "Leer"])
    _run(monkeypatch, tmp_path, ["done", "Leer"])
    capsys.readouterr()
    code = _run(monkeypatch, tmp_path, ["undo", "Leer"])
    assert code == 0
    assert capsys.readouterr().out == "«Leer» desmarcado el 2026-09-19.\n"


def test_rf5_undo_not_marked_shows_warning_and_exits_0(monkeypatch, tmp_path, capsys) -> None:
    _run(monkeypatch, tmp_path, ["add", "Leer"])
    capsys.readouterr()
    code = _run(monkeypatch, tmp_path, ["undo", "Leer"])
    assert code == 0
    assert capsys.readouterr().out == "«Leer» no estaba marcado el 2026-09-19.\n"


def test_rf4_done_with_valid_date(monkeypatch, tmp_path, capsys) -> None:
    _run(monkeypatch, tmp_path, ["add", "Leer"])
    capsys.readouterr()
    code = _run(monkeypatch, tmp_path, ["done", "Leer", "--date", "2026-09-01"])
    assert code == 0
    assert capsys.readouterr().out == "«Leer» marcado el 2026-09-01.\n"


def test_rf4_done_with_invalid_date_exits_1(monkeypatch, tmp_path, capsys) -> None:
    _run(monkeypatch, tmp_path, ["add", "Leer"])
    code = _run(monkeypatch, tmp_path, ["done", "Leer", "--date", "2026-02-30"])
    assert code == 1
    err = capsys.readouterr().err
    assert err.startswith("Error: la fecha «2026-02-30» no es válida")


def test_rf2_done_missing_habit_exits_1(monkeypatch, tmp_path, capsys) -> None:
    code = _run(monkeypatch, tmp_path, ["done", "Correr"])
    assert code == 1
    assert capsys.readouterr().err == "Error: el hábito «Correr» no existe.\n"


# --- T23: `rename` ---


def test_rf7_rename_shows_message_and_exits_0(monkeypatch, tmp_path, capsys) -> None:
    _run(monkeypatch, tmp_path, ["add", "Leer"])
    capsys.readouterr()
    code = _run(monkeypatch, tmp_path, ["rename", "Leer", "Lectura"])
    assert code == 0
    assert capsys.readouterr().out == "«Leer» renombrado a «Lectura».\n"


def test_rf7_rename_to_duplicate_exits_1(monkeypatch, tmp_path, capsys) -> None:
    _run(monkeypatch, tmp_path, ["add", "Leer"])
    _run(monkeypatch, tmp_path, ["add", "Correr"])
    code = _run(monkeypatch, tmp_path, ["rename", "Leer", "Correr"])
    assert code == 1
    assert capsys.readouterr().err == "Error: ya existe un hábito llamado «Correr».\n"


def test_rf7_rename_keeps_history(monkeypatch, tmp_path, capsys) -> None:
    _run(monkeypatch, tmp_path, ["add", "Leer"])
    _run(monkeypatch, tmp_path, ["done", "Leer"])
    _run(monkeypatch, tmp_path, ["rename", "Leer", "Lectura"])
    capsys.readouterr()
    _run(monkeypatch, tmp_path, ["list"])
    assert capsys.readouterr().out == "[x] Lectura — racha: 1 día\n"


# --- T24: `delete` with confirmation ---


@pytest.mark.parametrize("answer", ["s", "S", " s "])
def test_rf8_delete_confirmed_removes_habit(monkeypatch, tmp_path, capsys, answer) -> None:
    _run(monkeypatch, tmp_path, ["add", "Leer"])
    capsys.readouterr()
    monkeypatch.setattr("builtins.input", lambda prompt="": answer)
    code = _run(monkeypatch, tmp_path, ["delete", "Leer"])
    assert code == 0
    assert capsys.readouterr().out == "Hábito «Leer» borrado.\n"
    data = load(tmp_path / "habits.json")
    assert data["habits"] == []


@pytest.mark.parametrize("answer", ["n", "si", "sí", ""])
def test_rf8_delete_declined_cancels(monkeypatch, tmp_path, capsys, answer) -> None:
    _run(monkeypatch, tmp_path, ["add", "Leer"])
    capsys.readouterr()
    monkeypatch.setattr("builtins.input", lambda prompt="": answer)
    code = _run(monkeypatch, tmp_path, ["delete", "Leer"])
    assert code == 0
    assert capsys.readouterr().out == "Borrado cancelado.\n"
    data = load(tmp_path / "habits.json")
    assert len(data["habits"]) == 1


def test_rf8_delete_eof_cancels(monkeypatch, tmp_path, capsys) -> None:
    _run(monkeypatch, tmp_path, ["add", "Leer"])
    capsys.readouterr()

    def raise_eof(prompt: str = "") -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)
    code = _run(monkeypatch, tmp_path, ["delete", "Leer"])
    assert code == 0
    assert capsys.readouterr().out == "Borrado cancelado.\n"
    data = load(tmp_path / "habits.json")
    assert len(data["habits"]) == 1


def test_rf8_delete_ctrl_c_exits_130(monkeypatch, tmp_path, capsys) -> None:
    _run(monkeypatch, tmp_path, ["add", "Leer"])

    def raise_interrupt(prompt: str = "") -> str:
        raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", raise_interrupt)
    code = _run(monkeypatch, tmp_path, ["delete", "Leer"])
    assert code == 130
    data = load(tmp_path / "habits.json")
    assert len(data["habits"]) == 1


# --- T25: names starting with "-" ---


def test_rf0_add_name_after_double_dash(monkeypatch, tmp_path, capsys) -> None:
    code = _run(monkeypatch, tmp_path, ["add", "--", "-leer"])
    assert code == 0
    assert capsys.readouterr().out == "Hábito «-leer» creado.\n"


def test_rf10_add_dash_name_without_separator_exits_2(monkeypatch, tmp_path, capsys) -> None:
    code = _run(monkeypatch, tmp_path, ["add", "-leer"])
    assert code == 2
