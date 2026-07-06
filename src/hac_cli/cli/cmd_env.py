"""CLI commands for managing SAP Commerce environments."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from hac_cli.application.manage_environments import EnvironmentService
from hac_cli.infrastructure.config_store import TomlConfigStore
from hac_cli.infrastructure.secret_store import KeyringSecretStore

env_app = typer.Typer(no_args_is_help=True, rich_markup_mode="rich")
console = Console()


def _make_service() -> EnvironmentService:
    return EnvironmentService(
        config_store=TomlConfigStore(),
        secret_store=KeyringSecretStore(),
    )


@env_app.command("add")
def add_env(
    name: str = typer.Option(..., "--name", "-n", help="Short environment alias (e.g. dev)."),
    url: str = typer.Option(..., "--url", "-u", help="HAC base URL (e.g. https://dev-hac.example.com)."),
    username: str = typer.Option(..., "--user", "-U", help="HAC admin username."),
    timeout: int = typer.Option(30, "--timeout", "-t", help="Request timeout in seconds."),
    no_ssl_verify: bool = typer.Option(False, "--no-ssl-verify", help="Disable SSL verification (dev only)."),
) -> None:
    """Add or update a SAP Commerce environment."""
    password = typer.prompt(f"Password for {username}@{name}", hide_input=True, confirmation_prompt=True)
    svc = _make_service()
    svc.add_environment(
        name=name, url=url, username=username, password=password,
        timeout=timeout, verify_ssl=not no_ssl_verify,
    )
    console.print(f"[green]Environment '[bold]{name}[/bold]' saved.[/green]")


@env_app.command("list")
def list_envs() -> None:
    """List all configured environments."""
    svc = _make_service()
    envs = svc.list_environments()
    if not envs:
        console.print("[yellow]No environments configured. Run: hac env add[/yellow]")
        return
    table = Table(title="Configured Environments", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="bold")
    table.add_column("URL")
    table.add_column("Username")
    table.add_column("Timeout")
    table.add_column("SSL")
    for env in envs:
        table.add_row(env.name, env.url, env.username, str(env.timeout), "yes" if env.verify_ssl else "[red]no[/red]")
    console.print(table)


@env_app.command("remove")
def remove_env(
    name: str = typer.Argument(..., help="Environment name to remove."),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation."),
) -> None:
    """Remove an environment and its stored credentials."""
    if not force:
        typer.confirm(f"Remove environment '{name}' and its stored password?", abort=True)
    svc = _make_service()
    svc.remove_environment(name)
    console.print(f"[green]Environment '[bold]{name}[/bold]' removed.[/green]")


@env_app.command("test")
def test_env(
    name: str = typer.Argument(..., help="Environment name to test."),
) -> None:
    """Test connectivity and authentication for an environment."""
    import asyncio
    from hac_cli.infrastructure.hac_client import HacHttpClient

    svc = _make_service()
    env = svc.get_environment(name)
    if env is None:
        console.print(f"[red]Environment '[bold]{name}[/bold]' not found.[/red]")
        raise typer.Exit(1)

    password = svc.get_password(name)
    client = HacHttpClient(secret_store=KeyringSecretStore())

    with console.status(f"Testing connection to [bold]{name}[/bold]..."):
        ok = asyncio.run(client.test_connection(env))

    if ok:
        console.print(f"[green]Connection to '[bold]{name}[/bold]' successful.[/green]")
    else:
        console.print(f"[red]Connection to '[bold]{name}[/bold]' failed.[/red]")
        raise typer.Exit(1)
