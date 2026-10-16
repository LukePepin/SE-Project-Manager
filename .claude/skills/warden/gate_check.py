"""The warden's fixed checks: does an elicitation record define a project worth starting?

Status: PROPOSED (AI-drafted by Claude on 2026-10-08 from Luke's direction, D-015 and D-022;
not reviewed by Luke). The thresholds below are Claude's proposals.

Reads `items.md` (and `prioritization.md`, if present) from an elicitation folder written by
/elicit, runs the checks, and prints a Markdown report. Only stated items count: an item Claude
inferred never satisfies a check, so the warden cannot pass a project on Claude's words.

Each check fails to one of two levels:
  no-go   the goal is undefined, cannot be tested, or is mostly Claude's (WARD-02)
  shrink  the project is defined but loose: no threshold, no scope edge, no cost, no stop rule,
          or the Musts do not fit the budget

Verdict: no-go if any no-go check fails, else shrink if any shrink check fails, else go.
Exit code: 0 go, 1 shrink, 2 no-go. The /warden skill adds judgment on top (WARD-04).

Usage:
  python gate_check.py docs/se/elicitation/<date>/ [--max-inferred 0.5] [--out verdict_checks.md]
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

GO, SHRINK, NOGO = "go", "shrink", "no-go"
EXIT = {GO: 0, SHRINK: 1, NOGO: 2}


@dataclass
class Item:
    id: str
    type: str
    statement: str
    source: str
    basis: str
    lenses: set[str]
    status: str

    @property
    def live(self) -> bool:
        return not self.status.startswith("dropped")

    @property
    def stated(self) -> bool:
        return self.basis == "stated"


@dataclass
class Check:
    name: str
    passed: bool
    fails_to: str  # SHRINK or NOGO
    why: str
    evidence: list[str]


def parse_items(path: str | Path) -> list[Item]:
    """Rows of the items.md table. The statement may contain pipes, so fields are taken from both ends."""
    items = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not re.match(r"^\| E-\d+ \|", line):
            continue
        parts = [p.strip() for p in line.strip().strip("|").split("|")]
        if len(parts) < 7:
            raise ValueError(f"{path}: malformed row: {line[:80]}")
        lenses = {x.strip() for x in parts[-2].split(",") if x.strip().startswith("L")}
        items.append(
            Item(
                id=parts[0],
                type=parts[1],
                statement="|".join(parts[2:-4]).strip(),
                source=parts[-4],
                basis=parts[-3],
                lenses=lenses,
                status=parts[-1],
            )
        )
    if not items:
        raise ValueError(f"{path}: no E-nnn rows")
    return items


def run_checks(items: list[Item], prioritization: str | None = None, max_inferred: float = 0.5) -> list[Check]:
    live = [i for i in items if i.live]
    stated = [i for i in live if i.stated]

    def ids(xs):
        return [i.id for i in xs]

    purpose = [i for i in stated if i.type == "Need" and "L1" in i.lenses]
    measures = [i for i in stated if i.type == "Measure"]
    thresholds = [i for i in measures if "threshold" in i.statement.lower()]
    testable = [i for i in stated if "L9" in i.lenses]
    outs = [i for i in stated if i.type == "Out"]
    cost = [i for i in stated if "L10" in i.lenses]
    stop = [i for i in stated if "L14" in i.lenses]
    needs = [i for i in live if i.type == "Need"]
    inferred_needs = [i for i in needs if i.basis == "inferred"]  # context items (D-039) are not Claude's guesses
    share = len(inferred_needs) / len(needs) if needs else 1.0

    checks = [
        Check("Purpose", bool(purpose), NOGO,
              "a stated Need on what goes wrong today (L1): the project's purpose, task and role", ids(purpose)),
        Check("Success measure", bool(measures), NOGO,
              "a stated Measure: without one, nobody can tell whether the project worked", ids(measures)),
        Check("Testable", bool(testable), NOGO,
              "a stated item on how it will be tested (L9)", ids(testable)),
        Check("Luke's words", share <= max_inferred, NOGO,
              f"at most {max_inferred:.0%} of the live Needs inferred by Claude"
              f" (now {len(inferred_needs)} of {len(needs)}, {share:.0%})", ids(inferred_needs)),
        Check("Threshold", bool(thresholds), SHRINK,
              "a Measure with a threshold: the least Luke would accept", ids(thresholds)),
        Check("Scope edge", bool(outs), SHRINK,
              "a stated Out item: something the project will not do", ids(outs)),
        Check("Cost", bool(cost), SHRINK,
              "a stated item on hours or cost (L10)", ids(cost)),
        Check("Stop rule", bool(stop), SHRINK,
              "a stated item on what would stop or shrink it (L14)", ids(stop)),
    ]
    if prioritization is not None:
        fits = "**Infeasible:**" not in prioritization
        checks.append(Check("Musts fit the budget", fits, SHRINK,
                            "the Must items and their prerequisites fit the hours budget (prioritization.md)", []))
    return checks


def verdict(checks: list[Check]) -> str:
    failed = {c.fails_to for c in checks if not c.passed}
    return NOGO if NOGO in failed else SHRINK if SHRINK in failed else GO


def render(folder: Path, checks: list[Check], result: str, max_inferred: float) -> str:
    out = [
        "# Warden checks",
        "",
        "**Status: PROPOSED.** Generated by `gate_check.py` from"
        f" `{folder.as_posix()}/items.md`. Only stated items count. The `/warden` skill adds judgment;"
        " Luke decides, and a no-go stands unless Luke overrides it in the decision log (WARD-02).",
        "",
        f"**Checks verdict: {result.upper()}**",
        "",
        "| Check | Result | Fails to | Needs | Evidence |",
        "|---|---|---|---|---|",
    ]
    for c in checks:
        ev = ", ".join(c.evidence[:8]) + (" …" if len(c.evidence) > 8 else "")
        out.append(f"| {c.name} | {'pass' if c.passed else '**fail**'} | {c.fails_to} | {c.why} | {ev or '—'} |")
    out += ["", f"Thresholds are Claude's proposals: Luke's-words limit {max_inferred:.0%}."]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("folder", help="elicitation folder holding items.md")
    p.add_argument("--max-inferred", type=float, default=0.5)
    p.add_argument("--out", help="write the report here instead of stdout")
    args = p.parse_args(argv)

    folder = Path(args.folder)
    items = parse_items(folder / "items.md")
    pz = folder / "prioritization.md"
    checks = run_checks(items, pz.read_text(encoding="utf-8") if pz.exists() else None, args.max_inferred)
    result = verdict(checks)
    report = render(folder, checks, result, args.max_inferred)
    if args.out:
        Path(args.out).write_text(report + "\n", encoding="utf-8")
    else:
        print(report)
    return EXIT[result]


if __name__ == "__main__":
    sys.exit(main())
