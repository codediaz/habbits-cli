"""Tests for the pure domain logic in habits.core (spec 001)."""

import pytest

from habits.core import (
    DuplicateHabitError,
    HabitError,
    HabitNotFoundError,
    InvalidDateError,
    InvalidNameError,
    normalize_name,
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
