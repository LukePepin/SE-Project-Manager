"""T-3 (SE-03): the privacy check blocks a seeded leak and passes a clean push."""

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / ".claude" / "skills" / "privacy" / "privacy_check.py"
spec = importlib.util.spec_from_file_location("privacy_check", SCRIPT)
pc = importlib.util.module_from_spec(spec)
sys.modules["privacy_check"] = pc
spec.loader.exec_module(pc)

# Fake secrets are assembled at run time so this file never matches its own patterns.
FAKE_AWS = "AKIA" + "Q" * 16
FAKE_GH = "ghp" + "_" + "a1" * 20

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="needs git")


def sh(cwd, *args, check=True):
    return subprocess.run(list(args), cwd=cwd, capture_output=True, text=True, check=check)


def make_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    sh(repo, "git", "init", "-q", "-b", "main")
    sh(repo, "git", "config", "user.email", "test@example.com")
    sh(repo, "git", "config", "user.name", "Test")
    (repo / "scripts").mkdir()
    shutil.copy(SCRIPT, repo / "scripts" / "privacy_check.py")
    return repo


def test_scan_finds_terms_and_secrets_but_honors_allow():
    files = [
        ("notes.md", "met Pat Example at the lab\nkey " + FAKE_AWS + "\nfine line\n"),
        ("ok.md", "the word example here  privacy: allow\n"),
        ("cfg.py", "token = '" + FAKE_GH + "'\n"),
        (".env", "X=1\n"),
    ]
    hits = pc.scan(files, [("pat example", "collaborator name"), ("example", "word")])
    assert "notes.md:1: collaborator name" in hits
    assert "notes.md:2: AWS access key id" in hits
    assert any(h.startswith("cfg.py:1:") for h in hits)
    assert ".env: .env file" in hits
    assert not any(h.startswith("ok.md") for h in hits)
    assert all(FAKE_AWS not in h and "Pat Example" not in h for h in hits)  # never echo the secret


def test_term_list_must_not_be_published():
    hits = pc.scan([(".privacy-terms", "secret name\n")], [])
    assert hits and "must be git-ignored" in hits[0]


def test_pre_push_hook_blocks_leak_then_allows_clean_push(tmp_path):
    repo = make_repo(tmp_path)
    remote = tmp_path / "remote.git"
    sh(tmp_path, "git", "init", "-q", "--bare", str(remote))
    sh(repo, "git", "remote", "add", "origin", str(remote))
    code = pc.main(["--repo", str(repo), "--install-hook"])
    assert code == 0 and ".privacy-terms" in (repo / ".gitignore").read_text()
    (repo / ".privacy-terms").write_text("Zanzibar Quill  # fake private term\n")

    (repo / "plan.md").write_text("Meeting with Zanzibar Quill on Friday.\n")
    sh(repo, "git", "add", "-A")
    sh(repo, "git", "commit", "-q", "-m", "leak")
    blocked = sh(repo, "git", "push", "-q", "origin", "main", check=False)
    assert blocked.returncode != 0
    assert "fake private term" in blocked.stdout + blocked.stderr
    assert sh(remote, "git", "branch", "--list").stdout.strip() == ""  # nothing arrived

    (repo / "plan.md").write_text("Meeting on Friday.\n")
    sh(repo, "git", "commit", "-q", "-am", "fix")
    clean = sh(repo, "git", "push", "-q", "origin", "main", check=False)
    assert clean.returncode == 0, clean.stdout + clean.stderr
    assert "main" in sh(remote, "git", "branch", "--list").stdout


def test_private_branches_are_never_pushed(tmp_path):
    repo = make_repo(tmp_path)
    remote = tmp_path / "remote.git"
    sh(tmp_path, "git", "init", "-q", "--bare", str(remote))
    sh(repo, "git", "remote", "add", "origin", str(remote))
    pc.main(["--repo", str(repo), "--install-hook"])
    (repo / "a.md").write_text("hello\n")
    sh(repo, "git", "add", "-A")
    sh(repo, "git", "commit", "-q", "-m", "a")
    sh(repo, "git", "checkout", "-q", "-b", "private-notes")
    res = sh(repo, "git", "push", "-q", "origin", "private-notes", check=False)
    assert res.returncode != 0 and "private branch" in res.stdout + res.stderr


def test_install_refuses_to_clobber_a_different_hook(tmp_path):
    repo = make_repo(tmp_path)
    hook = repo / ".git" / "hooks" / "pre-push"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/bin/sh\necho mine\n")
    assert pc.main(["--repo", str(repo), "--install-hook"]) == 2
    assert hook.read_text() == "#!/bin/sh\necho mine\n"


def test_global_terms_apply_to_every_project(tmp_path, monkeypatch):
    g = tmp_path / "global"
    g.write_text("Quokka Lane  # Luke location\n")
    monkeypatch.setenv("GPP_PRIVACY_GLOBAL", str(g))
    repo = make_repo(tmp_path)
    (repo / "a.md").write_text("we live on Quokka Lane\n")
    assert pc.main(["--repo", str(repo)]) == 1
    hits = pc.scan([("a.md", "we live on Quokka Lane\n")], pc.load_terms(repo))
    assert hits == ["a.md:1: Luke location"]
    assert pc.scan([(".privacy-terms.global", "x\n")], [])  # the global list is never publishable


def test_all_history_finds_a_leak_that_was_later_removed(tmp_path, monkeypatch):
    monkeypatch.setenv("GPP_PRIVACY_GLOBAL", str(tmp_path / "none"))
    repo = make_repo(tmp_path)
    (repo / ".privacy-terms").write_text("Zanzibar Quill  # fake private term\n")
    (repo / ".gitignore").write_text(".privacy-terms\n")
    (repo / "a.md").write_text("Zanzibar Quill was here\n")
    sh(repo, "git", "add", "-A")
    sh(repo, "git", "commit", "-q", "-m", "leak")
    (repo / "a.md").write_text("clean\n")
    sh(repo, "git", "commit", "-q", "-am", "clean")
    assert pc.main(["--repo", str(repo)]) == 0
    assert pc.main(["--repo", str(repo), "--all-history"]) == 1
