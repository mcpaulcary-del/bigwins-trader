"""Requirement coverage table (spec §20).

Every CI-tested requirement ID of the milestones reached so far must appear in
at least one test name or docstring, and (with ``--junit``) at least one of
those tests must have passed. Prints a Markdown table; exits 1 on any gap.

Usage::

    python scripts/req_coverage.py --milestone M0 [--junit report.xml] [--tests tests]
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

MILESTONES: dict[str, tuple[str, ...]] = {
    "M0": ("OPS-05", "OPS-10", "OPS-11", "OPS-12", "SYS-13", "SYS-14", "MON-03"),
}
ORDER = ("M0", "M1", "M2", "M3", "M4", "M5", "M6", "M7")
# "_" is a word character, so test_OPS_10_x has no \b before OPS: use lookarounds.
ID_RE = re.compile(
    r"(?<![A-Za-z])(SYS|DAT|STR|PRT|RSK|EXE|LED|TAX|USR|MON|VAL|OPS|INF)[-_](\d{2})(?!\d)"
)


def required_ids(milestone: str) -> list[str]:
    ids: list[str] = []
    for m in ORDER[: ORDER.index(milestone) + 1]:
        ids.extend(MILESTONES.get(m, ()))
    return ids


def _ids(text: str | None) -> set[str]:
    return {f"{a}-{b}" for a, b in ID_RE.findall(text or "")}


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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--milestone", default="M0", choices=ORDER)
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
    if not ok:
        print("\nRequirement coverage FAILED", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
