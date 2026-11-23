"""The app's honest-scoreboard, research, Health, Costs, Digest, announcements and
previous-version-twin screens (BF-D75..BF-D80). Presentation only and read-only: every
figure comes from ``trader.ops_view`` / ``trader.info_view`` over what the trader, the
host worker and the private info archive already record. The one write (editing the
fixed running costs) goes through the trader's control server (``/act/costs``)."""

from __future__ import annotations

import time as _time
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from trader import info_view as iv
from trader import ops_view as ov
from trader.app_pages import (
    Extras,
    _srow,
    ago,
    aud,
    day,
    menu_row,
    pct,
    safe,
    shell,
    tone,
    when,
)
from trader.app_viz import spark
from trader.constants import ASX_TZ
from trader.webui import backlink, e, icon, plural, section, stat

TWO_GB = 2 * 1024**3


@dataclass
class Ops:
    score: ov.Scoreboard | None = None
    after_series: list[tuple[date, float]] = field(default_factory=list)  # gap over time
    costs: ov.CostReport | None = None
    fixed: ov.FixedCosts | None = None
    research: list[ov.ResearchLine] | None = None
    fresh: list[ov.Fresh] = field(default_factory=list)
    archive: iv.ArchiveStatus = field(default_factory=iv.ArchiveStatus)
    info_enabled: bool = False
    info_dir: Path | None = None
    eodhd: tuple[int, int] | None = None  # calls used today (GMT), the configured budget
    prev_twin: dict[str, Any] | None = None
    tax_note: str = ""
    store_days: list[date] = field(default_factory=list)
    shared: ov.Score | None = None  # the one scoreboard the digest uses too (BF-D81 M4)


_TAX: dict[str, tuple[float, tuple[Decimal | None, str]]] = {}


def _tax_estimate(src: Any, v: Any) -> tuple[Decimal | None, str]:
    """``ov.tax_estimate``, cached 10 minutes (the tax report is not cheap)."""
    if getattr(src, "marginal_rate", None) is None:
        return ov.tax_estimate(src, v.now.astimezone(ASX_TZ).date())
    key = f"{v.book}:{len(v.series)}"
    hit = _TAX.get(key)
    if hit and _time.monotonic() - hit[0] < 600:
        return hit[1]
    res = ov.tax_estimate(src, v.now.astimezone(ASX_TZ).date())
    _TAX.clear()
    _TAX[key] = (_time.monotonic(), res)
    return res


def shared_score(src: Any, v: Any) -> ov.Score:
    """The scoreboard of Home, Costs and the digest (``ov.build_score``)."""
    j = src.journal
    fc = ov.fixed_costs(j, getattr(src, "fixed_items", None),
                        Decimal(str(getattr(src, "fixed_total", 600))))  # fmt: skip
    no_tax: tuple[Decimal | None, str] = (None, "Tax: not available.")
    tax = safe(lambda: _tax_estimate(src, v), no_tax)
    return ov.build_score(j, src.book, v.series, v.index, fc, getattr(src, "commission", None),
                          Decimal(str(getattr(src, "fund_half_spread", "0.0005"))), tax)  # fmt: skip


