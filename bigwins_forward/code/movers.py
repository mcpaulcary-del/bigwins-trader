"""Big movers for the nightly report (INFORMATION ONLY; reads files, writes one markdown file; no network, no trades).

Rule (owner request 27 Nov 2026):
  - the 200 largest companies by traded value (latest scores_top300 snapshot) that moved +/-5% or more on the day;
  - any share held by a paper book that moved +/-3% or more, or had no close today;
  - at most 10 rows, largest absolute move first (holdings always kept).
Context per row: 6-month change and distance from the 12-month high (both rolled forward from the snapshot with
today's close, so approximate), Big Wins score rank (1 = best of 300) and which paper books hold it.

Usage: python3 movers.py [--day YYYY-MM-DD]   (default: latest bulk day)
"""
import argparse, csv, glob, gzip, json, os, sys

S = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BULK = f"{S}/bigwins_forward/data/bulk"
REC = f"{S}/onedrive/research2/68_forward_record"
OUT = f"{S}/bigwins_forward/out/movers"
TOP, BIG, HELD, MAXROWS = 200, 0.05, 0.03, 10


def px(day):
    rows = json.load(gzip.open(f"{BULK}/{day}/eod.json.gz"))
    return {r["code"]: r for r in rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--day")
    a = ap.parse_args()
    days = sorted(d for d in os.listdir(BULK) if os.path.exists(f"{BULK}/{d}/eod.json.gz"))
    day = a.day or days[-1]
    prev = [d for d in days if d < day]
    if day not in days or not prev:
        sys.exit(f"movers: no bulk file for {day} or no earlier day")
    p0, p1 = px(prev[-1]), px(day)
    snap = sorted(glob.glob(f"{REC}/scores_top300_*.csv"))[-1]
    sc = {r["code"]: r for r in csv.DictReader(open(snap))}
    held = {}
    hp = f"{REC}/paper/holdings_latest.csv"
    if os.path.exists(hp):
        for r in csv.DictReader(open(hp)):
            if r["book"].startswith(("H82", "EMG2", "BLIND3", "PAIR", "MOON", "EMG2_MOON")):
                held.setdefault(r["code"], set()).add(r["book"])
    rows = []
    for c in set(sc) | set(held):
        s = sc.get(c)
        big = s is not None and int(s["tv_rank"]) <= TOP
        if c not in p1 or p1[c]["date"] != day:
            if c in held:
                rows.append(dict(code=c, move=None, s=s, held=held[c], note="no close today"))
            continue
        if c not in p0:
            continue
        m = p1[c]["adjusted_close"] / p0[c]["adjusted_close"] - 1
        if (big and abs(m) >= BIG) or (c in held and abs(m) >= HELD):
            rows.append(dict(code=c, move=m, s=s, held=held.get(c, set()), note=""))
    rows.sort(key=lambda r: (not r["held"] and r["move"] is None, -abs(r["move"] or 0)))
    keep = [r for r in rows if r["held"]]
    for r in rows:
        if len(keep) >= MAXROWS:
            break
        if r not in keep:
            keep.append(r)
    keep.sort(key=lambda r: -abs(r["move"] or 0))
    lines = [f"# Big movers {day} (information only; snapshot {os.path.basename(snap)})", "",
             "| Code | Name | Day | 6 months | From 12m high | Score rank | Held by |", "|---|---|---|---|---|---|---|"]
    for r in keep:
        s, c = r["s"], r["code"]
        name = s["name"] if s else c
        six = high = rank = ""
        if s and r["move"] is not None:
            f = p1[c]["adjusted_close"] / float(s["close10"])
            six = f"{(1 + float(s['s2_mom6'])) * f - 1:+.0%}"
            high = f"{min(1.0, float(s['s3_near_high']) * f) - 1:+.0%}"
            rank = s["score_rank"]
        day_s = r["note"] if r["move"] is None else f"{r['move']:+.1%}"
        books = ", ".join(sorted(r["held"])) or "not held"
        lines.append(f"| {c} | {name} | {day_s} | {six} | {high} | {rank} | {books} |")
    if not keep:
        lines.append("| - | No big moves today | | | | | |")
    os.makedirs(OUT, exist_ok=True)
    open(f"{OUT}/movers_{day}.md", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
