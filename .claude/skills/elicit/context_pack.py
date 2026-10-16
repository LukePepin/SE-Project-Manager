"""Gather Luke's life context from Docket before /elicit asks anything (D-039).

Status: ACCEPTED as direction (Luke, 10/9: load "the ChatGPT/Docket/ file to read those .md files on my
life so I don't have to answer what else is going on"). Selection rules are Claude's defaults.

Docket (~/ChatGPT/Docket) is Luke's private chief-of-staff repo: Todoist is its execution surface and
Google Calendar its capacity. This copies, verbatim and labeled by source, the parts that say what else
is going on:
  - Hierarchy of Projects.md     areas, baselines and seasonal projects
  - agenda.md                    parked items
  - docket_memory.md             sections dated within --days (confirmed decisions)
  - the latest weekly review     capacity, allocation, deep-work blocks, anchors, next actions, waiting-for
  - the latest monthly goal pass next actions, drift, decision log
The weekly review is also the Todoist snapshot when no Todoist connector is available; its age is shown.

It reads files only, never Todoist, Calendar or the network, and writes one file: <out>/context.md.
With --project, it git-ignores context.md in that project's repo so personal context is never committed.

Usage:
  python context_pack.py OUT_FOLDER [--docket ~/ChatGPT/Docket] [--days 14] [--project PROJECT] [--today YYYY-MM-DD]
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date, timedelta
from pathlib import Path

DEFAULT_DOCKET = Path.home() / "ChatGPT" / "Docket"
REVIEW_KEYS = ("capacity", "allocation", "deep-work", "anchors", "one next action", "waiting for", "working week")
GOAL_KEYS = ("next actions", "drift", "decision log")
IGNORE_LINE = "**/elicitation/*/context.md"
MAX_SECTION = 6000


def sections(text: str, level: int = 2) -> list[tuple[str, str]]:
    """(heading, body) pairs for headings of exactly this level; a body stops at any heading of this level or higher."""
    out, head, buf, inside = [], "", [], False
    for line in text.splitlines():
        m = re.match(r"^(#{1,6}) (.*)$", line)
        if m and len(m.group(1)) <= level:
            if inside:
                out.append((head, "\n".join(buf).strip()))
            inside = len(m.group(1)) == level
            head, buf = m.group(2).strip(), []
        elif inside:
            buf.append(line)
    if inside:
        out.append((head, "\n".join(buf).strip()))
    return out


def clip(text: str) -> str:
    return text if len(text) <= MAX_SECTION else text[:MAX_SECTION] + "\n\n[... clipped; read the source for the rest]"


def dated(name: str) -> date | None:
    m = re.search(r"(\d{4}-\d{2}-\d{2})", name)
    return date.fromisoformat(m.group(1)) if m else None


def latest(folder: Path, pattern: str) -> Path | None:
    files = [f for f in folder.glob(pattern) if dated(f.name) or re.search(r"\d{4}-\d{2}", f.name)]
    return max(files, key=lambda f: f.name) if files else None


def build(docket: Path, days: int = 14, today: date | None = None) -> tuple[str, list[str]]:
    today = today or date.today()
    parts, used = [], []

    def add(label: str, body: str):
        if body.strip():
            parts.append(f"## {label}\n\n{clip(body.strip())}\n")
            used.append(label)

    hier = docket / "Hierarchy of Projects.md"
    if hier.exists():
        add("docket: Hierarchy of Projects.md", hier.read_text(encoding="utf-8"))
    agenda = docket / "agenda.md"
    if agenda.exists():
        for head, body in sections(agenda.read_text(encoding="utf-8")):
            if "parked" in head.lower():
                add(f"docket: agenda.md § {head}", body)
    memory = docket / "docket_memory.md"
    if memory.exists():
        since = today - timedelta(days=days)
        for head, body in sections(memory.read_text(encoding="utf-8")):
            d = dated(head)
            if d and d >= since:
                add(f"docket: docket_memory.md § {head}", body)
    reviews = docket / "claude" / "reviews"
    weekly = max((f for f in reviews.glob("20??-??-??.md")), key=lambda f: f.name, default=None) if reviews.exists() else None
    if weekly:
        age = (today - dated(weekly.name)).days
        parts.append(f"## Todoist and capacity snapshot\n\nFrom the latest weekly review, {weekly.name},"
                     f" {age} days old. Prefer a live Todoist connector when one is available.\n")
        for level in (2, 3):
            for head, body in sections(weekly.read_text(encoding="utf-8"), level):
                if any(k in head.lower() for k in REVIEW_KEYS):
                    add(f"docket: claude/reviews/{weekly.name} § {head}", body.split("\n### ")[0])
    goals = max((f for f in reviews.glob("goals-????-??.md")), key=lambda f: f.name, default=None) if reviews.exists() else None
    if goals:
        for head, body in sections(goals.read_text(encoding="utf-8")):
            if any(k in head.lower() for k in GOAL_KEYS):
                add(f"docket: claude/reviews/{goals.name} § {head}", body)
    header = (
        "# Context: what else is going on\n\n"
        f"**Context, not answers.** Copied verbatim from Luke's private Docket repo ({docket}) on {today},"
        " by `context_pack.py`. Items drawn from here are tagged `context`, never `stated`. Not for git: it is"
        " ignored in this project.\n\n"
        "**Live data, added by Claude below if a connector is available (read only):** `## Calendar` (busy hours"
        " per week, next 4 weeks) and `## Todoist` (open tasks and projects due in the next 4 weeks).\n"
    )
    if not parts:
        return header + "\nNo Docket files found.\n", used
    return header + "\n" + "\n".join(parts), used


def ignore_in_repo(project: Path) -> bool:
    """Add the context.md pattern to the project's .gitignore if it is a git repo. True if added."""
    if not (project / ".git").exists():
        return False
    gi = project / ".gitignore"
    lines = gi.read_text(encoding="utf-8").splitlines() if gi.exists() else []
    if IGNORE_LINE in lines:
        return False
    gi.write_text("\n".join(lines + [IGNORE_LINE]) + "\n", encoding="utf-8")
    return True


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("out", type=Path, help="the elicitation folder")
    p.add_argument("--docket", type=Path, default=DEFAULT_DOCKET)
    p.add_argument("--days", type=int, default=14, help="docket_memory sections from this many days back")
    p.add_argument("--project", type=Path, help="project folder; its .gitignore gets the context.md pattern")
    p.add_argument("--today", type=date.fromisoformat)
    args = p.parse_args(argv)
    text, used = build(args.docket.expanduser(), args.days, args.today)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "context.md").write_text(text, encoding="utf-8")
    print(f"Wrote {args.out / 'context.md'}: {len(used)} Docket excerpts, {len(text) // 1000} kB.")
    if args.project and ignore_in_repo(args.project):
        print(f"Added '{IGNORE_LINE}' to {args.project / '.gitignore'}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