def collect(src: Any, v: Any, journal_ok: bool) -> Ops:
    """Everything these screens need, each part failing soft."""
    j = src.journal
    o = Ops()
    o.info_enabled = bool(getattr(src, "info_enabled", False))
    o.info_dir = getattr(src, "info_dir", None)
    today = v.now.astimezone(ASX_TZ).date()
    sess = list(src.sessions()) if src.sessions else []
    o.fixed = ov.fixed_costs(j if journal_ok else None, getattr(src, "fixed_items", None),
                             Decimal(str(getattr(src, "fixed_total", 600))))  # fmt: skip
    o.research = safe(lambda: ov.research_lines(getattr(src, "scorecard", None), today), None)
    o.archive = safe(lambda: iv.status(o.info_dir, sess, today, v.now), iv.ArchiveStatus())
    if src.store_root is not None:
        files: list[Path] = safe(
            lambda: list((src.store_root / "raw" / "bulk_eod").glob("AU_*.json.gz")), []
        )
        o.store_days = sorted(d for d in (_bulk_day(p.name) for p in files) if d is not None)
    if not journal_ok:
        return o
    o.fresh = safe(lambda: ov.freshness(j, src.book, sess, v.now, o.info_enabled), [])
    sc = safe(lambda: shared_score(src, v), None)
    if sc is not None:
        o.shared, o.score, o.after_series, o.fixed, o.tax_note = (
            sc, sc.board, sc.gap_series, sc.fixed, sc.tax_note)  # fmt: skip
    o.costs = safe(lambda: ov.cost_report(j.fills(src.book), v.series, today, o.fixed,  # type: ignore[arg-type]
                                          Decimal(str(getattr(src, "half_spread", "0.005")))),
                   None)  # fmt: skip
    from trader.store_refresh import BUDGET_PREFIX

    gmt = v.now.astimezone(UTC).date()
    used = safe(lambda: sum(int(r.get("cost", 1)) for _, r, _ in
                            ov.job_rows(j, f"{BUDGET_PREFIX}{gmt}:")), None)  # fmt: skip
    if used is not None:
        o.eodhd = (used, int(getattr(src, "eodhd_budget", 100000)))
    pt = ov.state(j, "prev-twin")
    o.prev_twin = dict(pt[0]) if pt and isinstance(pt[0], dict) else None
    return o


def _bulk_day(name: str) -> date | None:
    try:
        return date.fromisoformat(name[3:13])
    except ValueError:
        return None


# ---------------------------------------------------------------- Home: the scoreboard


def score_card(o: Ops, v: Any) -> str:
    """The Home headline (BF-D75): the main line after costs against A200. Without a
    tax rate it says "after running costs, before tax" (BF-D81, review M2)."""
    s = o.score
    if s is None:
        return ""
    g = s.gap
    t = tone(g) if g is not None else ""
    head = (f'<p class="verdict {t}">{icon("arrow-up-right" if (g or 0) > 0 else "arrow-down-right")}'
            f"{e(s.sentence)}</p>") if g is not None else f'<p class="verdict">{e(s.sentence)}</p>'  # fmt: skip
    mine = "Big Wins, " + s.basis
    stats = (
        '<dl class="stats two">'
        + stat(mine[:1].upper() + mine[1:], aud(s.after_costs, dp=0),
               pct(s.mine_pct) + " on money put in", tone(s.mine_pct))
        + stat("Same money in A200", aud(s.a200, dp=0) if s.a200 is not None else "–",
               (pct(s.a200_pct) + " on money put in") if s.a200 is not None
               else "no fund prices yet", tone(s.a200_pct))
        + "</dl>"
    )  # fmt: skip
    gap = ""
    if len(o.after_series) > 1:
        gap = ('<div class="gaprow"><span class="caption">Gap over time</span>'
               + spark([x for _, x in o.after_series], 160, 28, "spk",
                       "Big Wins after running costs minus A200, over time", stretch=True)
               + "</div>")  # fmt: skip
    fc = o.fixed
    fixed_lab = {"app": "set in the app", "config": "from the server settings",
                 "total": "one yearly total"}.get(fc.source if fc else "", "")  # fmt: skip
    if fc is not None and fc.since is not None and fc.source == "app":
        fixed_lab += f" from {fc.since:%d %b %Y}"
    flows = [f for f in s.flows if f[0] > s.start or f[1] < 0]
    flow_row = (f"<tr><td>Later deposits and withdrawals <span class='sub'>each one goes "
                f"into or out of A200 on its own day</span></td><td class='r'>"
                f"{plural(len(flows), 'move')}</td></tr>" if flows else "")  # fmt: skip
    rows = (
        f"<tr><td>Account value <span class='sub'>brokerage and the spread are already in it"
        f"</span></td><td class='r'>{aud(s.value)}</td></tr>"
        f"<tr><td>Fixed running costs since {s.start:%d %b} <span class='sub'>"
        f"{aud(fc.per_year if fc else 0, dp=0)} a year, {e(fixed_lab)}</span></td>"
        f"<td class='r'>{aud(-s.fixed)}</td></tr>"
        + (f"<tr><td>Estimated tax on realised gains</td><td class='r'>{aud(-s.tax)}</td></tr>"
           if s.tax is not None else
           "<tr><td>Tax <span class='sub'>not included: your tax rate is not set</span></td>"
           "<td class='r'>–</td></tr>")
        + f"<tr><td><b>{e(s.basis[:1].upper() + s.basis[1:])}</b></td><td class='r'><b>"
        f"{aud(s.after_costs)}</b></td></tr>"
        + (f"<tr><td>A200: {aud(s.capital, dp=0)} put in, less its buys "
           f"({aud(s.a200_cost)}), held with dividends</td><td class='r'>{aud(s.a200)}</td></tr>"
           if s.a200 is not None else "")
        + flow_row
    )  # fmt: skip
    detail = (
        '<details class="about"><summary>What is counted</summary>'
        f"<table><tbody>{rows}</tbody></table>"
        f"<p class='caption'>{e(o.tax_note)} The fund also pays tax on its distributions; "
        "both sides are before your personal tax on dividends.</p>"
        f"<p class='caption'>{e(ov.EXIT_NOTE)}</p>"
        f"<p class='caption'>{e(ov.BACKTEST_NOTE)}</p>"
        '<p class="caption"><a href="/costs" data-nav aria-label="Running costs in detail">'
        "Running costs in detail</a></p></details>"
    )  # fmt: skip
    return section("Scoreboard · " + s.basis, head + stats + gap + detail, "scorecard")


