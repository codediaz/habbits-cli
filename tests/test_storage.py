"""Tests for JSON persistence in habits.storage (spec 001, RF-9)."""

import json
import os
from pathlib import Path

import pytest

from habits.storage import StorageError, StorageWriteError, load, save

VALID_JSON = (
    '{"version": 1, "habits": '
    '[{"name": "Leer", "done": ["2026-09-01", "2026-09-02"]}]}'
)


# --- T15: load valid data ---


def test_rf9_load_missing_file_returns_empty(tmp_path: Path) -> None:
    data = load(tmp_path / "does-not-exist.json")
    assert data == {"version": 1, "habits": []}


def test_rf9_load_valid_file(tmp_path: Path) -> None:
    path = tmp_path / "habits.json"
    path.write_text(VALID_JSON, encoding="utf-8")
    data = load(path)
    assert data == {
        "version": 1,
        "habits": [{"name": "Leer", "done": ["2026-09-01", "2026-09-02"]}],
    }


def test_rf9_load_accepts_bom(tmp_path: Path) -> None:
    path = tmp_path / "habits.json"
    path.write_bytes(VALID_JSON.encode("utf-8-sig"))
    data = load(path)
    assert data["habits"][0]["name"] == "Leer"


# --- T16: detect corrupt data (E-5), file untouched in every case ---


def _assert_untouched(path: Path, original: bytes) -> None:
    assert path.read_bytes() == original


def test_rf9_load_empty_file_is_corrupt(tmp_path: Path) -> None:
    path = tmp_path / "habits.json"
    path.write_text("", encoding="utf-8")
    original = path.read_bytes()
    with pytest.raises(StorageError):
        load(path)
    _assert_untouched(path, original)


def test_rf9_load_invalid_json_is_corrupt(tmp_path: Path) -> None:
    path = tmp_path / "habits.json"
    path.write_text("{not json", encoding="utf-8")
    original = path.read_bytes()
    with pytest.raises(StorageError):
        load(path)
    _assert_untouched(path, original)


def test_rf9_load_wrong_encoding_is_corrupt(tmp_path: Path) -> None:
    path = tmp_path / "habits.json"
    # Latin-1 bytes that are not valid UTF-8 (e.g. "Inglés" in Latin-1).
    path.write_bytes("Inglés".encode("latin-1"))
    original = path.read_bytes()
    with pytest.raises(StorageError):
        load(path)
    _assert_untouched(path, original)


def test_rf9_load_root_not_object_is_corrupt(tmp_path: Path) -> None:
    path = tmp_path / "habits.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")
    original = path.read_bytes()
    with pytest.raises(StorageError):
        load(path)
    _assert_untouched(path, original)


def test_rf9_load_missing_version_is_corrupt(tmp_path: Path) -> None:
    path = tmp_path / "habits.json"
    path.write_text('{"habits": []}', encoding="utf-8")
    original = path.read_bytes()
    with pytest.raises(StorageError):
        load(path)
    _assert_untouched(path, original)


def test_rf9_load_unknown_version_is_corrupt(tmp_path: Path) -> None:
    path = tmp_path / "habits.json"
    path.write_text('{"version": 2, "habits": []}', encoding="utf-8")
    original = path.read_bytes()
    with pytest.raises(StorageError):
        load(path)
    _assert_untouched(path, original)


def test_rf9_load_empty_name_is_corrupt(tmp_path: Path) -> None:
    path = tmp_path / "habits.json"
    path.write_text(
        '{"version": 1, "habits": [{"name": "", "done": []}]}', encoding="utf-8"
    )
    original = path.read_bytes()
    with pytest.raises(StorageError):
        load(path)
    _assert_untouched(path, original)


def test_rf9_load_invalid_date_is_corrupt(tmp_path: Path) -> None:
    path = tmp_path / "habits.json"
    path.write_text(
        '{"version": 1, "habits": '
        '[{"name": "Leer", "done": ["2026-02-30"]}]}',
        encoding="utf-8",
    )
    original = path.read_bytes()
    with pytest.raises(StorageError):
        load(path)
    _assert_untouched(path, original)


def test_rf9_load_duplicate_date_in_habit_is_corrupt(tmp_path: Path) -> None:
    path = tmp_path / "habits.json"
    path.write_text(
        '{"version": 1, "habits": '
        '[{"name": "Leer", "done": ["2026-09-01", "2026-09-01"]}]}',
        encoding="utf-8",
    )
    original = path.read_bytes()
    with pytest.raises(StorageError):
        load(path)
    _assert_untouched(path, original)


def test_rf9_load_duplicate_equivalent_names_is_corrupt(tmp_path: Path) -> None:
    path = tmp_path / "habits.json"
    path.write_text(
        '{"version": 1, "habits": '
        '[{"name": "Leer", "done": []}, {"name": "LEER", "done": []}]}',
        encoding="utf-8",
    )
    original = path.read_bytes()
    with pytest.raises(StorageError):
        load(path)
    _assert_untouched(path, original)


# --- T17: atomic save ---


def test_rf9_save_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "habits.json"
    data = {"version": 1, "habits": [{"name": "Leer", "done": ["2026-09-01"]}]}
    save(path, data)
    assert load(path) == data


def test_rf9_save_creates_missing_directory(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "dir" / "habits.json"
    data = {"version": 1, "habits": []}
    save(path, data)
    assert path.is_file()
    assert load(path) == data


def test_rf9_save_failure_keeps_original_intact(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "habits.json"
    original = {"version": 1, "habits": [{"name": "Leer", "done": []}]}
    save(path, original)
    original_bytes = path.read_bytes()

    def failing_replace(*_args: object, **_kwargs: object) -> None:
        raise OSError("simulated failure")

    monkeypatch.setattr(os, "replace", failing_replace)
    with pytest.raises(StorageWriteError):
        save(path, {"version": 1, "habits": [{"name": "Correr", "done": []}]})
    assert path.read_bytes() == original_bytes


# --- T18: write error (E-6) ---


def test_rf9_save_without_permission_raises_storage_write_error(
    tmp_path: Path,
) -> None:
    readonly_dir = tmp_path / "readonly"
    readonly_dir.mkdir()
    path = readonly_dir / "habits.json"
    original = {"version": 1, "habits": [{"name": "Leer", "done": []}]}
    save(path, original)
    original_bytes = path.read_bytes()

    readonly_dir.chmod(0o500)  # read + execute, no write
    try:
        with pytest.raises(StorageWriteError):
            save(path, {"version": 1, "habits": [{"name": "Correr", "done": []}]})
    finally:
        readonly_dir.chmod(0o700)
    assert path.read_bytes() == original_bytes


def test_rf9_storage_write_error_is_storage_error() -> None:
    assert issubclass(StorageWriteError, StorageError)
