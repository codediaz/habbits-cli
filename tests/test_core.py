"""Tests for the pure domain logic in habits.core (spec 001)."""

from datetime import date

import pytest

from habits.core import (
    DuplicateHabitError,
    HabitError,
    HabitNotFoundError,
    InvalidDateError,
    InvalidNameError,
    add_habit,
    current_streak,
    find_habit,
    list_rows,
    mark_done,
    name_key,
    normalize_name,
    parse_date,
    remove_habit,
    rename_habit,
    unmark_done,
    validate_name,
)


# --- T03: domain exceptions (RF-10, message table E-0, E-2, E-3, E-4) ---
# The CLI prints errors as "Error: <message>", so each test checks that full line.


@pytest.mark.parametrize(
    ("reason", "expected"),
    [
        ("está vacío", "Error: el nombre no es válido: está vacío."),
        (
            "tiene más de 50 caracteres",
            "Error: el nombre no es válido: tiene más de 50 caracteres.",
        ),
        (
            "contiene caracteres no imprimibles",
            "Error: el nombre no es válido: contiene caracteres no imprimibles.",
        ),
    ],
)
def test_rf10_e0_invalid_name_message(reason: str, expected: str) -> None:
    assert f"Error: {InvalidNameError(reason)}" == expected


def test_rf10_e2_duplicate_habit_message() -> None:
    assert f"Error: {DuplicateHabitError('leer')}" == (
        "Error: ya existe un hábito llamado «leer»."
    )


def test_rf10_e3_habit_not_found_message() -> None:
    assert f"Error: {HabitNotFoundError('Correr')}" == (
        "Error: el hábito «Correr» no existe."
    )


def test_rf10_e4_invalid_date_message() -> None:
    assert f"Error: {InvalidDateError('2026-02-30')}" == (
        "Error: la fecha «2026-02-30» no es válida "
        "(usa AAAA-MM-DD, entre 2000-01-01 y hoy)."
    )


@pytest.mark.parametrize(
    "error",
    [
        InvalidNameError("está vacío"),
        DuplicateHabitError("Leer"),
        HabitNotFoundError("Leer"),
        InvalidDateError("x"),
    ],
)
def test_rf10_domain_errors_share_base_class(error: HabitError) -> None:
    assert isinstance(error, HabitError)
    assert isinstance(error, Exception)


def test_rf10_errors_keep_their_data() -> None:
    assert InvalidNameError("está vacío").reason == "está vacío"
    assert DuplicateHabitError("Leer").name == "Leer"
    assert HabitNotFoundError("Leer").name == "Leer"
    assert InvalidDateError("2026-9-1").text == "2026-9-1"


# --- T04: name normalization (RF-0) ---


def test_rf0_normalize_strips_edge_spaces() -> None:
    assert normalize_name("  Leer  ") == "Leer"


def test_rf0_normalize_collapses_internal_spaces() -> None:
    assert normalize_name("Leer   un  libro") == "Leer un libro"


def test_rf0_normalize_treats_unicode_spaces_as_spaces() -> None:
    # NBSP, en space, ideographic space
    assert normalize_name("\u00a0Leer\u2002\u00a0libro\u3000") == "Leer libro"


def test_rf0_normalize_converts_nfd_to_nfc() -> None:
    decomposed = "Ingle\u0301s"  # "e" + combining acute accent
    assert normalize_name(decomposed) == "Ingl\u00e9s"
    assert len(normalize_name(decomposed)) == 6


def test_rf0_normalize_keeps_internal_tab() -> None:
    # A tab is not a space for RF-0: it must survive so validation can reject it.
    assert normalize_name("Leer\tlibro") == "Leer\tlibro"


def test_rf0_normalize_keeps_edge_tab() -> None:
    assert normalize_name(" \tLeer ") == "\tLeer"


def test_rf0_normalize_only_spaces_gives_empty() -> None:
    assert normalize_name(" \u00a0  ") == ""


def test_rf0_normalize_keeps_case_and_other_characters() -> None:
    assert normalize_name("-Leer 2 ÑANDÚ") == "-Leer 2 ÑANDÚ"


# --- T05: name validation (RF-0) ---


def test_rf0_validate_accepts_normal_name() -> None:
    assert validate_name("  Leer  ") == "Leer"


