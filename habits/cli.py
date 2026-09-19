"""Command-line interface: parses arguments and formats output."""

import argparse
import os
import sys
from datetime import date
from pathlib import Path

from habits.core import (
    HabitError,
    add_habit,
    find_habit,
    list_rows,
    mark_done,
    parse_date,
    remove_habit,
    rename_habit,
    unmark_done,
)
from habits.storage import StorageError, load, save

DEFAULT_FILE_NAME = ".habits.json"


class UsageError(Exception):
    """A command-line usage mistake (E-1): unknown command or bad arguments."""


class _ArgumentParser(argparse.ArgumentParser):
    """An ArgumentParser that raises instead of calling sys.exit (RF-10)."""

    def error(self, message: str) -> None:  # noqa: D102 - argparse override
        raise UsageError(message)


def _build_parser() -> _ArgumentParser:
    parser = _ArgumentParser(prog="habits", description="Registra hábitos y rachas.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Crea un hábito.")
    add_parser.add_argument("name")

    done_parser = subparsers.add_parser("done", help="Marca un hábito como hecho.")
    done_parser.add_argument("name")
    done_parser.add_argument("--date")

    undo_parser = subparsers.add_parser("undo", help="Desmarca un día de un hábito.")
    undo_parser.add_argument("name")
    undo_parser.add_argument("--date")

    subparsers.add_parser("list", help="Lista los hábitos con su racha.")

    rename_parser = subparsers.add_parser("rename", help="Renombra un hábito.")
    rename_parser.add_argument("old_name")
    rename_parser.add_argument("new_name")

    delete_parser = subparsers.add_parser("delete", help="Borra un hábito.")
    delete_parser.add_argument("name")

    return parser


def _data_path() -> Path:
    """Resolve the data file path (RF-9): $HABITS_FILE, or ~/.habits.json."""
    override = os.environ.get("HABITS_FILE")
    if override:
        return Path(override)
    return Path.home() / DEFAULT_FILE_NAME


def _format_streak(streak: int) -> str:
    unit = "día" if streak == 1 else "días"
    return f"racha: {streak} {unit}"


def _run_add(data: dict, args: argparse.Namespace, _today: date) -> tuple[str, bool]:
    name = add_habit(data, args.name)
    return f"Hábito «{name}» creado.", True


def _run_done(data: dict, args: argparse.Namespace, today: date) -> tuple[str, bool]:
    day = parse_date(args.date, today) if args.date else today
    habit = find_habit(data, args.name)
    changed = mark_done(data, args.name, day)
    text = day.isoformat()
    if changed:
        return f"«{habit['name']}» marcado el {text}.", True
    return f"«{habit['name']}» ya estaba marcado el {text}.", False


def _run_undo(data: dict, args: argparse.Namespace, today: date) -> tuple[str, bool]:
    day = parse_date(args.date, today) if args.date else today
    habit = find_habit(data, args.name)
    changed = unmark_done(data, args.name, day)
    text = day.isoformat()
    if changed:
        return f"«{habit['name']}» desmarcado el {text}.", True
    return f"«{habit['name']}» no estaba marcado el {text}.", False


def _run_list(data: dict, _args: argparse.Namespace, today: date) -> tuple[str, bool]:
    rows = list_rows(data, today)
    if not rows:
        return "No hay hábitos todavía.", False
    lines = [
        f"[{'x' if done_today else ' '}] {name} — {_format_streak(streak)}"
        for name, done_today, streak in rows
    ]
    return "\n".join(lines), False


def _run_rename(data: dict, args: argparse.Namespace, _today: date) -> tuple[str, bool]:
    old_name, new_name = rename_habit(data, args.old_name, args.new_name)
    return f"«{old_name}» renombrado a «{new_name}».", True


def _confirm_delete(name: str) -> bool:
    """Ask for confirmation (RF-8). Returns True only for an exact "s"/"S"."""
    try:
        answer = input(f"¿Borrar «{name}» y todo su historial? (s/n): ")
    except EOFError:
        return False
    return answer.strip() in {"s", "S"}


def _run_delete(data: dict, args: argparse.Namespace, _today: date) -> tuple[str, bool]:
    habit = find_habit(data, args.name)
    name = habit["name"]
    if not _confirm_delete(name):
        return "Borrado cancelado.", False
    remove_habit(data, name)
    return f"Hábito «{name}» borrado.", True


_HANDLERS = {
    "add": _run_add,
    "done": _run_done,
    "undo": _run_undo,
    "list": _run_list,
    "rename": _run_rename,
    "delete": _run_delete,
}


def main(argv: list[str] | None = None, *, today: date | None = None) -> int:
    """Run the CLI and return the process exit code (RF-10)."""
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except UsageError as error:
        print(f"Error: uso incorrecto. {error}", file=sys.stderr)
        return 2

    current_day = today if today is not None else date.today()
    path = _data_path()
    handler = _HANDLERS[args.command]

    try:
        data = load(path)
        try:
            message, changed = handler(data, args, current_day)
        except KeyboardInterrupt:
            return 130
        if changed:
            save(path, data)
    except (HabitError, StorageError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(message)
    return 0
