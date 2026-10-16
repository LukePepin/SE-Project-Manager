"""D-039: the Docket context loader for /elicit."""

import importlib.util
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("context_pack", ROOT / ".claude" / "skills" / "elicit" / "context_pack.py")
cp = importlib.util.module_from_spec(spec)
sys.modules["context_pack"] = cp
spec.loader.exec_module(cp)


def docket(tmp_path):
    d = tmp_path / "Docket"
    (d / "claude" / "reviews").mkdir(parents=True)
    (d / "Hierarchy of Projects.md").write_text("| 1 | Fitness | boxing |\n")
    (d / "agenda.md").write_text("# agenda\n\n## Parked ideas\n\n- [10/1] learn welding\n")
    (d / "docket_memory.md").write_text(
        "# Docket continuity\n\n## 2026-09-01 — old\n\nold decision\n\n## 2026-10-05 — recent\n\nnew decision\n")
    (d / "claude" / "reviews" / "2026-09-27.md").write_text("# old review\n\n## Coming-week capacity\n\nold\n")
    (d / "claude" / "reviews" / "2026-10-04.md").write_text(
        "# Weekly Review\n\n## Coming-week capacity — 10/4–10/11\n\n6 free hours\n\n### P1 count\n\n3\n\n"
        "## Inbox to zero\n\nskip me\n\n## Final weekly allocation\n\ntop\n\n### All deep-work blocks — 10/5\n\nTue 7-9\n")
    (d / "claude" / "reviews" / "goals-2026-10.md").write_text("# Goals\n\n## Next actions and feasibility\n\nchess 1000\n")
    return d


def test_selects_current_context_and_labels_sources(tmp_path):
    text, used = cp.build(docket(tmp_path), days=14, today=date(2026, 10, 9))
    assert "fitness" in text.lower() and "learn welding" in text
    assert "new decision" in text and "old decision" not in text
    assert "6 free hours" in text and "2026-10-04.md, 5 days old" in text and "skip me" not in text
    assert "Tue 7-9" in text and "chess 1000" in text and "\nold\n" not in text
    assert "docket: docket_memory.md § 2026-10-05 — recent" in used
    assert "**Context, not answers.**" in text


def test_missing_docket_is_not_an_error(tmp_path):
    text, used = cp.build(tmp_path / "nope", today=date(2026, 10, 9))
    assert used == [] and "No Docket files found" in text


def test_context_is_git_ignored_in_code_projects(tmp_path):
    proj = tmp_path / "proj"
    (proj / ".git").mkdir(parents=True)
    out = proj / "docs" / "se" / "elicitation" / "2026-10-09"
    assert cp.main([str(out), "--docket", str(docket(tmp_path)), "--project", str(proj), "--today", "2026-10-09"]) == 0
    assert (out / "context.md").exists()
    assert cp.IGNORE_LINE in (proj / ".gitignore").read_text()
    assert not cp.ignore_in_repo(proj)  # only once
    household = tmp_path / "attic"
    household.mkdir()
    assert not cp.ignore_in_repo(household)


def test_reads_files_only():
    src = (ROOT / ".claude" / "skills" / "elicit" / "context_pack.py").read_text()
    assert "urllib" not in src and "subprocess" not in src and "requests" not in src
