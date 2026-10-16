"""DASH-01, WARD-03 and MAINT-01 (SE-03): the static dashboard."""

import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_dashboard", ROOT / "dashboard" / "build_dashboard.py")
bd = importlib.util.module_from_spec(spec)
sys.modules["build_dashboard"] = bd
spec.loader.exec_module(bd)
spec2 = importlib.util.spec_from_file_location("init_project", ROOT / ".claude" / "skills" / "initialize" / "init_project.py")
ip = importlib.util.module_from_spec(spec2)
sys.modules["init_project"] = ip
spec2.loader.exec_module(ip)


def build(tmp_path):
    root = tmp_path / "Projects"
    home = tmp_path
    gated = tmp_path / "gated"
    gated.mkdir()
    (gated / "verdict.md").write_text("**Verdict: GO.** Fine.\n")
    ip.initialize(root / "Short<One>", "Short<One>", "short", record=gated, home=home)
    ip.initialize(root / "attic", "Attic", "short", kind="household", record=gated, home=home)
    rec = root / "Short<One>" / "docs" / "se" / "elicitation" / "2026-10-09"
    rec.mkdir(parents=True)
    (rec / "items.md").write_text(
        "| E-001 | Need | x | dump P1 | stated | L1 | active |\n| E-002 | Need | y | inferred from E-001 | inferred | L1 | active |\n")
    (rec / "verdict.md").write_text("**Verdict: NO-GO.** Undefined goal.\n")
    (root / "notes").mkdir()  # not a project: ignored
    out = tmp_path / "index.html"
    assert bd.main(["--roots", str(root), "--repo", str(ROOT), "--out", str(out)]) == 0
    return out.read_text()


def test_projects_and_verdicts_are_listed_without_a_skill_table(tmp_path):
    page = build(tmp_path)
    assert "Short&lt;One&gt;" in page and "<One>" not in page  # escaped
    assert "attic" in page and "Hands-on" in page and "Technical" in page
    assert "NO-GO" in page and "<table" not in page  # no skills table (10/9)
    assert ">notes<" not in page
    one = next(p for p in bd.projects([tmp_path / "Projects"]) if p.name == "Short<One>")
    detail_page = bd.pages().project_page(one, bd.detail(one), "tok")
    assert "2 items, 1 in your words" in detail_page and "The warden said no" in detail_page
    attic = next(p for p in bd.projects([tmp_path / "Projects"]) if p.name == "attic")
    assert "/elicit short " in bd.pages().project_page(attic, bd.detail(attic), "tok")
    assert "Short&lt;One&gt;" in detail_page and "<One>" not in detail_page


def test_page_is_self_contained(tmp_path):
    page = build(tmp_path)
    assert not re.search(r"""(src|href)=["']https?://""", page)
    assert "<script" not in page


def test_explain_back_counting():
    text = ("**Explain-back (Luke):** why?\n\n>\n\n## Next\n"
            "**Explain-back (Luke):** how?\n\n> Because it works.\n")
    assert bd.explain_backs(text) == (2, 1)


def test_builder_uses_only_the_standard_library():
    src = (ROOT / "dashboard" / "build_dashboard.py").read_text()
    imports = set(re.findall(r"^(?:import|from) (\w+)", src, re.M))
    assert imports <= {"__future__", "argparse", "hashlib", "html", "json", "os", "re", "subprocess", "sys", "webbrowser",
                       "dataclasses", "datetime", "pathlib", "urllib"}


def test_states_and_groups(tmp_path):
    from datetime import date
    p = bd.Project(name="x", path=tmp_path, tier="Short", verdict="GO", active="2026-10-08", hook="library")
    assert bd.state(p, date(2026, 10, 9)) == ("green", "on track")
    assert bd.state(bd.Project(name="x", path=tmp_path, tier="idea", active="2026-10-08"), date(2026, 10, 9))[0] == "yellow"
    p.verdict = "NO-GO"
    assert bd.state(p, date(2026, 10, 9))[0] == "red"
    p.verdict, p.active = "GO", "2026-08-01"
    assert bd.state(p, date(2026, 10, 9)) == ("red", "no activity for 69 days")
    p.closed = True
    assert bd.state(p, date(2026, 10, 9))[0] == "closed"


def test_closeout_detection(tmp_path):
    f = tmp_path / "SE-07.md"
    f.write_text("## Closeout\n\n<!-- written by the closeout tool -->\n\n## Next\n")
    assert not bd.has_closeout(f)
    f.write_text("## Closeout\n\nFinished 10/20: worth it.\n")
    assert bd.has_closeout(f)


def test_page_groups_by_folder_and_signature_tracks_changes(tmp_path):
    page = build(tmp_path)
    assert 'Projects<span class="cnt">' in page and '<section class="group">' in page
    projs = bd.projects([tmp_path / "Projects"])
    before = bd.signature(projs)
    (projs[0].path / "notes.md").write_text("# n\n\n## 2026-10-09\n\nnew\n")
    assert bd.signature(bd.projects([tmp_path / "Projects"])) != before