def fresh_note(o: Ops) -> str:
    bad = [f for f in o.fresh if f.bad]
    if not bad:
        return ""
    items = "; ".join(f"{f.name} {f.status}" for f in bad[:3])
    return (f'<a class="note bad notelink" href="/health" data-nav>{icon("alert-triangle")}'
            f"<span>{e(items)}. Tap for Health.</span></a>")  # fmt: skip


def fresh_row(o: Ops) -> str:
    if not o.fresh:
        return ""
    bad = [f for f in o.fresh if f.bad]
    val = "All on time" if not bad else f"{plural(len(bad), 'job')} late or failed"
    return _srow("Jobs", e(val), href="/health", tone="bad" if bad else "ok")


def research_section(o: Ops, today: date, compact: bool = False) -> str:
    """Research (information only): the kept paper lines, unranked, each labelled."""
    lines = o.research
    intro = ("<p class='caption'>Other paper strategies, tracked for research only. Listed in the "
             "registered order, not ranked: over a few months any difference is "
             f"<b>{e(ov.LUCK)}</b>. Their figures are before fixed costs.</p>")  # fmt: skip
    if lines is None:
        body = ("<p class='muted'>Not collected yet: the research record moves to this server "
                "after 30 Nov.</p>")  # fmt: skip
    else:
        items = []
        for ln in lines:
            if ln.ret is None:
                right = '<span class="sub">not started</span>'
            else:
                right = (f'<span class="rv">{pct(ln.ret)}</span><span class="sub">'
                         f"{pct(ln.vs_a200)} v A200</span>")  # fmt: skip
            cap = f"{aud(ln.capital, dp=0)} book" if ln.capital else ""
            st = f"from {day(ln.start)}" if ln.start else ""
            meta = " · ".join(x for x in (ln.id, cap, st) if x)
            items.append(
                f'<li class="rline"><span class="grow"><b>{e(ln.name)}</b>'
                f'<span class="sub">{e(meta)}</span><span class="sub">{e(ov.LUCK)}</span></span>'
                f'<span class="rr">{right}</span></li>'
            )
        body = f'<ul class="list">{"".join(items)}</ul>'
        asof = next((ln.asof for ln in lines if ln.asof), "")
        if asof:
            body += f"<p class='caption'>From the research record, {e(day(asof))}.</p>"
    if ov.retired_shown(today):
        body += (f"<p class='caption'>Retired 31 Dec 2026: {e(', '.join(ov.RETIRED_LINES))} "
                 "(history kept in the record).</p>")  # fmt: skip
    if compact:
        return ('<details class="about rsec"><summary>Research lines (information only)</summary>'
                + intro + body + "</details>")  # fmt: skip
    return section("Research (information only)", intro + body)


# ---------------------------------------------------------------- Health (BF-D77)

STATUS_PILL = {"ok": ("ok", "on time"), "late": ("bad", "late"), "failed": ("bad", "failed"),
               "off": ("", "off"), "new": ("", "not yet")}  # fmt: skip
