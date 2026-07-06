"""Structured logging with automatic secret redaction."""

from __future__ import annotations

import logging
import re
from typing import Optional

_SECRET_PATTERNS = [
    re.compile(r"(password[=: ]+)\S+", re.IGNORECASE),
    re.compile(r"(token[=: ]+)\S+", re.IGNORECASE),
    re.compile(r"(Authorization: )\S+", re.IGNORECASE),
    re.compile(r"(Cookie: ).*", re.IGNORECASE),
    re.compile(r"(CSRF[=: ]+)\S+", re.IGNORECASE),
    re.compile(r"(j_password[=: ]+)\S+", re.IGNORECASE),
]
_REDACTED = r"\g<1>[REDACTED]"


def redact(text: str) -> str:
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub(_REDACTED, text)
    return text


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact(str(record.msg))
        record.args = tuple(redact(str(a)) for a in (record.args or ()))
        return True


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        handler.addFilter(RedactingFilter())
        logger.addHandler(handler)
    if level is not None:
        logger.setLevel(level)
    return logger
