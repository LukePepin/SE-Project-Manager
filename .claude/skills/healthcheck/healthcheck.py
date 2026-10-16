"""Check that the library still works, and change nothing (MAINT-01, MAINT-02).

Status: PROPOSED (AI-drafted by Claude on 2026-10-08 from Luke's direction, E-061 and E-062;
not reviewed by Luke).

Checks:
  - every skill has a SKILL.md with a name matching its folder, a description, a status line and an explain-back
  - every Python script in the library compiles
  - the dashboard builds (into a temporary file)
  - the test suite passes, when the repo's .venv exists
It reports and exits 1 on any failure. It never edits a file; fixes wait for Luke's approval.

Usage:
  python .claude/skills/healthcheck/healthcheck.py [--no-tests]
"""

from __future__ import annotations

import argparse
import py_compile
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def check_skills(repo: Path) -> list[tuple[str, bool, str]]:
    out = []
    for d in sorted(p for p in (repo / ".claude" / "skills").iterdir() if p.is_dir()):
        md = d / "SKILL.md"
        if not md.exists():
            out.append((f"skill {d.name}", False, "no SKILL.md"))
            continue
        text = md.read_text(encoding="utf-8")
        name = re.search(r"^name:\s*(\S+)", text, re.M)
        problems = []
        if not name or name.group(1) != d.name:
            problems.append("frontmatter name does not match the folder")
        if not re.search(r"^description:\s*\S", text, re.M):
            problems.append("no description")
        status = re.search(r"\*\*Status:\s*([A-Z]+)", text)
        if not status:
            problems.append("no status line")
        if "**Explain-back (Luke):**" not in text:
            problems.append("no explain-back")
        out.append((f"skill {d.name}", not problems, "; ".join(problems) or (status.group(1) if status else "")))
    return out


def check_acceptance(repo: Path) -> list[tuple[str, bool, str]]:
    """An ACCEPTED skill must still match the content recorded when Luke accepted it (D-044, SAFE-03)."""
    sys.path.insert(0, str(repo / "dashboard"))
    try:
        import install_skills as inst
    except ImportError:
        return [("acceptance ledger", False, "dashboard/install_skills.py missing")]
    finally:
        sys.path.pop(0)
    out = []
    for name, st in inst.review_state(repo).items():
        ok = st != "changed since acceptance"
        out.append((f"acceptance {name}", ok, st if ok else "changed since acceptance: set it to REVIEWED and ask a new explain-back"))
    return out


def check_compile(repo: Path) -> list[tuple[str, bool, str]]:
    out = []
    files = sorted((repo / ".claude" / "skills").rglob("*.py")) + sorted((repo / "dashboard").glob("*.py"))
    for f in files:
        try:
            py_compile.compile(str(f), doraise=True, cfile=str(Path(tempfile.gettempdir()) / "gpp_healthcheck.pyc"))
            out.append((f"compile {f.relative_to(repo).as_posix()}", True, ""))
        except py_compile.PyCompileError as e:
            out.append((f"compile {f.relative_to(repo).as_posix()}", False, str(e).splitlines()[0]))
    return out


def check_dashboard(repo: Path) -> tuple[str, bool, str]:
    with tempfile.TemporaryDirectory() as tmp:
        res = subprocess.run([sys.executable, str(repo / "dashboard" / "build_dashboard.py"),
                              "--out", str(Path(tmp) / "index.html")], capture_output=True, text=True)
    return ("dashboard builds", res.returncode == 0, (res.stdout or res.stderr).strip().splitlines()[-1:][0]
            if (res.stdout or res.stderr).strip() else "")


def check_tests(repo: Path) -> tuple[str, bool, str]:
    py = repo / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if not py.exists():
        return ("test suite", True, "skipped: no .venv (see README)")
    res = subprocess.run([str(py), "-m", "pytest", "-q", "-p", "no:cacheprovider"], cwd=repo,
                         capture_output=True, text=True)
    last = (res.stdout.strip().splitlines() or [""])[-1]
    return ("test suite", res.returncode == 0, last)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--repo", type=Path, default=REPO)
    p.add_argument("--no-tests", action="store_true")
    args = p.parse_args(argv)
    results = check_skills(args.repo) + check_acceptance(args.repo) + check_compile(args.repo) + [check_dashboard(args.repo)]
    if not args.no_tests:
        results.append(check_tests(args.repo))
    failed = [r for r in results if not r[1]]
    print("# Health check\n\n| Check | Result | Note |\n|---|---|---|")
    for name, ok, note in results:
        print(f"| {name} | {'pass' if ok else '**FAIL**'} | {note} |")
    print(f"\n{len(results) - len(failed)} of {len(results)} checks pass. Nothing was changed."
          + (" Fixes wait for Luke's approval." if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
