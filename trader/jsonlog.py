"""JSON-lines structured logging (MON-03).

Every line has exactly these keys: ts (UTC ISO-8601), level, user, run_id, job,
event, symbol, client_order_id, reason_code, msg, data. No secrets; account
numbers show only the last 3 digits. Files rotate daily (UTC) and are kept
``LOG_RETENTION_DAYS`` (90) days. The audit log (database) is kept permanently.

Usage::

    log = get_logger("decide", user="a")
    log.info("decision made", event="decide.done", run_id=42, data={"n": 3})
"""

from __future__ import annotations

import json
import logging
import logging.handlers
import re
from collections.abc import Mapping
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Final

from trader.constants import ACCOUNT_VISIBLE_DIGITS, LOG_RETENTION_DAYS, REDACTED
from trader.secrets import SecretValue

LOG_FIELDS: Final = (
    "ts",
    "level",
    "user",
    "run_id",
    "job",
    "event",
    "symbol",
    "client_order_id",
    "reason_code",
    "msg",
    "data",
)
_CONTEXT_FIELDS: Final = (
    "user",
    "run_id",
    "job",
    "event",
    "symbol",
    "client_order_id",
    "reason_code",
)

# IBKR account ids: U1234567 / DU1234567.
_ACCOUNT_RE = re.compile(rf"\b(D?U)(\d+)(\d{{{ACCOUNT_VISIBLE_DIGITS}}})\b")
_SECRET_KEY_RE = re.compile(
    r"(?i)(pass(word|wd|phrase)?|secret|token|api[_-]?key|private[_-]?key|credential|"
    r"authorization|bearer|cookie)"
)
_SECRET_VALUE_RES: Final = (
    re.compile(r"\b\d{6,12}:[A-Za-z0-9_-]{30,}\b"),  # Telegram bot token
    re.compile(r"AGE-SECRET-KEY-1[0-9A-Z]+", re.I),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)((?:postgres(?:ql)?|mysql|redis|amqp)://[^:/@\s]+:)[^@\s]+(@)"),
    re.compile(r"(?i)([?&](?:api_token|api_key|token|key|password)=)[^&\s]+"),
    # key: value / key=value pairs in free text, e.g. a dict repr in a message
    re.compile(
        r"(?i)((?:pass(?:word|wd|phrase)?|secret|token|api[_-]?key|private[_-]?key|credential)"
        r"\w*['\"]?\s*[:=]\s*['\"]?)[^'\"\s,}&]+"
    ),
)


def mask_account(text: str) -> str:
    """``U1234567`` -> ``U****567`` (only the last 3 digits visible)."""
    return _ACCOUNT_RE.sub(lambda m: m.group(1) + "*" * len(m.group(2)) + m.group(3), text)


def _scrub_str(text: str) -> str:
    for rx in _SECRET_VALUE_RES:
        if rx.groups == 2:
            text = rx.sub(lambda m: m.group(1) + REDACTED + m.group(2), text)
        elif rx.groups == 1:
            text = rx.sub(lambda m: m.group(1) + REDACTED, text)
        else:
            text = rx.sub(REDACTED, text)
    return mask_account(text)


def scrub(value: Any, _depth: int = 0) -> Any:  # noqa: PLR0911, PLR0912
    """Make a value JSON-safe and free of secrets and full account numbers."""
    if _depth > 20:
        return "<max depth>"
    if isinstance(value, SecretValue):
        return REDACTED
    if value is None or isinstance(value, bool | int):
        return value
    if isinstance(value, float):
        return value
    if isinstance(value, Decimal):
        return str(value)  # SYS-13: never coerce money to float
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return _scrub_str(value.isoformat()) + "?naive"
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Enum):
        return scrub(value.value, _depth + 1)
    if isinstance(value, str):
        return _scrub_str(value)
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for k, v in value.items():
            key = str(k)
            out[key] = REDACTED if _SECRET_KEY_RE.search(key) else scrub(v, _depth + 1)
        return out
    if isinstance(value, list | tuple | set | frozenset):
        return [scrub(v, _depth + 1) for v in value]
    return _scrub_str(repr(value))


