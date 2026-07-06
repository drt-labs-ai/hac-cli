"""Custom Textual widgets for hac-cli TUI."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, RichLog


class ScriptInfoBar(Widget):
    """Displays name, category, and tags for the currently selected script."""

    DEFAULT_CSS = """
    ScriptInfoBar {
        height: 2;
        background: $surface;
        padding: 0 1;
    }
    """

    name_text: reactive[str] = reactive("")
    tags_text: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        yield Label("", id="script-name-label")
        yield Label("", id="script-tags-label")

    def watch_name_text(self, value: str) -> None:
        self.query_one("#script-name-label", Label).update(f"[bold]{value}[/bold]")

    def watch_tags_text(self, value: str) -> None:
        self.query_one("#script-tags-label", Label).update(
            f"[dim]tags: {value}[/dim]" if value else ""
        )


class OutputPanel(RichLog):
    """RichLog with helpers for HAC execution results."""

    DEFAULT_CSS = """
    OutputPanel {
        height: 1fr;
        border-top: solid $primary;
        padding: 0 1;
    }
    """

    def write_success(self, output: str, elapsed_ms: int) -> None:
        self.write(f"[bold green]SUCCESS[/bold green]  [dim]{elapsed_ms}ms[/dim]")
        self.write(output or "[dim](no output)[/dim]")

    def write_error(self, output: str, stack_trace: str | None, elapsed_ms: int) -> None:
        self.write(f"[bold red]ERROR[/bold red]  [dim]{elapsed_ms}ms[/dim]")
        if output:
            self.write(output)
        if stack_trace:
            self.write(f"[red]{stack_trace}[/red]")

    def write_running(self, script_name: str, env_name: str, commit: bool) -> None:
        mode = "[yellow]COMMIT[/yellow]" if commit else "[dim]dry run[/dim]"
        self.write(
            f"[cyan]Running:[/cyan] [bold]{script_name}[/bold]"
            f" → [bold]{env_name}[/bold]  {mode}"
        )
