"""Pure domain logic: no I/O, no system clock."""

import unicodedata


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