class JsonLinesFormatter(logging.Formatter):
    """Formats a record as one JSON object with the MON-03 fields, in order."""

    def __init__(self, default_user: str | None = None) -> None:
        super().__init__()
        self.default_user = default_user

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.fromtimestamp(record.created, tz=UTC)
        line: dict[str, Any] = {
            "ts": ts.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "level": record.levelname,
        }
        ctx: Mapping[str, Any] = getattr(record, "ctx", {})
        for f in _CONTEXT_FIELDS:
            v = ctx.get(f)
            if f == "user" and v is None:
                v = self.default_user
            if f == "job" and v is None:
                v = record.name
            line[f] = scrub(v)
        line["msg"] = scrub(record.getMessage())
        data = dict(ctx.get("data") or {})
        if record.exc_info:
            data["exc"] = self.formatException(record.exc_info)
        line["data"] = scrub(data)
        return json.dumps(line, ensure_ascii=False, separators=(",", ":"))


class StructLogger:
    """Thin wrapper that carries bound context (user, job, run_id ...)."""

    def __init__(self, logger: logging.Logger, **context: Any) -> None:
        unknown = set(context) - set(_CONTEXT_FIELDS)
        if unknown:
            raise ValueError(f"unknown log context fields: {sorted(unknown)}")
        self._logger = logger
        self._context = context

    def bind(self, **context: Any) -> StructLogger:
        return StructLogger(self._logger, **{**self._context, **context})

    def _log(self, level: int, msg: str, *, exc_info: bool = False, **fields: Any) -> None:
        unknown = set(fields) - {*_CONTEXT_FIELDS, "data"}
        if unknown:
            raise ValueError(f"unknown log fields: {sorted(unknown)}")
        ctx = {**self._context, **fields}
        self._logger.log(level, msg, extra={"ctx": ctx}, exc_info=exc_info)

    def debug(self, msg: str, **f: Any) -> None:
        self._log(logging.DEBUG, msg, **f)

    def info(self, msg: str, **f: Any) -> None:
        self._log(logging.INFO, msg, **f)

    def warning(self, msg: str, **f: Any) -> None:
        self._log(logging.WARNING, msg, **f)

    def error(self, msg: str, **f: Any) -> None:
        self._log(logging.ERROR, msg, **f)

    def exception(self, msg: str, **f: Any) -> None:
        self._log(logging.ERROR, msg, exc_info=True, **f)

    def critical(self, msg: str, **f: Any) -> None:
        self._log(logging.CRITICAL, msg, **f)


ROOT_LOGGER_NAME: Final = "trader"


def configure_logging(
    *,
    user: str | None = None,
    log_dir: Path | None = None,
    level: int = logging.INFO,
    stream: Any = None,
) -> logging.Logger:
    """Configure the ``trader`` logger: JSON lines to stderr and, if ``log_dir`` is
    given, to a daily-rotated file kept ``LOG_RETENTION_DAYS`` days (UTC)."""
    root = logging.getLogger(ROOT_LOGGER_NAME)
    root.handlers.clear()
    root.setLevel(level)
    root.propagate = False
    fmt = JsonLinesFormatter(default_user=user)
    sh = logging.StreamHandler(stream)
    sh.setFormatter(fmt)
    root.addHandler(sh)
    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        fh = logging.handlers.TimedRotatingFileHandler(
            log_dir / f"trader-{user or 'system'}.jsonl",
            when="midnight",
            utc=True,
            backupCount=LOG_RETENTION_DAYS,
            encoding="utf-8",
        )
        fh.setFormatter(fmt)
        root.addHandler(fh)
    return root


def get_logger(job: str, **context: Any) -> StructLogger:
    return StructLogger(logging.getLogger(f"{ROOT_LOGGER_NAME}.{job}"), job=job, **context)
