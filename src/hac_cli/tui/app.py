"""Interactive TUI for hac-cli — Textual-based environment/script browser."""

from __future__ import annotations

from typing import Optional

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import DataTable, Footer, Header, Input, Label, RichLog, Select, Static

from hac_cli.application.execute_groovy import ExecuteGroovyService
from hac_cli.domain.exceptions import HacCliError
from hac_cli.domain.models import Environment, ScriptMeta
from hac_cli.infrastructure.config_store import TomlConfigStore
from hac_cli.infrastructure.hac_client import HacHttpClient
from hac_cli.infrastructure.script_repository import FilesystemScriptRepository

_NO_ENV_MSG = "(none — run: hac env add)"


class HacApp(App[None]):
    """hac-cli interactive terminal — browse scripts, select environment, execute."""

    TITLE = "hac-cli"
    SUB_TITLE = "SAP Commerce HAC automation"

    CSS = """
    Screen {
        layers: base;
    }

    #toolbar {
        height: 3;
        background: $surface;
        padding: 0 1;
        border-bottom: solid $primary;
    }

    #env-label {
        content-align: center middle;
        width: auto;
    }

    #env-select {
        width: 30;
    }

    #mode-label {
        width: auto;
        content-align: center middle;
        padding: 0 1;
    }

    #main {
        height: 1fr;
    }

    #left-panel {
        width: 55%;
        border-right: solid $primary;
    }

    #right-panel {
        width: 45%;
    }

    #search-bar {
        height: 3;
        padding: 0 1;
        border-bottom: solid $surface;
    }

    #search-input {
        width: 1fr;
    }

    #category-select {
        width: 22;
    }

    #script-table {
        height: 1fr;
    }

    #preview-section {
        height: 55%;
        border-bottom: solid $primary;
    }

    .section-title {
        background: $primary;
        color: $text;
        text-style: bold;
        padding: 0 1;
        height: 1;
    }

    #preview-content {
        height: 1fr;
        padding: 1;
        overflow-y: auto;
    }

    #output-section {
        height: 45%;
    }

    #output-log {
        height: 1fr;
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("f5", "run_script", "Run", show=True),
        Binding("ctrl+t", "toggle_commit", "Toggle commit"),
        Binding("/", "focus_search", "Search"),
        Binding("escape", "clear_search", "Clear search"),
        Binding("e", "next_env", "Next env"),
    ]

    current_env: reactive[str] = reactive(_NO_ENV_MSG)
    commit_mode: reactive[bool] = reactive(False)
    selected_script: reactive[Optional[ScriptMeta]] = reactive(None)

    def __init__(self) -> None:
        super().__init__()
        self._config_store = TomlConfigStore()
        self._script_repo = FilesystemScriptRepository()
        self._environments: list[Environment] = []
        self._all_scripts: list[ScriptMeta] = []

    # -------------------------------------------------------------------------
    # Composition
    # -------------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Horizontal(id="toolbar"):
            yield Label("Environment: ", id="env-label")
            yield Select(
                options=[(_NO_ENV_MSG, "")],
                value="",
                id="env-select",
                allow_blank=False,
            )
            yield Label("  Mode: [bold green]DRY RUN[/bold green]", id="mode-label", markup=True)

        with Horizontal(id="main"):
            with Vertical(id="left-panel"):
                with Horizontal(id="search-bar"):
                    yield Input(placeholder="Search scripts…", id="search-input")
                    yield Select(
                        options=[("All categories", "")],
                        value="",
                        id="category-select",
                        allow_blank=False,
                    )
                yield DataTable(id="script-table", cursor_type="row", zebra_stripes=True)

            with Vertical(id="right-panel"):
                with Vertical(id="preview-section"):
                    yield Label("  Preview", classes="section-title")
                    yield Static(
                        "[dim]Select a script to preview its source.[/dim]",
                        id="preview-content",
                        markup=True,
                    )
                with Vertical(id="output-section"):
                    yield Label("  Output", classes="section-title")
                    yield RichLog(id="output-log", highlight=True, markup=True)

        yield Footer()

    # -------------------------------------------------------------------------
    # Startup
    # -------------------------------------------------------------------------

    def on_mount(self) -> None:
        self._load_environments()
        self._load_scripts()
        self._setup_script_table()

    def _load_environments(self) -> None:
        self._environments = self._config_store.list_environments()
        env_select = self.query_one("#env-select", Select)

        if self._environments:
            options = [(e.name, e.name) for e in self._environments]
            env_select.set_options(options)
            first = self._environments[0].name
            env_select.value = first
            self.current_env = first
        else:
            env_select.set_options([(_NO_ENV_MSG, "")])

    def _load_scripts(self) -> None:
        self._all_scripts = self._script_repo.list_scripts()
        categories = sorted({s.category for s in self._all_scripts})
        cat_options: list[tuple[str, str]] = [("All categories", "")] + [
            (c.title(), c) for c in categories
        ]
        self.query_one("#category-select", Select).set_options(cat_options)

    def _setup_script_table(self) -> None:
        table = self.query_one("#script-table", DataTable)
        table.add_columns("Path", "Name", "Description")
        self._refresh_script_table(self._all_scripts)

    def _refresh_script_table(self, scripts: list[ScriptMeta]) -> None:
        table = self.query_one("#script-table", DataTable)
        table.clear()
        for s in scripts:
            table.add_row(s.path, s.name, s.description or "", key=s.path)

    # -------------------------------------------------------------------------
    # Events
    # -------------------------------------------------------------------------

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        key = event.row_key.value
        if key is None:
            return
        script = next((s for s in self._all_scripts if s.path == str(key)), None)
        if script:
            self.selected_script = script
            self._show_preview(script)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search-input":
            self._apply_filters()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "env-select":
            val = str(event.value) if event.value else ""
            if val and val != _NO_ENV_MSG:
                self.current_env = val
        elif event.select.id == "category-select":
            self._apply_filters()

    # -------------------------------------------------------------------------
    # Reactive watches
    # -------------------------------------------------------------------------

    def watch_commit_mode(self, value: bool) -> None:
        label = self.query_one("#mode-label", Label)
        if value:
            label.update("  Mode: [bold yellow]COMMIT[/bold yellow]")
        else:
            label.update("  Mode: [bold green]DRY RUN[/bold green]")

    # -------------------------------------------------------------------------
    # Filtering
    # -------------------------------------------------------------------------

    def _apply_filters(self) -> None:
        search = self.query_one("#search-input", Input).value.strip()
        cat_val = self.query_one("#category-select", Select).value
        category = str(cat_val) if cat_val else ""

        scripts = self._all_scripts

        if category:
            scripts = [s for s in scripts if s.category == category]

        if search:
            if len(search) >= 2:
                matched = self._script_repo.search_scripts(search)
                matched_paths = {s.path for s in matched}
                if category:
                    scripts = [s for s in scripts if s.path in matched_paths]
                else:
                    scripts = [s for s in self._all_scripts if s.path in matched_paths]
            else:
                term = search.lower()
                scripts = [
                    s for s in scripts
                    if term in s.name.lower() or term in s.description.lower()
                ]

        self._refresh_script_table(scripts)

    # -------------------------------------------------------------------------
    # Script preview
    # -------------------------------------------------------------------------

    def _show_preview(self, script: ScriptMeta) -> None:
        preview = self.query_one("#preview-content", Static)
        try:
            content = self._script_repo.get_script_content(script.path)
            from rich.syntax import Syntax  # noqa: PLC0415
            preview.update(
                Syntax(content, "groovy", theme="monokai", line_numbers=True)
            )
        except Exception:
            preview.update(
                f"[bold]{script.name}[/bold]\n[dim]{script.description}[/dim]"
            )

    # -------------------------------------------------------------------------
    # Actions
    # -------------------------------------------------------------------------

    def action_run_script(self) -> None:
        if self.selected_script is None:
            self.notify("Select a script first (↑↓ to navigate).", severity="warning")
            return
        env_name = self.current_env
        if not env_name or env_name == _NO_ENV_MSG:
            self.notify(
                "No environment configured. Run: hac env add", severity="error"
            )
            return

        log = self.query_one("#output-log", RichLog)
        log.clear()
        mode = "[yellow]COMMIT[/yellow]" if self.commit_mode else "[dim]dry run[/dim]"
        log.write(
            f"[cyan]Executing:[/cyan] [bold]{self.selected_script.name}[/bold]"
            f" → [bold]{env_name}[/bold]  {mode}"
        )
        self._execute_script(
            env_name=env_name,
            script_path=self.selected_script.path,
            commit=self.commit_mode,
        )

    @work(exclusive=True, thread=False)
    async def _execute_script(
        self, env_name: str, script_path: str, commit: bool
    ) -> None:
        log = self.query_one("#output-log", RichLog)
        try:
            service = ExecuteGroovyService(
                hac_client=HacHttpClient(),
                config_store=self._config_store,
                script_repo=self._script_repo,
            )
            result = await service.execute(
                env_name=env_name,
                script_library_path=script_path,
                commit=commit,
            )
            if result.succeeded:
                log.write(
                    f"[bold green]SUCCESS[/bold green]  [dim]{result.execution_time_ms}ms[/dim]"
                )
                log.write(result.output or "[dim](no output)[/dim]")
            else:
                log.write(
                    f"[bold red]ERROR[/bold red]  [dim]{result.execution_time_ms}ms[/dim]"
                )
                if result.output:
                    log.write(result.output)
                if result.stack_trace:
                    log.write(f"[red]{result.stack_trace}[/red]")
        except HacCliError as exc:
            log.write(f"[bold red]FAILED:[/bold red] {exc}")
        except Exception as exc:
            log.write(f"[bold red]UNEXPECTED ERROR:[/bold red] {exc}")
            self.notify(str(exc), severity="error")

    def action_toggle_commit(self) -> None:
        self.commit_mode = not self.commit_mode
        self.notify(
            "Commit mode ON — changes will persist!" if self.commit_mode
            else "Dry run mode — changes rolled back.",
            severity="warning" if self.commit_mode else "information",
        )

    def action_focus_search(self) -> None:
        self.query_one("#search-input", Input).focus()

    def action_clear_search(self) -> None:
        inp = self.query_one("#search-input", Input)
        inp.value = ""
        self.query_one("#script-table", DataTable).focus()
        self._refresh_script_table(self._all_scripts)

    def action_next_env(self) -> None:
        if not self._environments:
            return
        try:
            idx = next(
                i for i, e in enumerate(self._environments)
                if e.name == self.current_env
            )
            next_env = self._environments[(idx + 1) % len(self._environments)]
        except StopIteration:
            next_env = self._environments[0]

        env_select = self.query_one("#env-select", Select)
        env_select.value = next_env.name
        self.current_env = next_env.name
        self.notify(f"Switched to: {next_env.name}", timeout=2)
