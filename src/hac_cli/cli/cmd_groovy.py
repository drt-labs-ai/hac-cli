"""CLI commands for Groovy script execution."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from hac_cli.application.execute_groovy import ExecuteGroovyService
from hac_cli.infrastructure.config_store import TomlConfigStore
from hac_cli.infrastructure.hac_client import HacHttpClient
from hac_cli.infrastructure.script_repository import FilesystemScriptRepository
from hac_cli.infrastructure.secret_store import KeyringSecretStore

groovy_app = typer.Typer(no_args_is_help=True, rich_markup_mode="rich")
console = Console()


def _make_service() -> ExecuteGroovyService:
    return ExecuteGroovyService(
        hac_client=HacHttpClient(secret_store=KeyringSecretStore()),
        config_store=TomlConfigStore(),
        secret_store=KeyringSecretStore(),
        script_repo=FilesystemScriptRepository(),
    )


@groovy_app.command("run")
def run_script(
    env: str = typer.Option(..., "--env", "-e", help="Target environment name."),
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="Path to a local .groovy file."),
    script: Optional[str] = typer.Option(None, "--script", "-s", help="Script library path (e.g. cache/clear_all_caches)."),
    inline: Optional[str] = typer.Option(None, "--inline", "-i", help="Inline Groovy code string."),
    commit: bool = typer.Option(False, "--commit", help="Commit the script execution (default: rollback)."),
    output_only: bool = typer.Option(False, "--output-only", help="Print raw output only (no formatting)."),
) -> None:
    """Execute a Groovy script on a SAP Commerce environment via HAC."""
    sources = [x for x in [file, script, inline] if x is not None]
    if len(sources) != 1:
        console.print("[red]Provide exactly one of: --file, --script, or --inline[/red]")
        raise typer.Exit(1)

    svc = _make_service()
    result = asyncio.run(
        svc.execute(
            env_name=env,
            file_path=file,
            script_library_path=script,
            inline_code=inline,
            commit=commit,
        )
    )

    if output_only:
        typer.echo(result.output)
        return

    status_color = "green" if result.succeeded else "red"
    status_label = "SUCCESS" if result.succeeded else "ERROR"

    console.print(
        Panel(
            result.output or "(no output)",
            title=f"[{status_color}]{status_label}[/{status_color}] — {env} — {result.execution_time_ms}ms",
            border_style=status_color,
        )
    )

    if result.stack_trace:
        console.print(Panel(result.stack_trace, title="[red]Stack Trace[/red]", border_style="red"))

    if not result.succeeded:
        raise typer.Exit(1)


@groovy_app.command("exec")
def exec_nlp(
    env: str = typer.Option(..., "--env", "-e", help="Target environment name."),
    nlp: str = typer.Argument(..., help="Natural language description of the script to run."),
    commit: bool = typer.Option(False, "--commit", help="Commit the script execution."),
) -> None:
    """Select and execute a script using natural language description."""
    svc = _make_service()
    matches = svc.find_scripts_by_nlp(nlp)

    if not matches:
        console.print(f"[yellow]No scripts matched: '{nlp}'[/yellow]")
        raise typer.Exit(1)

    if len(matches) == 1:
        chosen = matches[0]
    else:
        console.print("[cyan]Multiple matches found:[/cyan]")
        for i, m in enumerate(matches[:5], 1):
            console.print(f"  {i}. [bold]{m.name}[/bold] — {m.description}")
        idx = typer.prompt("Select script number", type=int, default=1)
        chosen = matches[idx - 1]

    console.print(f"Running: [bold]{chosen.name}[/bold]")

    result = asyncio.run(
        svc.execute(
            env_name=env,
            script_library_path=chosen.path,
            commit=commit,
        )
    )

    status_color = "green" if result.succeeded else "red"
    console.print(
        Panel(
            result.output or "(no output)",
            title=f"[{status_color}]{'SUCCESS' if result.succeeded else 'ERROR'}[/{status_color}]",
            border_style=status_color,
        )
    )

    if not result.succeeded:
        raise typer.Exit(1)
