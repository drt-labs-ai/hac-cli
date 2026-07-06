"""Entry point for the hac CLI."""

from __future__ import annotations

import typer

from hac_cli.cli.app import build_app


app = typer.Typer(
    name="hac",
    help="SAP Commerce HAC automation — execute Groovy scripts across environments.",
    no_args_is_help=False,
    rich_markup_mode="rich",
)

app = build_app()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