TIMER_WORDS = {"worker": "server worker", "backup": "nightly backup", "weekly": "weekly checks",
               "info": "announcements archive", "twin": "previous-version twin"}  # fmt: skip


def health(v: Any, x: Extras, o: Ops, version: str) -> str:
    parts = [backlink("/server", "Server") + "<h1>Health</h1>"]
    bad = [f for f in o.fresh if f.bad]
    parts.append(
        f'<p class="statusline"><span class="sd {"bad" if bad else "ok"}"></span>'
        + (f"{plural(len(bad), 'job')} late or failed" if bad else "Every job on time")
        + "</p>"
    )
    rows = (
        "".join(
            f'<li class="frow"><span class="grow"><b>{e(f.name)}</b><span class="sub">'
            f"{e(f.cadence)} · last {e(f.last)}</span>"
            + (
                f'<span class="sub warn">{e(f.detail)}</span>'
                if f.detail and f.status != "ok"
                else ""
            )
            + f'</span><span class="pill {STATUS_PILL[f.status][0]}">{STATUS_PILL[f.status][1]}</span></li>'
            for f in o.fresh
        )
        or "<li class='muted'>No journal yet.</li>"
    )
    parts.append(section("Scheduled jobs", f'<ul class="list">{rows}</ul><p class="caption">A late '
                         "or failed job sends one alert to your phone per incident.</p>"))  # fmt: skip
    # disk
    disk = ""
    if v.disk_free:
        free, total = v.disk_free
        low = free < TWO_GB
        used = 1 - free / total if total else 0
        disk = (f"<p><b class='num'>{free / 1024**3:.1f} GB</b> free of {total / 1024**3:.0f} GB"
                + (' <span class="pill bad">under 2 GB</span>' if low else "") + "</p>"
                f"<div class='meter{' crit' if low else ''}'><b style='width:{used * 100:.0f}%'></b></div>"
                + ("<p class='note bad'>Less than 2 GB free: ask Claude on the server to clean "
                   "old Docker images and logs.</p>" if low else ""))  # fmt: skip
    else:
        disk = "<p class='muted'>Not known.</p>"
    parts.append(section("Disk", disk))
    # backups
    b, rt = x.backup, x.restore_test
    parts.append(section("Backups", (
        "<ul class='list'>"
        + f"<li>Last backup: <b>{when(b[1]) if b else 'none yet'}</b>"
        + (f" <span class='pill {'ok' if b[0].get('ok') else 'bad'}'>{'OK' if b[0].get('ok') else 'FAILED'}</span>" if b else "")
        + "</li>"
        + f"<li>Last restore test: <b>{when(rt[1]) if rt else 'none yet'}</b>"
        + (f" <span class='pill {'ok' if rt[0].get('ok') else 'bad'}'>{'passed' if rt[0].get('ok') else 'FAILED'}</span>" if rt else "")
        + "</li></ul>" + '<p class="caption"><a href="/backups" data-nav>Backups</a></p>')))  # fmt: skip
    # prices
    used = (f"<li>EODHD calls used today: <b>{o.eodhd[0]:,}</b> of the app's own limit "
            f"{o.eodhd[1]:,} <span class='sub'>(the vendor's credit balance is not read)</span></li>"
            if o.eodhd else "")  # fmt: skip
    parts.append(section("Price data", (
        "<ul class='list'>"
        f"<li>Last price day in the store: <b>{v.store_day:%a %d %b %Y}</b></li>" if v.store_day
        else "<ul class='list'><li>Last price day: <b>none yet</b></li>")
        + (f"<li>Last download: <b>{when(v.store_refreshed_at)}</b></li>" if v.store_refreshed_at else "")
        + used + "</ul>"))  # fmt: skip
    # info archive
    a = o.archive
    if not o.info_enabled and not a.days:
        arch = ("<p class='muted'>Switched off. It is switched on after the research record moves "
                "to this server (after 30 Nov); then it collects each trading day's announcements "
                "the next morning.</p>")  # fmt: skip
    elif not a.days:
        arch = "<p class='muted'>Not collected yet: the first day arrives the morning after a trading day.</p>"
    else:
        missed = (f"<li class='warn'>Missed trading days: {e(', '.join(f'{d:%d %b}' for d in a.missed[-8:]))}"
                  + (f" and {len(a.missed) - 8} more" if len(a.missed) > 8 else "")
                  + "<div class='sub'>These cannot be collected later: the ASX page shows only "
                  "the previous trading day.</div></li>"
                  if a.missed else "<li>No trading day missed</li>")  # fmt: skip
        arch = (f"<ul class='list'><li>Last day stored: <b>{a.last:%a %d %b %Y}</b> "
                f"<span class='sub'>{plural(len(a.days), 'day')} in the archive</span></li>{missed}"
                f"<li>ASIC short positions: <b>{a.short_day:%d %b %Y}</b>" if a.short_day
                else f"<ul class='list'><li>Last day stored: <b>{a.last:%a %d %b %Y}</b></li>{missed}"
                "<li>ASIC short positions: <b>not collected yet</b>")  # fmt: skip
        arch += "</li></ul>"
    parts.append(section("Info archive", arch + "<p class='caption'>Private, for your own use only: "
                         "never shared. Information only: it feeds no strategy.</p>"))  # fmt: skip
    host = x.host[0] if x.host else {}
    tm = host.get("timers")
    if isinstance(tm, dict) and not all(tm.values()):
        gone = ", ".join(TIMER_WORDS.get(str(k), str(k)) for k, ok in tm.items() if not ok)
        parts.insert(2, f"<p class='note bad'>Timer not installed: {e(gone)}. The server worker "
                     "installs it within a minute; if this stays, run on the server: "
                     "<code>sudo bigwins install-worker</code>.</p>")  # fmt: skip
    # dead-man switch
    hb = x.heartbeat
    dm = host.get("daily_ping")
    parts.append(section("Outside alarm (healthchecks.io)", (
        "<ul class='list'>"
        + (f"<li>Heartbeat every 5 minutes: <span class='pill {'ok' if hb[0].get('ok') else 'bad'}'>"
           f"{'OK' if hb[0].get('ok') else 'FAILED'}</span> {ago(hb[1], v.now)}</li>" if hb
           else "<li>Heartbeat: <b>no ping yet</b> (off until set up)</li>")
        + ("<li>Daily-cycle check: <b>set up</b>"
           + (f" · last ping for {e(day(dm))}" if isinstance(dm, str) and dm[:2] == "20" else "")
           + "</li>" if host.get("daily_ping_set")
           else "<li>Daily-cycle check: <b>not set up</b> <span class='sub'>(optional, see the "
           "guide, part C5)</span></li>")
        + "</ul><p class='caption'>If the server goes silent, healthchecks.io tells your phone; "
          "the app cannot, because it runs on the same server.</p>")))  # fmt: skip
    # versions
    run = x.running
    parts.append(section("Versions", (
        "<table><tbody>"
        f"<tr><td class='sub'>App</td><td class='r'>{e(version)}</td></tr>"
        f"<tr><td class='sub'>Server code</td><td class='r mono'>{e(host.get('code_version', '–'))}</td></tr>"
        f"<tr><td class='sub'>Strategy</td><td class='r'>{e(run.get('version', '–'))}</td></tr>"
        f"<tr><td class='sub'>Strategy id</td><td class='r mono'>{e(run.get('id', '–'))}</td></tr>"
        "</tbody></table>")))  # fmt: skip
    return shell(v, x, "Health", "".join(parts), "server")


