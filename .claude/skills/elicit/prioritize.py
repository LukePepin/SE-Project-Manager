"""Stage 5 of /elicit: pick what fits the hours budget, and show how sure the pick is.

Status: PROPOSED (AI-drafted by Claude on 2026-10-08; not reviewed by Luke).

The model is the Next Release Problem (Bagnall, Rayward-Smith and Whittley, 2001),
a 0-1 knapsack with precedence:

    maximize    sum_i v_i x_i
    subject to  sum_i h_i x_i <= H            (Luke's hours budget, never invented)
                x_i >= x_j  when j requires i (dependencies)
                x_i  = 1    when i is a Must
                x_i in {0, 1}

v_i = sum_k w_k s_ik: swing weights w (normalized to sum 1) times Luke's 0-10 scores s.
Among equal-value picks the solver prefers fewer hours (a tie-break, not a goal).

Build order: the picked items in the order to build them, so that whenever work stops,
the most value is already done. Musts and what they require come first; within each group,
the available item with the most value per hour goes next, never ahead of what it requires.

Sensitivity: each draw perturbs the weights (Dirichlet around the elicited weights)
and every item's hours (times U(low, high), skewed high for the planning fallacy),
then re-solves. The share of draws that select an item says how robust the pick is.

Inputs:
  items.csv    columns id, hours, requires, must, plus optional label; every other
               column is a value measure scored 0-10. `requires` is a ;-separated id list.
  weights.csv  columns measure, swing (0-100 swing points; normalized here).

Usage:
  python prioritize.py items.csv weights.csv --budget 20 [--draws 1000] [--seed 0] [--out file.md]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

RESERVED = {"id", "label", "hours", "requires", "must"}
TRUE = {"1", "yes", "y", "true", "must"}
ROBUST, CONTESTED = 0.9, 0.1


@dataclass
class Items:
    ids: list[str]
    labels: list[str]
    hours: np.ndarray
    requires: list[list[int]]  # requires[j] = indices that j depends on
    must: np.ndarray  # bool
    measures: list[str]
    scores: np.ndarray  # shape (n_items, n_measures)


@dataclass
class Solution:
    feasible: bool
    selected: np.ndarray  # bool
    value: float
    hours: float
    overrun: float = 0.0  # hours over budget of the Must closure, when infeasible


def load_items(path: str | Path) -> Items:
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"{path}: no items")
    measures = [c for c in rows[0] if c not in RESERVED]
    if not measures:
        raise ValueError(f"{path}: no value-measure columns besides {sorted(RESERVED)}")
    ids = [r["id"].strip() for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError(f"{path}: duplicate ids")
    index = {i: k for k, i in enumerate(ids)}
    requires = []
    for r in rows:
        deps = [d.strip() for d in (r.get("requires") or "").split(";") if d.strip()]
        unknown = [d for d in deps if d not in index]
        if unknown:
            raise ValueError(f"{path}: {r['id']} requires unknown id(s) {unknown}")
        requires.append([index[d] for d in deps])
    scores = np.array([[float(r[m] or 0) for m in measures] for r in rows])
    if (scores < 0).any() or (scores > 10).any():
        raise ValueError(f"{path}: scores must be in 0-10")
    hours = np.array([float(r["hours"]) for r in rows])
    if (hours < 0).any():
        raise ValueError(f"{path}: hours must be non-negative")
    return Items(
        ids=ids,
        labels=[(r.get("label") or "").strip() for r in rows],
        hours=hours,
        requires=requires,
        must=np.array([(r.get("must") or "").strip().lower() in TRUE for r in rows]),
        measures=measures,
        scores=scores,
    )


def load_weights(path: str | Path, measures: list[str]) -> np.ndarray:
    with open(path, newline="", encoding="utf-8") as f:
        swing = {r["measure"].strip(): float(r["swing"]) for r in csv.DictReader(f)}
    missing = [m for m in measures if m not in swing]
    extra = [m for m in swing if m not in measures]
    if missing or extra:
        raise ValueError(f"{path}: weights do not match item measures (missing {missing}, extra {extra})")
    w = np.array([swing[m] for m in measures])
    if (w < 0).any() or w.sum() <= 0:
        raise ValueError(f"{path}: swings must be non-negative with a positive total")
    return w / w.sum()


def must_closure(items: Items) -> np.ndarray:
    """Every Must item plus everything it transitively requires."""
    keep = items.must.copy()
    stack = list(np.flatnonzero(keep))
    while stack:
        j = stack.pop()
        for i in items.requires[j]:
            if not keep[i]:
                keep[i] = True
                stack.append(i)
    return keep


def solve(items: Items, values: np.ndarray, hours: np.ndarray, budget: float) -> Solution:
    n = len(items.ids)
    closure = must_closure(items)
    need = float(hours[closure].sum())
    if need > budget + 1e-9:
        return Solution(False, closure, float(values[closure].sum()), need, need - budget)

    rows, lb, ub = [hours], [-np.inf], [budget]
    for j, deps in enumerate(items.requires):
        for i in deps:  # x_j - x_i <= 0
            row = np.zeros(n)
            row[j], row[i] = 1.0, -1.0
            rows.append(row)
            lb.append(-np.inf)
            ub.append(0.0)
    tie = 1e-6 * hours / max(float(hours.max()), 1.0)
    res = milp(
        c=-(values - tie),
        constraints=LinearConstraint(np.vstack(rows), lb, ub),
        integrality=np.ones(n),
        bounds=Bounds(items.must.astype(float), np.ones(n)),
    )
    if not res.success:
        raise RuntimeError(f"solver failed: {res.message}")
    x = res.x > 0.5
    return Solution(True, x, float(values[x].sum()), float(hours[x].sum()))


def sensitivity(
    items: Items,
    weights: np.ndarray,
    budget: float,
    draws: int = 1000,
    seed: int = 0,
    concentration: float = 50.0,
    hours_low: float = 0.75,
    hours_high: float = 1.5,
) -> tuple[np.ndarray, float]:
    """Share of draws selecting each item, and the share of draws where the Must set did not fit."""
    rng = np.random.default_rng(seed)
    hits = np.zeros(len(items.ids))
    infeasible = 0
    live = weights > 0  # a measure Luke gave zero swing stays at zero
    for _ in range(draws):
        w = np.zeros_like(weights)
        w[live] = rng.dirichlet(concentration * weights[live])
        h = items.hours * rng.uniform(hours_low, hours_high, size=len(items.ids))
        sol = solve(items, items.scores @ w, h, budget)
        if sol.feasible:
            hits += sol.selected
        else:
            infeasible += 1
    feasible = draws - infeasible
    freq = hits / feasible if feasible else np.zeros(len(items.ids))
    return freq, infeasible / draws


def build_order(items: Items, values: np.ndarray, selected: np.ndarray) -> list[int]:
    """Greedy order over the selected items: Must closure first, then value per hour, dependencies respected."""
    first = must_closure(items)
    done: set[int] = set()
    order: list[int] = []
    todo = set(np.flatnonzero(selected))
    while todo:
        ready = [k for k in todo if all(i in done for i in items.requires[k])]
        if not ready:  # a dependency cycle: take the rest in id order
            ready = sorted(todo)
        density = lambda k: values[k] / items.hours[k] if items.hours[k] > 0 else np.inf
        k = min(ready, key=lambda k: (not first[k], -density(k), items.ids[k]))
        order.append(k)
        done.add(k)
        todo.discard(k)
    return order


def _sha(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:12]


def render(items, weights, budget, base, freq, infeasible_share, args) -> str:
    v = items.scores @ weights
    out = [
        "# Prioritization (Stage 5)",
        "",
        "**Status: PROPOSED.** Generated by `prioritize.py`. The weights come from Luke's swings. Whether each"
        " row's hours and scores are Luke's or Claude's is recorded in `items.md` and `rounds.md`, not here."
        " The pick is advice, and Luke decides.",
        "",
        f"- Budget H: **{budget:g} h**",
        f"- Inputs: `{args.items}` (sha256 {_sha(args.items)}), `{args.weights}` (sha256 {_sha(args.weights)})",
        f"- Sensitivity: {args.draws} draws, seed {args.seed}, Dirichlet concentration {args.concentration:g},"
        f" hours x U({args.hours_low:g}, {args.hours_high:g})",
        "",
        "## Weights",
        "",
        "| Measure | Weight |",
        "|---|---|",
        *[f"| {m} | {w:.3f} |" for m, w in zip(items.measures, weights)],
        "",
        "## Base pick",
        "",
    ]
    if not base.feasible:
        names = ", ".join(i for i, k in zip(items.ids, base.selected) if k)
        out += [
            f"**Infeasible:** the Must items and what they require ({names}) need {base.hours:g} h,"
            f" {base.overrun:g} h over the budget. The Must tier does not fit; cut it or raise H.",
            "",
        ]
        return "\n".join(out)
    out += [
        f"Selected value {base.value:.2f} of {v.sum():.2f} available, using {base.hours:g} of {budget:g} h.",
        "",
        f"In {infeasible_share:.0%} of draws the Must set did not fit the budget." if infeasible_share else
        "The Must set fit the budget in every draw.",
        "",
        "| ID | Label | Must | Hours | Value | Base pick | Picked in draws | Read |",
        "|---|---|---|---|---|---|---|---|",
    ]
    order = sorted(range(len(items.ids)), key=lambda k: (-freq[k], -v[k]))
    for k in order:
        read = "robust" if freq[k] >= ROBUST else "contested" if freq[k] > CONTESTED else "out"
        out.append(
            f"| {items.ids[k]} | {items.labels[k]} | {'yes' if items.must[k] else ''} | {items.hours[k]:g}"
            f" | {v[k]:.2f} | {'x' if base.selected[k] else ''} | {freq[k]:.0%} | {read} |"
        )
    out += [
        "",
        f"**Robust** (picked in at least {ROBUST:.0%} of draws) is the MVCR candidate."
        f" **Contested** ({CONTESTED:.0%} to {ROBUST:.0%}) needs Luke's call; the weights alone do not settle it.",
        "",
        "## Build order",
        "",
        "Build the picked items in this order. If work stops early, everything above the stopping point is done:"
        " Musts and their prerequisites first, then the most value per hour.",
        "",
        "| Step | ID | Label | Must | Hours | Value per hour | Hours so far | Value so far |",
        "|---|---|---|---|---|---|---|---|",
    ]
    hours_so_far = value_so_far = 0.0
    for step, k in enumerate(build_order(items, v, base.selected), 1):
        hours_so_far += items.hours[k]
        value_so_far += v[k]
        vph = f"{v[k] / items.hours[k]:.2f}" if items.hours[k] > 0 else "-"
        out.append(
            f"| {step} | {items.ids[k]} | {items.labels[k]} | {'yes' if items.must[k] else ''} | {items.hours[k]:g}"
            f" | {vph} | {hours_so_far:g} | {value_so_far:.2f} |"
        )
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("items")
    p.add_argument("weights")
    p.add_argument("--budget", type=float, required=True, help="hours budget H, from Luke")
    p.add_argument("--draws", type=int, default=1000)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--concentration", type=float, default=50.0)
    p.add_argument("--hours-low", type=float, default=0.75)
    p.add_argument("--hours-high", type=float, default=1.5)
    p.add_argument("--out", help="write the Markdown report here instead of stdout")
    args = p.parse_args(argv)

    items = load_items(args.items)
    weights = load_weights(args.weights, items.measures)
    base = solve(items, items.scores @ weights, items.hours, args.budget)
    if base.feasible:
        freq, inf = sensitivity(
            items, weights, args.budget, args.draws, args.seed, args.concentration, args.hours_low, args.hours_high
        )
    else:
        freq, inf = np.zeros(len(items.ids)), 1.0
    report = render(items, weights, args.budget, base, freq, inf, args)
    if args.out:
        Path(args.out).write_text(report + "\n", encoding="utf-8")
    else:
        print(report)
    return 0 if base.feasible else 2


if __name__ == "__main__":
    sys.exit(main())
