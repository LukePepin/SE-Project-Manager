---
name: timeplan
description: Suggest how many hours a project deserves (the time equation), and propose its gate dates and calendar blocks. Nothing goes into Todoist, Calendar or GitHub until Luke approves. Use after the warden says go or shrink, when Luke asks "how long should this take?", "when will it be done?" or "make me a timeline", and at closeout to record actual hours.
argument-hint: "[project folder or name]"
---

# Timeplan: hours and dates

**Status: ACCEPTED** (explain-back answered and skills authorized by Luke, 2026-10-08, D-029). AI-drafted by Claude on 2026-10-08 from Luke's direction (Games-People-Play D-015, D-017, D-018; TIME-01 to TIME-03, TL-01, TL-02, INT-01, INT-02).

Both scripts use only the Python standard library, so any `python3` runs them.

## 1. Suggest hours (time equation)

1. Ask Luke in one multiple-choice box. Pre-fill from the elicitation record if it already holds an answer, and cite it.
   - **purpose**, 1 to 5: how much the outcome matters;
   - **length**: tiny (about 1 h of doing), small (4), medium (16), large (64), or a number of hours;
   - **complexity**, 1 to 5;
   - **availability**: hours per week.
2. Run:
   ```
   python <this skill>/time_equation.py suggest --purpose P --length L --complexity K --availability A --out <folder>/time.md
   ```
3. Tell Luke the suggested hours, the verdict and the tier. The verdict goes to the warden: a no-go or shrink here is a warden reason.
4. **Luke sets the budget.** Record both numbers in `time.md`: "Suggested h\*, Luke's budget H" (TIME-02). Never replace Luke's number with the suggestion.

## 2. Propose a timeline

1. Ask for the start date, and whether Luke wants weekly deep-work blocks (which day and time) and GitHub milestones (which repo).
2. Run:
   ```
   python <this skill>/timeline.py --hours H --per-week A --start YYYY-MM-DD --tier T --project NAME [--block SAT@10:00] [--github owner/repo] --out-dir <folder>
   ```
3. Show `timeline.md`, then ask **once, item by item**:
   - add the gates to Todoist;
   - import `timeline.ics` into Calendar (or create the events through the Calendar connector);
   - run the GitHub milestone commands.

   Do only what Luke approves, in that session (SAFE-05, TL-02). Until then, every date stays `PROPOSED`, and SE-00 mirrors Todoist, not this file.

## 3. Record actual hours, at each gate and at closeout

```
python <this skill>/time_equation.py record --project NAME --stage G1 --suggested S --actual A
```

Record progress at every gate you pass (`--stage G0`, `G1`, …), with the suggested and actual hours for that stage, not only at closeout (`--stage closeout`, the default). Before proposing a new timeline, read `calibration.csv` and say how past projects actually went.

This appends to `calibration.csv` and reports the error. Later suggestions are scaled by the median of actual/suggested (TIME-03).

## The equation

`need = length × complexity factor × calibration`. The outcome is worth `r` times its need (from purpose). An hour costs `c = max(1, 5 / availability)`. With diminishing returns `V(h) = r·need·(1 − e^(−h/need))`, the best number of hours is where the next hour stops paying for itself:

**h\* = need × ln(r / c)**, and 0 when r ≤ c (not worth starting).

The constants are Claude's `PROPOSED` defaults, listed at the top of `time_equation.py`. Calibration corrects them over time; Luke can also change them directly.

---

**Explain-back (Luke):** Why can the equation say no-go for a project you care about, and what makes its suggestions improve over time?

> the equation could say that the complexity and other factors are the proper are too long for its effort i.e the juice isn;t worth the squeeze, to improve the timeplan overtime review preview timeplans and when a project is completed or progressing access its data to see how long these things take.
>
> *(Answered 2026-10-08 in the review packet.)*
