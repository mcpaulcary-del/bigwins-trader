"""BF-D31: the daily EODHD bulk refresh of the price store on the server (mocked vendor).

Counted call budget (recorded before each request), idempotent, complete-or-nothing,
fail closed when stale (no decision; the owner is paged), key from the Docker secret only.
"""

from __future__ import annotations

import gzip
import json
from collections.abc import Mapping
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from trader.bf_app import RETRY_UNTIL, at
from trader.data.store import RawStore
from trader.journal import Journal
from trader.secrets import SecretError, SecretValue
from trader.store_refresh import BUDGET_PREFIX, STORE_PAGE_SLOT, JournalCallBudget, StoreRefresher

KEY = "k3y-not-real-0123456789"
D, PREV = date(2026, 11, 20), date(2026, 11, 19)
NOW = datetime(2026, 11, 20, 8, 35, tzinfo=UTC)  # 19:35 Sydney


def _gz(p: Path, obj: object) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(p, "wt", encoding="utf-8") as f:
        json.dump(obj, f)


def _rows(day: date, n: int) -> list[dict[str, Any]]:
    return [{"code": f"C{i:04d}", "exchange_short_name": "AU", "date": str(day),
             "close": 1.0 + i / 1000, "volume": 1000} for i in range(n)]  # fmt: skip


class Vendor:
    """EODHD's bulk endpoint, mocked: records each request and the journal's count then."""

    def __init__(self, j: Journal, eod_day: date = D, n: int = 1500, fail: str = "") -> None:
        self.j, self.eod_day, self.n, self.fail = j, eod_day, n, fail
        self.calls: list[tuple[str, dict[str, str], int]] = []

    def __call__(self, url: str, params: Mapping[str, str]) -> bytes:
        counted = len(self.j.job_records(BUDGET_PREFIX))
        self.calls.append((url, dict(params), counted))
        if self.fail:
            err = OSError(f"HTTP Error {self.fail} for {url}?api_token={params['api_token']}")
            err.code = int(self.fail)  # type: ignore[attr-defined]
            raise err
        typ = params.get("type")
        if typ == "dividends":
            rows: list[dict[str, Any]] = [
                {"code": "C0001", "date": str(D), "currency": "AUD", "unadjustedValue": "0.05"}
            ]
        elif typ == "splits":
            rows = [{"code": "C0002", "date": str(D), "split": "2.000000/1.000000"}]
        else:  # the last row per code: before EODHD has the day, yesterday's rows
            rows = _rows(self.eod_day, self.n) + _rows(PREV, 3)
        return json.dumps(rows).encode()


def _store(tmp: Path) -> Path:
    root = tmp / "eodhd"
    _gz(root / f"raw/bulk_eod/AU_{PREV}__20261119T092811Z.json.gz", _rows(PREV, 1500))
    (root / "manifest.tsv").write_text("utc\tkind\tsymbol\thttp\tcost\tbytes\tpayload_sha256"
                                       "\tfile\tfile_sha256\turl\n")  # fmt: skip
    return root


def _refresher(tmp: Path, vendor: Vendor, **kw: Any) -> StoreRefresher:
    return StoreRefresher(
        _store(tmp), RawStore(tmp / "raw", "owner"), transport=vendor,
        token=lambda: SecretValue(KEY), sleep=lambda s: None, **kw,
    )  # fmt: skip


def test_BF_D31_refresh_appends_the_days_bulk_files_counted_before_each_call(
    tmp_path: Path,
) -> None:
    j = Journal.sqlite()
    v = Vendor(j)
    r = _refresher(tmp_path, v)
    assert r.last_day() == PREV
    res = r.refresh(D, j, NOW)
    assert res.status == "REFRESHED" and res.rows == 1500 and res.calls == 3
    assert [c[1].get("type") for c in v.calls] == [None, "dividends", "splits"]
    assert all(c[0] == "https://eodhd.com/api/eod-bulk-last-day/AU" for c in v.calls)
    assert all(c[1]["date"] == str(D) and c[1]["api_token"] == KEY for c in v.calls)
    assert [c[2] for c in v.calls] == [1, 2, 3]  # each request recorded before it was sent
    assert JournalCallBudget(j, 100000).used(NOW.date()) == 300  # 100 a bulk request
    assert r.last_day() == D
    eod = r.files("bulk_eod", D)
    assert len(eod) == 1
    with gzip.open(eod[0], "rt") as f:
        rows = json.load(f)
    assert len(rows) == 1500 and {x["date"] for x in rows} == {str(D)}  # yesterday's dropped
    assert len(r.files("bulk_div", D)) == len(r.files("bulk_splits", D)) == 1
    man = (r.root / "manifest.tsv").read_text()
    assert man.count(f"\tAU_{D}\t") == 3 and KEY not in man and "api_token" not in man
    assert len(r.raw.files("eodhd")) == 3  # the unchanged responses (DAT-09)
    assert not list(r.root.rglob("*.part"))  # atomic writes
    # idempotent: a complete day is not fetched again
    again = r.refresh(D, j, NOW)
    assert again.status == "PRESENT" and len(v.calls) == 3


