"""Non-functional requirements (spec 001, RNF-2) and constitution principles 1 and 3."""

import ast
import sys
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent.parent / "habits"

NETWORK_MODULES = {
    "asyncio", "ftplib", "http", "imaplib", "poplib", "smtplib",
    "socket", "socketserver", "ssl", "urllib", "webbrowser", "xmlrpc",
}
CORE_FORBIDDEN_MODULES = {
    "io", "json", "os", "pathlib", "shutil", "subprocess", "sys", "tempfile", "time",
}
CORE_FORBIDDEN_CALLS = {"print", "input", "open", "now", "today", "utcnow"}


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _imported_modules(tree: ast.Module) -> set[str]:
    """Return the top-level names of every module imported in the tree."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def _called_names(tree: ast.Module) -> set[str]:
    """Return the names of every called function or method in the tree."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                names.add(node.func.attr)
    return names


def _package_files() -> list[Path]:
    return sorted(PACKAGE_DIR.glob("*.py"))


def test_package_exists() -> None:
    assert (PACKAGE_DIR / "core.py").is_file()
    assert _package_files()


def test_rnf2_only_stdlib_or_own_package() -> None:
    allowed = set(sys.stdlib_module_names) | {"habits"}
    offenders = {
        path.name: sorted(_imported_modules(_parse(path)) - allowed)
        for path in _package_files()
    }
    assert {name: mods for name, mods in offenders.items() if mods} == {}


def test_rnf2_no_network_modules() -> None:
    offenders = {
        path.name: sorted(_imported_modules(_parse(path)) & NETWORK_MODULES)
        for path in _package_files()
    }
    assert {name: mods for name, mods in offenders.items() if mods} == {}


def test_core_has_no_io_imports() -> None:
    imported = _imported_modules(_parse(PACKAGE_DIR / "core.py"))
    assert sorted(imported & CORE_FORBIDDEN_MODULES) == []


def test_core_has_no_io_or_clock_calls() -> None:
    called = _called_names(_parse(PACKAGE_DIR / "core.py"))
    assert sorted(called & CORE_FORBIDDEN_CALLS) == []
