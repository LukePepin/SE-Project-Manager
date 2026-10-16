"""/start: one pass from brain dump to plan, with three stops for Luke (D-047).

Status: PROPOSED (AI-drafted by Claude on 2026-10-10 from Luke's direction, D-047 to D-050;
not reviewed by Luke).

The stops are Luke's: (1) the brain dump, (2) one or two rounds of a few questions, (3) one approval
(verdict, proposed changes, hours budget, create). Everything between them is a short, fresh call to
Claude through the Claude Code CLI (`claude -p`), so it runs on Luke's Claude plan, not a pay-per-token
API key (PROPOSED: Claude's answer to Luke's question in D-049). Each call is stripped to save tokens: no tools, no MCP servers, no skills, no CLAUDE.md,
a stage-specific system prompt, and structured JSON out. The cheaper model does the cheaper stage
(tiers.json). Deterministic work stays in Python: the record files, the warden's floor, the time
equation and the initializer.

Large projects hand off to the full gate (/elicit long, /warden, /timeplan, /initialize) in a chat.

Rules kept from the full gate: Luke's words are stored verbatim by Python, never by the model;
every item is stated, inferred or context; the verdict can only be made stricter by the checks;
nothing is created until Luke approves; no git, Todoist, Calendar or messages.

Usage (the dashboard calls the same functions):
  python engine.py new (--project DIR | --root DIR --name NAME) --kind code|household --tier small|medium|large
                       (--dump TEXT | --dump-file FILE|-)
  python engine.py step RECORD                 run the next Claude stage (questions, or the plan)
  python engine.py answer RECORD --answers-file FILE [--stop]   FILE: JSON {"R1.Q1": "text", ...}
  python engine.py approve RECORD [--budget H] [--accept W1,W2] [--override TEXT]
  python engine.py stop RECORD
  python engine.py show RECORD
Exit code: 0 done, 2 refused.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS = HERE.parent
for sub in ("timeplan", "initialize", "elicit"):
    sys.path.insert(0, str(SKILLS / sub))
import context_pack  # noqa: E402
import init_project  # noqa: E402
import time_equation  # noqa: E402

TIERS = {k: v for k, v in json.loads((HERE / "tiers.json").read_text(encoding="utf-8")).items()
         if not k.startswith("_")}
STATE = "start.json"
NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.-]{0,59}$")
KINDS = ("code", "household")
ITEM_TYPES = ["Need", "Constraint", "Measure", "Risk", "Out", "Stakeholder", "Alternative", "Assumption", "Question"]
VERDICTS = ["GO", "SHRINK", "NO-GO"]
STALE_SECONDS = 600  # a stage still "busy" after this long died with its process: offer a retry
CALL_TIMEOUT = 300
MAX_USD_PER_CALL = 0.50  # API-price cap per call: stops a call that keeps retrying its JSON (seen once on 10/10)

ITEM = {"type": "object", "properties": {
    "id": {"type": "string"}, "type": {"type": "string", "enum": ITEM_TYPES}, "text": {"type": "string"},
    "source": {"type": "string"}, "basis": {"type": "string", "enum": ["stated", "inferred", "context"]},
    "lens": {"type": "array", "items": {"type": "string"}}},
    "required": ["id", "type", "text", "source", "basis"]}
ASK_SCHEMA = {"type": "object", "properties": {
    "items": {"type": "array", "items": ITEM},
    "covered": {"type": "array", "items": {"type": "string"}},
    "questions": {"type": "array", "items": {"type": "object", "properties": {
        "lens": {"type": "string"}, "text": {"type": "string"}}, "required": ["lens", "text"]}},
    "done": {"type": "boolean"}},
    "required": ["items", "covered", "questions", "done"]}
PLAN_SCHEMA = {"type": "object", "properties": {
    "items": {"type": "array", "items": ITEM},
    "verdict": {"type": "string", "enum": VERDICTS},
    "verdict_line": {"type": "string"},
    "reasons": {"type": "array", "items": {"type": "object", "properties": {
        "text": {"type": "string"}, "cites": {"type": "array", "items": {"type": "string"}}},
        "required": ["text", "cites"]}},
    "concerns": {"type": "array", "items": {"type": "string"}},
    "proposals": {"type": "array", "items": {"type": "object", "properties": {
        "id": {"type": "string"}, "change": {"type": "string"}, "why": {"type": "string"}},
        "required": ["id", "change", "why"]}},
    "goal": {"type": "string"}, "done_when": {"type": "string"},
    "time_inputs": {"type": "object", "properties": {
        "purpose": {"type": "integer", "minimum": 1, "maximum": 5},
        "length_hours": {"type": "number"},
        "complexity": {"type": "integer", "minimum": 1, "maximum": 5},
        "availability": {"type": ["number", "null"]},
        "why": {"type": "string"}},
        "required": ["purpose", "length_hours", "complexity", "availability", "why"]},
    "steps": {"type": "array", "items": {"type": "object", "properties": {
        "text": {"type": "string"}, "hours": {"type": "number"}}, "required": ["text", "hours"]}},
    "out_of_scope": {"type": "array", "items": {"type": "string"}}},
    "required": ["items", "verdict", "verdict_line", "reasons", "concerns", "proposals", "goal", "done_when",
                 "time_inputs", "steps", "out_of_scope"]}


class Refused(Exception):
    pass


class StageFailed(Exception):
    pass


# --------------------------------------------------------------------------- state

def load(record: Path) -> dict:
    return json.loads((Path(record) / STATE).read_text(encoding="utf-8"))


def save(record: Path, st: dict) -> None:
    record = Path(record)
    tmp = record / (STATE + ".tmp")
    tmp.write_text(json.dumps(st, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, record / STATE)
    render(record, st)


def latest_run(project: Path) -> Path | None:
    """The newest /start record in a project, or None."""
    runs = list(Path(project).glob("elicitation/*/" + STATE)) + list(Path(project).glob("docs/se/elicitation/*/" + STATE))
    return max(runs, key=lambda f: (f.parent.name, f.stat().st_mtime)).parent if runs else None


def phase(st: dict, now: float | None = None) -> str:
    """What the page should show: thinking, stale, error, answering, approving, done, stopped, handoff."""
    if st.get("busy"):
        if (now or time.time()) - st.get("busy_since", 0) > STALE_SECONDS:
            return "stale"
        return "thinking"
    if st.get("error"):
        return "error"
    return st["status"]


# --------------------------------------------------------------------------- new

def record_folder(project: Path, today: str) -> Path:
    base = project / "docs" / "se" / "elicitation" if (project / "docs" / "se").is_dir() else project / "elicitation"
    folder, n = base / today, 2
    while folder.exists():
        folder, n = base / f"{today}-{n}", n + 1
    return folder


def ignore_records(project: Path) -> bool:
    """Git-ignore elicitation records in a git repo: Luke's dump and life context stay off GitHub (D-035)."""
    if not (project / ".git").exists():
        return False
    gi = project / ".gitignore"
    lines = gi.read_text(encoding="utf-8").splitlines() if gi.exists() else []
    if any(line.strip() in ("**/elicitation/", "elicitation/", "/elicitation/") for line in lines):
        return False
    gi.write_text("\n".join(lines + ["# Games-People-Play: private elicitation records", "**/elicitation/"]) + "\n",
                  encoding="utf-8")
    return True


