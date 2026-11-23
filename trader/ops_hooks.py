"""The trader's loop hooks for the missed-job alarm and the weekly digest (BF-D77,
BF-D79), and the daily-cycle check the host worker pings healthchecks.io with (BF-D77 b).

* ``OpsHooks.tick`` (every scheduler pass, at most every few minutes): each late or
  failed job (``ops_view.freshness``) is PAGEd once per incident (Web Push + inbox); the
  incidents already told are kept in the journal (``freshness-told``), so a restart does
  not repeat them. On Fridays after the 22:45 report the week's digest goes to the inbox
  once (``digest-last``).
* ``cycle_ok_day``: the day whose daily cycle finished well (the report written, no
  error), or a non-trading day once it is over; the host worker pings the owner's
  optional ``healthchecks_daily_url`` once for each such day, so an outside service
  alerts the phone when the server goes silent.

Messages only: nothing here trades, approves or changes a setting.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from trader import info_view as iv
from trader import ops_view as ov
from trader.constants import ASX_TZ
from trader.journal import Journal

EVERY = timedelta(minutes=5)
DIGEST_AT = time(22, 55)  # Fridays, after the 22:45 daily report
KEEP_TOLD = 80


def cycle_ok_day(j: Journal, book: str, sessions: Sequence[date], now: datetime) -> date | None:
    """Today, once its cycle is complete and good (after 23:00 Sydney): a trading day
    needs its daily value record and a report job without an error; a non-trading day
    counts once it is over. None before the trader's first daily report."""
    t = now.astimezone(ASX_TZ)
    if t.time() < time(23, 0):
        return None
    if not ov.job_rows(j, f"value:{book}:", 1):
        return None  # the trader has not started its daily cycle yet
    d = t.date()
    if d not in set(sessions):
        return d
    if not ov.job_rows(j, f"value:{book}:{d}", 1):
        return None
    rep = ov.job_rows(j, f"{d}:22:45:report", 1)
    if not rep or (isinstance(rep[-1][1], Mapping) and rep[-1][1].get("error")):
        return None
    return d


@dataclass
class OpsHooks:
    journal: Journal
    book: str
    sessions: Callable[[], Sequence[date]]
    notify: Callable[..., int]
    info_enabled: bool = False
    index: Callable[[], list[tuple[date, float]]] | None = None  # A200 total-return level
    fixed_per_year: Decimal = Decimal(600)
    fixed_items: Mapping[str, Decimal] | None = None
    scorecard: Path | None = None
    info_dir: Path | None = None
    store_root: Path | None = None
    _last: datetime | None = field(default=None, repr=False)

    def tick(self, now: datetime) -> None:
        if self._last is not None and now - self._last < EVERY:
            return
        self._last = now
        self.alerts(now)
        self.weekly(now)

    # ------------------------------------------------------------ missed-job alarm
    def alerts(self, now: datetime) -> list[str]:
        from trader.app_store import set_state

        fresh = ov.freshness(self.journal, self.book, list(self.sessions()), now,
                             self.info_enabled)  # fmt: skip
        st = ov.state(self.journal, "freshness-told")
        told = [str(x) for x in st[0]] if st and isinstance(st[0], list) else []
        sent = []
        for f in fresh:
            if not f.bad or not f.incident or f.incident in told:
                continue
            what = "FAILED" if f.status == "failed" else "is late"
            self.notify(f"PAGE {f.name} {what}: {f.detail or 'last ' + f.last}. "
                        "See Server > Health.", "page", "/health")  # fmt: skip
            told.append(f.incident)
            sent.append(f.incident)
        if sent:
            set_state(self.journal, "freshness-told", told[-KEEP_TOLD:], now)
        return sent

    # ------------------------------------------------------------ the weekly digest
    def weekly(self, now: datetime) -> bool:
        from trader.app_store import set_state

        t = now.astimezone(ASX_TZ)
        if t.weekday() != 4 or t.time() < DIGEST_AT:
            return False
        st = ov.state(self.journal, "digest-last")
        if st and st[0] == str(t.date()):
            return False
        dg = self.build(t.date(), now)
        self.notify(dg.text(), "info", f"/digest?w={t.date()}")
        set_state(self.journal, "digest-last", str(t.date()), now)
        return True

    def build(self, friday: date, now: datetime) -> ov.Digest:
        j = self.journal
        series = [(date.fromisoformat(k.rsplit(":", 1)[1]), Decimal(str(r["value"])))
                  for k, r, _ in ov.job_rows(j, f"value:{self.book}:")]  # fmt: skip
        idx: list[tuple[date, float]] = []
        if self.index is not None:
            try:
                idx = list(self.index())
            except Exception:
                idx = []
        capital = sum((Decimal(str(m["amount"])) for m in j.cash_moves_of(self.book)
                       if m["kind"] == "DEPOSIT"), Decimal(0))  # fmt: skip
        fc = ov.fixed_costs(j, self.fixed_items, self.fixed_per_year)
        sb = ov.scoreboard(series, idx, capital, fc.per_year)
        mon, fri = ov.week_of(friday)
        week = [(d, v) for d, v in series if d < mon][-1:] + [(d, v) for d, v in series
                                                                if mon <= d <= fri]  # fmt: skip
        week_sb = ov.scoreboard(week, idx, week[0][1], Decimal(0)) if len(week) > 1 else None
        sess = list(self.sessions())
        fresh = ov.freshness(j, self.book, sess, now, self.info_enabled)
        today = now.astimezone(ASX_TZ).date()
        arch = iv.status(self.info_dir, sess, today)
        store_days: list[date] = []
        if self.store_root is not None:
            for p in (self.store_root / "raw" / "bulk_eod").glob("AU_*.json.gz"):
                try:
                    store_days.append(date.fromisoformat(p.name[3:13]))
                except ValueError:
                    continue
        needs = _needs(j, self.book)
        lines = ov.research_lines(self.scorecard, today)
        return ov.digest(j, self.book, friday, sb, week_sb, lines, fresh, arch.days,
                         sorted(store_days), needs)  # fmt: skip


