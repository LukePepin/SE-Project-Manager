"""D-052: project pages, documents, the library, and what Luke can do in the app. No Claude, no real `open`."""

import importlib.util
import json
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard"))
spec = importlib.util.spec_from_file_location("server", ROOT / "dashboard" / "server.py")
srv = importlib.util.module_from_spec(spec)
sys.modules["server"] = srv
spec.loader.exec_module(srv)
bd = srv.bd
pg = bd.pages()

PLAN = "# Site: plan\n\n**Goal:** Refresh the site\n\n**Done when:** pubs match\n\n## Steps\n\n- [ ] List diffs\n- [x] Edit pubs\n\n## Notes\n"


@pytest.fixture
def site(tmp_path):
    root = tmp_path / "Projects"
    p = root / "Site"
    p.mkdir(parents=True)
    (p / ".gpp-project").write_text("household\n")
    (p / "plan.md").write_text(PLAN)
    (p / "notes.md").write_text("# n\n\n## 2026-10-09 10:00\n\nfirst\n\n## 2026-10-10 11:00\n\nsecond <b>\n")
    (p / "run.command").write_text("#!/bin/sh\necho hi\n")
    return root, p


def test_detail_reads_goal_steps_notes_and_docs(site):
    root, p = site
    proj = bd.scan_project(p)
    d = bd.detail(proj)
    assert d.goal == "Refresh the site" and d.done_when == "pubs match"
    assert [(x, t) for _, x, t in d.steps] == [(False, "List diffs"), (True, "Edit pubs")]
    assert d.notes[0] == ("2026-10-10 11:00", "second <b>")  # newest first
    assert any(doc.path.name == "plan.md" for doc in d.docs)
    page = pg.project_page(proj, d, "tok", stamp="s")
    assert "second &lt;b&gt;" in page and "<b>\n" not in page and 'data-step="' in page and "1 of 2" in page


def test_steps_tick_and_add(site):
    _, p = site
    plan = p / "plan.md"
    idx = [i for i, ln in enumerate(plan.read_text().split("\n")) if "List diffs" in ln][0]
    bd.set_step(plan, idx, True)
    assert "- [x] List diffs" in plan.read_text()
    with pytest.raises(ValueError):
        bd.set_step(plan, 0, True)  # the title is not a step
    bd.add_step(plan, "  Preview   the site ")
    lines = plan.read_text().split("\n")
    assert lines.index("- [ ] Preview the site") == lines.index("- [x] Edit pubs") + 1
    bare = p / "bare.md"
    bare.write_text("# x\n")
    bd.add_step(bare, "First")
    assert "## Steps" in bare.read_text() and "- [ ] First" in bare.read_text()


def test_explain_backs_are_answered_verbatim_once(tmp_path):
    doc = tmp_path / "SKILL.md"
    doc.write_text("# X\n\n**Explain-back (Luke):** Why?\n\n>\n\n## After\n\n**Explain-back (Luke):** How?\n\n> Already.\n")
    assert bd.explain_back_list(doc.read_text()) == [("Why?", ""), ("How?", "Already.")]
    bd.answer_explain_back(doc, 0, "Because it  works.\nSecond line.", today="2026-10-10")
    text = doc.read_text()
    assert "> Because it  works.\n> Second line.\n>\n> *(Answered 2026-10-10 in the dashboard.)*\n\n## After" in text
    with pytest.raises(ValueError, match="already"):
        bd.answer_explain_back(doc, 1, "again")
    with pytest.raises(ValueError, match="empty"):
        bd.answer_explain_back(doc, 0, "  ")
    assert bd.explain_backs(doc.read_text()) == (2, 2)


def test_markdown_is_escaped_and_links_stay_local(tmp_path):
    html = pg.markdown("# T <x>\n\n| a | b |\n|---|---|\n| <i> | `c` |\n\n- [x] done\n- [ ] [next](plan.md)\n\n"
                       "> quote\n\n```\n<script>\n```\n\n[web](https://example.com) **bold**", tmp_path)
    assert "<script>" not in html and "&lt;script&gt;" in html and "<h1>T &lt;x&gt;</h1>" in html
    assert "<td>&lt;i&gt;</td>" in html and "<code>c</code>" in html and "☑" in html and "☐" in html
    assert f'/doc?p={urllib.parse.quote(str((tmp_path / "plan.md").resolve()), safe="")}' in html
    assert 'href="https://example.com"' in html and "<b>bold</b>" in html and "<blockquote>" in html


