"""Tests for the pure domain logic in habits.core (spec 001)."""

import pytest

from habits.core import (
    DuplicateHabitError,
    HabitError,
    HabitNotFoundError,
    InvalidDateError,
    InvalidNameError,
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
