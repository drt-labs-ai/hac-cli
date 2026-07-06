"""Root Typer application — registers all command groups."""

from __future__ import annotations

import typer

from hac_cli.cli.cmd_env import env_app
from hac_cli.cli.cmd_groovy import groovy_app
from hac_cli.cli.cmd_scripts import scripts_app


def build_app() -> typer.Typer:
    app = typer.Typer(
        name="hac",
        help=(
            "[bold green]hac-cli[/bold green] — SAP Commerce HAC automation.\n\n"
            "Execute Groovy scripts across environments without opening a browser."
        ),
        no_args_is_help=True,
        rich_markup_mode="rich",
        pretty_exceptions_enable=True,
        pretty_exceptions_show_locals=False,
    )

    app.add_typer(env_app, name="env", help="Manage SAP Commerce environments.")
    app.add_typer(groovy_app, name="groovy", help="Execute Groovy scripts via HAC.")
    app.add_typer(scripts_app, name="scripts", help="Browse and search the script library.")

    @app.callback(invoke_without_command=True)
    def _root(
        ctx: typer.Context,
        version: bool = typer.Option(False, "--version", "-V", help="Show version and exit."),
    ) -> None:
        if version:
            from hac_cli import __version__
            typer.echo(f"hac-cli {__version__}")
            raise typer.Exit()
        if ctx.invoked_subcommand is None:
            _launch_tui()

    return app


def _launch_tui() -> None:
    """Launch interactive TUI when hac is called with no subcommand."""
    try:
        from hac_cli.tui.app import HacApp
        HacApp().run()
    except ImportError:
        typer.echo("TUI requires textual: pip install 'hac-cli[tui]'", err=True)
        raise typer.Exit(1)
