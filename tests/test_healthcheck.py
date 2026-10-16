"""T-20 (SE-03): the health check reports a broken skill and changes nothing."""

import importlib.util
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("healthcheck", ROOT / ".claude" / "skills" / "healthcheck" / "healthcheck.py")
st = importlib.util.module_from_spec(spec)
sys.modules["healthcheck"] = st
spec.loader.exec_module(st)


def copy_library(tmp_path):
    lib = tmp_path / "lib"
    shutil.copytree(ROOT / ".claude", lib / ".claude", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(ROOT / "dashboard", lib / "dashboard", ignore=shutil.ignore_patterns("index.html"))
    return lib


def test_clean_library_passes(tmp_path):
    lib = copy_library(tmp_path)
    assert all(ok for _, ok, _ in st.check_skills(lib) + st.check_compile(lib))
    assert st.check_dashboard(lib)[1]


def test_broken_skill_and_script_are_reported_and_left_alone(tmp_path):
    lib = copy_library(tmp_path)
    md = lib / ".claude" / "skills" / "warden" / "SKILL.md"
    md.write_text(md.read_text().replace("**Explain-back (Luke):**", "Explain:"))
    bad = lib / ".claude" / "skills" / "warden" / "gate_check.py"
    bad.write_text("def broken(:\n")
    before = (md.read_text(), bad.read_text())
    assert st.main(["--repo", str(lib), "--no-tests"]) == 1
    skills = {n: (ok, note) for n, ok, note in st.check_skills(lib)}
    assert skills["skill warden"] == (False, "no explain-back")
    assert not dict((n, ok) for n, ok, _ in st.check_compile(lib))["compile .claude/skills/warden/gate_check.py"]
    assert (md.read_text(), bad.read_text()) == before
