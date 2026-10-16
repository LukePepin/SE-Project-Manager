"""SAFE-03 and D-044: only accepted, unchanged skills leave the repo, as pinned copies."""

import importlib.util
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("install_skills", ROOT / "dashboard" / "install_skills.py")
inst = importlib.util.module_from_spec(spec)
sys.modules["install_skills"] = inst
spec.loader.exec_module(inst)


def lib(tmp_path):
    repo = tmp_path / "repo"
    for name, status in (("alpha", "ACCEPTED"), ("beta", "REVIEWED")):
        d = repo / ".claude" / "skills" / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(f"---\nname: {name}\n---\n\n**Status: {status}** (test).\n")
        (d / "tool.py").write_text("print(1)\n")
    inst.accept("alpha", "Luke, test", repo, when="2026-10-09")
    return repo


def test_only_accepted_unchanged_skills_are_installed_as_copies(tmp_path):
    repo, home = lib(tmp_path), tmp_path / "home"
    assert inst.review_state(repo) == {"alpha": "accepted", "beta": "reviewed"}
    res = inst.install(repo, home)
    dest = inst.user_dir(home) / "alpha"
    assert res["alpha"] == "installed (pinned copy)" and "beta" not in res
    assert dest.is_dir() and not dest.is_symlink() and not (inst.user_dir(home) / "beta").exists()
    assert inst.status(repo, home) == {"alpha": "installed"}


def test_a_change_after_acceptance_withdraws_the_skill(tmp_path):
    repo, home = lib(tmp_path), tmp_path / "home"
    inst.install(repo, home)
    (repo / ".claude" / "skills" / "alpha" / "tool.py").write_text("print('changed')\n")
    assert inst.review_state(repo)["alpha"] == "changed since acceptance"
    installed_copy = (inst.user_dir(home) / "alpha" / "tool.py").read_text()
    assert installed_copy == "print(1)\n"  # the edit did not reach other chats
    res = inst.install(repo, home)
    assert res["alpha"].startswith("withdrawn") and not (inst.user_dir(home) / "alpha").exists()


def test_accept_refuses_a_skill_not_marked_accepted(tmp_path):
    repo = lib(tmp_path)
    try:
        inst.accept("beta", "x", repo)
        raise AssertionError("should refuse")
    except ValueError:
        pass


def test_old_links_are_replaced_and_foreign_skills_left_alone(tmp_path):
    repo, home = lib(tmp_path), tmp_path / "home"
    target = inst.user_dir(home)
    target.mkdir(parents=True)
    (target / "beta").symlink_to(repo / ".claude" / "skills" / "beta")
    foreign = target / "alpha"
    foreign.mkdir()
    (foreign / "SKILL.md").write_text("someone else's\n")
    res = inst.install(repo, home)
    assert res["alpha"].startswith("blocked") and (foreign / "SKILL.md").read_text() == "someone else's\n"
    assert res["beta"].startswith("withdrawn") and not (target / "beta").exists()


def test_the_real_library_ledger_matches_its_accepted_skills():
    states = inst.review_state(ROOT)
    assert "changed since acceptance" not in states.values(), states
