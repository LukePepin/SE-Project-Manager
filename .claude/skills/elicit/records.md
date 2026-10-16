# Elicitation record formats

**Status: PROPOSED.** AI-drafted by Claude on 2026-10-08.

Every file lives in `docs/se/elicitation/<YYYY-MM-DD>/` in the project.

**Status line.** Every Markdown file Claude writes here starts, under its title, with:

```
**Status: DRAFT.** Written by Claude from Luke's elicitation on <date>, tier <tier>. Stated items are Luke's words; everything else is `PROPOSED` until Luke confirms it.
```

The exceptions:
- `dump.md` starts with its own **Verbatim** line instead, because it is not AI-drafted.
- CSV files have no status line, because `prioritize.py` reads their first row as the header.
- `prioritization.md` is written by the script, with its own status line.

## context.md

Written by `context_pack.py` (Docket excerpts, verbatim and labeled), plus `## Calendar` and `## Todoist` sections Claude adds from read-only connectors. Personal: it is git-ignored, and it holds no confirmation numbers, links, locations or attendees.

## dump.md

```
# Brain dump: <project>, <date>

**Verbatim.** Luke's words, unedited, split at paragraph breaks. Tier: <tier>. Nothing here is drafted by Claude.

**P1.** <Luke's first paragraph, exactly as given>

**P2.** ...
```

A paragraph longer than about five sentences is also split into a numbered list of its sentences, one per line, with no word changed. Cite them as `dump P1.S7`.

## items.md

| ID | Type | Statement | Source | Basis | Lens | Status |
|---|---|---|---|---|---|---|
| E-001 | Need | "set it up once and reuse it" | dump P2 | stated | L1, L2 | active |
| E-002 | Constraint | Must run on macOS and Windows | inferred from E-014 | inferred | L5 | active |
| E-003 | Need | "the PI wants fewer conflicts" | dump P1, via the PI | stated | L1, L12 | active |
| E-004 | Question | Review time per week: none yet | R1.Q2 | stated | L7 | open |

- **Type:** Need, Constraint, Assumption, Stakeholder, Alternative, Risk, Measure, Out, Decision, Question.
- **Source:** `dump P<n>` or `dump P<n>.S<m>`, `R<round>.Q<n>`, `R<round>.X<n>` (said in a round without being asked), `S4.Q<n>`, `S5.Q<n>`, `S6.Q<n>`, `S7.Q<n>`, `explain-back (<file>)`, `chat <date>` (said outside a round, recorded later as an addendum), or `inferred from E-nnn` / `inferred from <file>`. Add `via <who>` when Luke relays someone else's want.
- **Basis:** `stated`, `inferred` or `context` (from `context.md`: Docket, Calendar or Todoist; D-039). Only Luke's confirmation (in a round, or in Stage 4 or 5) changes inferred to stated, and the Source then gains the round, e.g. `inferred from E-014; confirmed R2.Q1`.
- **Lens:** every lens the item covers. Only a stated item covers a lens.
- **Status:** `active`, `changed` (the Statement is edited, and the old text stays in `rounds.md`) or `dropped`. A Question item is `open` until answered, then `answered (E-nnn)`.

## rounds.md

```
## Round 1: <date>

| Q | Question | Lens / item | Luke's answer (verbatim) |
|---|---|---|---|
| R1.Q1 | What else could solve this, including doing nothing? | L15 | ... |

New: 2 Need, 1 Constraint, 0 Stakeholder, 0 Assumption, 1 Risk. Confirmed: E-002. Dropped: none.
```

At the end of the rounds:

```
## Stop

Reason: saturated | covered (Immediate) | stopped by Luke, not saturated | cap reached, not saturated
Uncovered lenses: ...

| Round | New stated N/C/S/A | New (all types) | Total items |
|---|---|---|---|
| dump | 14 | 22 | 22 |
| R1 | 5 | 7 | 29 |
| R2 | 0 | 1 | 30 |
| R3 | 0 | 0 | 30 |

Added after the stop (Stages 4 and 5): 2
```

Then, if the stages run:

```
## Stage 4

| Q | Question | Luke's answer (verbatim) |
|---|---|---|
| S4.Q1 | Picture every measure at its worst... which one would you move to its best? | ... |

## Stage 5

Stage 5 skipped: no hours budget.   <- or the S5 questions and answers, in the same table form
```

## goal.md (Immediate tier only)

```
# Goal

**Status: DRAFT.** ...

**Goal:** <one line> (E-001, E-003)
**Done when:** <one line, in Luke's words where possible> (E-007)
```

The initializer copies these two lines into the project README.

## weights.md and weights.csv

| Measure | Worst | Best | Rank | Swing | Weight |
|---|---|---|---|---|---|
| time_saved | rebuild by hand every time | new project ready in one command | 1 | 100 | 0.45 |

`weights.csv` (read by `prioritize.py`):

```
measure,swing
time_saved,100
privacy,80
```

The measure names must match the score columns in `items.csv`.

## items.csv

```
id,label,hours,requires,must,time_saved,privacy
E-003,Pre-push privacy scan,3,,yes,1,10
E-004,Term list per project,1,E-003,,1,7
```

- `requires` is a `;`-separated list of ids.
- `must` is `yes` or blank.
- Every column other than `id`, `label`, `hours`, `requires` and `must` is a value measure scored 0 to 10.

## prioritization.md

This file is written by `prioritize.py --out`. Do not edit it by hand. Rerun the script instead.

## cns.md

These are the sections listed in SKILL.md Stage 6. Every sentence cites E-ids or a question id, a section with nothing recorded says "none recorded", and the file ends with an explain-back.

## reconciliation.md

```
# Reconciliation: SE set vs elicitation, <date>

Requirements: 37. Traced to a stated item: n. Traced to inferred items only: n. Claude-originated, unconfirmed: n.
Items with no requirement: n.

| Requirement | Supported by | Verdict |
|---|---|---|
| LIB-01 | E-004 (stated) | traced |
| DASH-04 | none | Claude-originated, unconfirmed |
```
