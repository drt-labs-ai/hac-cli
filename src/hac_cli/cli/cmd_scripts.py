"""CLI commands for browsing the script library."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

from hac_cli.infrastructure.script_repository import FilesystemScriptRepository

scripts_app = typer.Typer(no_args_is_help=True, rich_markup_mode="rich")
console = Console()


@scripts_app.command("list")
def list_scripts(
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category."),
) -> None:
    """List all scripts in the library."""
    repo = FilesystemScriptRepository()
    scripts = repo.list_scripts(category=category)

    if not scripts:
        console.print("[yellow]No scripts found.[/yellow]")
        return

    table = Table(title="Script Library", show_header=True, header_style="bold cyan")
    table.add_column("Path", style="bold")
    table.add_column("Name")
    table.add_column("Description")
    table.add_column("Tags")

    for s in scripts:
        table.add_row(s.path, s.name, s.description, ", ".join(s.tags))

    console.print(table)


@scripts_app.command("search")
def search_scripts(
    query: str = typer.Argument(..., help="Search query (fuzzy match on name/description/tags)."),
) -> None:
    """Search for scripts by keyword."""
    repo = FilesystemScriptRepository()
    results = repo.search_scripts(query)

    if not results:
        console.print(f"[yellow]No scripts matched: '{query}'[/yellow]")
        return

    for s in results:
        console.print(f"[bold]{s.path}[/bold] — {s.name}")
        console.print(f"  {s.description}")
        if s.tags:
            console.print(f"  Tags: [dim]{', '.join(s.tags)}[/dim]")


@scripts_app.command("show")
def show_script(
    path: str = typer.Argument(..., help="Script library path (e.g. cache/clear_all_caches)."),
) -> None:
    """Display a script's source code."""
    repo = FilesystemScriptRepository()
    try:
        content = repo.get_script_content(path)
        console.print(Syntax(content, "groovy", theme="monokai", line_numbers=True))
    except FileNotFoundError:
        console.print(f"[red]Script not found: '{path}'[/red]")
        raise typer.Exit(1)