def _needs(j: Journal, book: str) -> list[str]:
    out = []
    try:
        lvl = j.safety_level().value
    except Exception:
        lvl = "NORMAL"
    if lvl != "NORMAL":
        out.append(f"Safety is {lvl}: see Controls")
    up = ov.state(j, "update-available")
    if up and isinstance(up[0], Mapping) and int(str(up[0].get("ahead") or 0)) > 0:
        out.append("An update is waiting for your approval (Server > Strategy)")
    return out


def record_archive(j: Journal, raw: Mapping[str, Any], now: datetime) -> dict[str, Any]:
    """The host's info-archive result (``trader-bf server-jobs info-archive``), cleaned:
    known keys and plain values only."""
    from trader.app_store import set_state
    from trader.server_status import clean_line

    rec: dict[str, Any] = {"ok": bool(raw.get("ok"))}
    d = ov._day(raw.get("day"))
    if d is not None:
        rec["day"] = str(d)
    for k in ("rows", "kept", "pdfs", "failed", "asic_new", "asic_files"):
        try:
            rec[k] = int(str(raw.get(k)))
        except (TypeError, ValueError):
            continue
    for k in ("error", "note"):
        if raw.get(k):
            rec[k] = clean_line(str(raw[k]))[:200]
    set_state(j, "info-archive-last", rec, now)
    return rec


def _twin_series(folder: Path, book: str) -> list[list[Any]]:
    """The daily values of the dry run's book in the newest journal of ``folder``."""
    from trader.journal import read_only_engine

    dbs = sorted(folder.glob("dryrun_*.sqlite3"), key=lambda p: p.stat().st_mtime)
    if not dbs:
        return []
    jj = Journal.read_only(read_only_engine(f"sqlite+pysqlite:///{dbs[-1]}"))
    try:
        return [[k.rsplit(":", 1)[1], float(str(r["value"]))]
                for k, r in jj.job_records(f"value:{book}:")]  # fmt: skip
    finally:
        jj.engine.dispose()


def _label(folder: Path) -> str:
    from trader.strategy_version import load_changelog

    f = folder / "strategy_changelog.yaml"
    notes = load_changelog(f.read_text(encoding="utf-8")) if f.is_file() else []
    return str(notes[0]["version"])[:60] if notes else "unversioned"


def record_prev_twin(j: Journal, root: Path, book: str, raw: Mapping[str, Any],
                     now: datetime) -> dict[str, Any]:  # fmt: skip
    """BF-D80: the host's nightly previous-version twin. Both versions replayed on paper
    by the existing dry-run machinery from the same start (``since``) with the same
    prices; their daily values go to app state ``prev-twin``."""
    from trader.app_store import set_state
    from trader.server_status import clean_line

    since = ov._day(raw.get("since"))
    rec: dict[str, Any] = {"ok": bool(raw.get("ok")), "since": str(since) if since else ""}
    if raw.get("error"):
        rec["error"] = clean_line(str(raw["error"]))[:200]
    if rec["ok"]:
        try:
            rec["new"] = _twin_series(root / "new", book)
            rec["prev"] = _twin_series(root / "prev", book)
            rec["new_label"], rec["prev_label"] = _label(root / "new"), _label(root / "prev")
        except Exception as e:  # a broken file is shown, never raised into the worker
            rec.update(ok=False, error=f"could not read the twin runs: {type(e).__name__}")
        if rec.get("new"):
            rec["to"] = rec["new"][-1][0]
            rec["capital"] = 10000
    set_state(j, "prev-twin", rec, now)
    return rec
