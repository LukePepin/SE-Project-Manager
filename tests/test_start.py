"""D-047 to D-050: /start, the engine and its dashboard pages. Claude is faked; no network, no CLI."""

import importlib.util
import json
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "start"))
sys.path.insert(0, str(ROOT / "dashboard"))
import engine as eng  # noqa: E402

spec = importlib.util.spec_from_file_location("server", ROOT / "dashboard" / "server.py")
srv = importlib.util.module_from_spec(spec)
sys.modules["server"] = srv
spec.loader.exec_module(srv)
bd = srv.bd

DUMP = "My website is out of date.\n\nJust refresh the content, no redesign."
USAGE = {"model": "fake", "input": 900, "output": 300, "cost_usd": 0.001, "seconds": 1.0}


def item(i, typ, text, src, basis="stated"):
    return {"id": f"E-{i:03d}", "type": typ, "text": text, "source": src, "basis": basis, "lens": []}


def plan(verdict="GO", items=None):
    return {"items": items if items is not None else [item(1, "Need", "out of date", "dump P1"),
                                                      item(2, "Measure", "pubs match my CV", "R1.Q1")],
            "verdict": verdict, "verdict_line": "Worth an evening.", "reasons": [{"text": "Real problem", "cites": ["E-001"]}],
            "concerns": ["Wednesday is busy (context)"], "proposals": [{"id": "W1", "change": "Pubs first", "why": "Most stale"}],
            "goal": "Refresh the site (dump P1)", "done_when": "\"pubs match my CV\" (R1.Q1)",
            "time_inputs": {"purpose": 3, "length_hours": 2, "complexity": 1, "availability": None, "why": "guess"},
            "steps": [{"text": "List what changed", "hours": 0.5}, {"text": "Edit pages", "hours": 1}],
            "out_of_scope": ["redesign"]}


class Fake:
    """Answers the ask stage with questions (until `rounds` asked), then the plan stage."""

    def __init__(self, questions=2, verdict="GO", plan_items=None):
        self.calls, self.questions, self.verdict, self.plan_items = [], questions, verdict, plan_items

    def __call__(self, model, effort, system, user, schema, thinking=False):
        self.calls.append({"model": model, "system": system, "user": user, "thinking": thinking,
                           "stage": "plan" if "verdict" in schema["properties"] else "ask"})
        if self.calls[-1]["stage"] == "ask":
            qs = [{"lens": "L18", "text": f"Question {k}?"} for k in range(1, self.questions + 1)]
            return {"items": [item(1, "Need", "out of date", "dump P1"),
                              item(2, "Need", "Luke wants a blog", "inferred from E-001"),
                              item(3, "Need", "fake stated", "my guess")],  # 'stated' with no Luke source
                    "covered": ["L1"], "questions": qs, "done": not qs}, dict(USAGE)
        return plan(self.verdict, self.plan_items), dict(USAGE)


@pytest.fixture(autouse=True)
def no_docket(tmp_path, monkeypatch):
    """Never read Luke's real Docket in a test."""
    monkeypatch.setattr(eng.context_pack, "DEFAULT_DOCKET", tmp_path / "no-docket")


@pytest.fixture
def project(tmp_path):
    p = tmp_path / "Projects" / "Site"
    p.mkdir(parents=True)
    return p


def test_small_run_end_to_end(project):
    fake = Fake()
    rec = eng.new(project, "code", "small", DUMP, today="2026-10-10")
    assert rec == project / "elicitation" / "2026-10-10"
    st = eng.step(rec, runner=fake, context="ctx")
    assert st["status"] == "answering" and [q["id"] for q in st["rounds"][0]["questions"]] == ["R1.Q1", "R1.Q2"]
    assert fake.calls[0]["model"] == "haiku" and fake.calls[0]["thinking"] is False
    assert "[dump P1] My website is out of date." in fake.calls[0]["user"] and "Today is" in fake.calls[0]["user"]
    assert [i["basis"] for i in st["items"]] == ["stated", "inferred", "inferred"]  # no Luke source: not stated
    st = eng.answer(rec, {"R1.Q1": "  pubs match my CV  ", "R1.Q2": ""})
    assert st["status"] == "planning"  # small has one round
    assert st["rounds"][0]["answers"] == {"R1.Q1": "pubs match my CV", "R1.Q2": ""}
    st = eng.step(rec, runner=fake, context="")
    assert fake.calls[1]["model"] == "sonnet" and "[R1.Q1] Luke: pubs match my CV" in fake.calls[1]["user"]
    assert st["status"] == "approving" and st["plan"]["verdict"] == "GO" and st["time"]["hours"] > 0
    assert (rec / "verdict.md").exists() and "**Verdict: GO**" in (rec / "verdict.md").read_text()
    st = eng.approve(rec, 2.0, ["W1", "W9"], today="2026-10-10")
    assert st["status"] == "done" and st["approved"]["accepted"] == ["W1"] and st["approved"]["rejected"] == []
    # an existing code project gets the record and nothing else
    assert sorted(x.name for x in project.iterdir()) == ["elicitation"]
    for f in ("dump.md", "rounds.md", "items.md", "verdict.md", "goal.md", "time.md", "plan.md"):
        assert (rec / f).exists(), f
    assert "> pubs match my CV" in (rec / "rounds.md").read_text()
    assert "**P1.** My website is out of date." in (rec / "dump.md").read_text()
    assert "Luke's budget | 2 h" in (rec / "time.md").read_text()
    assert "approved" in (rec / "verdict.md").read_text() and "By: Luke, 2026-10-10. Budget: 2 h." in (rec / "verdict.md").read_text()