# ---------------------------------------------------------------- Costs (BF-D76)


def costs(v: Any, x: Extras, o: Ops) -> str:
    parts = [backlink("/server", "Server") + "<h1>Running costs</h1>"]
    c = o.costs
    fc = o.fixed
    if c is None or fc is None:
        parts.append(
            section("Costs", "<p class='muted'>No costs yet: the book has not started.</p>")
        )
        return shell(v, x, "Costs", "".join(parts), "server")
    tone_ = (
        "bad" if (c.annual_pct or 0) >= 0.05 else ("amber" if (c.annual_pct or 0) >= 0.02 else "ok")
    )
    parts.append(f'<p class="verdict2"><span class="pill {tone_}">{e(c.verdict.split(":")[0])}</span> '
                 f"{e(c.verdict.split(':', 1)[1].strip() if ':' in c.verdict else c.verdict)}</p>")  # fmt: skip

    def table(r: ov.CostRow) -> str:
        lines = [("Brokerage and fees", r.brokerage, "from the fills"),
                 ("Spread (modelled)", r.spread, f"{c.half_spread * 100:.1f}% of each trade")]  # fmt: skip
        for k, lab, _ in fc.items:
            lines.append((lab, r.fixed_items.get(k, Decimal(0)), "fixed, pro rata"))
        body = "".join(
            f"<tr><td>{e(lab)}<div class='sub'>{e(sub)}</div></td><td class='r'>{aud(amt)}</td>"
            f"<td class='r sub'>{pct(r.share(amt), False)}</td></tr>"
            for lab, amt, sub in lines
        )
        return ("<table><thead><tr><th>Cost</th><th class='r'>$</th><th class='r'>% of account"
                f"</th></tr></thead><tbody>{body}<tr class='tot'><td><b>Total</b></td><td class='r'>"
                f"<b>{aud(r.total)}</b></td><td class='r'><b>{pct(r.share(r.total), False)}</b></td>"
                f"</tr></tbody></table><p class='caption'>{r.start:%d %b %Y} – {r.end:%d %b %Y}; "
                f"account {aud(r.account, dp=0)} at the end.</p>")  # fmt: skip

    parts.append(section("This financial year (from 1 July)", table(c.ytd)))
    parts.append(section("Since the start", table(c.since_start)))
    months = "".join(
        f"<tr><td>{e(r.label)}</td><td class='r'>{aud(r.brokerage + r.spread)}</td>"
        f"<td class='r'>{aud(r.fixed)}</td><td class='r'><b>{aud(r.total)}</b></td>"
        f"<td class='r sub'>{pct(r.share(r.total), False)}</td></tr>"
        for r in c.months
    )
    parts.append(section("By month", "<table><thead><tr><th>Month</th><th class='r'>Trading</th>"
                         "<th class='r'>Fixed</th><th class='r'>Total</th><th class='r'>%</th></tr>"
                         f"</thead><tbody>{months}</tbody></table>"))  # fmt: skip
    src = {"app": "set in this app", "config": "from the server settings (running_costs)",
           "total": "one yearly total from the server settings (costs.fixed_aud_per_year)"}[fc.source]  # fmt: skip
    fixed_rows = "".join(
        f"<li>{e(lab)}: <b>{aud(amt, dp=0)}</b> a year</li>" for _, lab, amt in fc.items
    )
    parts.append(section("Fixed costs a year", (
        f'<ul class="list">{fixed_rows}</ul><p class="caption">{e(src)}. The scoreboard on Home '
        "takes these off the account value.</p>"
        '<a class="btn sec wide" href="/act/costs">Edit the amounts</a>')))  # fmt: skip
    return shell(v, x, "Costs", "".join(parts), "server")


