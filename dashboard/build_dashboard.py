"""Build the Games-People-Play dashboard: one HTML page of Luke's projects and their next steps.

Status: DECIDED (D-028) (static local HTML, D-028; DASH-01, WARD-03, MAINT-01). The new-project,
notes and next-step tools (D-034) are served by dashboard/server.py; this module builds the page.

It reads files only. It needs no packages and no network, so it still launches after months untouched
on macOS or Windows (MAINT-01). For each project folder under the roots it shows: tier, document review
state, requirement statuses, open decisions, the latest elicitation record, the warden's verdict, the
time suggestion, the privacy hook, notes, and the next skill to run with the exact prompt for Claude.

Usage:
  python dashboard/build_dashboard.py [--roots ~/Projects ~/Research ~/School] [--out dashboard/index.html] [--open]
  python dashboard/server.py --open        (the same page, plus New project, notes and Copy buttons)
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import webbrowser
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from urllib.parse import quote

REPO = Path(__file__).resolve().parents[1]
START = REPO / ".claude" / "skills" / "start"
DEFAULT_ROOTS = ["~/Projects", "~/Research", "~/School"]
REQ_STATUSES = ["PROPOSED", "REVIEWED", "ACCEPTED", "IMPLEMENTED", "VERIFIED", "DEFERRED", "DROPPED"]
HOOK_MARK = "Games-People-Play privacy check"
CANDIDATE_MARK = ".gpp-project"  # written by the dashboard's New project form; holds the kind


@dataclass
class Skill:
    name: str
    description: str
    status: str
    path: Path


@dataclass
class Project:
    name: str
    path: Path
    kind: str = "code"
    tier: str = "none"
    docs: int = 0
    accepted_docs: int = 0
    explain_backs: int = 0
    answered: int = 0
    reqs: dict = field(default_factory=dict)
    open_decisions: int = 0
    record: str = ""
    record_path: str = ""
    items: int = 0
    stated: int = 0
    verdict: str = ""
    time: str = ""
    has_time: bool = False
    last_commit: str = ""
    hook: str = ""  # "library", "own", "none", or "" when not a git repo
    notes: int = 0
    last_note: str = ""
    dump: bool = False
    audited: bool = False
    root: str = ""
    active: str = ""  # newest file change or commit, YYYY-MM-DD
    closed: bool = False
    archived: bool = False
    group: str = ""  # Luke's dashboard folder (D-053); "" = shown under its root folder
    run: str = ""  # newest /start record folder (D-047)
    run_phase: str = ""
    run_tier: str = ""


def engine():
    """The /start engine (D-047), imported from the library."""
    if str(START) not in sys.path:
        sys.path.insert(0, str(START))
    import engine as eng
    return eng


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def frontmatter(text: str) -> dict[str, str]:
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    out = {}
    for line in (m.group(1).splitlines() if m else []):
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip().strip('"')
    return out


def doc_status(text: str) -> str:
    m = re.search(r"\*\*Status:\s*([A-Z]+)", text)
    return m.group(1) if m else ""


def explain_backs(text: str) -> tuple[int, int]:
    """(prompts, answered): an answer is a non-empty '> ' line after the prompt."""
    prompts = answered = 0
    for m in re.finditer(r"\*\*Explain-back \(Luke\):\*\*.*?\n(.*?)(?=\n#|\Z)", text, re.S):
        prompts += 1
        if any(line.startswith(">") and line.lstrip("> ").strip() for line in m.group(1).splitlines()):
            answered += 1
    return prompts, answered


def skills(repo: Path) -> list[Skill]:
    out = []
    for md in sorted((repo / ".claude" / "skills").glob("*/SKILL.md")):
        text = read(md)
        fm = frontmatter(text)
        out.append(Skill(fm.get("name", md.parent.name), fm.get("description", ""), doc_status(text) or "?", md))
    return out


def scan_project(path: Path) -> Project | None:
    se = path / "docs" / "se"
    plan = path / "plan.md"
    readme = path / "README.md"
    p = Project(name=path.name, path=path)
    run = engine().latest_run(path)
    run_state = {}
    if run is not None:
        try:
            run_state = json.loads((run / "start.json").read_text(encoding="utf-8"))
            p.run, p.run_phase, p.run_tier = str(run), engine().phase(run_state), run_state.get("tier", "")
        except (OSError, ValueError, KeyError):
            run = None
    if se.is_dir() and any(se.glob("SE-00*")):
        p.tier = "Long" if any(se.glob("SE-04*")) else "Short"
        docs = sorted(se.glob("SE-*.md")) + [se / "README.md"]
    elif (plan.exists() and not (path / ".git").exists() and read(path / CANDIDATE_MARK).strip() != "code"
          and run_state.get("kind") != "code"):  # /start writes plan.md for new code folders too
        p.kind = "household"
        p.tier = "Long" if (path / "decisions.md").exists() else "Short" if (path / "checklist.md").exists() else "Immediate"
        docs = [f for f in path.glob("*.md") if f.name not in ("notes.md", "brain_dump.md")]
    elif "**Goal:**" in read(readme):
        p.tier = "Immediate"
        docs = [readme]
    elif (path / CANDIDATE_MARK).exists():
        p.kind = read(path / CANDIDATE_MARK).strip() or "code"
        p.tier = "idea"
        docs = []
    elif (path / "brain_dump.md").exists():  # /start large saved a dump in an existing folder
        p.tier = "idea"
        docs = []
    elif run is not None:  # an existing folder Luke ran /start on: only the record was written there
        p.kind = run_state.get("kind", "code")
        p.tier = "idea"
        docs = []
    else:
        return None
    for d in docs:
        text = read(d)
        if not text:
            continue
        p.docs += 1
        p.accepted_docs += doc_status(text) in ("ACCEPTED", "VERIFIED")
        a, b = explain_backs(text)
        p.explain_backs += a
        p.answered += b
    se03 = next(iter(sorted(se.glob("SE-03*.md"))), None) if se.is_dir() else None
    if se03:
        for line in read(se03).splitlines():
            m = re.match(r"^\| [A-Z]+-\d+ \| [A-Z].*\| ([A-Z]+)[^|]*\|\s*$", line)
            if m and m.group(1) in REQ_STATUSES:
                p.reqs[m.group(1)] = p.reqs.get(m.group(1), 0) + 1
    se00 = next(iter(sorted(se.glob("SE-00*.md"))), None) if se.is_dir() else None
    if se00:
        section = read(se00).split("## Open decisions", 1)
        if len(section) == 2:
            body = section[1].split("\n## ", 1)[0]
            p.open_decisions = sum(1 for line in body.splitlines()
                                   if re.match(r"^\| (?:OD-)?\d+ \|", line) and "~~" not in line)
    records = sorted(list(path.glob("docs/se/elicitation/*/items.md")) + list(path.glob("elicitation/*/items.md")),
                     key=lambda f: f.parent.name)
    if records:
        rec = records[-1].parent
        p.record, p.record_path = rec.name, str(rec)
        rows = [line for line in read(rec / "items.md").splitlines() if re.match(r"^\| E-\d+ \|", line)]
        p.items = len(rows)
        p.stated = sum(1 for line in rows if "| stated |" in line)
        v = re.search(r"\*\*Verdict:\s*([A-Z-]+)", read(rec / "verdict.md"))
        p.verdict = v.group(1) if v else ""
        t = re.search(r"\*\*suggested hours h\\\*[^|]*\|\s*\*\*([\d.]+ h)", read(rec / "time.md"))
        p.time = t.group(1) if t else ""
        p.has_time = (rec / "time.md").exists()
    sections = re.split(r"^## .*$", read(path / "notes.md"), flags=re.M)
    p.notes = len(sections) - 1
    p.last_note = sections[-1].strip().splitlines()[0][:160] if p.notes and sections[-1].strip() else ""
    p.dump = (path / "brain_dump.md").exists()
    p.audited = any((path / "audit").glob("se_audit_*.md"))
    if (path / ".git").exists():
        try:
            p.last_commit = subprocess.run(["git", "-C", str(path), "log", "-1", "--format=%cs"],
                                           capture_output=True, text=True, timeout=10).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            p.last_commit = ""
        hook = read(path / ".git" / "hooks" / "pre-push")
        p.hook = "library" if HOOK_MARK in hook else "own" if hook else "none"
    p.active = max(filter(None, [p.last_commit, newest_change(path)]), default="")
    finished = re.search(r"\*\*Finished on:\*\*[ \t]*(\S.*)", read(path / "closeout.md"))
    p.closed = bool(finished) or any(has_closeout(f) for f in [path / "README.md", *path.glob("docs/se/SE-0[07]*.md")])
    return p


def has_closeout(f: Path) -> bool:
    """A '## Closeout' section with real text (not the template's comment): the closeout was filed (D-031)."""
    m = re.search(r"^## Closeout\s*\n(.*?)(?=^## |\Z)", read(f), re.M | re.S)
    return bool(m and re.sub(r"<!--.*?-->", "", m.group(1), flags=re.S).strip())


SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", "data", "runs", "archive"}


def newest_change(path: Path, limit: int = 4000) -> str:
    """Date of the newest file change, skipping bulky folders; looks at most `limit` files, so it stays fast."""
    newest, seen = 0.0, 0
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for f in filenames:
            if f.startswith("."):
                continue
            try:
                newest = max(newest, os.stat(os.path.join(dirpath, f)).st_mtime)
            except OSError:
                pass
            seen += 1
            if seen >= limit:
                break
        if seen >= limit:
            break
    return datetime.fromtimestamp(newest).strftime("%Y-%m-%d") if newest else ""


STALE_DAYS, DEAD_DAYS = 14, 30
ARCHIVE_FILE = REPO / "dashboard" / "archive.json"


def state_file(default: Path, env: str) -> Path:
    """Where the dashboard keeps Luke's local state; tests point GPP_ARCHIVE / GPP_GROUPS elsewhere."""
    return Path(os.environ[env]) if os.environ.get(env) else default


def load_archive(path: Path | None = None) -> set[str]:
    path = path or state_file(ARCHIVE_FILE, "GPP_ARCHIVE")
    try:
        import json
        return set(json.loads(path.read_text(encoding="utf-8")).get("archived", []))
    except (OSError, ValueError):
        return set()


def save_archive(paths: set[str], path: Path | None = None) -> None:
    path = path or state_file(ARCHIVE_FILE, "GPP_ARCHIVE")
    import json
    path.write_text(json.dumps({"archived": sorted(paths)}, indent=2) + "\n", encoding="utf-8")


def state(p: Project, today: date | None = None) -> tuple[str, str]:
    """('green' | 'yellow' | 'red' | 'closed', why). Red: blocked or stalled. Yellow: needs a step. Green: on track."""
    if p.closed:
        return "closed", "closed out"
    idle = (( today or date.today()) - date.fromisoformat(p.active)).days if p.active else None
    if p.verdict == "NO-GO":
        return "red", "the warden said no"
    if idle is not None and idle > DEAD_DAYS:
        return "red", f"no activity for {idle} days"
    if not p.verdict:
        return "yellow", "not gated yet"
    if p.verdict == "SHRINK":
        return "yellow", "the warden said shrink"
    if p.hook == "none":
        return "yellow", "no privacy hook"
    if idle is not None and idle > STALE_DAYS:
        return "yellow", f"quiet for {idle} days"
    return "green", "on track"


KIND_LABEL = {"code": "Technical", "household": "Hands-on"}
TIER_LABEL = {"small": "Small", "medium": "Medium", "large": "Large"}
TIER_HINT = {
    "small": "An afternoon to a few evenings. One round of up to 3 questions. Haiku asks, Sonnet plans.",
    "medium": "A few weeks of evenings. Up to 2 rounds of 4 questions. Sonnet throughout.",
    "large": "A semester or more. Saves the dump; the full gate with SE documents runs in a Claude chat.",
}
KIND_HINT = {
    "code": "Software, research or anything with code: a git repo and SE documents.",
    "household": "Physical or life projects (the attic, moving): a printable plan, no code.",
}


RUN_STEP = {
    "thinking": "Claude is working on it: open it to watch",
    "stale": "A Claude step stopped part way: open it and retry",
    "error": "A Claude step failed: open it and retry",
    "asking": "Next: Claude picks your questions",
    "answering": "Answer a few questions",
    "planning": "Next: Claude drafts the verdict and plan",
    "approving": "Approve the verdict, budget and plan",
}


def recommend(p: Project) -> tuple[str, str]:
    """The next step, and the prompt to paste into Claude. The prompt starts with the slash command."""
    path = str(p.path)
    initialized = p.tier not in ("idea", "none")
    if p.run and p.run_phase in RUN_STEP:
        return RUN_STEP[p.run_phase], f"/start continue {p.run}"
    if p.run and p.run_phase == "stopped":
        return "Stopped at the gate: archive it, or start again", f"/start small {path}"
    if p.run and p.run_phase == "done":
        if p.hook == "none":
            return "Install the privacy hook before any push", f"/privacy {path}"
        return "Build it from the plan. Close it when it's done, demoed, due, or you've learned enough", f"/closeout {path}"
    if not p.record and not initialized:
        if p.dump:  # /start large saved the dump for the full gate in a chat
            return "Large: run the full gate from your brain dump", f"/elicit long {path}"
        kind = "household" if p.kind == "household" else "code"
        return "Start it: brain dump, a few questions, one approval (about 15 minutes)", f"/start small {path} --kind {kind}"
    if initialized and not p.record:
        tier = p.tier.lower() if p.tier in ("Short", "Long") else "immediate"
        return "Never gated: elicit (it checks the existing documents against your words)", f"/elicit {tier} {path}"
    if not p.verdict:
        return "Gate it with the warden", f"/warden {p.record_path}"
    if p.verdict == "NO-GO":
        return "The warden said no: stop, or log an override", f"The warden said NO-GO for {path}. Help me decide: stop, or override?"
    if not initialized and not p.has_time:
        return "Size it: suggested hours and a timeline", f"/timeplan {path}"
    if not initialized:
        kind = " --kind household" if p.kind == "household" else ""
        return "Set it up at its tier", f"/initialize {path} --from {p.record_path}{kind}"
    if p.hook == "none":
        return "Install the privacy hook before any push", f"/privacy {path}"
    if p.tier in ("Short", "Long") and not p.audited:
        return "Get a fresh-agent audit of the documents", f"/se-audit {path}"
    return "Build it. Close it when it's done, demoed, due, or you've learned enough", f"/closeout {path}"


GROUPS_FILE = REPO / "dashboard" / "groups.json"
GROUP_NAME = re.compile(r"^[^\x00-\x1f/\\]{1,40}$")


def load_groups(path: Path | None = None) -> dict:
    """Luke's dashboard folders (D-053): {"groups": [names in order], "assign": {project path: name}}.
    They only group cards on the dashboard; no project folder moves on disk."""
    path = path or state_file(GROUPS_FILE, "GPP_GROUPS")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        groups = [g for g in data.get("groups", []) if isinstance(g, str)]
        assign = {k: v for k, v in data.get("assign", {}).items() if v in groups}
        return {"groups": groups, "assign": assign}
    except (OSError, ValueError, AttributeError):
        return {"groups": [], "assign": {}}


def save_groups(data: dict, path: Path | None = None) -> None:
    (path or state_file(GROUPS_FILE, "GPP_GROUPS")).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def group_name(name: str) -> str:
    name = " ".join(name.split())
    if not GROUP_NAME.match(name):
        raise ValueError("A folder name is 1 to 40 characters, without / or \\.")
    return name


def add_group(name: str, path: Path | None = None) -> str:
    data, name = load_groups(path), group_name(name)
    if name.lower() in (g.lower() for g in data["groups"]):
        raise ValueError(f"There is already a folder called {name}.")
    data["groups"].append(name)
    save_groups(data, path)
    return name


def rename_group(old: str, new: str, path: Path | None = None) -> str:
    data, new = load_groups(path), group_name(new)
    if old not in data["groups"]:
        raise ValueError("No such folder.")
    if new != old and new.lower() in (g.lower() for g in data["groups"]):
        raise ValueError(f"There is already a folder called {new}.")
    data["groups"] = [new if g == old else g for g in data["groups"]]
    data["assign"] = {k: (new if v == old else v) for k, v in data["assign"].items()}
    save_groups(data, path)
    return new


def delete_group(name: str, path: Path | None = None) -> int:
    """Remove a dashboard folder; its projects go back under their root folders. Returns how many moved."""
    data = load_groups(path)
    if name not in data["groups"]:
        raise ValueError("No such folder.")
    moved = sum(1 for v in data["assign"].values() if v == name)
    data["groups"] = [g for g in data["groups"] if g != name]
    data["assign"] = {k: v for k, v in data["assign"].items() if v != name}
    save_groups(data, path)
    return moved


def move_group(name: str, step: int, path: Path | None = None) -> None:
    data = load_groups(path)
    g = data["groups"]
    if name not in g:
        raise ValueError("No such folder.")
    i = g.index(name)
    j = max(0, min(len(g) - 1, i + step))
    g.insert(j, g.pop(i))
    save_groups(data, path)


def assign_group(project: str, name: str, path: Path | None = None) -> None:
    data = load_groups(path)
    if name and name not in data["groups"]:
        raise ValueError("No such folder.")
    if name:
        data["assign"][project] = name
    else:
        data["assign"].pop(project, None)
    save_groups(data, path)


def projects(roots: list[Path], archive: Path | None = None, groups: Path | None = None) -> list[Project]:
    archived = load_archive(archive)
    assign = load_groups(groups)["assign"]
    out = []
    for root in roots:
        if not root.is_dir():
            continue
        for child in sorted(root.iterdir()):
            if child.is_dir() and not child.name.startswith("."):
                p = scan_project(child)
                if p:
                    p.root = str(root)
                    p.archived = str(child) in archived
                    p.group = assign.get(str(child), "")
                    out.append(p)
    return out


def signature(projs: list[Project]) -> str:
    """Changes whenever anything shown on the page would change."""
    key = "|".join(f"{p.path}:{p.archived}:{p.group}:{p.tier}:{p.record}:{p.verdict}:{p.has_time}:{p.notes}:{p.active}:{p.hook}:{p.audited}"
                   f":{p.closed}:{p.docs}:{p.answered}:{sorted(p.reqs.items())}" for p in projs)
    return hashlib.sha1(key.encode()).hexdigest()[:16]


def skill_summary(repo: Path = REPO) -> str:
    """One line on the library (DASH-01 as rewritten by D-044): how many skills, and how many await review."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import install_skills as inst
        states = inst.review_state(repo)
    except Exception:
        return "skills: state unknown"
    finally:
        sys.path.pop(0)
    ok = sum(1 for v in states.values() if v == "accepted")
    waiting = [k for k, v in states.items() if v != "accepted"]
    return (f"{len(states)} skills: {ok} accepted" + (f", {len(waiting)} awaiting your explain-back"
            f" ({', '.join('/' + w for w in waiting)}; usable in Games-People-Play chats)" if waiting else ""))


def e(x) -> str:
    return html.escape(str(x))


def tier_label(p: Project) -> str:
    if p.run and p.tier in ("idea", "Immediate"):
        return TIER_LABEL.get(p.run_tier, p.run_tier)
    return "idea" if p.tier == "idea" else f"{p.tier} tier"


def folders(roots: list[Path]) -> list[Path]:
    """Existing project folders /start may use: direct children of the roots (D-047)."""
    out = []
    for r in roots:
        if r.is_dir():
            out += sorted((c for c in r.iterdir() if c.is_dir() and not c.name.startswith(".")), key=lambda c: c.name.lower())
    return out



# ---------------------------------------------------------------- one project's details (D-052)

@dataclass
class Doc:
    path: Path
    title: str
    group: str
    status: str = ""
    prompts: int = 0
    answered: int = 0


@dataclass
class Detail:
    goal: str = ""
    done_when: str = ""
    budget: str = ""
    plan_file: str = ""
    steps: list = field(default_factory=list)  # (line index, done, text)
    reasons: list = field(default_factory=list)
    docs: list = field(default_factory=list)
    decisions: list = field(default_factory=list)  # (id, text)
    records: list = field(default_factory=list)  # dicts
    notes: list = field(default_factory=list)  # (when, text), newest first
    git: dict = field(default_factory=dict)


STEP = re.compile(r"^(\s*)- \[( |x|X)\] (.*)$")
TEXT_EXT = {".md", ".txt"}


def plan_file(p: Project) -> Path | None:
    """The plan Luke works from: plan.md in the project, else the newest record's plan.md."""
    if (p.path / "plan.md").exists():
        return p.path / "plan.md"
    plans = sorted(list(p.path.glob("elicitation/*/plan.md")) + list(p.path.glob("docs/se/elicitation/*/plan.md")),
                   key=lambda f: f.parent.name)
    return plans[-1] if plans else None


def field_line(text: str, label: str) -> str:
    m = re.search(rf"\*\*{label}:\*\*\s*(.+)", text)
    return m.group(1).strip() if m else ""


def title_of(f: Path) -> str:
    m = re.search(r"^# (.+)$", read(f), re.M)
    return m.group(1).strip() if m else f.name


def detail(p: Project) -> Detail:
    d = Detail()
    pf = plan_file(p)
    records = sorted(list(p.path.glob("elicitation/*")) + list(p.path.glob("docs/se/elicitation/*")),
                     key=lambda f: f.name, reverse=True)
    records = [r for r in records if r.is_dir()]
    for src in [pf, records[0] / "goal.md" if records else None, p.path / "README.md"]:
        if src and src.exists():
            text = read(src)
            d.goal = d.goal or field_line(text, "Goal")
            d.done_when = d.done_when or field_line(text, "Done when")
    if pf:
        d.plan_file = str(pf)
        d.steps = [(i, m.group(2) != " ", m.group(3)) for i, line in enumerate(read(pf).splitlines())
                   if (m := STEP.match(line))]
        d.budget = field_line(read(pf), "Time")
    if records:
        body = read(records[0] / "verdict.md").split("## Reasons", 1)
        if len(body) == 2:
            d.reasons = [ln[2:].strip() for ln in body[1].split("\n## ", 1)[0].splitlines() if ln.startswith("- ")][:8]
    for r in records[:6]:
        v = re.search(r"\*\*Verdict:\s*([A-Z-]+)", read(r / "verdict.md"))
        rec = {"name": r.name, "path": str(r), "verdict": v.group(1) if v else "", "run": "", "tier": ""}
        if (r / "start.json").exists():
            try:
                st = json.loads((r / "start.json").read_text(encoding="utf-8"))
                rec["run"], rec["tier"] = engine().phase(st), st.get("tier", "")
            except (OSError, ValueError, KeyError):
                pass
        d.records.append(rec)
    groups = [("Project", sorted(p.path.glob("*.md"))), ("SE documents", sorted(p.path.glob("docs/se/*.md"))),
              ("Audits", sorted(p.path.glob("audit/*.md"))),
              ("Latest record", sorted(records[0].glob("*.md")) if records else [])]
    for group, files in groups:
        for f in files[:30]:
            text = read(f)
            a, b = explain_backs(text)
            d.docs.append(Doc(f, title_of(f), group, doc_status(text), a, b))
    se00 = next(iter(sorted(p.path.glob("docs/se/SE-00*.md"))), None)
    if se00:
        section = read(se00).split("## Open decisions", 1)
        if len(section) == 2:
            for line in section[1].split("\n## ", 1)[0].splitlines():
                m = re.match(r"^\| ((?:OD-)?\d+) \| (.+?) \|", line)
                if m and "~~" not in line:
                    d.decisions.append((m.group(1), re.sub(r"[*`]", "", m.group(2))[:240]))
    parts = re.split(r"^## (.*)$", read(p.path / "notes.md"), flags=re.M)
    d.notes = [(parts[i].strip(), parts[i + 1].strip()) for i in range(1, len(parts) - 1, 2)][::-1]
    if (p.path / ".git").exists():
        def git(*args):
            try:
                return subprocess.run(["git", "-C", str(p.path), *args], capture_output=True, text=True,
                                      timeout=10).stdout.strip()
            except (OSError, subprocess.SubprocessError):
                return ""
        d.git = {"branch": git("rev-parse", "--abbrev-ref", "HEAD"),
                 "dirty": len([x for x in git("status", "--porcelain").splitlines() if x.strip()]),
                 "commits": [c.split("\t", 1) for c in git("log", "-6", "--format=%cs%x09%s").splitlines() if "\t" in c],
                 "remote": git("remote", "get-url", "origin")}
    return d


def set_step(plan: Path, index: int, done: bool) -> None:
    """Tick or untick one checklist line of a plan (D-052). Only a '- [ ]' line can change."""
    lines = plan.read_text(encoding="utf-8").split("\n")
    m = STEP.match(lines[index]) if 0 <= index < len(lines) else None
    if not m:
        raise ValueError("That line is not a checklist step.")
    lines[index] = f"{m.group(1)}- [{'x' if done else ' '}] {m.group(3)}"
    plan.write_text("\n".join(lines), encoding="utf-8")


def add_step(plan: Path, text: str) -> None:
    """Add a step at the end of the plan's checklist (after its last '- [ ]' line, else under '## Steps')."""
    text = " ".join(text.split())[:300]
    if not text:
        raise ValueError("The step is empty.")
    lines = plan.read_text(encoding="utf-8").split("\n")
    at = max((i for i, ln in enumerate(lines) if STEP.match(ln)), default=None)
    if at is None:
        at = next((i for i, ln in enumerate(lines) if ln.strip() == "## Steps"), None)
        if at is None:
            lines += ["", "## Steps", ""]
            at = len(lines) - 1
        else:
            at += 1
    lines.insert(at + 1, f"- [ ] {text}")
    plan.write_text("\n".join(lines), encoding="utf-8")


def answer_explain_back(doc: Path, n: int, answer: str, today: str | None = None) -> None:
    """Write Luke's answer, verbatim, under the n-th explain-back prompt (D-052). An answered prompt is left alone."""
    answer = answer.strip()
    if not answer:
        raise ValueError("The answer is empty.")
    lines = doc.read_text(encoding="utf-8").split("\n")
    hits = [i for i, ln in enumerate(lines) if "**Explain-back (Luke):**" in ln]
    if not 0 <= n < len(hits):
        raise ValueError("No such explain-back.")
    i = hits[n] + 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    j = i
    while j < len(lines) and lines[j].startswith(">"):
        if lines[j].lstrip("> ").strip():
            raise ValueError("That explain-back is already answered.")
        j += 1
    quoted = [f"> {ln}" if ln.strip() else ">" for ln in answer.splitlines()]
    quoted += [">", f"> *(Answered {today or date.today().isoformat()} in the dashboard.)*"]
    lines[i:j] = ([""] if i == hits[n] + 1 else []) + quoted
    doc.write_text("\n".join(lines), encoding="utf-8")


def explain_back_list(text: str) -> list[tuple[str, str]]:
    """(prompt, answer) for each explain-back in a document; answer is '' when unanswered."""
    out = []
    for m in re.finditer(r"\*\*Explain-back \(Luke\):\*\*(.*?)\n(.*?)(?=\n\*\*Explain-back|\n#|\n---|\Z)", text, re.S):
        ans = "\n".join(ln.lstrip(">").strip() for ln in m.group(2).splitlines() if ln.startswith(">")).strip()
        out.append((m.group(1).strip(), ans))
    return out


# ---------------------------------------------------------------- pages (dashboard/pages.py)

def pages():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import pages as pg
    return pg


def page(projs: list[Project], skls: list[Skill], roots: list[Path], token: str = "", message: str = "",
         skills_ok: bool | None = None, selected: str = "") -> str:
    """The home page: every project as a card. Without a token, a static snapshot with no forms or scripts."""
    return pages().home(projs, roots, token=token, message=message, skills_ok=skills_ok)


def run_page(st: dict, record: Path, token: str, message: str = "") -> str:
    return pages().run_page(st, record, token, message)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--roots", nargs="+", default=DEFAULT_ROOTS)
    ap.add_argument("--repo", type=Path, default=REPO, help="the library repo whose skills are counted")
    ap.add_argument("--out", type=Path, default=REPO / "dashboard" / "index.html")
    ap.add_argument("--open", action="store_true", help="open the page in the browser")
    args = ap.parse_args(argv)
    roots = [Path(r).expanduser() for r in args.roots]
    projs, skls = projects(roots), skills(args.repo)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(page(projs, skls, roots), encoding="utf-8")
    print(f"Wrote {args.out}: {len(projs)} projects, {len(skls)} skills.")
    if args.open:
        webbrowser.open(args.out.resolve().as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
