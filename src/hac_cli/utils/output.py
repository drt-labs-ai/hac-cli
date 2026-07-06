"""Rich console output helpers."""

from __future__ import annotations

from rich.console import Console
from rich.theme import Theme

_THEME = Theme({
    "success": "bold green",
    "error": "bold red",
    "warning": "bold yellow",
    "info": "bold cyan",
    "dim": "dim white",
})

console = Console(theme=_THEME)
err_console = Console(stderr=True, theme=_THEME)


def print_success(msg: str) -> None:
    console.print(f"[success]{msg}[/success]")


def print_error(msg: str) -> None:
    err_console.print(f"[error]{msg}[/error]")


def print_warning(msg: str) -> None:
    console.print(f"[warning]{msg}[/warning]")


def print_info(msg: str) -> None:
    console.print(f"[info]{msg}[/info]")