# ---------------------------------------------------------------- the weekly digest (BF-D79)


def digest_for(src: Any, v: Any, o: Ops, friday: date, x: Extras) -> ov.Digest:
    """The same digest as the Friday inbox message (``ops_hooks.build_digest``)."""
    from trader.ops_hooks import build_digest

    sc = o.shared or shared_score(src, v)
    sess = list(src.sessions()) if src.sessions else []
    return build_digest(src.journal, src.book, friday, v.now, sc, v.series, v.index, sess,
                        o.info_enabled, getattr(src, "scorecard", None), o.info_dir,
                        o.store_days, getattr(src, "approval_deadline", "15:20"))  # fmt: skip


def last_friday(today: date) -> date:
    return today - timedelta(days=(today.weekday() - 4) % 7)


def digest_page(src: Any, v: Any, x: Extras, o: Ops, qs: dict[str, str]) -> str:
    today = v.now.astimezone(ASX_TZ).date()
    try:
        fri = last_friday(date.fromisoformat(qs.get("w", "")[:10]))
    except ValueError:
        fri = last_friday(today)
    dg = digest_for(src, v, o, fri, x)
    prev = fri - timedelta(days=7)
    nav = (f'<div class="seg sm"><a href="/digest?w={prev}" data-nav>{icon("chevron-left")} Week before</a>'
           + (f'<a href="/digest?w={fri + timedelta(days=7)}" data-nav>Next week {icon("chevron-right")}</a>'
              if fri + timedelta(days=7) <= today else "") + "</div>")  # fmt: skip

    def block(title: str, lines: Sequence[str], empty: str = "") -> str:
        if not lines and not empty:
            return ""
        items = "".join(f"<li>{e(t)}</li>" for t in lines) or f"<li class='muted'>{e(empty)}</li>"
        return section(title, f'<ul class="list">{items}</ul>')

    s = o.score
    head = ""
    if s is not None and s.gap is not None:
        head = f'<p class="verdict {tone(s.gap)}">{e(s.sentence)}</p>'
    body = (
        backlink("/inbox", "Inbox")
        + f"<h1>Weekly digest</h1><p class='caption'>{dg.week_start:%a %d %b} – {dg.week_end:%a %d %b %Y}</p>"
        + nav + head
        + block("Main strategy against A200", dg.main)
        + section("Research lines (information only, unranked)",
                  "<p class='caption'>Each " + e(ov.LUCK) + ".</p><ul class='list'>"
                  + "".join(f"<li>{e(t)}</li>" for t in dg.research) + "</ul>")
        + block("Data collected", dg.data)
        + block("Alerts this week", dg.alerts, "No alerts.")
        + block("Needs you", dg.needs, "Nothing needs you.")
    )  # fmt: skip
    return shell(v, x, "Digest", body, "inbox")


