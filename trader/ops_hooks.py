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


# incidents the trader already pages itself (the failed report, prices not refreshed, a
# failed backup or restore test, no good backup for 26 hours): only the daily reminder
ALREADY_PAGED = frozenset({("daily", "failed"), ("prices", "late"), ("backup", "failed"),
                           ("backup", "late"), ("restore", "failed")})  # fmt: skip
REMIND_EVERY = timedelta(hours=24)


def series_of(j: Journal, book: str) -> list[tuple[date, Decimal]]:
    out = []
    for k, r, _ in ov.job_rows(j, f"value:{book}:"):
        d = ov._day(k.rsplit(":", 1)[1])
        if d is not None and isinstance(r, Mapping) and r.get("value") is not None:
            out.append((d, Decimal(str(r["value"]))))
    return out


def build_digest(
    j: Journal,
    book: str,
    friday: date,
    now: datetime,
    score: ov.Score,
    series: Sequence[tuple[date, Decimal]],
    index: Sequence[tuple[date, float]],
    sessions: Sequence[date],
    info_enabled: bool,
    scorecard: Path | None,
    info_dir: Path | None,
    store_days: Sequence[date],
    approval_deadline: str = "15:20",
) -> ov.Digest:
    """The week's digest; the inbox message and the app's /digest page both come from
    here, with the same scoreboard (BF-D81, review M4)."""
    today = now.astimezone(ASX_TZ).date()
    fresh = ov.freshness(j, book, sessions, now, info_enabled)
    arch = iv.status(info_dir, sessions, today, now)
    needs = _needs(j, book, now, approval_deadline)
    lines = ov.research_lines(scorecard, today)
    return ov.digest(j, book, friday, score.board, ov.week_change(series, index, friday), lines,
                     fresh, arch.days, sorted(store_days), needs)  # fmt: skip


def store_days_of(store_root: Path | None) -> list[date]:
    out: list[date] = []
    if store_root is not None:
        for p in (store_root / "raw" / "bulk_eod").glob("AU_*.json.gz"):
            d = ov._day(p.name[3:13])
            if d is not None:
                out.append(d)
    return sorted(out)


