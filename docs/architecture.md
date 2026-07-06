# Architecture

## Overview

hac-cli follows a **clean architecture** (ports and adapters) so that the core domain has zero
external dependencies and every infrastructure concern is swappable.

```
┌──────────────────────────────────────────────────────────────────┐
│  Entry Points                                                    │
│  ┌─────────────┐   ┌──────────────────────────────────────────┐ │
│  │  CLI Layer  │   │             TUI Layer                    │ │
│  │  (Typer)    │   │  (Textual — tui/app.py)                  │ │
│  └──────┬──────┘   └───────────────────┬──────────────────────┘ │
│         │                              │                         │
│         └──────────────┬───────────────┘                        │
│                        ▼                                         │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                  Application Layer                          ││
│  │   ExecuteGroovyService    EnvironmentService                ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          │  depends on ports only               │
│                          ▼                                       │
│  ┌───────────────────────────────────────────────────────────── ┐│
│  │                    Domain Layer                             ││
│  │   models.py   ports.py   exceptions.py                     ││
│  │   (pure Python — zero external imports)                    ││
│  └───────────────────────────────────────────────────────────── ┘│
│                          ▲                                       │
│                 implements ports                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │               Infrastructure Layer                          ││
│  │   HacHttpClient   TomlConfigStore   KeyringSecretStore      ││
│  │   FilesystemScriptRepository                                ││
│  └─────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

## Dependency Rule

Dependencies flow **inward only**:

- CLI → Application → Domain ← Infrastructure

The domain never imports from infrastructure. Infrastructure imports domain models and
implements domain ports. This means the entire HAC HTTP stack can be replaced without
touching a single CLI command.

## HAC Authentication Flow

```
Client                          HAC Server
  │                                │
  │── GET /login ─────────────────▶│
  │◀─ 200 + HTML (CSRF in input) ──│
  │                                │
  │── POST /j_spring_security_check│
  │   j_username, j_password, _csrf│
  │◀─ 302 → / (success)  ──────────│
  │      or 302 → /login?error ────│
  │                                │
  │── GET /console/scripting/api/ ─▶│
  │◀─ 200 + HTML (CSRF in meta) ───│
  │                                │
  │── POST /console/scripting/api/execute
  │   script=..., commit=false/true│
  │   X-CSRF-TOKEN: <token>        │
  │◀─ 200 + JSON result ───────────│
```

### Session Caching

`HacHttpClient` keeps a `_CachedSession` (cookie jar + creation time) per environment
in memory. TTL is 30 minutes. On any 401/403 or a CSRF-page redirect to `/login`, the
session is invalidated and a single re-authentication is attempted before raising.

## Configuration & Secrets

| Data | Storage | File |
|---|---|---|
| Environment URL, username, timeout | TOML file | `~/.hac-cli/config.toml` |
| Passwords | OS keychain | macOS Keychain / Windows Credential Manager / libsecret |
| Session cookies | In-memory only | Never persisted |
| CSRF tokens | In-memory, per-request | Never persisted |

The `HAC_CONFIG_PATH` environment variable redirects the TOML config directory.
The `HAC_SCRIPTS_PATH` environment variable redirects the script library root.
Both are evaluated at class instantiation, not at module import.

## Script Library Format

Scripts live in `scripts/<category>/<name>.groovy`. The optional frontmatter:

```groovy
// @meta
// name: Human Readable Name
// description: One-line description
// category: cache
// tags: [cache, performance]
// params: [paramName]
// @end
```

`FilesystemScriptRepository` parses this with a regex, falls back to a title-cased
stem if no frontmatter is present. Fuzzy search uses `thefuzz` with a 40-point cutoff.

## Error Hierarchy

```
HacCliError
├── EnvironmentNotFoundError(name)
├── HacAuthenticationError(env_name)
├── HacConnectionError(url, reason)
├── ScriptExecutionError(env_name, message)
├── ScriptNotFoundError(path)
└── MissingCredentialsError(env_name)
```

All exceptions carry enough context to produce a user-friendly error message without
leaking credentials.

## TUI Architecture (Textual)

```
HacApp (textual.App)
├── Header
├── Horizontal#toolbar
│   ├── Label
│   ├── Select#env-select      ← environment switcher
│   └── Label#mode-label       ← DRY RUN / COMMIT indicator
├── Horizontal#main
│   ├── Vertical#left-panel
│   │   ├── Horizontal#search-bar
│   │   │   ├── Input#search-input
│   │   │   └── Select#category-select
│   │   └── DataTable#script-table
│   └── Vertical#right-panel
│       ├── Vertical#preview-section
│       │   ├── Label (title)
│       │   └── Static#preview-content   ← Rich Syntax object
│       └── Vertical#output-section
│           ├── Label (title)
│           └── RichLog#output-log
└── Footer
```

Reactive properties (`current_env`, `commit_mode`, `selected_script`) drive UI state.
Script execution runs via `@work(exclusive=True, thread=False)` — Textual's async worker
system that prevents UI freeze and serialises concurrent execute calls.

## Extension Points

| Feature | Add port to | Implement in | Register in |
|---|---|---|---|
| FlexibleSearch | `domain/ports.py` | `infrastructure/hac_flexsearch_client.py` | `cli/cmd_flexsearch.py` |
| ImpEx import | `domain/ports.py` | `infrastructure/hac_impex_client.py` | `cli/cmd_impex.py` |
| CronJob trigger | `domain/ports.py` | `infrastructure/hac_cronjob_client.py` | `cli/cmd_cronjobs.py` |
| Remote script repo | `IScriptRepository` | `infrastructure/remote_script_repo.py` | `cli/app.py` |
| Parallel execution | `ExecuteGroovyService` | `asyncio.gather()` | `cmd_groovy.py` |
| NLP selection | `IScriptRepository.search_scripts` | Claude API call | `nlp_selector.py` |