def test_new_household_folder_is_set_up_only_after_approval(tmp_path):
    root = tmp_path / "Projects"
    root.mkdir()
    target = eng.make_folder(root, "Attic", "household")
    rec = eng.new(target, "household", "small", DUMP, created=True)
    fake = Fake()
    eng.step(rec, runner=fake, context="")
    eng.answer(rec, {"R1.Q1": "pubs match my CV"}, stop=True)
    eng.step(rec, runner=fake, context="")
    assert not (target / "plan.md").exists()
    eng.approve(rec, None, [])
    text = (target / "plan.md").read_text()
    assert "**Goal:** Refresh the site" in text and "- [ ] List what changed (about 0.5 h)" in text
    assert "Luke's budget not set" in text


def test_medium_asks_two_rounds_and_thinks_when_planning(project):
    fake = Fake()
    rec = eng.new(project, "code", "medium", DUMP)
    eng.step(rec, runner=fake, context="")
    st = eng.answer(rec, {"R1.Q1": "a"})
    assert st["status"] == "asking"
    st = eng.step(rec, runner=fake, context="")
    assert st["status"] == "answering" and st["rounds"][1]["questions"][0]["id"] == "R2.Q1"
    eng.answer(rec, {"R2.Q1": "b"})
    st = eng.step(rec, runner=fake, context="")
    assert st["status"] == "approving" and fake.calls[-1]["thinking"] is True
    assert [c["model"] for c in fake.calls] == ["sonnet", "sonnet", "sonnet"]


def test_no_questions_goes_straight_to_the_plan(project):
    rec = eng.new(project, "code", "small", DUMP)
    st = eng.step(rec, runner=Fake(questions=0), context="")
    assert st["status"] == "approving" and len(st["usage"]) == 2


def test_the_floor_makes_the_verdict_stricter_never_looser(project):
    rec = eng.new(project, "code", "small", DUMP)
    only_inferred = [item(1, "Need", "x", "inferred from nothing", "inferred")]
    st = eng.step(rec, runner=Fake(questions=0, verdict="GO", plan_items=only_inferred), context="")
    assert st["plan"]["verdict"] == "NO-GO" and st["plan"]["model_verdict"] == "GO"
    with pytest.raises(eng.Refused, match="override"):
        eng.approve(rec, 1, [])
    st = eng.approve(rec, 1, [], override="I need it for the lab meeting")
    assert st["status"] == "done" and "Override of NO-GO" in (rec / "verdict.md").read_text()
    rec2 = eng.new(project, "code", "small", DUMP)
    st = eng.step(rec2, runner=Fake(questions=0, verdict="NO-GO"), context="")
    assert st["plan"]["verdict"] == "NO-GO"  # the model's no-go stands even when the checks pass
    assert rec2.name == f"{rec.name}-2"


def test_no_stated_measure_is_a_shrink(project):
    rec = eng.new(project, "code", "small", DUMP)
    st = eng.step(rec, runner=Fake(questions=0, plan_items=[item(1, "Need", "x", "dump P1")]), context="")
    assert st["plan"]["verdict"] == "SHRINK" and "Measure" in st["plan"]["floor"][0]


def test_errors_are_kept_for_a_retry(project):
    def broken(*a, **k):
        raise eng.StageFailed("Claude Code is not logged in")
    rec = eng.new(project, "code", "small", DUMP)
    st = eng.step(rec, runner=broken, context="")
    assert eng.phase(st) == "error" and "logged in" in st["error"] and st["status"] == "asking"
    st["error"] = ""
    eng.save(rec, st)
    assert eng.phase(eng.step(rec, runner=Fake(), context="")) == "answering"


