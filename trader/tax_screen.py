"""The app's Tax screen and its EOFY CSV (BF-D44). Estimate for your records - not tax
advice. Paper account: no real tax.

Australian individual investor, financial year 1 July - 30 June, from the journal's real
fills, brokerage, corporate actions and code changes through the BF-D29 tax engine
(``trader.tax_report``; read-only): realised gains and losses parcel by parcel (cost base
incl. buy brokerage, proceeds net of sell brokerage, trade-date CGT events), the 50%
discount on parcels sold later than 12 months after purchase (``tax.discount_rule``),
losses applied to non-discount gains first, then discount-eligible gains, then the
discount; carry-forward; dividends with franking where known (else a clear gap);
unrealised gains of the holdings and when each parcel becomes discount eligible; an
estimate at ``tax.marginal_rate`` if set (server only); 30-day re-buy flags (TR 2008/1,
information only) and the engine's own flags. The CSV is a GET download (read-only).
"""

from __future__ import annotations

import csv
import io
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, date, timedelta
from decimal import Decimal
from typing import Any

from trader.app_pages import Extras, aud, safe, shell, tone
from trader.constants import ASX_TZ
from trader.journal import FillRecord
from trader.orders import Side
from trader.tax_report import (
    NOT_ADVICE,
    TaxParams,
    TaxReport,
    build_report,
    fy_label,
    fy_of,
    run_engine,
)
from trader.webui import e, section, tile

LABEL = "Estimate for your records — not tax advice. Paper account: no real tax."
CSV_COLUMNS = ("section", "code", "qty", "acquired", "disposed", "cost_base", "proceeds",
               "gain", "discount_eligible", "discount_applied", "method", "note")  # fmt: skip
WASH_DAYS = 30


def _params(src: Any) -> TaxParams:
    p = getattr(src, "tax_params", None)
    return p if isinstance(p, TaxParams) else TaxParams(discount_rule="12_months")


def years(src: Any, today: date) -> list[int]:
    fills: list[FillRecord] = safe(lambda: src.journal.fills(src.book), [])
    first = min((fy_of(f.executed_at.astimezone(ASX_TZ).date()) for f in fills),
                default=fy_of(today))  # fmt: skip
    return list(range(fy_of(today), first - 1, -1))


def _fy(qs: Mapping[str, str], ys: list[int]) -> int:
    want = qs.get("fy", "")
    for y in ys:
        if fy_label(y) == want:
            return y
    return ys[0]


@dataclass(frozen=True)
class Unrealised:
    code: str
    qty: Decimal
    acquired: date
    cost: Decimal
    value: Decimal | None
    eligible_from: date


def unrealised(src: Any, marks: Mapping[str, Decimal], today: date) -> list[Unrealised]:
    p = _params(src)
    eng = run_engine(src.journal, src.book, p, today)
    out = []
    for par in eng.parcels:
        if par.qty <= 0:
            continue
        m = marks.get(par.code)
        out.append(Unrealised(par.code, par.qty, par.acquired, par.cost,
                              None if m is None else (m * par.qty).quantize(Decimal("0.01")),
                              p.eligible_from(par.acquired)))  # fmt: skip
    return sorted(out, key=lambda u: (u.code, u.acquired))


def rebuy_flags(src: Any, start: date, end: date) -> list[str]:
    """A sale followed by a buy of the same code within 30 days (information only)."""
    allf: list[FillRecord] = safe(lambda: src.journal.fills(src.book), [])
    fills = sorted(allf, key=lambda f: f.executed_at if f.executed_at.tzinfo
                   else f.executed_at.replace(tzinfo=UTC))  # fmt: skip
    out = []
    for s in fills:
        if s.side is not Side.SELL:
            continue
        sd = s.executed_at.astimezone(ASX_TZ).date()
        if not start <= sd <= end:
            continue
        for b in fills:
            bd = b.executed_at.astimezone(ASX_TZ).date()
            if (
                b.side is Side.BUY
                and b.entity == s.entity
                and sd <= bd <= sd + timedelta(WASH_DAYS)
            ):
                out.append(f"{s.entity}: sold {sd:%d %b %Y}, bought again {bd:%d %b %Y} "
                           f"({(bd - sd).days} days later)")  # fmt: skip
                break
    return out


def report(src: Any, y: int) -> TaxReport:
    return build_report(src.journal, src.book, fy_label(y), _params(src), paper=True)


