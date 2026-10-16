"""Lay down a project's files for its tier: code or household (INIT-01 to INIT-08, HOME-01, INT-03, SAFE-03).

Status: PROPOSED (AI-drafted by Claude on 2026-10-08 from Luke's direction, D-006, D-014, D-015;
not reviewed by Luke).

Rules it enforces:
  - writes exactly the tier's files and never overwrites one (it skips existing files, so running it
    again at a higher tier adds only the missing documents)
  - never runs git (INIT-05); it prints the commands instead
  - refuses a code project inside an iCloud-synced folder (INIT-08); household folders may live anywhere
  - accepts only an elicited and warden-gated project (D-032): the record must hold a verdict.md;
    a NO-GO stops it unless an override decision is given (WARD-02)
  - installs only library skills whose SKILL.md says `Status: ACCEPTED` (SAFE-03)

Usage:
  python init_project.py TARGET --name NAME --tier immediate|short|long [--kind code|household]
                         --from ELICITATION_FOLDER [--skills elicit,warden] [--override-no-go D-nnn]
Exit code: 0 done, 2 refused.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE / "templates"
LIBRARY = HERE.parent  # .claude/skills
TIER_DOCS = {
    "immediate": "No SE documents: a goal line and a done-when line in the README.",
    "short": "README and SE-00 to SE-03.",
    "long": "README and SE-00 to SE-07.",
}


class Refused(Exception):
    pass


def icloud_roots(home: Path) -> list[Path]:
    return [home / "Library" / "Mobile Documents", home / "Library" / "CloudStorage", home / "Documents", home / "Desktop"]


def in_icloud(target: Path, home: Path) -> Path | None:
    t = target.expanduser().resolve()
    for root in icloud_roots(home):
        try:
            t.relative_to(root.resolve())
            return root
        except ValueError:
            continue
    return None


def goal_lines(record: Path | None) -> dict[str, str]:
    """Goal and done-when from the record's goal.md (Immediate) or cns.md, else placeholders."""
    vals = {"goal": "<!-- from the elicitation record -->", "done_when": "<!-- from the elicitation record -->"}
    if record and (record / "goal.md").exists():
        text = (record / "goal.md").read_text(encoding="utf-8")
        for key, label in (("goal", "Goal"), ("done_when", "Done when")):
            m = re.search(rf"\*\*{label}:\*\*\s*(.+)", text)
            if m:
                vals[key] = m.group(1).strip()
    return vals


def warden_verdict(record: Path | None) -> str | None:
    if not record or not (record / "verdict.md").exists():
        return None
    m = re.search(r"\*\*Verdict:\s*([A-Z-]+)", (record / "verdict.md").read_text(encoding="utf-8"))
    return m.group(1) if m else None


def content_hash(skill: Path) -> str:
    """Same hash as dashboard/install_skills.py: the content Luke accepted."""
    import hashlib
    skip = {"__pycache__", "calibration.csv", ".DS_Store", ".games-people-play"}
    h = hashlib.sha256()
    for f in sorted(p for p in skill.rglob("*") if p.is_file() and not (set(p.relative_to(skill).parts) & skip)):
        h.update(f.relative_to(skill).as_posix().encode() + b"\0" + f.read_bytes() + b"\0")
    return h.hexdigest()


def skill_status(skill_dir: Path) -> str:
    """ACCEPTED only if the status line says so and, where a ledger exists, the content still matches it (D-044)."""
    md = skill_dir / "SKILL.md"
    if not md.exists():
        return "missing"
    m = re.search(r"\*\*Status:\s*([A-Z]+)", md.read_text(encoding="utf-8"))
    status = m.group(1) if m else "unknown"
    ledger = skill_dir.parent / "accepted.json"
    if status == "ACCEPTED" and ledger.exists():
        import json
        try:
            want = json.loads(ledger.read_text(encoding="utf-8")).get(skill_dir.name, {}).get("sha256")
        except ValueError:
            want = None
        if want != content_hash(skill_dir):
            return "CHANGED-SINCE-ACCEPTANCE"
    return status


def render(text: str, values: dict[str, str]) -> str:
    for k, v in values.items():
        text = text.replace("{{" + k + "}}", v)
    return text


