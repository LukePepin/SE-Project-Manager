"""T-16 (SE-03): the warden's fixed checks on scratch elicitation records."""

import importlib.util
import sys
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[1] / ".claude" / "skills" / "warden"
spec = importlib.util.spec_from_file_location("gate_check", SKILL / "gate_check.py")
gc = importlib.util.module_from_spec(spec)
sys.modules["gate_check"] = gc  # dataclasses look the module up while it loads
spec.loader.exec_module(gc)

HEADER = "| ID | Type | Statement | Source | Basis | Lens | Status |\n|---|---|---|---|---|---|---|\n"
CLEAR = [
    "| E-001 | Need | \"my receipts are never where I need them\" | dump P1 | stated | L1 | active |",
    "| E-002 | Measure | Find a receipt in under a minute; threshold: 2 min | R1.Q1 | stated | L18 | active |",
    "| E-003 | Need | \"drop a scan and check it is filed\" | R1.Q2 | stated | L9 | active |",
    "| E-004 | Out | No phone app | R1.Q3 | stated | L17 | active |",
    "| E-005 | Constraint | \"an afternoon at most\" | dump P2 | stated | L10, L14 | active |",
]


def record(tmp_path, rows, prioritization=None):
    folder = tmp_path / "rec"
    folder.mkdir()
    (folder / "items.md").write_text("# Items\n\n" + HEADER + "\n".join(rows) + "\n")
    if prioritization is not None:
        (folder / "prioritization.md").write_text(prioritization)
    return folder


def run(folder, **kw):
    items = gc.parse_items(folder / "items.md")
    pz = folder / "prioritization.md"
    checks = gc.run_checks(items, pz.read_text() if pz.exists() else None, **kw)
    return gc.verdict(checks), {c.name: c for c in checks}


def test_clear_goal_is_go(tmp_path):
    result, checks = run(record(tmp_path, CLEAR))
    assert result == gc.GO
    assert checks["Purpose"].evidence == ["E-001"]


def test_undefined_goal_is_no_go(tmp_path):
    rows = [r for r in CLEAR if "E-001" not in r]  # no purpose
    result, checks = run(record(tmp_path, rows))
    assert result == gc.NOGO
    assert not checks["Purpose"].passed


def test_untestable_goal_is_no_go(tmp_path):
    rows = [r for r in CLEAR if "E-003" not in r]  # nothing tagged L9
    result, checks = run(record(tmp_path, rows))
    assert result == gc.NOGO
    assert not checks["Testable"].passed


def test_inferred_items_never_pass_a_check(tmp_path):
    rows = [CLEAR[0].replace("| stated |", "| inferred |")] + CLEAR[1:]
    result, checks = run(record(tmp_path, rows))
    assert not checks["Purpose"].passed
    assert result == gc.NOGO


def test_mostly_claude_needs_is_no_go(tmp_path):
    extra = [
        f"| E-01{k} | Need | Claude's idea {k} | inferred from E-001 | inferred | L2 | active |" for k in range(3)
    ]
    result, checks = run(record(tmp_path, CLEAR + extra))
    assert not checks["Luke's words"].passed  # 3 of 5 needs inferred
    assert result == gc.NOGO


def test_dropped_items_do_not_count(tmp_path):
    rows = [CLEAR[0].replace("| active |", "| dropped: no (R2.Q1) |")] + CLEAR[1:]
    result, _ = run(record(tmp_path, rows))
    assert result == gc.NOGO


def test_loose_scope_is_shrink(tmp_path):
    rows = [r for r in CLEAR if "E-004" not in r]  # no Out item
    result, checks = run(record(tmp_path, rows))
    assert result == gc.SHRINK
    assert not checks["Scope edge"].passed


def test_musts_over_budget_is_shrink(tmp_path):
    result, checks = run(record(tmp_path, CLEAR, prioritization="**Infeasible:** the Must items ..."))
    assert result == gc.SHRINK
    assert not checks["Musts fit the budget"].passed


def test_statement_with_pipes_parses(tmp_path):
    rows = CLEAR + ["| E-009 | Assumption | a | b \\| c | dump P3 | stated | L5 | active |"]
    items = gc.parse_items(record(tmp_path, rows) / "items.md")
    assert items[-1].basis == "stated" and items[-1].lenses == {"L5"}


def test_cli_exit_codes(tmp_path):
    go = record(tmp_path, CLEAR)
    assert gc.main([str(go), "--out", str(tmp_path / "v.md")]) == 0
    assert "Checks verdict: GO" in (tmp_path / "v.md").read_text()
    nogo = tmp_path / "nogo"
    nogo.mkdir()
    (nogo / "items.md").write_text(HEADER + CLEAR[1] + "\n")
    assert gc.main([str(nogo), "--out", str(tmp_path / "n.md")]) == 2


def test_empty_record_is_an_error(tmp_path):
    folder = tmp_path / "empty"
    folder.mkdir()
    (folder / "items.md").write_text("# nothing\n")
    with pytest.raises(ValueError):
        gc.parse_items(folder / "items.md")


def test_context_items_are_not_counted_as_claudes(tmp_path):
    ctx = [f"| E-02{k} | Need | from Docket {k} | context: docket_memory.md | context | L10 | active |" for k in range(4)]
    result, checks = run(record(tmp_path, CLEAR + ctx))
    assert checks["Luke's words"].passed and result == gc.GO
