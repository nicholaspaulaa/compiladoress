"""Logs estruturados JSON com structlog (PRD §16.1, issue #36)."""

from __future__ import annotations

import hashlib
import logging
import re
import sys

import structlog

_CONFIGURED = False
_TOKEN_QUERY_RE = re.compile(r"(token=)[^&\s\"']+", re.IGNORECASE)


def redact_sensitive_query(text: str) -> str:
    """Remove JWT e outros segredos de query strings em mensagens de log."""
    return _TOKEN_QUERY_RE.sub(r"\1[REDACTED]", text)


class RedactSensitiveQueryFilter(logging.Filter):
    """Filtra access logs do Werkzeug que incluem ?token=... na URL."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_sensitive_query(record.msg)
        if record.args:
            record.args = tuple(
                redact_sensitive_query(arg) if isinstance(arg, str) else arg
                for arg in record.args
            )
        return True


def hash_user_id(user_id: str | None) -> str | None:
    """Retorna SHA-256 truncado do user_id — sem PII em claro nos logs."""
    if not user_id:
        return None
    digest = hashlib.sha256(user_id.encode("utf-8")).hexdigest()
    return digest[:16]


def configure_structlog(*, level: int = logging.INFO) -> None:
    """Configura structlog + stdlib logging para JSON no stdout."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            timestamper,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            timestamper,
        ],
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(RedactSensitiveQueryFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    _CONFIGURED = True


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Logger bound com nome do modulo (ex: simples.compile)."""
    return structlog.get_logger(name)
