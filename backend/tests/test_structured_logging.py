"""Testes de logs estruturados structlog (issue #36)."""

import json
import logging
from io import StringIO

import structlog

from structured_logging import (
    RedactSensitiveQueryFilter,
    configure_structlog,
    get_logger,
    hash_user_id,
    redact_sensitive_query,
)


def test_hash_user_id_truncates_and_hides_raw_value():
    raw = "550e8400-e29b-41d4-a716-446655440000"
    hashed = hash_user_id(raw)
    assert hashed is not None
    assert len(hashed) == 16
    assert raw not in hashed
    assert hash_user_id(raw) == hashed


def test_hash_user_id_none_for_empty():
    assert hash_user_id(None) is None
    assert hash_user_id("") is None


def test_structlog_emits_json_with_required_fields():
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
        ],
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )
    handler.setFormatter(formatter)

    test_logger = logging.getLogger("simples.test")
    test_logger.handlers = [handler]
    test_logger.setLevel(logging.INFO)
    test_logger.propagate = False

    bound = structlog.get_logger("simples.test")
    bound.info("compile_start", user_id_hash=hash_user_id("user-abc"), channel="http")

    payload = json.loads(stream.getvalue().strip())
    assert payload["event"] == "compile_start"
    assert payload["level"] == "info"
    assert "timestamp" in payload
    assert payload["user_id_hash"] == hash_user_id("user-abc")
    assert payload["channel"] == "http"
    assert "user-abc" not in stream.getvalue()


def test_redact_sensitive_query_removes_jwt_from_url():
    raw = 'GET /ws/run?token=eyJhbGciOiJIUzI1NiJ9.secret HTTP/1.1'
    redacted = redact_sensitive_query(raw)
    assert "eyJhbGci" not in redacted
    assert "token=[REDACTED]" in redacted


def test_redact_filter_sanitizes_log_record_args():
    record = logging.LogRecord(
        name="werkzeug",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg='"%s" %s %s',
        args=('GET /ws/run?token=secret-jwt HTTP/1.1', 200, "-"),
        exc_info=None,
    )
    RedactSensitiveQueryFilter().filter(record)
    assert "secret-jwt" not in record.args[0]
    assert "token=[REDACTED]" in record.args[0]


def test_configure_structlog_is_idempotent():
    configure_structlog()
    configure_structlog()
    logger = get_logger("simples.api")
    assert logger is not None