def plan_files(kind: str, tier: str) -> list[tuple[Path, Path]]:
    """(template file, relative output path) pairs for this kind and tier."""
    base = TEMPLATES / kind / tier
    pairs = [(f, f.relative_to(base)) for f in sorted(base.rglob("*")) if f.is_file()]
    if kind == "code":
        common = TEMPLATES / "code" / "common"
        pairs += [(f, f.relative_to(common)) for f in sorted(common.iterdir()) if f.is_file()]
    return pairs


def initialize(target: Path, name: str, tier: str, kind: str = "code", record: Path | None = None,
               skills: list[str] | None = None, override: str | None = None, home: Path | None = None,
               today: str | None = None) -> dict:
    home = home or Path.home()
    if kind == "code":
        cloud = in_icloud(target, home)
        if cloud:
            raise Refused(f"{target} is inside {cloud}, which iCloud syncs; a git repo there gets corrupted"
                          " (Games-People-Play D-008). Pick a folder under ~/Projects, ~/Research or ~/School.")
    if record is None or not Path(record).is_dir():
        raise Refused("no elicitation record. The initializer does no ideation: run /elicit, then /warden,"
                      " and pass --from <elicitation folder> (D-032).")
    verdict = warden_verdict(record)
    if verdict is None:
        raise Refused(f"{record} has no warden verdict (verdict.md). Run /warden first (D-032).")
    if verdict == "NO-GO" and not override:
        raise Refused("the warden's verdict is NO-GO. Luke can override it by logging a decision"
                      " and passing --override-no-go D-nnn.")
    values = {"name": name, "date": today or date.today().isoformat(), "tier": tier.capitalize(),
              "tier_docs": TIER_DOCS[tier],
              "elicitation": str(record), **goal_lines(record)}
    target.mkdir(parents=True, exist_ok=True)
    written, skipped = [], []
    for src, rel in plan_files(kind, tier):
        out = target / rel
        if out.exists():
            skipped.append(str(rel))
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render(src.read_text(encoding="utf-8"), values), encoding="utf-8")
        written.append(str(rel))
    installed, refused = [], []
    for s in skills or []:
        src = LIBRARY / s
        status = skill_status(src)
        if kind != "code":
            refused.append(f"{s}: household projects get no skills")
        elif status != "ACCEPTED":
            refused.append(f"{s}: status is {status}; only ACCEPTED skills leave the library (SAFE-03)")
        elif (target / ".claude" / "skills" / s).exists():
            skipped.append(f".claude/skills/{s}")
        else:
            shutil.copytree(src, target / ".claude" / "skills" / s,
                            ignore=shutil.ignore_patterns("__pycache__", "calibration.csv"))
            installed.append(s)
    return {"written": written, "skipped": skipped, "installed": installed, "refused": refused,
            "verdict": verdict, "override": override}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("target", type=Path)
    p.add_argument("--name", required=True)
    p.add_argument("--tier", choices=sorted(TIER_DOCS), required=True)
    p.add_argument("--kind", choices=["code", "household"], default="code")
    p.add_argument("--from", dest="record", type=Path, required=True,
                   help="elicitation folder holding verdict.md (and cns.md or goal.md)")
    p.add_argument("--skills", default="", help="comma-separated library skills to install")
    p.add_argument("--override-no-go", dest="override", help="decision id that overrides a warden NO-GO")
    args = p.parse_args(argv)
    try:
        res = initialize(args.target, args.name, args.tier, args.kind, args.record,
                         [s for s in args.skills.split(",") if s], args.override)
    except Refused as e:
        print(f"Refused: {e}")
        return 2
    print(f"Initialized {args.target} ({args.kind}, {args.tier}).")
    for key in ("written", "skipped", "installed", "refused"):
        if res[key]:
            print(f"  {key}: " + ", ".join(res[key]))
    if res["verdict"]:
        print(f"  warden verdict: {res['verdict']}" + (f" (overridden by {res['override']})" if res["override"] else ""))
    if args.kind == "code":
        print("  Not done (needs Luke's approval): git init, the first commit, the privacy hook.")
        print(f"    git -C \"{args.target}\" init && git -C \"{args.target}\" add -A")
    return 0


if __name__ == "__main__":
    sys.exit(main())
