"""Requirement coverage table (spec v2.10 §20).

Every CI-tested requirement ID of the milestones reached so far must appear in
at least one test name or docstring, and (with ``--junit``) at least one of
those tests must have passed. Prints a Markdown table; exits 1 on any gap.

It also fails if any code or test refers to a withdrawn requirement ID
(§20; withdrawn IDs are listed in change log CL-C and CL-F).

Usage::

    python scripts/req_coverage.py --milestone M1 [--junit report.xml] [--tests tests]
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


def _ids_range(prefix: str, lo: int, hi: int) -> tuple[str, ...]:
    return tuple(f"{prefix}-{i:02d}" for i in range(lo, hi + 1))


MILESTONES: dict[str, tuple[str, ...]] = {
    "M0": ("OPS-05", "OPS-10", "OPS-11", "OPS-12", "SYS-13", "SYS-14", "MON-03"),
    "M1": (
        *_ids_range("DAT", 1, 23),
        "SYS-12",
        "SYS-20",
        *_ids_range("SYS", 29, 32),
    ),
}
# B-fast (FD v3.0 §21.1): the BW-* requirements BF1-BF4 build and test.
MILESTONES["BF"] = (
    "BW-SYS-03", "BW-SYS-04", "BW-SYS-10", "BW-SYS-12", "BW-STR-10", "BW-UNI-01",
    "BW-UNI-02", "BW-UNI-03", "BW-UNI-11", "BW-RSK-01", "BW-RSK-02", "BW-RSK-03",
    "BW-RSK-06", "BW-RSK-07", "BW-RSK-08", "BW-RSK-11", "BW-RSK-20", "BW-RSK-22",
    "BW-RSK-27", "BW-RSK-29", "BW-RSK-30", "BW-EXE-06", "BW-EXE-09", "BW-APR-03",
    "BW-APR-04", "BW-APR-05", "BW-TAX-01", "BW-TAX-02",
)  # fmt: skip
ORDER = ("M0", "M1", "BF", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9", "M10")
PREFIXES = "SYS|DAT|PRT|RSK|EXE|LED|TAX|USR|MON|VAL|OPS|INF|RND|SIZ|MKT|ENG|USE|BP|STR|ADP|FUT"
# "_" is a word character, so test_OPS_10_x has no \b before OPS: use lookarounds.
# FD v3.0 IDs are "BW-<AREA>-<nn>", a separate namespace that may reuse v2.10 numbers
# (including withdrawn ones), so the v2.10 pattern skips anything preceded by "BW-".
ID_RE = re.compile(rf"(?<![A-Za-z])(?<!BW[-_])({PREFIXES})[-_](\d{{2}})(?!\d)")
BW_RE = re.compile(r"(?<![A-Za-z])BW[-_]([A-Z]{2,3})[-_](\d{2})(?!\d)")

# Withdrawn requirement IDs (v2.10 change log CL-C and CL-F). Built from ranges so that
# this file itself contains no withdrawn ID literal.
WITHDRAWN: frozenset[str] = frozenset(
    {
        *_ids_range("STR", 1, 5),
        *_ids_range("STR", 10, 12),
        *_ids_range("PRT", 1, 5),
        *_ids_range("SYS", 21, 22),
        *_ids_range("SYS", 25, 28),
        *(f"RSK-{n:02d}" for n in (5, 20, 21, 23)),
        *_ids_range("VAL", 1, 13),
        *(f"USR-{n:02d}" for n in (2, 6, 12)),
        *_ids_range("ADP", 1, 4),
        *_ids_range("FUT", 1, 7),
    }
)
# Directories scanned for withdrawn IDs. The v1.x migrations 0001-0004 are history
# and are not rewritten (they contain no requirement IDs).
CODE_DIRS = ("trader", "tests", "scripts", "migrations")


def required_ids(milestone: str) -> list[str]:
    ids: list[str] = []
    for m in ORDER[: ORDER.index(milestone) + 1]:
        ids.extend(MILESTONES.get(m, ()))
    return ids


def _ids(text: str | None) -> set[str]:
    old = {f"{a}-{b}" for a, b in ID_RE.findall(text or "")}
    return old | {f"BW-{a}-{b}" for a, b in BW_RE.findall(text or "")}


def scan_tests(test_dir: Path) -> dict[str, set[str]]:
    """Map requirement ID -> set of test node names ``module::[Class::]test``."""
    found: dict[str, set[str]] = defaultdict(set)
    for path in sorted(test_dir.rglob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        mod = path.with_suffix("").relative_to(test_dir.parent).as_posix().replace("/", ".")

        def visit(node: ast.AST, prefix: str, inherited: set[str], mod: str = mod) -> None:
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.ClassDef) and child.name.startswith("Test"):
                    ids = inherited | _ids(child.name) | _ids(ast.get_docstring(child))
                    visit(child, f"{prefix}{child.name}::", ids)
                elif isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef) and (
                    child.name.startswith("test")
                ):
                    ids = inherited | _ids(child.name) | _ids(ast.get_docstring(child))
                    for rid in ids:
                        found[rid].add(f"{mod}::{prefix}{child.name}")

        visit(tree, "", set())
    return found


def junit_results(path: Path) -> dict[str, str]:
    """Map ``module::[Class::]test`` (without parametrisation) -> passed/failed/skipped."""
    out: dict[str, str] = {}
    for case in ET.parse(path).getroot().iter("testcase"):  # noqa: S314
        classname = case.get("classname", "")
        name = case.get("name", "").split("[")[0]
        parts = classname.split(".")
        # classname is "tests.test_x" or "tests.test_x.TestClass"
        if parts and parts[-1].startswith("Test"):
            key = ".".join(parts[:-1]) + "::" + parts[-1] + "::" + name
        else:
            key = classname + "::" + name
        if case.find("failure") is not None or case.find("error") is not None:
            status = "failed"
        elif case.find("skipped") is not None:
            status = "skipped"
        else:
            status = "passed"
        prev = out.get(key)
        # any failing parametrisation fails the test; otherwise passed beats skipped
        if prev == "failed" or status == "failed":
            out[key] = "failed"
        elif prev == "passed" or status == "passed":
            out[key] = "passed"
        else:
            out[key] = status
    return out


def withdrawn_refs(root: Path) -> list[str]:
    """Every ``path:line: ID`` where code or tests refer to a withdrawn requirement ID."""
    hits: list[str] = []
    for d in CODE_DIRS:
        for path in sorted((root / d).rglob("*.py")):
            for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                for rid in _ids(line) & WITHDRAWN:
                    hits.append(f"{path.relative_to(root)}:{n}: {rid}")
    return hits


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--milestone", default="M1", choices=ORDER)
    ap.add_argument("--tests", type=Path, default=Path("tests"))
    ap.add_argument("--junit", type=Path)
    args = ap.parse_args(argv)

    found = scan_tests(args.tests)
    results = junit_results(args.junit) if args.junit else None
    ok = True
    print(f"## Requirement coverage ({args.milestone}, cumulative)\n")
    print("| Requirement | Tests | Passed | Status |")
    print("| --- | --- | --- | --- |")
    for rid in required_ids(args.milestone):
        tests = sorted(found.get(rid, set()))
        if results is None:
            passed = "n/a"
            good = bool(tests)
        else:
            n_pass = sum(1 for t in tests if results.get(t) == "passed")
            n_fail = sum(1 for t in tests if results.get(t) == "failed")
            passed = f"{n_pass}/{len(tests)}"
            good = n_pass > 0 and n_fail == 0
        ok &= good
        print(f"| {rid} | {len(tests)} | {passed} | {'OK' if good else 'MISSING/FAILED'} |")
    refs = withdrawn_refs(args.tests.resolve().parent)
    if refs:
        ok = False
        print("\nWithdrawn requirement IDs referenced (spec §20 forbids this):")
        for r in refs:
            print(f"- {r}")
    if not ok:
        print("\nRequirement coverage FAILED", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