def test_rf0_validate_rejects_empty_name() -> None:
    with pytest.raises(InvalidNameError) as exc_info:
        validate_name("")
    assert exc_info.value.reason == "está vacío"


def test_rf0_validate_rejects_only_spaces() -> None:
    with pytest.raises(InvalidNameError) as exc_info:
        validate_name("      ")
    assert exc_info.value.reason == "está vacío"


def test_rf0_validate_accepts_fifty_characters() -> None:
    name = "a" * 50
    assert validate_name(name) == name


def test_rf0_validate_rejects_fifty_one_characters() -> None:
    with pytest.raises(InvalidNameError) as exc_info:
        validate_name("a" * 51)
    assert exc_info.value.reason == "tiene más de 50 caracteres"


def test_rf0_validate_rejects_internal_tab() -> None:
    with pytest.raises(InvalidNameError) as exc_info:
        validate_name("Leer\tlibro")
    assert exc_info.value.reason == "contiene caracteres no imprimibles"


def test_rf0_validate_accepts_numeric_name() -> None:
    assert validate_name("2026") == "2026"


def test_rf0_validate_accepts_name_starting_with_dash() -> None:
    assert validate_name("-leer") == "-leer"


# --- T06: comparison key and lookup (RF-0, RF-2) ---


def test_rf0_name_key_equal_case() -> None:
    assert name_key("Leer") == name_key("LEER")


def test_rf0_name_key_eszett_equals_ss() -> None:
    assert name_key("straße") == name_key("strasse")


def test_rf0_name_key_accents_are_distinct() -> None:
    assert name_key("Inglés") != name_key("ingles")


def test_rf0_name_key_nfc_equals_nfd() -> None:
    assert name_key("Inglés") == name_key("Inglés")


def _data(*names: str) -> dict:
    return {"version": 1, "habits": [{"name": n, "done": []} for n in names]}


def test_rf2_find_habit_returns_matching_dict() -> None:
    data = _data("Leer", "Correr")
    habit = find_habit(data, "leer")
    assert habit["name"] == "Leer"


def test_rf2_find_habit_missing_raises() -> None:
    data = _data("Leer")
    with pytest.raises(HabitNotFoundError) as exc_info:
        find_habit(data, "Correr")
    assert exc_info.value.name == "Correr"


# --- T07: create habit (RF-1) ---


def test_rf1_add_habit_creates_entry() -> None:
    data = _data()
    name = add_habit(data, "  Leer  ")
    assert name == "Leer"
    assert data["habits"] == [{"name": "Leer", "done": []}]


def test_rf1_add_habit_rejects_duplicate_case_insensitive() -> None:
    data = _data("Leer")
    with pytest.raises(DuplicateHabitError) as exc_info:
        add_habit(data, "LEER")
    assert exc_info.value.name == "LEER"
    assert data["habits"] == [{"name": "Leer", "done": []}]


def test_rf1_add_habit_rejects_invalid_name_without_changes() -> None:
    data = _data("Leer")
    with pytest.raises(InvalidNameError):
        add_habit(data, "")
    assert data["habits"] == [{"name": "Leer", "done": []}]


# --- T08: date validation (RF-4) ---


def test_rf4_parse_date_accepts_today() -> None:
    today = date(2026, 9, 19)
    assert parse_date("2026-09-19", today) == today


def test_rf4_parse_date_accepts_lower_bound() -> None:
    today = date(2026, 9, 19)
    assert parse_date("2000-01-01", today) == date(2000, 1, 1)


def test_rf4_parse_date_rejects_before_lower_bound() -> None:
    today = date(2026, 9, 19)
    with pytest.raises(InvalidDateError):
        parse_date("1999-12-31", today)


def test_rf4_parse_date_rejects_future() -> None:
    today = date(2026, 9, 19)
    with pytest.raises(InvalidDateError):
        parse_date("2026-09-20", today)


def test_rf4_parse_date_rejects_nonexistent_day() -> None:
    today = date(2026, 9, 19)
    with pytest.raises(InvalidDateError):
        parse_date("2026-02-30", today)


def test_rf4_parse_date_rejects_invalid_month() -> None:
    today = date(2026, 9, 19)
    with pytest.raises(InvalidDateError):
        parse_date("2026-13-01", today)


