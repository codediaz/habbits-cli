"""JSON persistence: the only module that touches the data file (RF-9)."""

import json
import os
from datetime import date
from pathlib import Path

from habits.core import name_key

CURRENT_VERSION = 1


class StorageError(Exception):
    """E-5: the data file is missing, unreadable or corrupt."""

    def __init__(self) -> None:
        super().__init__(
            "los datos guardados están dañados o no se pueden leer; "
            "no se han modificado."
        )


class StorageWriteError(StorageError):
    """E-6: the data could not be saved; the previous data is kept."""

    def __init__(self) -> None:
        # Deliberately skip StorageError.__init__: the E-6 text differs from E-5.
        Exception.__init__(
            self, "no se han podido guardar los datos; se conservan los anteriores."
        )


def _empty_data() -> dict:
    return {"version": CURRENT_VERSION, "habits": []}


def _validate_schema(data: object) -> dict:
    """Check the structure described in spec section 5; raise StorageError otherwise."""
    if not isinstance(data, dict):
        raise StorageError
    if data.get("version") != CURRENT_VERSION:
        raise StorageError
    habits = data.get("habits")
    if not isinstance(habits, list):
        raise StorageError

    seen_keys: set[str] = set()
    for habit in habits:
        if not isinstance(habit, dict):
            raise StorageError
        name = habit.get("name")
        done = habit.get("done")
        if not isinstance(name, str) or not name:
            raise StorageError
        if not isinstance(done, list):
            raise StorageError

        key = name_key(name)
        if key in seen_keys:
            raise StorageError
        seen_keys.add(key)

        seen_dates: set[str] = set()
        for text in done:
            if not isinstance(text, str):
                raise StorageError
            try:
                date.fromisoformat(text)
            except ValueError as error:
                raise StorageError from error
            if text in seen_dates:
                raise StorageError
            seen_dates.add(text)

    return {"version": CURRENT_VERSION, "habits": habits}


def load(path: Path) -> dict:
    """Load the habits data from `path` (RF-9).

    A missing file is treated as an empty collection. Any other read or
    parse failure raises StorageError (E-5) without modifying the file.
    """
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        return _empty_data()
    except (OSError, UnicodeDecodeError) as error:
        raise StorageError from error

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as error:
        raise StorageError from error

    return _validate_schema(parsed)


def save(path: Path, data: dict) -> None:
    """Save `data` to `path` atomically (RF-9).

    Creates the parent directory if it does not exist. Any failure raises
    StorageWriteError (E-6) and leaves the previous file untouched.
    """
    to_write = {
        "version": CURRENT_VERSION,
        "habits": [
            {"name": habit["name"], "done": sorted(habit["done"])}
            for habit in data["habits"]
        ],
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path.with_name(f"{path.name}.tmp")
        temp_path.write_text(
            json.dumps(to_write, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        os.replace(temp_path, path)
    except OSError as error:
        raise StorageWriteError from error
