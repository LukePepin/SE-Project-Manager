"""T-17 and T-18 (SE-03): the time equation and the timeline proposal."""

import importlib.util
import math
import re
import sys
from datetime import date
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[1] / ".claude" / "skills" / "timeplan"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SKILL / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # dataclasses look the module up while it loads
    spec.loader.exec_module(mod)
    return mod


te = load("time_equation")
tl = load("timeline")


def test_suggestion_rises_with_length_and_complexity():
    small = te.suggest(3, 4, 2, 5).hours
    longer = te.suggest(3, 16, 2, 5).hours
    harder = te.suggest(3, 4, 4, 5).hours
    assert longer > small and harder > small


def test_equation_matches_hand_calculation():
    s = te.suggest(purpose=4, length=10, complexity=3, availability=10)
    assert s.need == pytest.approx(16.0)
    assert s.hours == pytest.approx(16.0 * math.log(4.0))
    assert s.verdict == "go" and s.tier == "short"


def test_low_purpose_is_no_go():
    s = te.suggest(1, 16, 3, 10)
    assert s.hours == 0 and s.verdict == "no-go"


def test_scarce_hours_shrink_then_stop_a_project():
    plenty = te.suggest(3, 16, 2, 10)
    scarce = te.suggest(3, 16, 2, 2.5)  # c = 2: ln(2.5 / 2) is small
    none = te.suggest(3, 16, 2, 1)  # c = 5 > r
    assert plenty.verdict == "go"
    assert scarce.verdict == "shrink" and scarce.hours < plenty.hours
    assert none.verdict == "no-go"


def test_length_classes_and_bad_input():
    assert te.parse_length("small") == 4.0 and te.parse_length("2.5") == 2.5
    with pytest.raises(ValueError):
        te.suggest(6, 4, 2, 5)


def test_record_reports_error_and_calibrates(tmp_path):
    cal = tmp_path / "calibration.csv"
    res = te.record(cal, "attic", suggested=4, actual=6, when="2026-10-20")
    assert res["error_hours"] == 2 and res["ratio"] == 1.5
    te.record(cal, "bedroom", suggested=2, actual=2, when="2026-10-27")
    te.record(cal, "packing", suggested=10, actual=20, when="2026-11-03")
    factor, n = te.load_calibration(cal)
    assert n == 3 and factor == 1.5  # median of 1.5, 1.0, 2.0
    calibrated = te.suggest(3, 4, 1, 5, factor, n)
    assert calibrated.need == pytest.approx(6.0)


def test_timeline_dates_follow_hours_per_week():
    gates = tl.plan(hours=10, per_week=5, start=date(2026, 10, 12), tier="short")
    assert [g.name for g in gates][0] == "G0 Charter"
    assert gates[-1].cumulative == pytest.approx(10)
    assert gates[-1].due == date(2026, 10, 26)  # 2 weeks
    assert all(a.due <= b.due for a, b in zip(gates, gates[1:]))


def test_blocks_cover_the_hours_weekly():
    blks = tl.blocks(10, 4, date(2026, 10, 12), "SAT@10:00")  # Monday start
    assert [round(h, 6) for _, h in blks] == [4, 4, 2]
    assert blks[0][0].weekday() == 5 and blks[0][0].hour == 10
    assert (blks[1][0] - blks[0][0]).days == 7


def test_cli_writes_proposals_only(tmp_path):
    code = tl.main(["--hours", "8", "--per-week", "4", "--start", "2026-10-12", "--tier", "short",
                    "--project", "attic", "--block", "SAT@10:00", "--github", "lpep/attic", "--out-dir", str(tmp_path)])
    assert code == 0
    md = (tmp_path / "timeline.md").read_text()
    ics = (tmp_path / "timeline.ics").read_bytes()
    assert "Status: PROPOSED" in md and "gh api repos/lpep/attic/milestones" in md
    assert ics.count(b"BEGIN:VEVENT") == 4 + 2 and b"\r\n" in ics


def test_no_network_code_in_the_scripts():
    for name in ("timeline.py", "time_equation.py"):
        src = (SKILL / name).read_text()
        assert not re.search(r"^\s*(import|from)\s+(urllib|http|socket|requests)", src, re.M), name