def test_a_stage_that_died_shows_as_stale(project):
    rec = eng.new(project, "code", "small", DUMP)
    st = eng.load(rec)
    st.update(busy="ask", busy_since=time.time() - eng.STALE_SECONDS - 1)
    assert eng.phase(st) == "stale"
    st["busy_since"] = time.time()
    assert eng.phase(st) == "thinking"


def test_refusals(project, tmp_path):
    with pytest.raises(eng.Refused, match="empty"):
        eng.new(project, "code", "small", "  ")
    with pytest.raises(eng.Refused, match="Tier"):
        eng.new(project, "code", "huge", DUMP)
    with pytest.raises(eng.Refused):
        eng.make_folder(tmp_path, "../escape", "code")
    rec = eng.new(project, "code", "small", DUMP)
    with pytest.raises(eng.Refused):
        eng.answer(rec, {})
    with pytest.raises(eng.Refused):
        eng.approve(rec, 1, [])


def test_large_hands_off_to_the_full_gate(project):
    out = eng.new(project, "code", "large", DUMP)
    assert out == project and (project / "brain_dump.md").exists() and not (project / "elicitation").exists()
    assert "Verbatim" in (project / "brain_dump.md").read_text()


def test_records_are_git_ignored_in_a_repo(project):
    (project / ".git").mkdir()
    (project / ".gitignore").write_text("node_modules/\n")
    eng.new(project, "code", "small", DUMP)
    assert "**/elicitation/" in (project / ".gitignore").read_text().splitlines()
    eng.new(project, "code", "small", DUMP)
    assert (project / ".gitignore").read_text().count("**/elicitation/") == 1


def test_the_real_call_is_stripped(monkeypatch):
    seen = {}

    class Done:
        stdout = json.dumps({"is_error": False, "structured_output": {"ok": True}, "total_cost_usd": 0.002,
                             "duration_ms": 1500, "usage": {"input_tokens": 800, "output_tokens": 100}})
        stderr = ""

    def run(cmd, **kw):
        seen["cmd"], seen["kw"] = cmd, kw
        return Done()
    monkeypatch.setattr(eng.subprocess, "run", run)
    monkeypatch.setattr(eng, "find_claude", lambda: "claude")
    data, usage = eng.run_claude("haiku", "low", "SYS", "USER", {"type": "object"})
    cmd = seen["cmd"]
    for flag in ("--tools", "--strict-mcp-config", "--disable-slash-commands", "--no-session-persistence",
                 "--json-schema", "--system-prompt"):
        assert flag in cmd
    assert cmd[cmd.index("--tools") + 1] == "" and cmd[cmd.index("--model") + 1] == "haiku"
    assert json.loads(cmd[cmd.index("--settings") + 1]) == {"alwaysThinkingEnabled": False}
    assert "--effort" not in cmd  # effort only matters with thinking on
    assert float(cmd[cmd.index("--max-budget-usd") + 1]) == eng.MAX_USD_PER_CALL
    assert seen["kw"]["input"] == "USER" and seen["kw"]["cwd"] != str(ROOT)
    assert data == {"ok": True} and usage["input"] == 800 and usage["seconds"] == 1.5


def test_context_digest_is_short_and_capacity_first(tmp_path):
    docket = tmp_path / "Docket"
    (docket / "claude" / "reviews").mkdir(parents=True)
    (docket / "Hierarchy of Projects.md").write_text("# H\n\n" + "areas " * 2000)
    (docket / "claude" / "reviews" / "2026-10-04.md").write_text("# R\n\n## Working week and capacity\n\nMon: thesis.\n")
    text = eng.context_digest(800, docket, today=__import__("datetime").date(2026, 10, 10))
    assert len(text) <= 800 and text.index("capacity") < (text.find("Hierarchy") if "Hierarchy" in text else 10 ** 6)
    assert eng.context_digest(800, tmp_path / "missing") == ""


# ------------------------------------------------------------------ the dashboard

def run_server(roots, runner):
    server = ThreadingHTTPServer(("127.0.0.1", 0), srv.make_handler(roots, ROOT, "test-token", runner=runner))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def post(url, data):
    return urllib.request.urlopen(urllib.request.Request(url, data=urllib.parse.urlencode(data, doseq=True).encode()),
                                  timeout=5)


def wait_for(rec, phase, seconds=5):
    end = time.time() + seconds
    while time.time() < end:
        if eng.phase(eng.load(rec)) == phase:
            return
        time.sleep(0.05)
    raise AssertionError(f"never reached {phase}: {eng.phase(eng.load(rec))}")