def test_both_themes_follow_the_system():
    page = pg.shell("x", "<p>hi</p>", "tok")
    assert "prefers-color-scheme:dark" in page and 'name="color-scheme" content="light dark"' in page
    assert "Brain dump</b></li>" not in page  # the old skill flow bar is gone


def run_server(root, opened):
    server = ThreadingHTTPServer(("127.0.0.1", 0), srv.make_handler(
        [root], ROOT, "test-token", opener=lambda path, how: opened.append((path, how)) or "Opened"))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def post(url, data):
    return urllib.request.urlopen(urllib.request.Request(url, data=urllib.parse.urlencode(data).encode()), timeout=5)


def test_server_pages_and_actions(site, tmp_path):
    root, p = site
    opened = []
    server, base = run_server(root, opened)
    q = urllib.parse.quote
    try:
        home = urllib.request.urlopen(base + "/", timeout=5).read().decode()
        assert f"/project?p={q(str(p), safe='')}" in home and 'id="filter"' in home
        page = urllib.request.urlopen(base + f"/project?p={q(str(p))}", timeout=5).read().decode()
        assert "Refresh the site" in page and "Open folder" in page
        doc = urllib.request.urlopen(base + f"/doc?p={q(str(p / 'plan.md'))}", timeout=5).read().decode()
        assert "<h1>Site: plan</h1>" in doc
        # open: only inside projects; a script is revealed by open_path, never run (checked below)
        r = json.loads(post(base + "/open", {"token": "test-token", "path": str(p), "how": "terminal"}).read())
        assert r["ok"] and opened[-1] == (p.resolve(), "terminal")
        with pytest.raises(urllib.error.HTTPError) as e:
            post(base + "/open", {"token": "test-token", "path": str(tmp_path), "how": "open"})
        assert e.value.code == 400
        with pytest.raises(urllib.error.HTTPError) as e:
            post(base + "/open", {"token": "wrong", "path": str(p)})
        assert e.value.code == 403
        # tick a step, add a step, add a note
        idx = [i for i, ln in enumerate((p / "plan.md").read_text().split("\n")) if "List diffs" in ln][0]
        assert json.loads(post(base + "/project/step", {"token": "test-token", "plan": str(p / "plan.md"),
                                                         "line": str(idx), "done": "1"}).read())["ok"]
        assert "- [x] List diffs" in (p / "plan.md").read_text()
        with pytest.raises(urllib.error.HTTPError):
            post(base + "/project/step", {"token": "test-token", "plan": str(p / "notes.md"), "line": "0", "done": "1"})
        res = post(base + "/project/addstep", {"token": "test-token", "plan": str(p / "plan.md"), "text": "Ship it"})
        assert "Step added" in res.read().decode() and "- [ ] Ship it" in (p / "plan.md").read_text()
        res = post(base + "/note", {"token": "test-token", "project": str(p), "text": "from the page",
                                    "back": f"/project?p={q(str(p))}"})
        assert "from the page" in res.read().decode()
        with pytest.raises(urllib.error.HTTPError):
            urllib.request.urlopen(base + f"/doc?p={q(str(tmp_path))}", timeout=5)
    finally:
        server.shutdown()
        server.server_close()


def test_open_never_runs_a_program(site, monkeypatch):
    _, p = site
    calls = []
    monkeypatch.setattr(srv.subprocess, "Popen", lambda cmd, **kw: calls.append(cmd))
    monkeypatch.setattr(srv.sys, "platform", "darwin")
    assert srv.open_path(p / "run.command", "open") == "Shown in Finder"
    assert calls[-1] == ["open", "-R", str(p / "run.command")]
    srv.open_path(p / "plan.md", "open")
    assert calls[-1] == ["open", str(p / "plan.md")]
    srv.open_path(p, "terminal")
    assert calls[-1] == ["open", "-a", "Terminal", str(p)]