def test_rf4_parse_date_rejects_missing_leading_zeros() -> None:
    today = date(2026, 9, 19)
    with pytest.raises(InvalidDateError):
        parse_date("2026-9-1", today)


def test_rf4_parse_date_rejects_other_format() -> None:
    today = date(2026, 9, 19)
    with pytest.raises(InvalidDateError):
        parse_date("19/09/2026", today)


# --- T09: mark a day (RF-3, RF-4) ---


def test_rf3_mark_done_marks_today() -> None:
    data = _data("Leer")
    today = date(2026, 9, 19)
    changed = mark_done(data, "Leer", today)
    assert changed is True
    assert find_habit(data, "Leer")["done"] == ["2026-09-19"]


def test_rf3_mark_done_twice_returns_false_without_changes() -> None:
    data = _data("Leer")
    today = date(2026, 9, 19)
    mark_done(data, "Leer", today)
    changed = mark_done(data, "Leer", today)
    assert changed is False
    assert find_habit(data, "Leer")["done"] == ["2026-09-19"]


def test_rf4_mark_done_past_day() -> None:
    data = _data("Leer")
    changed = mark_done(data, "Leer", date(2026, 9, 1))
    assert changed is True
    assert find_habit(data, "Leer")["done"] == ["2026-09-01"]


def test_rf9_mark_done_keeps_done_sorted() -> None:
    data = _data("Leer")
    mark_done(data, "Leer", date(2026, 9, 19))
    mark_done(data, "Leer", date(2026, 9, 1))
    mark_done(data, "Leer", date(2026, 9, 10))
    assert find_habit(data, "Leer")["done"] == [
        "2026-09-01",
        "2026-09-10",
        "2026-09-19",
    ]


# --- T10: unmark a day (RF-5) ---


def test_rf5_unmark_done_removes_marked_day() -> None:
    data = _data("Leer")
    mark_done(data, "Leer", date(2026, 9, 19))
    changed = unmark_done(data, "Leer", date(2026, 9, 19))
    assert changed is True
    assert find_habit(data, "Leer")["done"] == []


def test_rf5_unmark_done_not_marked_returns_false() -> None:
    data = _data("Leer")
    changed = unmark_done(data, "Leer", date(2026, 9, 19))
    assert changed is False
    assert find_habit(data, "Leer")["done"] == []


def test_rf5_unmark_done_missing_habit_raises() -> None:
    data = _data()
    with pytest.raises(HabitNotFoundError):
        unmark_done(data, "Leer", date(2026, 9, 19))


# --- T11: current streak (RF-6) ---


def test_rf6_streak_zero_when_no_dates() -> None:
    assert current_streak(set(), date(2026, 9, 19)) == 0


def test_rf6_streak_only_today() -> None:
    today = date(2026, 9, 19)
    assert current_streak({today}, today) == 1


def test_rf6_streak_kept_when_today_unmarked_but_yesterday_marked() -> None:
    today = date(2026, 9, 19)
    yesterday = date(2026, 9, 18)
    assert current_streak({yesterday}, today) == 1


def test_rf6_streak_broken_by_one_day_gap() -> None:
    today = date(2026, 9, 19)
    dates = {today, date(2026, 9, 17)}  # missing the 18th
    assert current_streak(dates, today) == 1


def test_rf6_streak_ignores_input_order() -> None:
    today = date(2026, 9, 19)
    dates = {date(2026, 9, 17), today, date(2026, 9, 18)}
    assert current_streak(dates, today) == 3


def test_rf6_streak_crosses_month_boundary() -> None:
    today = date(2026, 3, 1)
    dates = {date(2026, 2, 28), today}
    assert current_streak(dates, today) == 2


def test_rf6_streak_crosses_year_boundary() -> None:
    today = date(2026, 1, 1)
    dates = {date(2025, 12, 31), today}
    assert current_streak(dates, today) == 2


def test_rf6_streak_leap_day() -> None:
    today = date(2024, 3, 1)
    dates = {date(2024, 2, 29), date(2024, 2, 28), today}
    assert current_streak(dates, today) == 3


