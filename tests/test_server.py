"""D-034: the dashboard server's New project, notes and next-step recommendations."""

import importlib.util
import re
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


def test_create_project_makes_only_a_candidate_folder(tmp_path):
    t = srv.create_project([tmp_path], str(tmp_path), "Attic", "household", "Clear the attic.\nIt is full.", when="2026-10-09 10:00")
    assert sorted(p.name for p in t.iterdir()) == [".gpp-project", "brain_dump.md", "notes.md"]
    assert "Clear the attic.\nIt is full." in (t / "brain_dump.md").read_text()
    p = bd.scan_project(t)
    assert p.tier == "idea" and p.kind == "household"
    assert bd.recommend(p) == ("Large: run the full gate from your brain dump", f"/elicit long {t}")
    assert bd.KIND_LABEL[p.kind] == "Hands-on"


@pytest.mark.parametrize("name", ["../escape", ".hidden", "a/b", "", "x" * 61])
def test_bad_names_are_refused(tmp_path, name):
    with pytest.raises(srv.Refused):
        srv.create_project([tmp_path], str(tmp_path), name, "code", "")


def test_unknown_root_and_existing_folder_are_refused(tmp_path):
    with pytest.raises(srv.Refused, match="roots"):
        srv.create_project([tmp_path / "a"], str(tmp_path), "X", "code", "")
    srv.create_project([tmp_path], str(tmp_path), "X", "code", "")
    with pytest.raises(srv.Refused, match="exists"):
        srv.create_project([tmp_path], str(tmp_path), "X", "code", "")


def test_notes_append_only_to_known_projects(tmp_path):
    t = srv.create_project([tmp_path], str(tmp_path), "P", "code", "")
    srv.add_note([t], str(t), "first", when="2026-10-09 10:00")
    srv.add_note([t], str(t), "second thought", when="2026-10-09 11:00")
    text = (t / "notes.md").read_text()
    assert text.index("first") < text.index("second thought")
    p = bd.scan_project(t)
    assert p.notes == 2 and p.last_note == "second thought" and not p.dump
    with pytest.raises(srv.Refused):
        srv.add_note([t], str(tmp_path / "elsewhere"), "x")


def test_recommendations_walk_the_flow(tmp_path):
    t = srv.create_project([tmp_path], str(tmp_path), "Flow", "code", "")
    rec = t / "docs" / "se" / "elicitation" / "2026-10-09"
    rec.mkdir(parents=True)
    (rec / "items.md").write_text("| E-001 | Need | x | dump P1 | stated | L1 | active |\n")
    assert bd.recommend(bd.scan_project(t))[1].startswith("/warden ")
    (rec / "verdict.md").write_text("**Verdict: GO.** ok\n")
    assert bd.recommend(bd.scan_project(t))[1] == f"/timeplan {t}"
    (rec / "time.md").write_text("x\n")
    assert bd.recommend(bd.scan_project(t))[1] == f"/initialize {t} --from {rec}"
    (rec / "verdict.md").write_text("**Verdict: NO-GO.** no\n")
    assert bd.recommend(bd.scan_project(t))[0].startswith("The warden said no")


def run_server(tmp_path):
    token = "test-token"  # fake test value; privacy: allow
    server = ThreadingHTTPServer(("127.0.0.1", 0), srv.make_handler([tmp_path], ROOT, token))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def post(url, data, origin=None):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode())
    if origin:
        req.add_header("Origin", origin)
    return urllib.request.urlopen(req, timeout=5)


def test_server_creates_projects_and_refuses_forged_requests(tmp_path):
    server, base = run_server(tmp_path)
    try:
        page = urllib.request.urlopen(base + "/", timeout=5).read().decode()
        assert 'name="gpp-token" content="test-token"' in page and "New project" in page
        new = urllib.request.urlopen(base + "/new", timeout=5).read().decode()
        assert 'name="token" value="test-token"' in new and 'action="/start"' in new and "<textarea" in new
        res = post(base + "/new", {"token": "test-token", "root": str(tmp_path), "name": "Demo", "kind": "code", "dump": "hi"})
        assert "Created" in res.read().decode() and (tmp_path / "Demo" / "notes.md").exists()
        with pytest.raises(urllib.error.HTTPError) as bad_token:
            post(base + "/new", {"token": "wrong", "root": str(tmp_path), "name": "Evil", "kind": "code"})
        assert bad_token.value.code == 403
        with pytest.raises(urllib.error.HTTPError) as cross:
            post(base + "/note", {"token": "test-token", "project": str(tmp_path / "Demo"), "text": "x"},
                 origin="https://evil.example")
        assert cross.value.code == 403
        assert not (tmp_path / "Evil").exists()
        stamp1 = urllib.request.urlopen(base + "/stamp", timeout=5).read().decode()
        post(base + "/note", {"token": "test-token", "project": str(tmp_path / "Demo"), "text": "changed"})
        assert urllib.request.urlopen(base + "/stamp", timeout=5).read().decode() != stamp1
    finally:
        server.shutdown()
        server.server_close()


def test_static_page_has_no_forms_or_script(tmp_path):
    page = bd.page([], bd.skills(ROOT), [tmp_path])
    assert "<form" not in page and "<script" not in page and "open_dashboard.command" in page
    assert not re.search(r"""(src|href)=["']https?://""", page)


def test_initialized_but_never_gated_projects_go_to_elicit(tmp_path):
    t = tmp_path / "old"
    (t / "docs" / "se").mkdir(parents=True)
    (t / "docs" / "se" / "SE-00_project_plan.md").write_text("# SE-00\n")
    step, prompt = bd.recommend(bd.scan_project(t))
    assert step.startswith("Never gated") and prompt == f"/elicit short {t}"


def test_every_prompt_starts_with_a_slash_command_or_plain_text(tmp_path):
    t = srv.create_project([tmp_path], str(tmp_path), "S", "code", "")
    prompt = bd.recommend(bd.scan_project(t))[1]
    assert re.match(r"^/[a-z-]+ ", prompt)


def test_second_launch_reuses_the_running_dashboard(tmp_path, monkeypatch):
    server, base = run_server(tmp_path)
    opened = []
    monkeypatch.setattr(srv.webbrowser, "open", lambda url: opened.append(url))
    try:
        port = server.server_address[1]
        assert srv.main(["--port", str(port), "--open", "--roots", str(tmp_path)]) == 0
        assert opened == [f"http://127.0.0.1:{port}/"]
    finally:
        server.shutdown()
        server.server_close()


def test_archive_toggles_without_touching_the_project(tmp_path, monkeypatch):
    archive = tmp_path / "archive.json"
    monkeypatch.setattr(bd, "ARCHIVE_FILE", archive)
    t = srv.create_project([tmp_path], str(tmp_path), "Park", "household", "")
    before = sorted(x.name for x in t.iterdir())
    bd.save_archive({str(t)}, archive)
    assert bd.projects([tmp_path], archive)[0].archived
    page = bd.page(bd.projects([tmp_path], archive), [], [tmp_path], token="x")
    assert "Archived (1)" in page and '<span class="meta">0 active' in page
    assert "Unarchive" in bd.pages().project_page(bd.projects([tmp_path], archive)[0], bd.Detail(), "x")
    assert sorted(x.name for x in t.iterdir()) == before
