"""bigwins worker (BF-D78): the private info archive, server copy of the research script.

Owner decision 24 Nov 2026 (ledger seq 96): automated access to asx.com.au is allowed
ONLY for this archive. Private, personal, non-commercial use: the data is never shared
and never leaves the owner's server and app. INFORMATION ONLY: nothing here feeds the
strategy, a paper line or the trader.

What it collects (polite: one request every 2 seconds, a plain user agent):
  1. ASX announcements of the previous trading day (one list page) ->
     ``asx_notices/<YYYY-MM-DD>/list.csv`` with every headline;
  2. the PDFs of director-interest notices (Appendix 3Y / 3X / 3Z) and capital-raising
     notices -> ``pdf/<CODE>_<idsId>.pdf`` and ``.txt`` (``pdftotext -layout``);
  3. ASIC's daily aggregated short positions (published a few trading days late) ->
     ``asic_short/RR<date>-<ver>-SSDailyAggShortPos.csv.gz``, every listed day not yet
     stored, at most ``--asic-limit`` new files a run (the first runs backfill slowly).

Idempotent: a day with ``DONE`` or a short file already stored is skipped. Run by the
host worker as the trader's uid (never root) the morning after each trading day, only
when ``info_archive.archive_enabled`` is true; the data folder is ``INFO_ARCHIVE_DIR``
(deploy/.env, default /var/lib/bigwins/info), outside the repository. The last line of
output is a JSON summary that the worker records in the app. Standard library only.

    python3 -I deploy/info_archive.py --out DIR [--asic-limit N] [asx] [asic]
"""

from __future__ import annotations

import argparse
import csv
import gzip
import html
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from typing import Any

UA = {"User-Agent": "Mozilla/5.0 (private personal research; low rate)"}
GAP = 2.0
LIST_URL = "https://www.asx.com.au/asx/v2/statistics/prevBusDayAnns.do"
BASE = "https://www.asx.com.au"
ASIC_INDEX = "https://download.asic.gov.au/short-selling/short-selling-data.json"
ASIC_BASE = "https://download.asic.gov.au/short-selling/"
KEEP = re.compile(
    r"director'?s?.? interest|appendix 3[xyz]|proposed issue|application for quotation|placement|"
    r"entitlement|capital raising|share purchase plan|cleansing|appendix 2a|appendix 3b",
    re.I,
)
ROW = re.compile(
    r"<tr[^>]*>\s*<td>(\w+)</td>\s*<td>\s*(\d\d/\d\d/\d{4})<br>\s*"
    r'<span class="dates-time">([^<]+)</span>\s*</td>(.*?)</tr>',
    re.S,
)
MIN_ROWS = 50  # fewer means the page format changed: stop, never store a partial day
ASIC_DAYS = 90  # BF-D81 (review S5): only the recent short positions (the app shows these)
ASX_HOSTS = ("asx.com.au",)  # the owner's exception covers these hosts only
ASIC_HOSTS = ("download.asic.gov.au",)
_last = [0.0]


def host_ok(url: str, hosts: tuple[str, ...]) -> bool:
    """https on one of ``hosts`` (or a sub-domain of it), nothing else."""
    try:
        u = urllib.parse.urlsplit(url)
    except ValueError:
        return False
    h = (u.hostname or "").lower()
    return u.scheme == "https" and any(h == x or h.endswith("." + x) for x in hosts)


class _Pinned(urllib.request.HTTPRedirectHandler):
    """Follow a redirect only to an allowed host (BF-D81: no off-host redirects)."""

    def __init__(self, hosts: tuple[str, ...]) -> None:
        self.hosts = hosts

    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any,
                         newurl: str) -> Any:  # fmt: skip
        if not host_ok(newurl, self.hosts):
            raise urllib.error.HTTPError(newurl, code, "redirect to another host refused",
                                         headers, fp)  # fmt: skip
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def get(url: str, hosts: tuple[str, ...] = ASX_HOSTS) -> bytes:
    if not host_ok(url, hosts):
        raise ValueError(f"not an allowed host: {urllib.parse.urlsplit(url).hostname}")
    wait = GAP - (time.time() - _last[0])
    if wait > 0:
        time.sleep(wait)
    opener = urllib.request.build_opener(_Pinned(hosts))
    err: Exception | None = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=UA)  # noqa: S310 - pinned https hosts
            with opener.open(req, timeout=60) as r:
                _last[0] = time.time()
                return bytes(r.read(50_000_000))
        except Exception as e:  # retried, then raised
            _last[0] = time.time()
            err = e
            time.sleep(5 * (attempt + 1))
    assert err is not None
    raise err


def parse_list(page: str) -> tuple[str, list[dict[str, Any]]]:
    """The day (YYYY-MM-DD) and the rows of the previous-business-day page."""
    m = re.search(r"published on\s+(\d{1,2}) (\w+) (\d{4})", page)
    if not m:
        raise ValueError("no 'published on' date: page format changed?")
    day = time.strftime("%Y-%m-%d", time.strptime(" ".join(m.groups()), "%d %B %Y"))
    rows = []
    for code, dt, tm, rest in ROW.findall(page):
        a = re.search(r'href="([^"]+)">\s*([^<]+?)\s*<br>', rest, re.S)
        if not a:
            continue
        url = html.unescape(a.group(1))
        ids = re.search(r"idsId=(\d+)", url)
        head = html.unescape(a.group(2)).strip()
        rows.append({"code": code, "date": dt, "time": tm.strip(),
                     "price_sensitive": int("pricesens" in rest), "headline": head,
                     "ids_id": ids.group(1) if ids else "",
                     "kept": int(bool(KEEP.search(head)))})  # fmt: skip
    return day, rows