def test_rf6_streak_unmark_middle_breaks_it() -> None:
    # Days 17, 18 marked; 19 removed; today is the 19th -> only yesterday counts.
    today = date(2026, 9, 19)
    dates = {date(2026, 9, 17), date(2026, 9, 18)}
    assert current_streak(dates, today) == 2


def test_rf6_streak_unmark_today_counts_up_to_yesterday() -> None:
    today = date(2026, 9, 19)
    dates = {date(2026, 9, 18), date(2026, 9, 17)}  # today's mark removed
    assert current_streak(dates, today) == 2


def test_rf6_streak_ignores_future_dates() -> None:
    today = date(2026, 9, 19)
    dates = {today, date(2026, 9, 20)}  # a future date somehow in the data
    assert current_streak(dates, today) == 1


def test_rf6_streak_three_years() -> None:
    today = date(2026, 9, 19)
    start = date(2023, 9, 19)
    days = (today - start).days + 1
    dates = {date.fromordinal(start.toordinal() + i) for i in range(days)}
    assert current_streak(dates, today) == days


# --- T12: list rows (RF-6) ---


def test_rf6_list_rows_empty() -> None:
    assert list_rows(_data(), date(2026, 9, 19)) == []


def test_rf6_list_rows_alphabetical_case_insensitive() -> None:
    data = _data("leer", "Correr")
    rows = list_rows(data, date(2026, 9, 19))
    assert [name for name, _, _ in rows] == ["Correr", "leer"]


def test_rf6_list_rows_tie_break_by_original_name() -> None:
    data = _data("beta", "Alfa", "alfa")
    rows = list_rows(data, date(2026, 9, 19))
    assert [name for name, _, _ in rows] == ["Alfa", "alfa", "beta"]


def test_rf6_list_rows_done_today_flag_and_streak() -> None:
    today = date(2026, 9, 19)
    data = _data("Leer")
    mark_done(data, "Leer", today)
    rows = list_rows(data, today)
    assert rows == [("Leer", True, 1)]


def test_rf6_list_rows_not_done_today() -> None:
    today = date(2026, 9, 19)
    data = _data("Leer")
    rows = list_rows(data, today)
    assert rows == [("Leer", False, 0)]


# --- T13: rename habit (RF-7) ---


def test_rf7_rename_habit_keeps_history() -> None:
    data = _data("Leer")
    mark_done(data, "Leer", date(2026, 9, 19))
    old, new = rename_habit(data, "Leer", "Lectura")
    assert (old, new) == ("Leer", "Lectura")
    habit = find_habit(data, "Lectura")
    assert habit["done"] == ["2026-09-19"]


def test_rf7_rename_to_own_name_with_different_case_is_accepted() -> None:
    data = _data("leer")
    old, new = rename_habit(data, "leer", "Leer")
    assert (old, new) == ("leer", "Leer")
    assert find_habit(data, "leer")["name"] == "Leer"
    assert len(data["habits"]) == 1


def test_rf7_rename_to_other_habits_name_rejected() -> None:
    data = _data("Leer", "Correr")
    with pytest.raises(DuplicateHabitError):
        rename_habit(data, "Leer", "Correr")


def test_rf7_rename_to_empty_name_rejected() -> None:
    data = _data("Leer")
    with pytest.raises(InvalidNameError):
        rename_habit(data, "Leer", "   ")


def test_rf7_rename_to_fifty_one_characters_rejected() -> None:
    data = _data("Leer")
    with pytest.raises(InvalidNameError):
        rename_habit(data, "Leer", "a" * 51)


def test_rf7_rename_missing_habit_raises() -> None:
    data = _data()
    with pytest.raises(HabitNotFoundError):
        rename_habit(data, "Leer", "Lectura")


# --- T14: remove habit (RF-8) ---


def test_rf8_remove_habit_deletes_it_with_history() -> None:
    data = _data("Leer", "Correr")
    mark_done(data, "Leer", date(2026, 9, 19))
    name = remove_habit(data, "Leer")
    assert name == "Leer"
    assert list_rows(data, date(2026, 9, 19)) == [("Correr", False, 0)]


def test_rf8_remove_missing_habit_raises() -> None:
    data = _data()
    with pytest.raises(HabitNotFoundError):
        remove_habit(data, "Leer")
