"""T-14 and T-15 (SE-03): the /elicit prioritizer against hand-checkable cases."""

import importlib.util
import itertools
import sys
from pathlib import Path

import numpy as np
import pytest

SKILL = Path(__file__).resolve().parents[1] / ".claude" / "skills" / "elicit"
spec = importlib.util.spec_from_file_location("prioritize", SKILL / "prioritize.py")
pz = importlib.util.module_from_spec(spec)
sys.modules["prioritize"] = pz  # dataclasses look the module up while it loads
spec.loader.exec_module(pz)


def make(hours, requires=None, must=None, scores=None):
    n = len(hours)
    return pz.Items(
        ids=[f"E-{k:03d}" for k in range(n)],
        labels=[""] * n,
        hours=np.array(hours, dtype=float),
        requires=requires or [[] for _ in range(n)],
        must=np.array(must or [False] * n),
        measures=["m"],
        scores=np.array(scores if scores is not None else [[1.0]] * n),
    )


def brute_force(items, values, budget):
    best = -1.0
    n = len(items.ids)
    for bits in itertools.product([0, 1], repeat=n):
        x = np.array(bits, dtype=bool)
        if items.hours[x].sum() > budget + 1e-9:
            continue
        if any(x[j] and not x[i] for j, deps in enumerate(items.requires) for i in deps):
            continue
        if (items.must & ~x).any():
            continue
        best = max(best, values[x].sum())
    return best


def check_constraints(items, sol, budget):
    x = sol.selected
    assert items.hours[x].sum() <= budget + 1e-9
    assert not (items.must & ~x).any()
    for j, deps in enumerate(items.requires):
        for i in deps:
            assert not x[j] or x[i], f"{items.ids[j]} picked without {items.ids[i]}"


@pytest.mark.parametrize("seed", range(5))
def test_milp_matches_brute_force(seed):
    rng = np.random.default_rng(seed)
    n = 10
    requires = [[] for _ in range(n)]
    for j in range(1, n):
        if rng.random() < 0.4:
            requires[j] = [int(rng.integers(0, j))]
    must = [False] * n
    must[0] = True
    items = make(rng.integers(1, 8, n).tolist(), requires, must)
    values = rng.uniform(0, 10, n)
    budget = 20.0
    sol = pz.solve(items, values, items.hours, budget)
    assert sol.feasible
    check_constraints(items, sol, budget)
    assert sol.value == pytest.approx(brute_force(items, values, budget), abs=1e-6)


def test_dependency_pulls_in_its_prerequisite():
    # E-001 is worth a lot but needs E-000, which is worth nothing on its own.
    items = make([3, 3, 4], requires=[[], [0], []])
    sol = pz.solve(items, np.array([0.0, 10.0, 5.0]), items.hours, budget=6)
    assert sol.selected.tolist() == [True, True, False]


def test_infeasible_must_reports_overrun():
    # Must E-002 requires E-000; together 9 h against a budget of 6.
    items = make([4, 2, 5], requires=[[], [], [0]], must=[False, False, True])
    sol = pz.solve(items, np.ones(3), items.hours, budget=6)
    assert not sol.feasible
    assert sol.overrun == pytest.approx(3.0)
    assert sol.selected.tolist() == [True, False, True]


def test_zero_value_items_are_left_out():
    items = make([1, 1])
    sol = pz.solve(items, np.array([5.0, 0.0]), items.hours, budget=10)
    assert sol.selected.tolist() == [True, False]


def test_sensitivity_dominant_and_dominated():
    # E-000: high value, cheap. E-002: no value on any measure.
    items = make([1, 6, 2], scores=[[10.0, 10.0], [5.0, 4.0], [0.0, 0.0]])
    items.measures = ["a", "b"]
    freq, infeasible = pz.sensitivity(items, np.array([0.6, 0.4]), budget=5, draws=200, seed=1)
    assert infeasible == 0
    assert freq[0] == 1.0
    assert freq[2] == 0.0


def test_unknown_dependency_is_an_error(tmp_path):
    f = tmp_path / "items.csv"
    f.write_text("id,hours,requires,must,m\nE-001,1,E-999,,5\n")
    with pytest.raises(ValueError, match="unknown"):
        pz.load_items(f)


def test_weights_are_normalized_swings(tmp_path):
    f = tmp_path / "weights.csv"
    f.write_text("measure,swing\na,100\nb,60\nc,40\n")
    assert pz.load_weights(f, ["a", "b", "c"]) == pytest.approx([0.5, 0.3, 0.2])


def test_weights_must_match_measures(tmp_path):
    f = tmp_path / "weights.csv"
    f.write_text("measure,swing\na,100\n")
    with pytest.raises(ValueError, match="missing"):
        pz.load_weights(f, ["a", "b"])


def test_cli_on_the_example(tmp_path):
    out = tmp_path / "prioritization.md"
    code = pz.main([
        str(SKILL / "example" / "items.csv"),
        str(SKILL / "example" / "weights.csv"),
        "--budget", "12", "--draws", "200", "--out", str(out),
    ])
    text = out.read_text()
    assert code == 0
    assert "Budget H: **12 h**" in text
    assert "| E-001 |" in text and "| E-003 |" in text
    assert "seed 0" in text and text.count("sha256") == 2


def test_cli_exit_code_when_must_does_not_fit(tmp_path):
    out = tmp_path / "p.md"
    code = pz.main([
        str(SKILL / "example" / "items.csv"),
        str(SKILL / "example" / "weights.csv"),
        "--budget", "2", "--out", str(out),
    ])
    assert code == 2
    assert "Infeasible" in out.read_text()


def test_build_order_puts_musts_first_and_respects_dependencies():
    # E-002 is a Must that requires E-000; E-001 has the best value per hour but is not a Must.
    items = make([2, 1, 3], requires=[[], [], [0]], must=[False, False, True])
    values = np.array([1.0, 9.0, 3.0])
    order = pz.build_order(items, values, np.array([True, True, True]))
    assert order == [0, 2, 1]


def test_build_order_uses_value_per_hour_among_free_items():
    items = make([4, 1, 2])
    order = pz.build_order(items, np.array([4.0, 3.0, 5.0]), np.array([True, True, True]))
    assert order == [1, 2, 0]  # 3.0/h, 2.5/h, 1.0/h