# ---------------------------------------------------------------- announcements on a share (BF-D78)

FLAG_PILL = {"raise": "amber", "halt": "bad", "takeover": "amber", "director": ""}


def announcements(info_dir: Path | None, code: str, today: date) -> str:
    """The last 90 days of headlines, director trades and the short position."""
    if info_dir is None:
        return section("Announcements", f"<p class='muted'>{iv.NOT_COLLECTED}: the private "
                       "announcements archive is not on this server yet.</p>")  # fmt: skip
    ns = iv.notices(info_dir, code, today)
    sp = iv.short_position(info_dir, code)
    parts = []
    if ns is None:
        parts.append(f"<p class='muted'>{iv.NOT_COLLECTED}: the archive starts collecting after "
                     "the research record moves to this server.</p>")  # fmt: skip
    elif not ns:
        parts.append("<p class='muted'>No announcements in the last 90 days.</p>")
    else:
        flagged = {f: sum(1 for n in ns if f in n.flags) for f in ("raise", "halt", "takeover")}
        chips = "".join(f'<span class="pill {FLAG_PILL[f]}">{e(lab)} · {flagged[f]}</span>'
                        for f, lab in iv.FLAG_WORDS if flagged.get(f))  # fmt: skip
        if chips:
            parts.append(f'<div class="pills">{chips}</div>')
        items = []
        for n in ns[:60]:
            fl = "".join(f'<span class="pill {FLAG_PILL[f]}">{e(dict(iv.FLAG_WORDS)[f])}</span>'
                         for f in n.flags if f != "director")  # fmt: skip
            ps = ' <span class="pill nodot">price sensitive</span>' if n.price_sensitive else ""
            items.append(f'<li class="ann"><span class="sub">{n.day:%d %b} · {e(n.time)}</span>'
                         f"<div>{e(n.headline)}</div>"
                         + (f'<div class="pills">{fl}{ps}</div>' if fl or ps else "") + "</li>")  # fmt: skip
        parts.append(f'<ul class="list">{"".join(items)}</ul>')
        if len(ns) > 60:
            parts.append(f"<p class='caption'>{len(ns) - 60} older not shown.</p>")
        trades = [n for n in ns if n.trade is not None]
        if trades:
            rows = "".join(_trade_row(n) for n in trades[:20])
            parts.append('<h3 class="h3">Director trades</h3>'
                         f"<table><tbody>{rows}</tbody></table>"
                         "<p class='caption'>Read from the notices by a cautious rule: only an "
                         "on-market purchase or sale counts; option, right and plan issues are "
                         "not buys; anything else says unclear.</p>")  # fmt: skip
    if sp is None:
        sp_html = (f"<p class='muted small'>Short position: {iv.NOT_COLLECTED.lower()}.</p>"
                   if info_dir is not None else "")  # fmt: skip
    else:
        chg = (f" <span class='sub'>({sp.before_pct:.2f}% on {sp.before_day:%d %b})</span>"
               if sp.before_pct is not None and sp.before_day else "")  # fmt: skip
        sp_html = (f"<p>Short position: <b>{sp.pct:.2f}%</b> of the shares on {sp.day:%d %b %Y}"
                   f"{chg}</p><p class='caption'>ASIC's daily report, a few trading days behind.</p>")  # fmt: skip
    return section("Announcements · last 90 days", "".join(parts) + sp_html
                   + "<p class='caption'>Information only: it feeds no strategy. Private, "
                   "for your own use.</p>")  # fmt: skip