def last_friday(now: datetime) -> date:
    """The latest Friday whose digest is due (from 22:55 that Friday)."""
    t = now.astimezone(ASX_TZ)
    fri = t.date() - timedelta(days=(t.weekday() - 4) % 7)
    if fri == t.date() and t.time() < DIGEST_AT:
        fri -= timedelta(days=7)
    return fri


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
    commission: Callable[[Decimal], Decimal] | None = None  # A200's buys (the IBKR plan)
    fund_half_spread: Decimal = Decimal("0.0005")
    tax_src: Any = None  # the tax inputs (marginal_rate, tax_params, ...); None = no tax
    approval_deadline: str = "15:20"
    _last: datetime | None = field(default=None, repr=False)

    def tick(self, now: datetime) -> None:
        if self._last is not None and now - self._last < EVERY:
            return
        self._last = now
        for name, fn in (("alarm", self.alerts), ("digest", self.weekly)):
            try:
                fn(now)
            except Exception as e:  # BF-D81 (review S4): the monitor's own failure pages once
                self._monitor_failed(name, e, now)

    def _monitor_failed(self, name: str, e: Exception, now: datetime) -> None:
        from trader.app_store import set_state

        key = f"{name}:{now.astimezone(ASX_TZ).date()}"
        st = ov.state(self.journal, "monitor-failed")
        if st and st[0] == key:
            return
        self.notify(f"PAGE the app's {name} check itself failed ({type(e).__name__}). The "
                    "jobs may still be fine: look at Server > Health and the trader log.",
                    "page", "/health")  # fmt: skip
        set_state(self.journal, "monitor-failed", key, now)

    # ------------------------------------------------------------ missed-job alarm
    def alerts(self, now: datetime) -> list[str]:
        """One push per new incident (none for incidents the trader already pages), then
        a reminder once a day while it lasts."""
        from trader.app_store import set_state

        fresh = ov.freshness(self.journal, self.book, list(self.sessions()), now,
                             self.info_enabled)  # fmt: skip
        st = ov.state(self.journal, "freshness-told")
        raw = st[0] if st else None
        if isinstance(raw, Mapping):
            told: dict[str, str] = dict(raw)
        else:  # the first build kept a plain list
            told = dict.fromkeys(map(str, raw or []), now.isoformat())
        sent = []
        for f in fresh:
            if not f.bad or not f.incident:
                continue
            prev = told.get(f.incident)
            what = "FAILED" if f.status == "failed" else "is late"
            if prev is None:
                told[f.incident] = now.isoformat()
                if (f.key, f.status) in ALREADY_PAGED:
                    continue  # the trader's own page said it; the reminder follows tomorrow
                text = (f"PAGE {f.name} {what}: {f.detail or 'last ' + f.last}. "
                        "See Server > Health.")  # fmt: skip
            elif now - datetime.fromisoformat(prev) >= REMIND_EVERY:
                told[f.incident] = now.isoformat()
                still = "failed" if f.status == "failed" else "late"
                text = (f"PAGE reminder: {f.name} still {still} "
                        f"({f.detail or 'last ' + f.last}). See Server > Health.")  # fmt: skip
            else:
                continue
            self.notify(text, "page", "/health")
            sent.append(f.incident)
        live = {f.incident for f in fresh if f.bad and f.incident}
        keep = {k: v for k, v in told.items() if k in live}
        if sent or keep != told or not isinstance(raw, Mapping):
            set_state(self.journal, "freshness-told", keep, now)
        return sent

    # ------------------------------------------------------------ the weekly digest
    def weekly(self, now: datetime) -> bool:
        """Fridays from 22:55; a digest missed while the trader was down is sent late."""
        from trader.app_store import set_state

        fri = last_friday(now)
        st = ov.state(self.journal, "digest-last")
        if st and str(st[0]) >= str(fri):
            return False
        dg = self.build(fri, now)
        late = "" if now.astimezone(ASX_TZ).date() == fri else " (sent late)"
        text = dg.text().replace("\n", f"{late}\n", 1) if late else dg.text()
        self.notify(text, "info", f"/digest?w={fri}")
        set_state(self.journal, "digest-last", str(fri), now)
        return True

    def score(self, series: Sequence[tuple[date, Decimal]],
              idx: Sequence[tuple[date, float]], today: date) -> ov.Score:  # fmt: skip
        j = self.journal
        fc = ov.fixed_costs(j, self.fixed_items, self.fixed_per_year)
        tax = ov.tax_estimate(self.tax_src, today) if self.tax_src is not None else (
            None, "Tax: not included (your tax rate is not set on the server).")  # fmt: skip
        return ov.build_score(j, self.book, series, idx, fc, self.commission,
                              self.fund_half_spread, tax)  # fmt: skip

    def build(self, friday: date, now: datetime) -> ov.Digest:
        j = self.journal
        series = series_of(j, self.book)
        idx: list[tuple[date, float]] = []
        if self.index is not None:
            try:
                idx = list(self.index())
            except Exception:
                idx = []
        if series:
            idx = [(d, x) for d, x in idx if series[0][0] <= d <= series[-1][0] and x > 0]
        today = now.astimezone(ASX_TZ).date()
        return build_digest(j, self.book, friday, now, self.score(series, idx, today), series,
                            idx, list(self.sessions()), self.info_enabled, self.scorecard,
                            self.info_dir, store_days_of(self.store_root),
                            self.approval_deadline)  # fmt: skip


def _needs(j: Journal, book: str, now: datetime | None = None,
           approval_deadline: str = "15:20") -> list[str]:  # fmt: skip
    out = []
    if now is not None:
        from trader.app_pages import waiting_batches

        try:
            n = sum(w.n for w in waiting_batches(j, book, now, approval_deadline))
        except Exception:
            n = 0
        if n:
            out.append(f"{ov.plural(n, 'order')} waiting for your approval")
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
