"""Core domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    AUTH_FAILED = "auth_failed"


@dataclass(frozen=True)
class Environment:
    name: str
    url: str
    username: str
    timeout: int = 30
    verify_ssl: bool = True

    @property
    def hac_base_url(self) -> str:
        return self.url.rstrip("/")

    @property
    def login_url(self) -> str:
        return f"{self.hac_base_url}/j_spring_security_check"

    @property
    def scripting_url(self) -> str:
        return f"{self.hac_base_url}/console/scripting/api/"

    @property
    def login_page_url(self) -> str:
        return f"{self.hac_base_url}/login"

    @property
    def execute_url(self) -> str:
        return f"{self.hac_base_url}/console/scripting/api/execute"


@dataclass(frozen=True)
class ExecutionContext:
    environment: Environment
    script_content: str
    commit: bool = False
    timeout_override: Optional[int] = None

    @property
    def effective_timeout(self) -> int:
        return self.timeout_override or self.environment.timeout


@dataclass
class ExecutionResult:
    status: ExecutionStatus
    output: str
    execution_time_ms: int
    stack_trace: Optional[str] = None
    environment_name: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def succeeded(self) -> bool:
        return self.status == ExecutionStatus.SUCCESS


@dataclass(frozen=True)
class ScriptMeta:
    name: str
    description: str
    category: str
    path: str
    tags: tuple[str, ...] = ()
    params: tuple[str, ...] = ()