def make_folder(root: Path, name: str, kind: str) -> Path:
    name = name.strip()
    if not NAME.match(name) or name.endswith(".") or ".." in name:
        raise Refused("Name: letters, numbers, spaces, - _ . (up to 60), starting with a letter or number.")
    target = Path(root).expanduser() / name
    if target.exists():
        raise Refused(f"{target} already exists. Pick it as an existing folder instead.")
    target.mkdir(parents=True)
    (target / ".gpp-project").write_text(kind + "\n", encoding="utf-8")
    return target


def new(project: Path, kind: str, tier: str, dump: str, name: str | None = None, created: bool = False,
        today: str | None = None) -> Path:
    """Start a run. Returns the record folder (for a large project, the project folder: it hands off)."""
    project = Path(project).expanduser()
    if tier not in TIERS:
        raise Refused(f"Tier must be one of {', '.join(TIERS)}.")
    if kind not in KINDS:
        raise Refused("Kind must be code or household.")
    if not project.is_dir():
        raise Refused(f"{project} is not a folder.")
    if not dump.strip():
        raise Refused("The brain dump is empty. Everything about the project, in any order, is the first stop.")
    today = today or date.today().isoformat()
    name = name or project.name
    if "handoff" in TIERS[tier]:
        bd = project / "brain_dump.md"
        if bd.exists():
            raise Refused(f"{bd} already exists; run {TIERS[tier]['handoff']} {project} in a Claude chat.")
        bd.write_text(f"# Brain dump: {name}, {today}\n\n**Verbatim.** Typed by Luke for /start large."
                      f" /elicit uses it as its Stage 0 dump.\n\n{dump.strip()}\n", encoding="utf-8")
        return project
    rec = record_folder(project, today)
    rec.mkdir(parents=True)
    st = {"version": 1, "name": name, "project": str(project), "kind": kind, "tier": tier, "created": created,
          "started": datetime.now().isoformat(timespec="seconds"), "status": "asking", "busy": "", "error": "",
          "dump": [p for p in re.split(r"\n\s*\n", dump.strip()) if p.strip()],
          "items": [], "covered": [], "rounds": [], "plan": None, "time": None, "approved": None,
          "result": None, "usage": [], "ignored_in_git": ignore_records(project)}
    save(rec, st)
    return rec