def _trade_row(n: iv.Notice) -> str:
    t = n.trade
    assert t is not None
    word = {"buy": "On-market buy", "sell": "On-market sell", "not a buy": "Not a buy",
            "unclear": "Unclear"}[t.kind]  # fmt: skip
    cls = {"buy": "ok", "sell": "bad", "not a buy": "", "unclear": "amber"}[t.kind]
    num = f"{t.number:,}" if t.number else ""
    val = (
        aud(t.value, dp=0)
        if t.value is not None
        else ("value unclear" if t.kind in ("buy", "sell") else "")
    )
    return (f"<tr><td><span class='pill {cls}'>{e(word)}</span><div class='sub'>{n.day:%d %b} · "
            f"{e(t.why)}</div></td><td class='r'>{e(num)}<div class='sub'>{e(val)}</div></td></tr>")  # fmt: skip


# ---------------------------------------------------------------- previous-version twin (BF-D80)


def prev_twin_section(pt: dict[str, Any] | None) -> str:
    if not pt or not pt.get("since"):
        return section("Did the last update help?", (
            "<p class='muted'>Nothing to compare yet. After the next strategy update the server "
            "also runs the previous version on paper (a simulated twin), so this shows whether "
            "the update helped.</p>"))  # fmt: skip
    if not pt.get("ok", True):
        return section("Did the last update help?", f"<p class='note bad'>The twin run failed: "
                       f"{e(str(pt.get('error', ''))[:200])}</p>")  # fmt: skip
    new = [(str(d), float(v)) for d, v in pt.get("new", [])]
    old = [(str(d), float(v)) for d, v in pt.get("prev", [])]
    if not new or not old:
        return section("Did the last update help?", "<p class='muted'>The first night's run is "
                       "still to come.</p>")  # fmt: skip
    cap = float(pt.get("capital") or new[0][1])
    nv, ov_ = new[-1][1], old[-1][1]
    diff = nv - ov_
    if abs(diff) <= 1:
        sentence = "So far the two versions are level."
    else:
        who = "this version" if diff > 0 else "the previous version"
        sentence = (f"So far {who} is ahead by {aud(abs(diff), dp=0)}; over a few weeks that "
                    f"is {ov.LUCK}.")  # fmt: skip
    d = dict(old)
    gaps = [v - d[k] for k, v in new if k in d]
    return section("Did the last update help?", (
        f'<p class="verdict2">{e(sentence)}</p>'
        '<dl class="stats two">'
        + stat(f"This version ({pt.get('new_label', 'new')})", aud(nv, dp=0), pct(nv / cap - 1))
        + stat(f"Previous ({pt.get('prev_label', 'old')})", aud(ov_, dp=0), pct(ov_ / cap - 1))
        + "</dl>"
        + (spark(gaps, 160, 28, "spk", "This version minus the previous one", stretch=True)
           if len(gaps) > 1 else "")
        + f"<p class='caption'>Both simulated (paper twins) with {aud(cap, dp=0)} from "
          f"{e(day(pt['since']))}, the same prices and costs; only the strategy version differs. "
          f"Updated {e(day(pt.get('to', '')))}.</p>"))  # fmt: skip


def server_rows(o: Ops) -> str:
    """Server menu rows for Health, Costs and the digest."""
    bad = [f for f in o.fresh if f.bad]
    return (menu_row("/health", "activity", "Health", "Jobs, disk, backups, data, versions",
                     value=f"{len(bad)} late" if bad else "OK", nav=True)
            + menu_row("/costs", "chart", "Running costs", "Monthly and this year, % of account",
                       nav=True)
            + menu_row("/digest", "calendar", "Weekly digest", "Fridays after the close", nav=True))  # fmt: skip
