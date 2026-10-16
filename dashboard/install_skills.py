"""Make the library's accepted skills available in every Claude Code chat (SAFE-03, D-044).

Status: DECIDED (D-038 asked for it; D-044 tied it to accepted content after the 10/9 audit, finding B1).

Claude Code loads project skills from <repo>/.claude/skills and user skills from ~/.claude/skills.
A skill leaves this repo only when both hold:
  - its SKILL.md status line says ACCEPTED (Luke answered its explain-back), and
  - its content is byte-for-byte what was accepted: the hash recorded in .claude/skills/accepted.json.
A skill edited after acceptance is "changed since acceptance" and is withdrawn from ~/.claude/skills until
Luke answers a new explain-back and it is re-accepted (--accept). Installs are pinned copies, not links,
so an edit here never reaches other chats on its own. It never overwrites a skill it did not install.
Chats opened in this repo always see every skill, accepted or not.

Usage:
  python dashboard/install_skills.py              show each skill's state
  python dashboard/install_skills.py --install    copy in accepted skills; withdraw changed or unaccepted ones
  python dashboard/install_skills.py --accept NAME --by "Luke, explain-back 2026-10-09"
                                                  record NAME's current content as accepted (only after
                                                  Luke answered its explain-back)
  python dashboard/install_skills.py --remove     remove everything this script installed
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MARK = ".games-people-play"  # dropped into installed copies; holds the content hash
IGNORE = {"__pycache__", "calibration.csv", ".DS_Store", MARK}


def user_dir(home: Path | None = None) -> Path:
    return (home or Path.home()) / ".claude" / "skills"


def skills_dir(repo: Path) -> Path:
    return repo / ".claude" / "skills"


def ledger_path(repo: Path) -> Path:
    return skills_dir(repo) / "accepted.json"


def content_hash(skill: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(p for p in skill.rglob("*") if p.is_file() and not (set(p.relative_to(skill).parts) & IGNORE)):
        h.update(f.relative_to(skill).as_posix().encode() + b"\0" + f.read_bytes() + b"\0")
    return h.hexdigest()


def ledger(repo: Path = REPO) -> dict:
    try:
        return json.loads(ledger_path(repo).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def status_line(skill: Path) -> str:
    m = re.search(r"\*\*Status:\s*([A-Z]+)", (skill / "SKILL.md").read_text(encoding="utf-8"))
    return m.group(1) if m else "?"


def review_state(repo: Path = REPO) -> dict[str, str]:
    """skill -> 'accepted', 'changed since acceptance', or its status line (REVIEWED, PROPOSED...)."""
    led, out = ledger(repo), {}
    for md in sorted(skills_dir(repo).glob("*/SKILL.md")):
        skill = md.parent
        st = status_line(skill)
        if st != "ACCEPTED":
            out[skill.name] = st.lower()
        elif led.get(skill.name, {}).get("sha256") != content_hash(skill):
            out[skill.name] = "changed since acceptance"
        else:
            out[skill.name] = "accepted"
    return out


def accepted(repo: Path = REPO) -> list[Path]:
    """Skills allowed to leave the repo: ACCEPTED and unchanged since."""
    return [skills_dir(repo) / n for n, st in review_state(repo).items() if st == "accepted"]


def accept(name: str, by: str, repo: Path = REPO, when: str | None = None) -> str:
    skill = skills_dir(repo) / name
    if status_line(skill) != "ACCEPTED":
        raise ValueError(f"{name}'s SKILL.md status is not ACCEPTED; set it after Luke answers the explain-back")
    led = ledger(repo)
    led[name] = {"sha256": content_hash(skill), "date": when or date.today().isoformat(), "by": by}
    ledger_path(repo).write_text(json.dumps(led, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return led[name]["sha256"]


def ours(dest: Path) -> bool:
    return dest.is_symlink() and REPO.resolve() in dest.resolve().parents or (dest / MARK).exists()


def status(repo: Path = REPO, home: Path | None = None) -> dict[str, str]:
    """skill -> 'installed', 'missing', 'outdated' or 'blocked', for the skills allowed to leave."""
    out = {}
    for src in accepted(repo):
        dest = user_dir(home) / src.name
        if (dest / MARK).exists():
            out[src.name] = "installed" if (dest / MARK).read_text().strip() == content_hash(src) else "outdated"
        elif dest.is_symlink() and ours(dest):
            out[src.name] = "outdated"  # an old link install: replace with a pinned copy
        else:
            out[src.name] = "blocked" if dest.exists() or dest.is_symlink() else "missing"
    return out


def install(repo: Path = REPO, home: Path | None = None) -> dict[str, str]:
    target = user_dir(home)
    target.mkdir(parents=True, exist_ok=True)
    allowed = {p.name: p for p in accepted(repo)}
    result = {}
    for name in sorted(p.parent.name for p in skills_dir(repo).glob("*/SKILL.md")):
        dest = target / name
        mine = (dest / MARK).exists() or (dest.is_symlink() and skills_dir(repo).resolve() in dest.resolve().parents)
        if name not in allowed:
            if mine:
                dest.unlink() if dest.is_symlink() else shutil.rmtree(dest)
                result[name] = "withdrawn (not accepted, or changed since acceptance)"
            continue
        if (dest.exists() or dest.is_symlink()) and not mine:
            result[name] = "blocked: another skill already uses this name"
            continue
        if dest.is_symlink():
            dest.unlink()
        elif dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(allowed[name], dest, ignore=shutil.ignore_patterns(*IGNORE))
        (dest / MARK).write_text(content_hash(allowed[name]) + "\n", encoding="utf-8")
        result[name] = "installed (pinned copy)"
    return result


def remove(repo: Path = REPO, home: Path | None = None) -> list[str]:
    removed = []
    for md in skills_dir(repo).glob("*/SKILL.md"):
        dest = user_dir(home) / md.parent.name
        if (dest / MARK).exists():
            shutil.rmtree(dest)
            removed.append(dest.name)
        elif dest.is_symlink() and skills_dir(repo).resolve() in dest.resolve().parents:
            dest.unlink()
            removed.append(dest.name)
    return sorted(removed)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = p.add_mutually_exclusive_group()
    g.add_argument("--install", action="store_true")
    g.add_argument("--remove", action="store_true")
    g.add_argument("--accept", metavar="NAME")
    p.add_argument("--by", default="")
    args = p.parse_args(argv)
    if args.accept:
        if not args.by:
            p.error("--accept needs --by (whose explain-back, and when)")
        print(f"/{args.accept}: accepted at {accept(args.accept, args.by)[:12]}")
    elif args.install:
        for name, what in install().items():
            print(f"/{name}: {what}")
        print("New Claude Code chats will see the change. Restart open chats to pick it up.")
    elif args.remove:
        print("Removed: " + (", ".join(remove()) or "nothing"))
    else:
        inst = status()
        for name, st in review_state().items():
            print(f"/{name}: {st}" + (f", {inst[name]}" if name in inst else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