# --------------------------------------------------------------------------- Claude

def find_claude() -> str:
    for c in (os.environ.get("GPP_CLAUDE"), shutil.which("claude"), str(Path.home() / ".local/bin/claude"),
              "/opt/homebrew/bin/claude", "/usr/local/bin/claude"):
        if c and Path(c).exists():
            return c
    raise StageFailed("Claude Code (the `claude` command) was not found. Install it, or set GPP_CLAUDE to its path.")


def run_claude(model: str, effort: str | None, system: str, user: str, schema: dict,
               thinking: bool = False) -> tuple[dict, dict]:
    """One stripped `claude -p` call on Luke's plan: no tools, MCP, skills or CLAUDE.md; JSON out.

    Thinking is off unless the tier asks for it: on 10/10 a Haiku question round spent 12k thinking
    tokens and 2 minutes with it on (even at --effort low), and 1.6k tokens and 15 s with it off."""
    cmd = [find_claude(), "-p", "--model", model, "--output-format", "json", "--tools", "",
           "--system-prompt", system, "--strict-mcp-config", "--disable-slash-commands",
           "--no-session-persistence", "--setting-sources", "", "--json-schema", json.dumps(schema),
           "--settings", json.dumps({"alwaysThinkingEnabled": bool(thinking)}),
           "--max-budget-usd", f"{MAX_USD_PER_CALL:g}"]
    if effort and thinking:
        cmd += ["--effort", effort]
    with tempfile.TemporaryDirectory() as cwd:  # no project CLAUDE.md gets picked up
        try:
            out = subprocess.run(cmd, input=user, capture_output=True, text=True, timeout=CALL_TIMEOUT, cwd=cwd)
        except subprocess.TimeoutExpired:
            raise StageFailed(f"Claude took longer than {CALL_TIMEOUT // 60} minutes. Try again.")
    try:
        res = json.loads(out.stdout)
    except ValueError:
        msg = (out.stderr or out.stdout).strip()[:400]
        raise StageFailed(f"Claude Code did not answer ({msg or 'no output'}). Is it logged in? Run `claude` once.")
    if res.get("is_error") or res.get("structured_output") is None:
        raise StageFailed(f"Claude Code returned an error: {str(res.get('result') or res.get('subtype'))[:400]}")
    u = res.get("usage", {})
    usage = {"model": model, "input": u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0)
             + u.get("cache_creation_input_tokens", 0), "output": u.get("output_tokens", 0),
             "cost_usd": res.get("total_cost_usd", 0.0), "seconds": round(res.get("duration_ms", 0) / 1000, 1),
             "turns": res.get("num_turns", 1)}  # 2 is normal for JSON output; more means retries
    return res["structured_output"], usage


