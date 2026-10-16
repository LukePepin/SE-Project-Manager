"""Draft a project's closeout from its recorded files only (CLOSE-01 to CLOSE-04, TIME-03).

Status: PROPOSED (AI-drafted by Claude on 2026-10-08 from Luke's direction, D-007 and D-016;
not reviewed by Luke).

It collects, without interpreting:
  - every SE-03 requirement with its current status (CLOSE-03)
  - every SE-00 open decision, with a column for Luke: closed, dropped or carried forward
  - the elicitation record, the warden's verdict, and the suggested and actual hours (TIME-03)
  - the recorded result files it can find (audit/, runs/, results/, docs/se/evidence/), by path (CLOSE-01)
  - the project's own skills and commands that are not in the library: candidates to harvest (CLOSE-04)
It refuses a project that was never fully initialized (D-031). It writes no statement, summary,
lessons or interpretation: it lists the closeout questions, and Luke's answers go under them verbatim
(CLOSE-02, D-031). A git tag is proposed and never created.

Usage:
  python closeout.py PROJECT [--actual-hours 5.5] [--library ~/Projects/Games-People-Play] [--out FILE]
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

LIBRARY = Path(__file__).resolve().parents[3]
RESULT_DIRS = ["audit", "runs", "results", "docs/se/evidence"]
REASONS = ["about two hours of interest left", "demo done", "deadline reached", "learned what I wanted",
           "warden or time equation said stop", "other"]
QUESTIONS = [
    "Why are you closing it now? (" + "; ".join(REASONS) + ")",
    "Did it meet its done-when line and the thresholds of its measures? Where not, why not?",
    "In your own words, what is this project and what did it achieve? (the closing statement)",
    "What did you learn: the how and why, not the implementation details?",
    "What would you do differently?",
    "What transfers to other projects, and should any of it go into the library?",
    "Was it worth the hours it took?",
]


class NotInitialized(Exception):
    pass


def check_initialized(project: Path) -> str:
    """Return the kind, or raise: a closeout needs the documents to review (D-031)."""
    se = project / "docs" / "se"
    if (project / "plan.md").exists() and not se.exists():
        return "household"
    if any(se.glob("SE-00*")) and any(se.glob("SE-03*")):
        return "code"
    if "**Goal:**" in (project / "README.md").read_text(encoding="utf-8") if (project / "README.md").exists() else False:
        return "code"
    raise NotInitialized(f"{project} has no SE set, goal line or household plan. Run /elicit, /warden and"
                         " /initialize first, or close it informally.")


def table_rows(text: str, pattern: str) -> list[list[str]]:
    rows = []
    for line in text.splitlines():
        if re.match(pattern, line):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    return rows


def requirements(se03: Path) -> list[tuple[str, str, str]]:
    if not se03.exists():
        return []
    out = []
    for cells in table_rows(se03.read_text(encoding="utf-8"), r"^\| [A-Z]+-\d+ \| [A-Z]"):
        if len(cells) >= 3:
            text = cells[1] if len(cells[1]) <= 90 else cells[1][:87] + "..."
            out.append((cells[0], text, cells[-1]))
    return out


def open_decisions(se00: Path) -> list[tuple[str, str, bool]]:
    if not se00.exists():
        return []
    parts = se00.read_text(encoding="utf-8").split("## Open decisions", 1)
    if len(parts) < 2:
        return []
    body = parts[1].split("\n## ", 1)[0]
    out = []
    for cells in table_rows(body, r"^\| (?:OD-)?\d+ \|"):
        text = re.sub(r"\*\*|~~", "", cells[1])
        out.append((cells[0], text if len(text) <= 90 else text[:87] + "...", "~~" in cells[1]))
    return out


def harvest_candidates(project: Path, library: Path) -> list[str]:
    have = {p.name for p in (library / ".claude" / "skills").glob("*")} | \
           {p.stem for p in (library / ".claude" / "commands").glob("*.md")}
    found = [f"skill {p.name}" for p in (project / ".claude" / "skills").glob("*") if p.is_dir() and p.name not in have]
    found += [f"command /{p.stem}" for p in (project / ".claude" / "commands").glob("*.md") if p.stem not in have]
    return sorted(found)


def suggested_hours(project: Path) -> float | None:
    for rec in sorted(project.glob("docs/se/elicitation/*/time.md"), reverse=True):
        m = re.search(r"\*\*suggested hours h\\\*[^|]*\|\s*\*\*([\d.]+) h", rec.read_text(encoding="utf-8"))
        if m:
            return float(m.group(1))
    return None


def draft(project: Path, actual: float | None = None, library: Path = LIBRARY, today: str | None = None) -> str:
    today = today or date.today().isoformat()
    project = project.resolve()
    check_initialized(project)
    se = project / "docs" / "se"
    se00 = next(iter(sorted(se.glob("SE-00*.md"))), se / "SE-00_project_plan.md")
    se03 = next(iter(sorted(se.glob("SE-03*.md"))), se / "SE-03_requirements.md")
    tier = "Long" if any(se.glob("SE-04*")) else "Short" if se00.exists() else "Immediate"
    where = {"Long": "a closeout section in SE-07", "Short": "a closeout section in SE-00",
             "Immediate": "a closeout note in the README"}[tier]
    reqs, decs = requirements(se03), open_decisions(se00)
    records = sorted(project.glob("docs/se/elicitation/*/"))
    verdict = ""
    if records:
        m = re.search(r"\*\*Verdict:\s*([A-Z-]+)", (records[-1] / "verdict.md").read_text(encoding="utf-8")) \
            if (records[-1] / "verdict.md").exists() else None
        verdict = m.group(1) if m else ""
    results = [p.relative_to(project).as_posix() for d in RESULT_DIRS for p in sorted((project / d).rglob("*"))
               if p.is_file()]
    sug = suggested_hours(project)
    items = []
    if records and (records[-1] / "items.md").exists():
        items = [line for line in (records[-1] / "items.md").read_text(encoding="utf-8").splitlines()
                 if re.match(r"^\| E-\d+ \|", line)]
    decisions = len(re.findall(r"^\| D-\d+ \|", se00.read_text(encoding="utf-8"), re.M)) if se00.exists() else 0
    counts: dict[str, int] = {}
    for _, _, s in reqs:
        key = s.split(" ")[0]
        counts[key] = counts.get(key, 0) + 1
    out = [
        f"# Closeout draft: {project.name}, {today}",
        "",
        f"**Status: DRAFT.** Gathered by `closeout.py` from recorded files only. Tier {tier}: once Luke approves,"
        f" this goes into {where} (D-028). Claude wrote none of the answers below; they are Luke's, verbatim (D-031).",
        "",
        "## Closeout counts",
        "",
        f"- Requirements: {len(reqs)}; decisions logged: {decisions}; open decisions: {sum(1 for d in decs if not d[2])}",
        f"- Elicitation items: {len(items)}, {sum(1 for i in items if '| stated |' in i)} in Luke's words",
        "",
        "## Final requirement statuses",
        "",
        ("Counts: " + ", ".join(f"{n} {k}" for k, n in sorted(counts.items()))) if reqs else "No SE-03 requirements found.",
        "",
    ]
    if reqs:
        out += ["| Requirement | Text | Status at closeout |", "|---|---|---|",
                *[f"| {i} | {t} | {s} |" for i, t, s in reqs], ""]
    out += ["## Open decisions", ""]
    if decs:
        out += ["| # | Decision | Already closed? | Luke: closed, dropped or carried forward |", "|---|---|---|---|",
                *[f"| {n} | {t} | {'yes' if c else 'no'} | |" for n, t, c in decs], ""]
    else:
        out += ["None recorded.", ""]
    out += [
        "## Time",
        "",
        f"- Suggested: {f'{sug:g} h' if sug is not None else 'none recorded'}",
        f"- Actual: {f'{actual:g} h' if actual is not None else 'Luke to fill in'}",
    ]
    if sug is not None and actual is not None:
        out += [f"- Error: {actual - sug:+g} h. Record it: `time_equation.py record --project \"{project.name}\""
                f" --suggested {sug:g} --actual {actual:g}`"]
    out += ["", "## Record", "",
            f"- Elicitation: {records[-1].relative_to(project).as_posix() if records else 'none'}",
            f"- Warden verdict: {verdict or 'none'}",
            "- Result files: " + (", ".join(results) if results else "none found"), "",
            "## Harvest candidates (offer each for the library)", ""]
    cands = harvest_candidates(project, library)
    out += [*[f"- {c}" for c in cands]] if cands else ["None: every skill here is already in the library."]
    out += ["", "## Closeout questions (Luke answers; Claude never drafts these)", ""]
    for n, q in enumerate(QUESTIONS, 1):
        out += [f"**Q{n}. {q}**", "", "> ", ""]
    out += ["## Proposed, not run", "", f"- `git tag -a closeout-{today} -m \"Closeout\"` (only after Luke approves)", ""]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("project", type=Path)
    p.add_argument("--actual-hours", type=float)
    p.add_argument("--library", type=Path, default=LIBRARY)
    p.add_argument("--out", type=Path)
    args = p.parse_args(argv)
    try:
        text = draft(args.project, args.actual_hours, args.library)
    except NotInitialized as e:
        print(f"Refused: {e}")
        return 2
    out = args.out or args.project / "docs" / "se" / f"closeout_{date.today().isoformat()}.md"
    if out.exists():
        print(f"Refused: {out} exists; pass --out to write elsewhere.")
        return 2
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text + "\n", encoding="utf-8")
    print(f"Wrote {out}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