def test_BF_D31_store_reader_sees_the_refreshed_day(tmp_path: Path) -> None:
    from trader.data.forward_store import ForwardStore

    j = Journal.sqlite()
    r = _refresher(tmp_path, Vendor(j, n=1000), min_rows=1000, min_share=0.5)
    man = ["utc\tkind\tsymbol\thttp\tcost\tbytes\tpayload_sha256\tfile\tfile_sha256\turl"]
    _gz(r.root / "raw/eod/C0001.AU__1.json.gz", [{"date": str(PREV), "close": 1.0, "volume": 5}])
    man.append("t\teod\tC0001.AU\t200\t1\t1\tx\traw/eod/C0001.AU__1.json.gz\tx\tu")
    (r.root / "manifest.tsv").write_text("\n".join(man) + "\n")
    (r.root / "symbols.csv").write_text("Code,Name,Type\nC0001,One Ltd,Common Stock\n")
    assert r.refresh(D, j, NOW).ok
    sess = [date(2026, 11, 17), date(2026, 11, 18), PREV, D]
    p = ForwardStore(r.root).build_panel(D, sess, history=4)
    k = p.entities.index("C0001")
    assert p.close[-1, k] == pytest.approx(1.001)  # D's close from the refreshed bulk file


def test_BF_D31_incomplete_or_early_data_writes_nothing(tmp_path: Path) -> None:
    j = Journal.sqlite()
    r = _refresher(tmp_path, Vendor(j, eod_day=PREV))  # EODHD has not got D yet
    res = r.refresh(D, j, NOW)
    assert res.status == "NOT_READY" and "0 of 1503 rows" in res.note and res.calls == 2
    assert r.last_day() == PREV and r.files("bulk_div", D) == []
    j2 = Journal.sqlite()
    r2 = _refresher(tmp_path / "b", Vendor(j2, n=1200), attempts=1)  # < 90% of yesterday
    assert r2.refresh(D, j2, NOW).status == "NOT_READY" and r2.last_day() == PREV


def test_BF_D31_budget_fails_closed_before_the_request(tmp_path: Path) -> None:
    j = Journal.sqlite()
    v = Vendor(j)
    r = _refresher(tmp_path, v, calls_per_day=250)  # two bulk requests fit, not three
    res = r.refresh(D, j, NOW)
    assert res.status == "BUDGET" and res.fatal and "DATA_BUDGET" in res.note
    assert len(v.calls) == 2  # the third was never sent
    assert r.last_day() == PREV  # nothing written: complete or nothing
    with pytest.raises(Exception, match="DATA_BUDGET"):
        JournalCallBudget(j, 250).reserve("x", 100, NOW)
    tomorrow = datetime(2026, 11, 21, 0, 1, tzinfo=UTC)  # the GMT day resets the count
    JournalCallBudget(j, 250).reserve("x", 100, tomorrow)


def test_BF_D31_key_only_from_the_secret_and_never_in_a_message(tmp_path: Path) -> None:
    j = Journal.sqlite()
    v = Vendor(j, fail="401")
    r = _refresher(tmp_path, v)
    res = r.refresh(D, j, NOW)
    assert res.status == "REFUSED" and res.fatal and KEY not in res.note and "401" in res.note
    v5 = Vendor(j, fail="503")
    r5 = _refresher(tmp_path / "c", v5)
    res5 = r5.refresh(D, j, NOW)
    assert res5.status == "FAILED" and not res5.fatal and KEY not in res5.note
    assert len(v5.calls) == 2  # retried within the slot

    def no_secret() -> SecretValue:
        raise SecretError("secret 'eodhd_api_token' not found in /run/secrets")

    v0 = Vendor(j)
    r0 = StoreRefresher(_store(tmp_path / "d"), RawStore(tmp_path / "r0", "owner"),
                        transport=v0, token=no_secret)  # fmt: skip
    assert r0.refresh(D, j, NOW).status == "NO_SECRET" and v0.calls == []