# --------------------------------------------------------------------------- stage inputs

def context_digest(chars: int, docket: Path | None = None, today: date | None = None) -> str:
    """A few lines of what else is going on (capacity and commitments first), cut to `chars` (D-047)."""
    docket = docket or context_pack.DEFAULT_DOCKET
    if chars <= 0 or not docket.exists():
        return ""
    text, _ = context_pack.build(docket, days=7, today=today)
    secs = re.split(r"^## ", text, flags=re.M)[1:]
    rank = ("capacity", "working week", "allocation", "anchors", "next action", "docket_memory", "parked")
    picked = sorted(secs, key=lambda s: next((i for i, k in enumerate(rank) if k in s.split("\n", 1)[0].lower()),
                                             len(rank)))
    out, per = [], max(300, chars // 4)
    for s in picked:
        head, _, body = s.partition("\n")
        body = re.sub(r"\n{2,}", "\n", body.strip())
        chunk = f"[{head.strip()}]\n{body[:per]}"
        if sum(len(c) for c in out) + len(chunk) > chars:
            break
        out.append(chunk)
    return "\n".join(out)


def luke_text(st: dict) -> str:
    lines = ["## Luke's brain dump (verbatim)"] + [f"[dump P{i}] {p}" for i, p in enumerate(st["dump"], 1)]
    for r in st["rounds"]:
        for q in r["questions"]:
            a = r["answers"].get(q["id"], "").strip()
            lines += [f"\n[{q['id']}] Q ({q['lens']}): {q['text']}", f"[{q['id']}] Luke: {a or '(no answer)'}"]
    return "\n".join(lines)


def items_text(items: list[dict]) -> str:
    return "\n".join(f"{i['id']} | {i['type']} | {i['text']} | {i['source']} | {i['basis']}" for i in items)


def stage_input(st: dict, context: str) -> str:
    cfg = TIERS[st["tier"]]
    today = date.today()
    parts = [f"Today is {today:%A} {today.isoformat()}.",
             f"Project: {st['name']} (kind: {st['kind']}; tier: {cfg['label']})", luke_text(st)]
    if st["items"]:
        parts.append("## Items so far\n" + items_text(st["items"]))
    if context:
        parts.append("## Context (Luke's calendar and notes; not Luke's words in this conversation)\n" + context)
    return "\n\n".join(parts)


def system_prompt(stage: str, st: dict) -> str:
    cfg = TIERS[st["tier"]]
    text = (HERE / "prompts" / f"{stage}.md").read_text(encoding="utf-8")
    return (text.replace("{questions}", str(cfg["questions"])).replace("{lenses}", ", ".join(cfg["lenses"]))
            .replace("{plan_steps}", str(cfg["plan_steps"])).replace("{tier_label}", f"{cfg['label']}: {cfg['about']}"))


def clean_items(raw: list[dict]) -> list[dict]:
    """Renumber E-001.. in order and keep only the fields we store; never trust a 'stated' with no Luke source."""
    out = []
    for n, i in enumerate(raw, 1):
        basis = i.get("basis", "inferred")
        src = i.get("source", "").strip()
        if basis == "stated" and not re.search(r"\b(dump P\d+|R\d+\.Q\d+)", src):
            basis = "inferred"
        out.append({"id": f"E-{n:03d}", "type": i.get("type", "Question"), "text": i.get("text", "").strip(),
                    "source": src, "basis": basis, "lens": [x for x in i.get("lens", []) if re.match(r"^L\d+$", x)]})
    return out


def floor(items: list[dict]) -> tuple[str, list[str]]:
    """The fixed checks, a floor under the model's verdict: only Luke's stated items count (WARD-02)."""
    stated = [i for i in items if i["basis"] == "stated"]
    own = [i for i in items if i["basis"] != "context"]
    why = []
    if not any(i["type"] == "Need" for i in stated):
        return "NO-GO", ["No problem in Luke's own words: no stated Need."]
    if not any(i["type"] == "Measure" for i in stated):
        why.append("No stated way to tell it is done (no stated Measure).")
    if own and sum(i["basis"] == "inferred" for i in own) / len(own) > 0.5:
        why.append("More than half the items are Claude's inferences.")
    return ("SHRINK" if why else "GO"), why


def stricter(a: str, b: str) -> str:
    return max(a, b, key=VERDICTS.index)


# --------------------------------------------------------------------------- stages

def step(record: Path, runner=run_claude, context: str | None = None) -> dict:
    """Run the next Claude stage: questions while rounds remain, then the plan. Safe to call twice."""
    record = Path(record)
    st = load(record)
    if phase(st) == "thinking":
        return st
    if st["status"] not in ("asking", "planning"):
        return st
    cfg = TIERS[st["tier"]]
    stage = "ask" if st["status"] == "asking" else "plan"
    st.update(busy=stage, busy_since=time.time(), error="")
    save(record, st)
    try:
        ctx = context_digest(cfg["context_chars"]) if context is None else context
        if stage == "ask":
            data, usage = runner(cfg["models"]["ask"], cfg["effort"]["ask"], system_prompt("ask", st),
                                 stage_input(st, ctx), ASK_SCHEMA, thinking=cfg["thinking"]["ask"])
            st["usage"].append({"stage": f"ask R{len(st['rounds']) + 1}", **usage})
            st["items"] = clean_items(data.get("items", []))
            st["covered"] = sorted(set(data.get("covered", [])))
            qs = [q for q in data.get("questions", []) if q.get("text", "").strip()][:cfg["questions"]]
            if qs and not data.get("done"):
                n = len(st["rounds"]) + 1
                st["rounds"].append({"n": n, "answers": {}, "questions": [
                    {"id": f"R{n}.Q{k}", "lens": q.get("lens", ""), "text": q["text"].strip()} for k, q in enumerate(qs, 1)]})
                st["status"] = "answering"
            else:
                st["status"] = "planning"
        if st["status"] == "planning":
            data, usage = runner(cfg["models"]["plan"], cfg["effort"]["plan"], system_prompt("plan", st),
                                 stage_input(st, ctx), PLAN_SCHEMA, thinking=cfg["thinking"]["plan"])
            st["usage"].append({"stage": "plan", **usage})
            st["items"] = clean_items(data.pop("items", [])) or st["items"]
            fl, why = floor(st["items"])
            data["model_verdict"] = data["verdict"]
            data["verdict"] = stricter(data["verdict"], fl)
            data["floor"] = why
            st["plan"] = data
            st["time"] = time_suggestion(data["time_inputs"])
            st["status"] = "approving"
    except Exception as e:  # noqa: BLE001  shown to Luke with a Retry button
        st["error"] = str(e) if isinstance(e, StageFailed) else f"{type(e).__name__}: {e}"
    st.update(busy="", busy_since=0)
    save(record, st)
    return st


def time_suggestion(ti: dict) -> dict:
    avail = ti.get("availability")
    assumed = not avail or avail <= 0
    avail = time_equation.REF_AVAILABILITY if assumed else float(avail)
    factor, n = time_equation.load_calibration(time_equation.DEFAULT_CALIBRATION)
    try:
        s = time_equation.suggest(int(ti["purpose"]), max(0.25, float(ti["length_hours"])), int(ti["complexity"]),
                                  avail, factor, n)
    except (ValueError, KeyError) as e:
        return {"error": str(e)}
    return {"hours": round(s.hours, 1), "need": round(s.need, 1), "verdict": s.verdict, "weeks": round(s.weeks, 1),
            "availability": avail, "assumed_availability": assumed, "calibration_n": n, "inputs": ti}


def answer(record: Path, answers: dict[str, str], stop: bool = False) -> dict:
    """Store Luke's answers verbatim; the next step asks again or plans."""
    record = Path(record)
    st = load(record)
    if st["status"] != "answering" or phase(st) == "thinking":
        raise Refused("There are no open questions to answer.")
    r = st["rounds"][-1]
    for q in r["questions"]:
        r["answers"][q["id"]] = (answers.get(q["id"]) or "").strip()
    more = len(st["rounds"]) < TIERS[st["tier"]]["rounds"]
    st["status"] = "asking" if (more and not stop) else "planning"
    if stop:
        st["stopped_rounds"] = True
    save(record, st)
    return st


def approve(record: Path, budget: float | None, accepted: list[str], override: str = "",
            today: str | None = None, by: str = "Luke") -> dict:
    """Luke's one approval: record it, then write the plan and set the project up (no git, ever)."""
    record = Path(record)
    st = load(record)
    if st["status"] != "approving" or phase(st) == "thinking":
        raise Refused("Nothing is waiting for approval.")
    plan = st["plan"]
    if plan["verdict"] == "NO-GO" and not override.strip():
        raise Refused("The warden said NO-GO. Stop here, or give your reason to override it.")
    if budget is not None and budget <= 0:
        raise Refused("The budget is hours: a positive number.")
    ids = [p["id"] for p in plan["proposals"]]
    st["approved"] = {"by": by,
                      "date": today or date.today().isoformat(), "budget": budget,
                      "accepted": [i for i in ids if i in accepted], "rejected": [i for i in ids if i not in accepted],
                      "override": override.strip()}
    project = Path(st["project"])
    result = {"written": [], "skipped": [], "notes": []}
    plan_text = plan_md(st)
    (record / "plan.md").write_text(plan_text, encoding="utf-8")
    result["written"].append(str((record / "plan.md").relative_to(project)))
    if st["kind"] == "household" or st["created"]:
        out = project / "plan.md"
        if out.exists():
            result["skipped"].append("plan.md")
        else:
            out.write_text(plan_text, encoding="utf-8")
            result["written"].append("plan.md")
        try:
            res = init_project.initialize(project, st["name"], TIERS[st["tier"]]["init_tier"], st["kind"], record,
                                          override=("Luke's override: " + override.strip()) if override.strip() else None)
            result["written"] += res["written"]
            result["skipped"] += res["skipped"]
        except init_project.Refused as e:
            result["notes"].append(f"Initializer refused: {e}")
    else:
        result["notes"].append("Existing code project: only the record and its plan were written; nothing else"
                               " in the folder changed.")
    if st.get("ignored_in_git"):
        result["notes"].append("Added **/elicitation/ to .gitignore, so the record stays off GitHub.")
    st["result"] = result
    st["status"] = "done"
    save(record, st)
    return st


def stop(record: Path) -> dict:
    record = Path(record)
    st = load(record)
    st.update(status="stopped", busy="", error="")
    save(record, st)
    return st


# --------------------------------------------------------------------------- record files

def cell(s: str) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ")


def usage_line(st: dict) -> str:
    u = st.get("usage", [])
    if not u:
        return "No Claude calls yet."
    tin, tout = sum(x["input"] for x in u), sum(x["output"] for x in u)
    cost, secs = sum(x["cost_usd"] for x in u), sum(x["seconds"] for x in u)
    models = ", ".join(sorted({x["model"] for x in u}))
    return (f"{len(u)} Claude calls ({models}): {tin:,} tokens in, {tout:,} out, {secs:.0f} s of Claude time."
            f" API-price equivalent ${cost:.3f}; run through Claude Code it counts against your plan's limits instead.")


def plan_md(st: dict) -> str:
    p, t, a = st["plan"], st.get("time") or {}, st.get("approved") or {}
    lines = [f"# {st['name']}: plan", "",
             f"Started {st['started'][:10]} with /start {st['tier']}. Status: DRAFT, until Luke says it's right.", "",
             f"**Goal:** {p['goal']}", "", f"**Done when:** {p['done_when']}", "",
             f"**Warden:** {p['verdict']}. {p['verdict_line']}", ""]
    if t.get("hours") is not None:
        lines.append(f"**Time:** suggested {t['hours']:g} h, Luke's budget "
                     + (f"{a['budget']:g} h" if a.get("budget") else "not set"))
        lines.append("")
    accepted = [x for x in p["proposals"] if x["id"] in a.get("accepted", [])]
    if accepted:
        lines += ["**Changes Luke approved:**", ""] + [f"- {x['id']}: {x['change']}" for x in accepted] + [""]
    lines += ["## Steps", ""] + [f"- [ ] {s['text']} (about {s['hours']:g} h)" for s in p["steps"]]
    if p["out_of_scope"]:
        lines += ["", "## Not in this project", ""] + [f"- {x}" for x in p["out_of_scope"]]
    lines += ["", "## Notes", ""]
    return "\n".join(lines) + "\n"


def render(record: Path, st: dict) -> None:
    """The human-readable record. Formats match the full gate's, so the dashboard and /closeout read them."""
    record = Path(record)
    head = f"**Status: PROPOSED** except Luke's words. Written by /start ({st['tier']}) for {st['name']}."
    dump = [f"# Brain dump: {st['name']}, {st['started'][:10]}", "", "**Verbatim.** Luke's words, unedited,"
            " split at paragraph breaks.", ""] + [f"**P{i}.** {p}\n" for i, p in enumerate(st["dump"], 1)]
    (record / "dump.md").write_text("\n".join(dump), encoding="utf-8")
    rounds = [f"# Rounds: {st['name']}", "", head, ""]
    for r in st["rounds"]:
        rounds += [f"## Round {r['n']}", ""]
        for q in r["questions"]:
            a = r["answers"].get(q["id"])
            rounds += [f"**{q['id']}** ({q['lens']}) {q['text']}", "", f"> {a}" if a else "> (not answered yet)"
                       if a is None else "> (no answer)", ""]
    if st.get("stopped_rounds"):
        rounds.append("Luke skipped to the plan before the round cap.")
    rounds += ["", f"**Usage:** {usage_line(st)}"]
    (record / "rounds.md").write_text("\n".join(rounds) + "\n", encoding="utf-8")
    items = [f"# Items: {st['name']}", "", head, "", "| ID | Type | Statement | Source | Basis | Lens | Status |",
             "|---|---|---|---|---|---|---|"] + [
        f"| {i['id']} | {i['type']} | {cell(i['text'])} | {cell(i['source'])} | {i['basis']} | {', '.join(i['lens'])} | active |"
        for i in st["items"]]
    (record / "items.md").write_text("\n".join(items) + "\n", encoding="utf-8")
    p = st.get("plan")
    if not p:
        return
    a = st.get("approved")
    v = [f"# Warden verdict: {st['name']}, {st['started'][:10]}", "",
         "**Status: PROPOSED.** Written by Claude as the warden (/start). Luke decides.", "",
         f"**Verdict: {p['verdict']}** {p['verdict_line']}", ""]
    if p.get("floor"):
        v += ["Checks (the floor; only Luke's stated items count): " + " ".join(p["floor"]),
              f"The model's own verdict was {p['model_verdict']}." if p["model_verdict"] != p["verdict"] else "", ""]
    v += ["## Reasons", ""] + [f"- {r['text']} ({', '.join(r['cites']) or 'no stated item'})" for r in p["reasons"]]
    if p["proposals"]:
        v += ["", "## Proposed changes", "", "| # | Change | Why | Luke |", "|---|---|---|---|"]
        for x in p["proposals"]:
            said = "" if not a else ("approved" if x["id"] in a["accepted"] else "not approved")
            v.append(f"| {x['id']} | {cell(x['change'])} | {cell(x['why'])} | {said} |")
    if p["concerns"]:
        v += ["", "## Concerns (inferred or context, not reasons)", ""] + [f"- {c}" for c in p["concerns"]]
    if a:
        v += ["", "## Luke's approval", "",
              f"By: {a['by']}, {a['date']}. Budget: " + (f"{a['budget']:g} h." if a["budget"] else "not set.")
              + (f" Approved: {', '.join(a['accepted'])}." if a["accepted"] else " No changes approved.")
              + (f" **Override of NO-GO:** \"{a['override']}\"" if a["override"] else "")]
    (record / "verdict.md").write_text("\n".join(v) + "\n", encoding="utf-8")
    (record / "goal.md").write_text(
        f"# Goal\n\n{head}\n\n**Goal:** {p['goal']}\n**Done when:** {p['done_when']}\n", encoding="utf-8")
    t = st.get("time") or {}
    if t.get("hours") is not None:
        ti = t["inputs"]
        (record / "time.md").write_text("\n".join([
            "# Time suggestion", "", "**Status: PROPOSED.** The inputs are Claude's estimates; Luke sets the budget"
            " and the record keeps both numbers (TIME-02).", "",
            f"Inputs (Claude's): purpose {ti['purpose']}, length {ti['length_hours']:g} h of doing, complexity"
            f" {ti['complexity']}, availability {t['availability']:g} h/week"
            + (" (assumed: not in Luke's words or context)" if t["assumed_availability"] else "") + f". {ti['why']}", "",
            "| Step | Value |", "|---|---|",
            f"| need | {t['need']:g} h |",
            f"| **suggested hours h\\* = need x ln(r / c)** | **{t['hours']:.1f} h** |",
            f"| verdict | **{t['verdict']}** |",
            f"| Luke's budget | {a['budget']:g} h |" if a and a.get("budget") else "| Luke's budget | not set yet |",
        ]) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- CLI

def show(st: dict) -> str:
    ph = phase(st)
    out = [f"{st['name']} ({st['tier']}, {st['kind']}): {ph}"]
    if st.get("error"):
        out.append(f"Error: {st['error']}")
    if ph == "answering":
        out += [f"{q['id']}: {q['text']}" for q in st["rounds"][-1]["questions"]]
    if ph in ("approving", "done") and st["plan"]:
        p, t = st["plan"], st["time"] or {}
        out += [f"Verdict: {p['verdict']}. {p['verdict_line']}"] + [f"  - {r['text']}" for r in p["reasons"]]
        out += [f"{x['id']}: {x['change']} ({x['why']})" for x in p["proposals"]]
        out += [f"Goal: {p['goal']}", f"Done when: {p['done_when']}"]
        if t.get("hours") is not None:
            out.append(f"Suggested hours: {t['hours']:g}" + (" (availability assumed)" if t["assumed_availability"] else ""))
        out += [f"  [ ] {s['text']} ({s['hours']:g} h)" for s in p["steps"]]
    if st.get("result"):
        out += [f"{k}: {', '.join(v)}" for k, v in st["result"].items() if v]
    out.append(usage_line(st))
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new")
    n.add_argument("--project", type=Path)
    n.add_argument("--root", type=Path)
    n.add_argument("--name")
    n.add_argument("--kind", choices=KINDS, default="code")
    n.add_argument("--tier", choices=sorted(TIERS), default="small")
    n.add_argument("--dump")
    n.add_argument("--dump-file")
    for c in ("step", "answer", "approve", "stop", "show"):
        s = sub.add_parser(c)
        s.add_argument("record", type=Path)
        if c == "answer":
            s.add_argument("--answers-file", required=True)
            s.add_argument("--stop", action="store_true")
        if c == "approve":
            s.add_argument("--budget", type=float)
            s.add_argument("--accept", default="")
            s.add_argument("--override", default="")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "new":
            dump = args.dump or (sys.stdin.read() if args.dump_file == "-" else
                                 Path(args.dump_file).read_text(encoding="utf-8") if args.dump_file else "")
            created = False
            if args.project:
                project = args.project
            elif args.root and args.name:
                project, created = make_folder(args.root, args.name, args.kind), True
            else:
                raise Refused("Give --project, or --root and --name.")
            rec = new(project, args.kind, args.tier, dump, args.name, created)
            if "handoff" in TIERS[args.tier]:
                print(f"Large: saved the dump to {rec / 'brain_dump.md'}. Next, in a Claude chat:"
                      f" {TIERS[args.tier]['handoff']} {rec}")
            else:
                print(f"Record: {rec}")
            return 0
        if args.cmd == "step":
            st = step(args.record)
        elif args.cmd == "answer":
            st = answer(args.record, json.loads(Path(args.answers_file).read_text(encoding="utf-8")), args.stop)
        elif args.cmd == "approve":
            st = approve(args.record, args.budget, [x.strip() for x in args.accept.split(",") if x.strip()],
                         args.override)
        elif args.cmd == "stop":
            st = stop(args.record)
        else:
            st = load(args.record)
        print(show(st))
        return 1 if st.get("error") else 0
    except Refused as e:
        print(f"Refused: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