def asx_notices(out: str) -> dict[str, Any]:
    page = get(LIST_URL).decode("utf-8", "replace")
    day, rows = parse_list(page)
    d = os.path.join(out, "asx_notices", day)
    if os.path.exists(os.path.join(d, "DONE")):
        return {"day": day, "note": "already stored"}
    if len(rows) < MIN_ROWS:
        raise ValueError(f"{day}: only {len(rows)} rows parsed - page format changed?")
    os.makedirs(os.path.join(d, "pdf"), exist_ok=True)
    lst = os.path.join(d, "list.csv")
    with open(lst + ".part", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    os.replace(lst + ".part", lst)
    got = fail = 0
    for r in rows:
        if not r["kept"] or not r["ids_id"]:
            continue
        p = os.path.join(d, "pdf", f"{r['code']}_{r['ids_id']}.pdf")
        if os.path.exists(p):
            continue
        try:
            terms = get(f"{BASE}/asx/v2/statistics/displayAnnouncement.do?display=pdf"
                        f"&idsId={r['ids_id']}").decode("utf-8", "replace")  # fmt: skip
            m = re.search(r'name="pdfURL" value="([^"]+)"', terms)
            pdf_url = html.unescape(m.group(1)) if m else ""
            if not host_ok(pdf_url, ASX_HOSTS):  # BF-D81: the PDF only from an ASX host
                raise ValueError("no PDF link on an ASX host")
            b = get(pdf_url)
            if not b.startswith(b"%PDF"):
                raise ValueError("not a PDF")
            with open(p + ".part", "wb") as fh:  # a part-written file is never kept
                fh.write(b)
            txt = p[:-4] + ".txt"
            subprocess.run(["pdftotext", "-layout", p + ".part", txt + ".part"], timeout=60,  # noqa: S603, S607
                           check=False, capture_output=True)  # fmt: skip
            if os.path.exists(txt + ".part"):
                os.replace(txt + ".part", txt)
            os.replace(p + ".part", p)
            got += 1
        except Exception as e:  # one notice failing never stops the day
            fail += 1
            print("pdf fail", r["code"], r["ids_id"], type(e).__name__, file=sys.stderr)
    summary = {"rows": len(rows), "kept": sum(r["kept"] for r in rows), "pdfs": got,
               "failed": fail, "utc": time.strftime("%FT%TZ", time.gmtime())}  # fmt: skip
    with open(os.path.join(d, "DONE"), "w", encoding="utf-8") as fh:
        fh.write(json.dumps(summary))
    return {"day": day, **summary}


def asic_short(out: str, limit: int | None, today: date | None = None) -> dict[str, Any]:
    d = os.path.join(out, "asic_short")
    os.makedirs(d, exist_ok=True)
    idx = json.loads(get(ASIC_INDEX, ASIC_HOSTS))
    day0 = today or date.today()  # noqa: DTZ011 - the server runs on Sydney time
    since = (day0 - timedelta(days=ASIC_DAYS)).strftime("%Y%m%d")
    new = 0
    for e in idx:
        date_, ver = str(e.get("date", "")), str(e.get("version", ""))
        if not (date_.isdigit() and len(date_) == 8 and ver.isdigit()) or date_ < since:
            continue
        name = f"RR{date_}-{ver}-SSDailyAggShortPos.csv"
        p = os.path.join(d, name + ".gz")
        if os.path.exists(p):
            continue
        if limit is not None and new >= limit:
            break
        try:
            b = get(ASIC_BASE + name, ASIC_HOSTS)
        except Exception as ex:
            print("asic fail", name, type(ex).__name__, file=sys.stderr)
            continue
        with gzip.open(p + ".part", "wb") as f:
            f.write(b)
        os.replace(p + ".part", p)
        new += 1
    have = len([x for x in os.listdir(d) if x.endswith(".csv.gz")])
    return {"asic_new": new, "asic_files": have}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", required=True, help="the data folder (outside the repository)")
    ap.add_argument("--asic-limit", type=int, default=400)
    ap.add_argument("what", nargs="*", default=["asx", "asic"], choices=["asx", "asic"])
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    res: dict[str, Any] = {"ok": True}
    errors = []
    if "asx" in a.what:
        try:
            res.update(asx_notices(a.out))
        except Exception as e:
            errors.append(f"announcements: {type(e).__name__}: {e}"[:200])
    if "asic" in a.what:
        try:
            res.update(asic_short(a.out, a.asic_limit))
        except Exception as e:
            errors.append(f"ASIC short positions: {type(e).__name__}"[:200])
    if errors:
        res["ok"] = False
        res["error"] = "; ".join(errors)
    print(json.dumps(res))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