def screen(v: Any, x: Extras, src: Any, qs: Mapping[str, str]) -> str:
    today = v.now.astimezone(ASX_TZ).date()
    seg = ('<div class="seg"><a href="/holdings" data-nav>Holdings</a>'
           '<a class="on" href="/tax" data-nav>Tax</a></div>')  # fmt: skip
    ys = years(src, today)
    y = _fy(qs, ys)
    picker = "".join(
        f'<a class="chip{" on" if yy == y else ""}" href="/tax?fy={fy_label(yy)}" data-nav>'
        f"FY {fy_label(yy)}</a>"
        for yy in ys
    )
    r = safe(lambda: report(src, y), None)
    p = _params(src)
    head = (seg + f'<p class="note">{e(LABEL)}</p><div class="seg">{picker}</div>'
            f"<p class='small muted'>1 Jul {y} – 30 Jun {y + 1} · parcels matched "
            f"<b>{e(p.method)}</b> · discount: {e(p.rule_text())}</p>")  # fmt: skip
    if r is None:
        return shell(
            v,
            x,
            "Tax",
            head + section("Tax", "<p class='muted'>No trades recorded yet.</p>"),
            "holdings",
        )
    s = r.summary
    t = r.totals()
    divs = t["dividends"] or Decimal(0)
    specials = t["specials"] or Decimal(0)
    credits = t["franking_credits"] or Decimal(0)
    rate = getattr(src, "marginal_rate", None)
    tiles = (
        tile("Net capital gain", aud(s.net_gain), "after losses and discount", tone(s.net_gain))
        + tile("Losses carried forward", aud(s.carried_out), f"carried in {aud(s.carried_in)}")
        + tile("Dividends", aud(divs + specials), f"franking credits {aud(credits)}")
        + tile("Brokerage", aud((t["brokerage_buys"] or 0) + (t["brokerage_sells"] or 0)),
               "in cost bases and proceeds")
    )  # fmt: skip
    if rate is not None:
        taxable = s.net_gain + divs + specials + credits + (t["distributions"] or 0)
        est = (taxable * Decimal(str(rate)) - credits).quantize(Decimal("0.01"))
        tiles += tile(
            "Estimated tax", aud(est), f"at {Decimal(str(rate)) * 100:.1f}% less franking credits"
        )
    else:
        tiles += tile("Estimated tax", "-", "set tax.marginal_rate on the server")
    order = (
        "<table><tbody>"
        f"<tr><td>Gains not eligible for the discount</td><td class='r'>{aud(s.short_gains)}</td></tr>"
        f"<tr><td>Discount-eligible gains</td><td class='r'>{aud(s.long_gains)}</td></tr>"
        f"<tr><td>Capital losses this year</td><td class='r'>{aud(-s.losses)}</td></tr>"
        f"<tr><td>Losses carried in</td><td class='r'>{aud(-s.carried_in)}</td></tr>"
        f"<tr><td>Losses used on non-discount gains</td><td class='r'>{aud(-s.applied_short)}</td></tr>"
        f"<tr><td>Losses used on discount-eligible gains</td><td class='r'>{aud(-s.applied_long)}</td></tr>"
        f"<tr><td>50% discount</td><td class='r'>{aud(-s.discount)}</td></tr>"
        f"<tr><td><b>Net capital gain</b></td><td class='r'><b>{aud(s.net_gain)}</b></td></tr>"
        f"<tr><td>Net capital loss to next year</td><td class='r'>{aud(s.carried_out)}</td></tr>"
        "</tbody></table>"
        "<p class='small muted'>Order: this year's losses, then earlier losses, go against "
        "non-discount gains first, then discount-eligible gains; the 50% discount applies to "
        "what is left (ATO method statement).</p>"
    )
    sales = "".join(
        f"<tr><td><b>{e(c.code)}</b><div class='sub'>{c.qty.normalize():f} · "
        f"{c.acquired:%d %b %y} → {c.disposed:%d %b %y}</div></td>"
        f"<td class='r'>{aud(c.proceeds)}<div class='sub'>cost {aud(c.cost_base)}</div></td>"
        f"<td class='r {tone(c.gain)}'>{aud(c.gain, True)}<div class='sub'>"
        f"{'discount' if c.long else 'no discount'}{' ⚠ near the line' if c.near_line else ''}"
        "</div></td></tr>"
        for c in r.cgt if c.acquired is not None
    ) + "".join(
        f"<tr><td><b>{e(c.code)}</b><div class='sub'>{e(c.event)} {c.disposed:%d %b %y}</div></td>"
        f"<td class='r'>{aud(c.proceeds)}</td><td class='r'>{aud(c.gain, True)}</td></tr>"
        for c in r.cgt if c.acquired is None
    )  # fmt: skip
    sales_html = (f"<table><thead><tr><th>Parcel sold</th><th class='r'>Proceeds</th>"
                  f"<th class='r'>Gain</th></tr></thead><tbody>{sales}</tbody></table>"
                  if sales else "<p class='muted'>No sales in this year.</p>")  # fmt: skip
    fr = ("<p>Franking credits: <b>" + aud(credits) + "</b></p>"
          if not t["franking_not_known"] else
          f"<p class='warn'>Franking credits: not in the data for {aud(t['franking_not_known'])} "
          "of dividends — enter them from your dividend statements.</p>")  # fmt: skip
    div_html = (
        f"<p>Dividends {aud(divs)} · specials {aud(specials)} · withholding "
        f"{aud(t['withholding'])} · fund distributions {aud(t['distributions'])}</p>{fr}"
    )
    marks = {h.code: h.mark for h in v.holdings if h.mark is not None}
    unr: list[Unrealised] = safe(lambda: unrealised(src, marks, today), [])
    un_rows = "".join(
        f"<tr><td><b>{e(u.code)}</b><div class='sub'>{u.qty.normalize():f} bought {u.acquired:%d %b %y}</div></td>"
        f"<td class='r {tone(None if u.value is None else u.value - u.cost)}'>"
        f"{aud(None if u.value is None else u.value - u.cost, True)}<div class='sub'>cost {aud(u.cost)}</div></td>"
        f"<td class='r small'>{'discount now' if u.eligible_from <= today else 'discount from ' + format(u.eligible_from, '%d %b %Y')}</td></tr>"
        for u in unr
    )  # fmt: skip
    un_html = (f"<table><tbody>{un_rows}</tbody></table><p class='small muted'>Gain if sold at "
               "the last price, before selling brokerage.</p>" if un_rows
               else "<p class='muted'>Nothing held.</p>")  # fmt: skip
    start, end = date(y, 7, 1), date(y + 1, 6, 30)
    flags = list(r.flags) + [f"Re-bought within 30 days (TR 2008/1, information only): {f}"
                             for f in rebuy_flags(src, start, end)]  # fmt: skip
    fl = "".join(f"<li class='small'>{e(f)}</li>" for f in flags)
    body = (
        head
        + section(f"FY {fy_label(y)}", f'<div class="tiles">{tiles}</div>')
        + section("Capital gains, step by step", order)
        + section("Sales, parcel by parcel", sales_html)
        + section("Dividends", div_html)
        + section("If you sold today", un_html)
        + (section("Check with your accountant", f'<ul class="list">{fl}</ul>') if fl else "")
        + f'<a class="btn sec wide" href="/tax.csv?fy={fy_label(y)}" download>⬇ EOFY CSV for '
        "your accountant / myTax</a>"
        f"<footer>{e(NOT_ADVICE)} {e(LABEL)}</footer>"
    )
    return shell(v, x, "Tax", body, "holdings")


