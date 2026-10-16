"""T-11 (SE-03): the closeout draft cites recorded files only and creates no tag."""

import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


co = load("closeout", ROOT / ".claude" / "skills" / "closeout" / "closeout.py")
ip = load("init_project", ROOT / ".claude" / "skills" / "initialize" / "init_project.py")


def project(tmp_path):
    p = tmp_path / "Projects" / "demo"
    gated = tmp_path / "gated"
    gated.mkdir()
    (gated / "verdict.md").write_text("**Verdict: GO.** Fine.\n")
    ip.initialize(p, "Demo", "short", record=gated, home=tmp_path)
    se = p / "docs" / "se"
    (se / "SE-03_requirements.md").write_text(
        "| ID | Requirement | Method | Trace | Allocated | Verified by | Status |\n|---|---|---|---|---|---|---|\n"
        "| R-1 | The tool shall file a scan. | T | E-001 | Tool | T-1 | VERIFIED (T-1, runs/r1.md) |\n"
        "| R-2 | The tool shall rename by date. | T | E-002 | Tool | T-2 | PROPOSED |\n")
    (se / "SE-00_project_plan.md").write_text(
        "# SE-00\n\n## Open decisions\n\n| # | Decision | Owner | Needed by |\n|---|---|---|---|\n"
        "| 1 | **Storage.** Local or cloud. | Luke | G1 |\n| 2 | ~~**Name.**~~ Closed by D-003. | Luke | — |\n\n## Change control\n")
    rec = se / "elicitation" / "2026-10-09"
    rec.mkdir(parents=True)
    (rec / "verdict.md").write_text("**Verdict: GO.** Fine.\n")
    (rec / "time.md").write_text("| **suggested hours h\\* = need x ln(r / c)** | **4.5 h** |\n")
    (p / "runs").mkdir()
    (p / "runs" / "r1.md").write_text("result\n")
    (p / ".claude" / "skills" / "scanfiler").mkdir(parents=True)
    return p


def test_draft_lists_every_requirement_decision_and_result(tmp_path):
    p = project(tmp_path)
    text = co.draft(p, actual=6, library=ROOT, today="2026-10-20")
    assert "| R-1 |" in text and "| R-2 |" in text and "VERIFIED" in text
    assert re.search(r"\| 1 \| Storage\. Local or cloud\. \| no \|", text)
    assert re.search(r"\| 2 \| Name\. Closed by D-003\. \| yes \|", text)
    assert "runs/r1.md" in text and "Warden verdict: GO" in text
    assert "Suggested: 4.5 h" in text and "Error: +1.5 h" in text
    assert "skill scanfiler" in text
    assert "closeout section in SE-00" in text and "## Closeout counts" in text
    assert "Q3. In your own words" in text and "Why are you closing it now?" in text
    answers = re.findall(r"^> (.*)$", text, re.M)
    assert answers and all(a == "" for a in answers)  # no answer is drafted for Luke


def test_uninitialized_project_is_refused(tmp_path):
    bare = tmp_path / "bare"
    bare.mkdir()
    (bare / "notes.md").write_text("an idea\n")
    assert co.main([str(bare), "--out", str(tmp_path / "x.md"), "--library", str(ROOT)]) == 2
    assert not (tmp_path / "x.md").exists()


def test_cli_never_overwrites_and_never_tags(tmp_path):
    p = project(tmp_path)
    out = tmp_path / "c.md"
    assert co.main([str(p), "--out", str(out), "--library", str(ROOT)]) == 0
    assert co.main([str(p), "--out", str(out), "--library", str(ROOT)]) == 2
    src = (ROOT / ".claude" / "skills" / "closeout" / "closeout.py").read_text()
    assert "subprocess" not in src  # it cannot run git at all