def test_dashboard_runs_start_through_its_three_stops(tmp_path):
    root = tmp_path / "Projects"
    root.mkdir()
    server, base = run_server([root], Fake())
    try:
        page = urllib.request.urlopen(base + "/new", timeout=5).read().decode()
        assert 'action="/start"' in page and 'value="small" checked' in page and "Medium" in page
        res = post(base + "/start", {"token": "test-token", "existing": "", "name": "Site", "root": str(root),
                                     "kind": "code", "tier": "small", "dump": DUMP})
        assert "/run?r=" in res.url
        rec = eng.latest_run(root / "Site")
        wait_for(rec, "answering")
        page = urllib.request.urlopen(base + "/run?r=" + urllib.parse.quote(str(rec)), timeout=5).read().decode()
        assert "Question 1?" in page and 'name="a_R1.Q1"' in page
        post(base + "/run/answer", {"token": "test-token", "r": str(rec), "a_R1.Q1": "pubs match my CV", "action": "send"})
        wait_for(rec, "approving")
        page = urllib.request.urlopen(base + "/run?r=" + urllib.parse.quote(str(rec)), timeout=5).read().decode()
        assert "Warden: GO" in page and 'name="accept" value="W1"' in page and "Use " in page
        assert not (root / "Site" / "plan.md").exists()  # nothing is set up before approval
        post(base + "/run/approve", {"token": "test-token", "r": str(rec), "budget": "2", "accept": ["W1"]})
        st = eng.load(rec)
        assert st["status"] == "done" and st["approved"]["accepted"] == ["W1"]
        assert st["approved"]["by"] == "Luke, in the dashboard" and (root / "Site" / "plan.md").exists()
        home = urllib.request.urlopen(base + "/", timeout=5).read().decode()
        assert "Small" in home and "/project?p=" in home
        proj = urllib.request.urlopen(base + "/project?p=" + urllib.parse.quote(str(root / "Site")), timeout=5).read().decode()
        assert "/closeout" in proj and "List what changed" in proj
    finally:
        server.shutdown()
        server.server_close()


def test_dashboard_refuses_records_outside_its_folders_and_forged_posts(tmp_path):
    root = tmp_path / "Projects"
    (root / "Mine").mkdir(parents=True)
    other = tmp_path / "Elsewhere"
    other.mkdir()
    outside = eng.new(other, "code", "small", DUMP)
    server, base = run_server([root], Fake())
    try:
        with pytest.raises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(base + "/run?r=" + urllib.parse.quote(str(outside)), timeout=5)
        assert e.value.code == 404
        with pytest.raises(urllib.error.HTTPError) as e:
            post(base + "/run/stop", {"token": "wrong", "r": str(outside)})
        assert e.value.code == 403
        with pytest.raises(urllib.error.HTTPError) as e:
            post(base + "/start", {"token": "test-token", "existing": str(other), "tier": "small", "kind": "code",
                                   "dump": DUMP})
        assert e.value.code == 400
        res = post(base + "/start", {"token": "test-token", "existing": str(root / "Mine"), "tier": "large",
                                     "kind": "code", "dump": DUMP})
        assert "/elicit long" in res.read().decode() and (root / "Mine" / "brain_dump.md").exists()
    finally:
        server.shutdown()
        server.server_close()


def test_app_mode_stops_when_the_window_is_gone(tmp_path):
    server = ThreadingHTTPServer(("127.0.0.1", 0), srv.make_handler([tmp_path], ROOT, "t"))
    last = [time.time() - 10]
    srv.watch_idle(server, last, 0.3)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    t.join(3)
    assert not t.is_alive()
    server.server_close()


def test_a_step_orphaned_by_a_restart_offers_a_retry_at_once(tmp_path):
    root = tmp_path / "Projects"
    (root / "Site").mkdir(parents=True)
    rec = eng.new(root / "Site", "code", "small", DUMP)
    st = eng.load(rec)
    st.update(busy="ask", busy_since=time.time() - 30)  # an earlier server was mid-step
    eng.save(rec, st)
    server, base = run_server([root], Fake())
    try:
        state = urllib.request.urlopen(base + "/run/state?r=" + urllib.parse.quote(str(rec)), timeout=5).read().decode()
        assert state == "error" and "closed while Claude" in eng.load(rec)["error"]
        post(base + "/run/retry", {"token": "test-token", "r": str(rec)})
        wait_for(rec, "answering")
    finally:
        server.shutdown()
        server.server_close()
