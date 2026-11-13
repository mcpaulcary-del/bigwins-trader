"""MON-03: logs are JSON lines with ts (UTC ISO-8601), level, user, run_id, job,
event, symbol, client_order_id, reason_code, msg, data. No secrets; account
numbers show only the last 3 digits. Kept 90 days."""

from __future__ import annotations

import io
import json
import logging
import logging.handlers
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from trader.constants import LOG_RETENTION_DAYS
from trader.enums import ReasonCode
from trader.jsonlog import LOG_FIELDS, configure_logging, get_logger, mask_account, scrub
from trader.secrets import SecretValue


@pytest.fixture
def stream() -> io.StringIO:
    s = io.StringIO()
    configure_logging(user="a", stream=s, level=logging.DEBUG)
    return s


def _lines(stream: io.StringIO) -> list[dict[str, Any]]:
    return [json.loads(line) for line in stream.getvalue().splitlines()]


def test_MON_03_fields_exact_and_ordered(stream: io.StringIO) -> None:
    log = get_logger("decide", run_id=7)
    log.info(
        "planned",
        event="decide.done",
        symbol="BHP",
        client_order_id="a-2026-11-16-BHP-B-0",
        reason_code=ReasonCode.MIN_ORDER,
        data={"qty": 10},
    )
    (line,) = _lines(stream)
    assert tuple(line) == LOG_FIELDS
    assert line["level"] == "INFO"
    assert line["user"] == "a"
    assert line["run_id"] == 7
    assert line["job"] == "decide"
    assert line["event"] == "decide.done"
    assert line["symbol"] == "BHP"
    assert line["reason_code"] == "MIN_ORDER"
    assert line["msg"] == "planned"
    assert line["data"] == {"qty": 10}


def test_MON_03_missing_fields_are_null(stream: io.StringIO) -> None:
    get_logger("backup").warning("x")
    (line,) = _lines(stream)
    assert set(line) == set(LOG_FIELDS)
    assert line["symbol"] is None and line["run_id"] is None
    assert line["data"] == {}


def test_MON_03_ts_is_utc_iso8601(stream: io.StringIO) -> None:
    get_logger("x").info("hello")
    (line,) = _lines(stream)
    assert line["ts"].endswith("Z")
    ts = datetime.fromisoformat(line["ts"].replace("Z", "+00:00"))
    assert ts.utcoffset() is not None and ts.utcoffset().total_seconds() == 0  # type: ignore[union-attr]
    assert abs((datetime.now(UTC) - ts).total_seconds()) < 60


def test_MON_03_account_numbers_masked(stream: io.StringIO) -> None:
    get_logger("recon").info("account U1234567 ok", data={"acct": "DU7654321", "n": ["U1234567"]})
    raw = stream.getvalue()
    assert "1234567" not in raw and "7654321" not in raw
    (line,) = _lines(stream)
    assert line["msg"] == "account U****567 ok"
    assert line["data"]["acct"] == "DU****321"
    assert mask_account("U12345") == "U**345"


@pytest.mark.parametrize(
    ("payload", "secret"),
    [
        ({"telegram_bot_token": "abc"}, "abc"),
        ({"password": "hunter2"}, "hunter2"),
        ({"nested": {"api_key": "k-123"}}, "k-123"),
        ({"x": SecretValue("s3cr3t-value")}, "s3cr3t-value"),
        ({"url": "postgresql://u:pa55word@db/x"}, "pa55word"),
        (
            {"m": "bot 123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsawQ"},
            "AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsawQ",
        ),
        ({"m": "GET /api?api_token=deadbeef42&fmt=json"}, "deadbeef42"),
        ({"h": "Authorization: Bearer eyJabc.def"}, "eyJabc.def"),
    ],
)
def test_MON_03_no_secrets_in_logs(
    stream: io.StringIO, payload: dict[str, Any], secret: str
) -> None:
    get_logger("x").info(f"msg {payload!s}", data=payload)
    assert secret not in stream.getvalue()


def test_MON_03_decimal_logged_as_string(stream: io.StringIO) -> None:
    get_logger("x").info("m", data={"px": Decimal("59.6100")})
    assert _lines(stream)[0]["data"]["px"] == "59.6100"


def test_MON_03_exception_captured_in_data(stream: io.StringIO) -> None:
    try:
        raise RuntimeError("boom")
    except RuntimeError:
        get_logger("x").exception("failed")
    line = _lines(stream)[0]
    assert line["level"] == "ERROR"
    assert "boom" in line["data"]["exc"]


def test_MON_03_unknown_fields_rejected() -> None:
    with pytest.raises(ValueError, match="unknown"):
        get_logger("x").info("m", account="U1234567")


def test_MON_03_file_rotation_keeps_90_days(tmp_path: Path) -> None:
    root = configure_logging(user="b", log_dir=tmp_path, stream=io.StringIO())
    fh = [h for h in root.handlers if isinstance(h, logging.handlers.TimedRotatingFileHandler)]
    assert len(fh) == 1
    assert fh[0].backupCount == LOG_RETENTION_DAYS == 90
    assert fh[0].utc is True
    assert fh[0].when == "MIDNIGHT"
    get_logger("x").info("to file")
    for h in root.handlers:
        h.flush()
    line = json.loads((tmp_path / "trader-b.jsonl").read_text().splitlines()[0])
    assert line["user"] == "b"
    for h in list(root.handlers):
        h.close()
        root.removeHandler(h)


def test_MON_03_naive_datetime_flagged() -> None:
    assert scrub(datetime(2026, 1, 1)).endswith("?naive")
    assert scrub(datetime(2026, 1, 1, tzinfo=UTC)) == "2026-01-01T00:00:00Z"
