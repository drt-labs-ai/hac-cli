"""Domain exceptions."""

from __future__ import annotations


class HacCliError(Exception):
    """Base exception for hac-cli."""


class EnvironmentNotFoundError(HacCliError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Environment '{name}' not found. Run: hac env add --name {name}")
        self.name = name


class HacAuthenticationError(HacCliError):
    def __init__(self, env_name: str) -> None:
        super().__init__(f"Authentication failed for environment '{env_name}'.")
        self.env_name = env_name


class HacConnectionError(HacCliError):
    def __init__(self, url: str, reason: str) -> None:
        super().__init__(f"Cannot connect to HAC at '{url}': {reason}")
        self.url = url


class ScriptExecutionError(HacCliError):
    def __init__(self, env_name: str, message: str) -> None:
        super().__init__(f"Script execution failed on '{env_name}': {message}")
        self.env_name = env_name


class ScriptNotFoundError(HacCliError):
    def __init__(self, path: str) -> None:
        super().__init__(f"Script not found in library: '{path}'")
        self.path = path


class MissingCredentialsError(HacCliError):
    def __init__(self, env_name: str) -> None:
        super().__init__(
            f"No password stored for environment '{env_name}'. "
            f"Run: hac env add --name {env_name}"
        )
        self.env_name = env_name


class CommitBlockedBySafeModeError(HacCliError):
    def __init__(self, env_name: str) -> None:
        super().__init__(
            f"Environment '{env_name}' is in safe mode — commit=True is blocked. "
            f"To allow commits, run: hac env add --name {env_name} ... --no-safe-mode"
        )
        self.env_name = env_name
