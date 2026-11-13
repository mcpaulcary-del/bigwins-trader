"""The CI requirement-coverage gate itself (§20 code quality rules)."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

from tests.conftest import REPO


def _mod() -> ModuleType:
    spec = importlib.util.spec_from_file_location("req_coverage", REPO / "scripts/req_coverage.py")
    assert spec is not None
    assert spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_scanner_finds_ids_in_names_and_docstrings(tmp_path: Path) -> None:
    d = tmp_path / "tests"
    d.mkdir()
    (d / "test_x.py").write_text(
        "def test_OPS_10_name() -> None:\n    pass\n\n"
        'def test_doc() -> None:\n    """MON-03 here."""\n\n'
        'class TestSYS13:\n    """SYS-13"""\n    def test_a(self) -> None:\n        pass\n'
    )
    found = _mod().scan_tests(d)
    assert found["OPS-10"] == {"tests.test_x::test_OPS_10_name"}
    assert found["MON-03"] == {"tests.test_x::test_doc"}
    assert found["SYS-13"] == {"tests.test_x::TestSYS13::test_a"}


def test_gate_fails_when_an_m0_id_has_no_test(tmp_path: Path) -> None:
    d = tmp_path / "tests"
    d.mkdir()
    (d / "test_x.py").write_text("def test_OPS_10() -> None:\n    pass\n")
    assert _mod().main(["--milestone", "M0", "--tests", str(d)]) == 1


def test_gate_passes_on_this_repo() -> None:
    assert _mod().main(["--milestone", "M0", "--tests", str(REPO / "tests")]) == 0