def test_BF_D31_config_has_no_key_field_and_the_cli_reads_the_secret(tmp_path: Path) -> None:
    from trader.bfast_cli import store_refresher
    from trader.bfast_config import StoreRefreshCfg, load_bfast_config

    with pytest.raises(ValidationError):
        StoreRefreshCfg.model_validate({"raw_dir": "/x", "api_token": "abc"})
    cfg = load_bfast_config(Path(__file__).resolve().parent.parent / "config" / "bfast.yaml")
    assert cfg.data.store_refresh is not None
    raw = cfg.model_dump()
    raw["data"]["forward_store"] = str(_store(tmp_path))
    raw["data"]["store_refresh"]["raw_dir"] = str(tmp_path / "raw")
    r = store_refresher(type(cfg).model_validate(raw))
    assert r is not None and r.bulk_call_cost == 100 and r.calls_per_day == 100000
    with pytest.raises(SecretError):  # the Docker secret file, /run/secrets/eodhd_api_token
        r.token()
    assert r.refresh(D, Journal.sqlite(), NOW).status == "NO_SECRET"


# ---------------------------------------------------------------- in the app


def _app_with(tmp: Path, vendor_fail: str = "", eod_day: date | None = None) -> Any:
    from tests.test_bf_app import D0, _app

    app, _, tr = _app(D0)
    v = Vendor(app.j, eod_day=eod_day or D0, fail=vendor_fail)
    r = StoreRefresher(
        tmp / "eodhd", RawStore(tmp / "raw", "owner"), transport=v,
        token=lambda: SecretValue(KEY), sleep=lambda s: None,
    )  # fmt: skip
    prev = max(d for d in app.sessions if d < D0)
    _gz(r.root / f"raw/bulk_eod/AU_{prev}__1.json.gz", _rows(prev, 1500))
    app.store_refresh = r
    return app, tr, v


def test_BF_D31_no_decision_on_a_stale_store_then_paged(tmp_path: Path) -> None:
    from tests.test_bf_app import D0

    app, tr, _ = _app_with(tmp_path)
    assert app.job_decide(D0, at(D0, "22:20")) is False  # waits: the refresh may still land
    assert app.j.batches_of(app.s.book) == []
    assert app.job_decide(D0, at(D0, RETRY_UNTIL)) is True
    assert app.j.batches_of(app.s.book) == [] and app.j.batches_of(app.s.sim_book) == []
    rec = dict(app.j.job_records(f"decide:{app.s.book}:{D0}"))
    assert "price store stale" in rec[f"decide:{app.s.book}:{D0}"]["data_block"]
    assert any("rule 14 data block" in m and "price store stale" in m for _, m in tr.outbox)


def test_BF_D31_refresh_job_then_the_decision_goes_ahead(tmp_path: Path) -> None:
    from tests.test_bf_app import D0

    app, tr, v = _app_with(tmp_path)
    app.run_job("store_refresh", D0, at(D0, "17:35"))
    assert app.j.job_done(f"store-refresh:{D0}") and len(v.calls) == 3
    app.run_job("store_refresh", D0, at(D0, "18:35"))  # once a day
    assert len(v.calls) == 3
    assert app.job_decide(D0, at(D0, "22:20")) is True
    assert app.j.batches_of(app.s.book)  # the start decision's batches
    assert not any("price store" in m for _, m in tr.outbox)


def test_BF_D31_refresh_pages_once_at_the_last_slot_or_at_once_when_fatal(
    tmp_path: Path,
) -> None:
    from tests.test_bf_app import D0

    prev = max(d for d in _app_with(tmp_path / "x")[0].sessions if d < D0)
    app, tr, _ = _app_with(tmp_path / "a", eod_day=prev)  # EODHD late all evening
    app.run_job("store_refresh", D0, at(D0, "17:35"))
    assert not any("PAGE price store" in m for _, m in tr.outbox)
    app.run_job("store_refresh", D0, at(D0, STORE_PAGE_SLOT))
    app.run_job("store_refresh", D0, at(D0, "22:10"))
    pages = [m for _, m in tr.outbox if "PAGE price store not refreshed" in m]
    assert len(pages) == 1 and "NOT_READY" in pages[0] and KEY not in pages[0]
    app2, tr2, _ = _app_with(tmp_path / "b", vendor_fail="403")
    app2.run_job("store_refresh", D0, at(D0, "17:35"))
    assert [m for _, m in tr2.outbox if "PAGE price store" in m and "REFUSED" in m]