def csv_export(src: Any, qs: Mapping[str, str]) -> str:
    """The year's disposals and dividends (read-only GET)."""
    today = src.clock().astimezone(ASX_TZ).date()
    ys = years(src, today)
    y = _fy(qs, ys)
    r = report(src, y)
    p = _params(src)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(CSV_COLUMNS)
    s = r.summary
    for c in r.cgt:
        disc = Decimal(0)
        if c.long and c.gain > 0 and s.long_gains:  # losses used on discount gains, pro rata
            used = s.applied_long * c.gain / s.long_gains
            disc = ((c.gain - used) * Decimal("0.5")).quantize(Decimal("0.01"))
        w.writerow(["disposal", c.code, f"{c.qty.normalize():f}", c.acquired or "", c.disposed,
                    f"{c.cost_base:.2f}", f"{c.proceeds:.2f}", f"{c.gain:.2f}",
                    "yes" if c.long else "no", f"{disc:.2f}", p.method, c.event])  # fmt: skip
    for i in r.income:
        w.writerow(["income", i.code, i.held, "", i.pay_date or i.ex_date or "", "", f"{i.cash:.2f}",
                    f"{i.income:.2f}", "", "", "", f"{i.kind} franking credit {i.franking_credit:.2f}"
                    + ("" if i.franked_pct is not None else " (franking not known)")])  # fmt: skip
    w.writerow(["summary", "", "", "", "", "", "", f"{s.net_gain:.2f}", "", f"{s.discount:.2f}",
                p.method, f"net capital gain FY {fy_label(y)}; loss carried forward {s.carried_out:.2f}"])  # fmt: skip
    w.writerow(["note", "", "", "", "", "", "", "", "", "", "", LABEL])
    return buf.getvalue()
