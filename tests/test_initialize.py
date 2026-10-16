"""T-5, T-7, T-8 and T-19 (SE-03): the initializer's tiers, refusals and household folders."""

import importlib.util
import sys
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[1] / ".claude" / "skills" / "initialize"
spec = importlib.util.spec_from_file_location("init_project", SKILL / "init_project.py")
ip = importlib.util.module_from_spec(spec)
sys.modules["init_project"] = ip
spec.loader.exec_module(ip)

SHORT = {"README.md", "AGENTS.md", "CLAUDE.md", "docs/se/README.md", "docs/se/SE-00_project_plan.md",
         "docs/se/SE-01_charter.md", "docs/se/SE-02_conops.md", "docs/se/SE-03_requirements.md"}
LONG_EXTRA = {"docs/se/SE-04_architecture.md", "docs/se/SE-05_icd.md", "docs/se/SE-06_vv_plan.md",
              "docs/se/SE-07_reports.md"}


def files(root):
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


@pytest.fixture
def home(tmp_path):
    h = tmp_path / "home"
    (h / "Documents").mkdir(parents=True)
    (h / "Projects").mkdir()
    rec = h / "record"
    rec.mkdir()
    (rec / "verdict.md").write_text("**Verdict: GO.** Fine.\n")
    return h


def init(target, name, tier, home, **kw):
    kw.setdefault("record", home / "record")
    return ip.initialize(target, name, tier, home=home, **kw)


def test_each_tier_gets_exactly_its_documents(home):
    imm = home / "Projects" / "imm"
    init(imm, "Imm", "immediate", home)
    assert files(imm) == {"README.md", "AGENTS.md", "CLAUDE.md"}
    short = home / "Projects" / "short"
    init(short, "Short", "short", home)
    assert files(short) == SHORT
    long = home / "Projects" / "long"
    init(long, "Long", "long", home)
    assert files(long) == SHORT | LONG_EXTRA


def test_documents_carry_status_line_explain_back_and_no_placeholders_left(home):
    t = home / "Projects" / "p"
    init(t, "Attic Plan", "long", home, today="2026-10-09")
    for rel in files(t) - {"CLAUDE.md", "AGENTS.md"}:
        text = (t / rel).read_text()
        assert "{{" not in text, rel
        if rel.startswith("docs/se/"):
            assert "**Status: DRAFT.**" in text and "**Explain-back (Luke):**" in text, rel
    assert "@AGENTS.md" in (t / "CLAUDE.md").read_text()


def test_promotion_adds_only_missing_documents(home):
    t = home / "Projects" / "grow"
    init(t, "Grow", "short", home)
    (t / "docs/se/SE-01_charter.md").write_text("Luke's own charter\n")
    before = {r: (t / r).read_bytes() for r in files(t)}
    res = init(t, "Grow", "long", home)
    assert set(res["written"]) == LONG_EXTRA
    assert all((t / r).read_bytes() == b for r, b in before.items())


def test_code_project_in_icloud_is_refused_but_household_is_not(home):
    with pytest.raises(ip.Refused, match="iCloud"):
        init(home / "Documents" / "repo", "X", "short", home)
    assert not (home / "Documents" / "repo").exists()
    res = init(home / "Documents" / "attic", "Attic", "short", home, kind="household")
    assert set(res["written"]) == {"plan.md", "checklist.md", "closeout.md"}


def test_household_folder_is_plain_markdown_without_git_or_code(home):
    t = home / "Projects" / "packing"
    init(t, "Packing to move", "long", home, kind="household")
    assert files(t) == {"plan.md", "checklist.md", "closeout.md", "decisions.md"}
    assert not (t / ".git").exists()
    for rel in files(t):
        text = (t / rel).read_text()
        assert "```" not in text and max(len(line) for line in text.splitlines()) <= 100


def test_warden_no_go_stops_initialization_unless_overridden(home, tmp_path):
    rec = tmp_path / "rec"
    rec.mkdir()
    (rec / "verdict.md").write_text("# Warden verdict\n\n**Verdict: NO-GO.** The goal is undefined.\n")
    with pytest.raises(ip.Refused, match="NO-GO"):
        ip.initialize(home / "Projects" / "bad", "Bad", "short", record=rec, home=home)
    res = ip.initialize(home / "Projects" / "bad", "Bad", "short", record=rec, override="D-007", home=home)
    assert res["override"] == "D-007" and res["written"]


def test_goal_lines_come_from_the_record(home, tmp_path):
    rec = tmp_path / "rec2"
    rec.mkdir()
    (rec / "verdict.md").write_text("**Verdict: GO.** Fine.\n")
    (rec / "goal.md").write_text("# Goal\n\n**Goal:** File receipts by store and date (E-001)\n"
                                 "**Done when:** a scan is filed within a minute (E-007)\n")
    t = home / "Projects" / "receipts"
    ip.initialize(t, "Receipts", "immediate", record=rec, home=home)
    readme = (t / "README.md").read_text()
    assert "File receipts by store and date (E-001)" in readme and "within a minute (E-007)" in readme


def test_only_accepted_skills_are_installed(home):
    t = home / "Projects" / "skills"
    res = init(t, "Skills", "short", home, skills=["elicit", "warden"])
    statuses = {"elicit": ip.skill_status(ip.LIBRARY / "elicit"), "warden": ip.skill_status(ip.LIBRARY / "warden")}
    for s, status in statuses.items():
        if status == "ACCEPTED":
            assert s in res["installed"] and (t / ".claude/skills" / s / "SKILL.md").exists()
        else:
            assert any(r.startswith(s + ":") for r in res["refused"])
            assert not (t / ".claude/skills" / s).exists()


def test_cli_refusal_exit_code(home, monkeypatch):
    monkeypatch.setattr(ip.Path, "home", staticmethod(lambda: home))
    assert ip.main([str(home / "Documents" / "r"), "--name", "R", "--tier", "short", "--from", str(home / "record")]) == 2


def test_no_ideation_without_an_elicited_and_gated_record(home, tmp_path):
    with pytest.raises(ip.Refused, match="no elicitation record"):
        ip.initialize(home / "Projects" / "idea", "Idea", "short", home=home)
    ungated = tmp_path / "ungated"
    ungated.mkdir()
    (ungated / "items.md").write_text("| E-001 | Need | x | dump P1 | stated | L1 | active |\n")
    with pytest.raises(ip.Refused, match="no warden verdict"):
        ip.initialize(home / "Projects" / "idea", "Idea", "short", record=ungated, home=home)
    assert not (home / "Projects" / "idea").exists()