def test_accept_after_an_answered_explain_back(tmp_path, monkeypatch):
    repo = tmp_path / "lib"
    skill = repo / ".claude" / "skills" / "demo"
    skill.mkdir(parents=True)
    (repo / ".claude" / "skills" / "accepted.json").write_text("{}")
    md = skill / "SKILL.md"
    md.write_text("---\nname: demo\ndescription: d\n---\n\n**Status: PROPOSED** (by Claude).\n\n"
                  "**Explain-back (Luke):** Why?\n\n>\n")
    with pytest.raises(srv.Refused, match="explain-back"):
        srv.accept_skill(repo, "demo")
    bd.answer_explain_back(md, 0, "Because.")
    msg = srv.accept_skill(repo, "demo")
    assert "accepted" in msg and "**Status: ACCEPTED** (Luke answered the explain-back in the dashboard" in md.read_text()
    ledger = json.loads((repo / ".claude" / "skills" / "accepted.json").read_text())
    assert ledger["demo"]["sha256"] == srv.inst.content_hash(skill)
    with pytest.raises(srv.Refused):
        srv.accept_skill(repo, "../etc")


def test_dashboard_folders_group_cards_without_moving_anything(site, tmp_path):
    root, p = site
    before = sorted(x.name for x in p.iterdir())
    assert bd.add_group("Side projects") == "Side projects"
    with pytest.raises(ValueError, match="already"):
        bd.add_group("side PROJECTS")
    for bad in ("", "a/b", "x" * 41):
        with pytest.raises(ValueError):
            bd.add_group(bad)
    bd.add_group("House")
    bd.assign_group(str(p), "House")
    with pytest.raises(ValueError):
        bd.assign_group(str(p), "Nope")
    proj = bd.projects([root])[0]
    assert proj.group == "House"
    page = pg.home(bd.projects([root]), [root], token="tok")
    assert 'data-drop="House"' in page and 'data-drop="Side projects"' in page and 'draggable="true"' in page
    assert page.index('data-drop="Side projects"') < page.index('data-drop="House"')
    assert 'data-filter="state"' in page and 'id="sort"' in page
    bd.move_group("House", -1)
    assert bd.load_groups()["groups"] == ["House", "Side projects"]
    assert bd.rename_group("House", "Home") == "Home" and bd.projects([root])[0].group == "Home"
    assert bd.delete_group("Home") == 1 and bd.projects([root])[0].group == ""
    assert sorted(x.name for x in p.iterdir()) == before  # nothing on disk moved
    sig = bd.signature(bd.projects([root]))
    bd.assign_group(str(p), "Side projects")
    assert bd.signature(bd.projects([root])) != sig  # the page refreshes after a drop


def test_server_folder_routes(site, tmp_path):
    root, p = site
    server, base = run_server(root, [])
    try:
        res = post(base + "/group/add", {"token": "test-token", "name": "Thesis"})
        assert "Added the folder Thesis" in res.read().decode()
        r = json.loads(post(base + "/group/move", {"token": "test-token", "path": str(p), "group": "Thesis"}).read())
        assert r["ok"] and bd.load_groups()["assign"] == {str(p): "Thesis"}
        page = urllib.request.urlopen(base + f"/project?p={urllib.parse.quote(str(p))}", timeout=5).read().decode()
        assert 'data-group-for=' in page and '<option value="Thesis" selected>' in page
        with pytest.raises(urllib.error.HTTPError) as e:
            post(base + "/group/move", {"token": "test-token", "path": str(tmp_path), "group": "Thesis"})
        assert e.value.code == 400
        r = json.loads(post(base + "/group/move", {"token": "test-token", "path": str(p), "group": ""}).read())
        assert r["ok"] and bd.load_groups()["assign"] == {}
        res = post(base + "/group/delete", {"token": "test-token", "name": "Thesis"})
        assert "Removed the folder" in res.read().decode() and bd.load_groups()["groups"] == []
    finally:
        server.shutdown()
        server.server_close()
