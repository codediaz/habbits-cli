"""Pure domain logic: no I/O, no system clock."""

import unicodedata
from datetime import date, timedelta


class HabitError(Exception):
    """Base class for domain errors; str() is the user message without "Error: "."""


class InvalidNameError(HabitError):
    """E-0: the habit name breaks RF-0."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"el nombre no es válido: {reason}.")


class DuplicateHabitError(HabitError):
    """E-2: another habit already has an equivalent name."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"ya existe un hábito llamado «{name}».")


class HabitNotFoundError(HabitError):
    """E-3: no habit matches the given name."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"el hábito «{name}» no existe.")


class InvalidDateError(HabitError):
    """E-4: the date is malformed, does not exist or is out of range."""

    def __init__(self, text: str) -> None:
        self.text = text
        super().__init__(
            f"la fecha «{text}» no es válida (usa AAAA-MM-DD, entre 2000-01-01 y hoy)."
        )


def normalize_name(raw: str) -> str:
    """Apply RF-0 normalization: NFC, Unicode spaces collapsed to one and trimmed.

    Only space separators (category Zs) count as spaces; tabs and other
    control characters are kept so that validation can reject them.
    """
    text = unicodedata.normalize("NFC", raw)
    words: list[str] = []
    current: list[str] = []
    for char in text:
        if unicodedata.category(char) == "Zs":
            if current:
                words.append("".join(current))
                current = []
        else:
            current.append(char)
    if current:
        words.append("".join(current))
    return " ".join(words)


MAX_NAME_LENGTH = 50


def validate_name(raw: str) -> str:
    """Apply RF-0 validation: normalize and reject an invalid name (E-0).

    A name is invalid when, after normalization, it is empty, has more
    than MAX_NAME_LENGTH code points, or contains a non-printable
    character (e.g. a tab).
    """
    name = normalize_name(raw)
    if not name:
        raise InvalidNameError("está vacío")
    if len(name) > MAX_NAME_LENGTH:
        raise InvalidNameError(f"tiene más de {MAX_NAME_LENGTH} caracteres")
    if not name.isprintable():
        raise InvalidNameError("contiene caracteres no imprimibles")
    return name


def name_key(name: str) -> str:
    """Return the RF-0 comparison key: NFC-normalized and case-folded.

    Accents are kept (so they still distinguish names); casefold() also
    handles cases such as "ß" == "ss".
    """
    return unicodedata.normalize("NFC", name).casefold()


def find_habit(data: dict, name: str) -> dict:
    """Return the habit dict matching `name` (RF-2), or raise E-3."""
    key = name_key(name)
    for habit in data["habits"]:
        if name_key(habit["name"]) == key:
            return habit
    raise HabitNotFoundError(name)


def add_habit(data: dict, raw_name: str) -> str:
    """Create a habit with an empty history (RF-1). Returns the stored name."""
    name = validate_name(raw_name)
    key = name_key(name)
    for habit in data["habits"]:
        if name_key(habit["name"]) == key:
            raise DuplicateHabitError(raw_name)
    data["habits"].append({"name": name, "done": []})
    return name


MIN_DATE = date(2000, 1, 1)
DATE_FORMAT_LENGTH = 10  # len("AAAA-MM-DD")


def parse_date(text: str, today: date) -> date:
    """Parse an AAAA-MM-DD date within [MIN_DATE, today] (RF-4), or raise E-4."""
    parts = text.split("-")
    if len(parts) != 3 or len(text) != DATE_FORMAT_LENGTH:
        raise InvalidDateError(text)
    year_text, month_text, day_text = parts
    if not (
        len(year_text) == 4
        and len(month_text) == 2
        and len(day_text) == 2
        and year_text.isdigit()
        and month_text.isdigit()
        and day_text.isdigit()
    ):
        raise InvalidDateError(text)
    try:
        parsed = date(int(year_text), int(month_text), int(day_text))
    except ValueError as error:
        raise InvalidDateError(text) from error
    if not (MIN_DATE <= parsed <= today):
        raise InvalidDateError(text)
    return parsed


def mark_done(data: dict, name: str, day: date) -> bool:
    """Mark `day` as done for the habit (RF-3, RF-4).

    Returns False (without changes) if the day was already marked.
    """
    habit = find_habit(data, name)
    text = day.isoformat()
    if text in habit["done"]:
        return False
    habit["done"] = sorted([*habit["done"], text])
    return True


def unmark_done(data: dict, name: str, day: date) -> bool:
    """Remove `day` from the habit's history (RF-5).

    Returns False (without changes) if the day was not marked.
    """
    habit = find_habit(data, name)
    text = day.isoformat()
    if text not in habit["done"]:
        return False
    habit["done"] = [d for d in habit["done"] if d != text]
    return True


def current_streak(done_dates: set[date], today: date) -> int:
    """Count the consecutive marked days ending today or yesterday (RF-6)."""
    if today in done_dates:
        day = today
    elif (today - timedelta(days=1)) in done_dates:
        day = today - timedelta(days=1)
    else:
        return 0
    count = 0
    while day in done_dates:
        count += 1
        day -= timedelta(days=1)
    return count


def list_rows(data: dict, today: date) -> list[tuple[str, bool, int]]:
    """Return (name, done_today, streak) for each habit, ordered per RF-6."""
    rows = []
    for habit in data["habits"]:
        done_dates = {date.fromisoformat(text) for text in habit["done"]}
        rows.append(
            (habit["name"], today.isoformat() in habit["done"], current_streak(done_dates, today))
        )
    rows.sort(key=lambda row: (name_key(row[0]), row[0]))
    return rows


def rename_habit(data: dict, old_name: str, new_raw_name: str) -> tuple[str, str]:
    """Rename a habit, keeping its history (RF-7). Returns (old, new)."""
    habit = find_habit(data, old_name)
    new_name = validate_name(new_raw_name)
    new_key = name_key(new_name)
    for other in data["habits"]:
        if other is not habit and name_key(other["name"]) == new_key:
            raise DuplicateHabitError(new_raw_name)
    previous_name = habit["name"]
    habit["name"] = new_name
    return previous_name, new_name


def remove_habit(data: dict, name: str) -> str:
    """Delete a habit and its history (RF-8). Returns its stored name."""
    habit = find_habit(data, name)
    data["habits"].remove(habit)
    return habit["name"]
