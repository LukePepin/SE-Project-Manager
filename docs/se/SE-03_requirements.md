# SE-03 Requirements and verification traceability

**Status: DRAFT,** current to D-060 (2026-10-10, closeout: every deferred requirement dropped). AI-drafted by Claude from Luke's direction. Explain-backs on SE documents are waived (D-029). Every behavior is `PROPOSED` unless it cites a D-nnn decision. **Frozen until G1** (D-027, W3): new needs go into the elicitation record (see Pending).

**Status progression:** `PROPOSED` → `REVIEWED` → `ACCEPTED` → `IMPLEMENTED` → `VERIFIED (test, evidence)`. Off the path: `DEFERRED (D-nnn)`, kept for later; `DROPPED (D-nnn)`, removed.

Each requirement has one "shall", one method (T test, D demonstration, I inspection) and a trace: needs (N), use cases (SE-02), decisions, and the Luke's-words items (E-nnn). E-ids are listed in [trace_items.md](trace_items.md), a committed, redacted copy of the git-ignored record. **Claude's** marks a requirement no Luke statement supports, kept by the decision named.

**Components:** Elic (`/elicit`), Opt (prioritizer), Ward (`/warden`), Time and TL (`/timeplan`), Init (`/initialize`), Aud (`/se-audit`), Dash (dashboard), Priv (`/privacy`), Lib (the library and its installer), Close (`/closeout`), Health (`/healthcheck`).

## Stakeholder needs

| Need | Statement |
|---|---|
| N1 | Luke starts a project without rebuilding the setup by hand. |
| N3 | A fix to a skill is made once and reaches every copy, after review. |
| N4 | Nothing private leaks. |
| N5 | Luke reviews and understands every AI-written piece before relying on it. |
| N6 | It costs little time (D-004) and works on Luke's machines (D-019). |
| N7 | The SE effort fits the project's size (D-006). |
| N8 | A closeout traces to recorded evidence (D-007). |
| N9 | What Luke knows is written down before drafting, and every requirement traces to Luke's words or is marked as Claude's (D-010). |
| N10 | Any project, technical or household, goes through the same gate (D-014). |
| N11 | A project gets the hours it is worth, and a no-go comes early (D-015, E-066). |

N2 (learning Claude's features) was dropped by D-021.

## ELIC: elicitation (D-010 to D-013, D-039, D-040)

| ID | Requirement | Method | Trace | Allocated | Verified by | Status |
|---|---|---|---|---|---|---|
| ELIC-01 | The elicit skill shall save Luke's brain dump and every probe answer verbatim before extracting anything from them. | I | N9; UC-13; D-013; E-016 | Elic | I-6 | PROPOSED |
| ELIC-02 | Every elicited item shall cite its source and carry one basis: stated, inferred or context. | T, I | N9; UC-13; D-039; E-020 | Elic | T-12, I-6 | PROPOSED |
| ELIC-03 | Each probe round shall ask at most five questions, open questions before closed ones. | I | N5; UC-14; R13; **Claude's** (D-044) | Elic | I-6 | PROPOSED |
| ELIC-04a | Elicitation shall stop on Luke's word, on the tier cap, or on its tier's stop rule as defined in the elicit skill. | T | N6; UC-14; D-012 | Elic | T-13 | PROPOSED |
| ELIC-04b | The record shall state the stop reason and show the discovery curve. | I | N9; UC-14; D-012 | Elic | I-6 | PROPOSED |
| ELIC-05 | Elicitation shall scale with the tier: a dump and one round for Immediate, at most six rounds for Short, at most ten for Long. | T | N7; UC-14; D-006; E-064 | Elic | T-13 | PROPOSED |
| ELIC-06a | The CNS shall be built from the record only, citing an E-id or question id in every sentence. | I | N9; UC-13; D-011; E-011 | Elic | I-6 | PROPOSED |
| ELIC-06b | The skill shall log as a decision only what Luke stated. | I | N5; UC-13; E-020 | Elic | I-6 | PROPOSED |
| ELIC-07 | When a project already has an SE set, the skill shall trace each requirement to stated items, inferred items only, or nothing, and propose edits without making them. | D | N9; UC-16; E-019 | Elic | DM-5 | PROPOSED |

## OPT: weighting and prioritization (D-012)

| ID | Requirement | Method | Trace | Allocated | Verified by | Status |
|---|---|---|---|---|---|---|
| OPT-01 | The weights shall come from Luke's swing ranking and swing points, normalized to sum to one. | T | N9; UC-15; D-012 | Opt | T-14 | PROPOSED |
| OPT-02a | Prioritization shall use only an hours budget, item hours and scores that Luke gave or confirmed. | I | N5; UC-15; D-016; E-068 | Elic | I-6 | PROPOSED |
| OPT-02b | With no budget, the record shall say that prioritization was skipped. | I | N9; UC-15; **Claude's** (D-044) | Elic | I-6 | PROPOSED |
| OPT-03 | The prioritizer shall return a pick of maximum weighted value within the budget that includes every Must item and every prerequisite of a picked item. | T | N11; UC-15; D-012; E-069 | Opt | T-14 | PROPOSED |
| OPT-04 | When the Must items and their prerequisites exceed the budget, the prioritizer shall report the overrun in hours instead of a pick. | T | N11; UC-15; R11; **Claude's** (D-044) | Opt | T-14 | PROPOSED |
| OPT-05 | The prioritizer shall report, for each item, the share of perturbed draws that select it, with the seed and a hash of each input. | T | N9; UC-15; R11; E-011 | Opt | T-15 | PROPOSED |

## GATE: warden, time and timeline (D-015)

| ID | Requirement | Method | Trace | Allocated | Verified by | Status |
|---|---|---|---|---|---|---|
| WARD-01 | After elicitation, the warden shall return go, shrink or no-go, with each reason citing E-ids. | T, I | N11; UC-17; D-015; E-006, E-010 | Ward | T-16, I-7 | PROPOSED |
| WARD-02a | The warden shall return no-go when the goal is undefined, cannot be tested, or rests mostly on Claude's inferences. | T | N11; UC-17; E-003, E-028 | Ward | T-16 | PROPOSED |
| WARD-02b | The initializer shall not run after a no-go unless Luke has logged an override decision. | T | N5; UC-17; D-032 | Init | T-21 | PROPOSED |
| WARD-03 | The warden's verdict shall be written to the project's record and shown on the dashboard. | I | N5; UC-17; E-020, E-083 | Ward, Dash | I-7 | PROPOSED |
| WARD-04 | The warden shall apply no rescope, redirect or cut until Luke approves it as a logged decision. | T | N5; UC-17; D-022; E-074, E-075, E-084 | Ward | T-16 | PROPOSED |
| TIME-01 | The time equation shall suggest a project's hours from its purpose, length, complexity and Luke's availability, in hours only. | T | N11; UC-18; D-017; E-042 | Time | T-17 | PROPOSED |
| TIME-02 | The record shall show both the suggested hours and Luke's budget. | I | N5; UC-18; E-068 | Time | I-7 | PROPOSED |
| TIME-03 | The time equation shall compare suggested with actual hours at each gate and at closeout, and scale later suggestions by the record. | T | N11; UC-18; E-085 | Time | T-17 | PROPOSED |
| TL-01 | The timeline tool shall propose gate dates from the budget and Luke's hours per week. | T | N1; UC-18; D-015; E-065 | TL | T-18 | PROPOSED |
| TL-02a | Proposed dates shall be marked `PROPOSED` until Luke approves them. | T | N5; UC-18; E-045 | TL | T-18 | PROPOSED |
| TL-02b | Proposed dates shall enter Todoist or Google Calendar only after Luke approves them in that session. | T | N5; UC-18; D-018; E-045 | TL | T-18 | PROPOSED |

## INIT and HOME: project initializer (D-006, D-014, D-032)

| ID | Requirement | Method | Trace | Allocated | Verified by | Status |
|---|---|---|---|---|---|---|
| INIT-01 | The initializer shall write exactly the chosen tier's documents. | T | N7; UC-2, UC-9; D-006; E-064 | Init | T-7, DM-2 | PROPOSED |
| INIT-02a | Every file the initializer writes shall carry a status line, except the one-line `CLAUDE.md` import stub. | I | N5; UC-2; E-021 | Init | I-3 | PROPOSED |
| INIT-02b | Every SE document the initializer writes shall end with an explain-back prompt. | I | N5; UC-2; E-054 | Init | I-3 | PROPOSED |
| INIT-03 | Every date the initializer writes shall come from Todoist, from Luke, or from an approved timeline, with each missing date listed as an open decision. | I | N5; UC-2; E-036, E-065 | Init | I-3 | PROPOSED |
| INIT-04 | The initializer shall log as decisions only what Luke stated. | I | N5; UC-2; E-020 | Init | I-3 | PROPOSED |
| INIT-05 | The initializer shall not run git init, commit or push. | T | N4; UC-2; **Claude's** (D-020) | Init | T-2 | PROPOSED |
| INIT-06 | The initializer shall install only accepted, unchanged library skills that Luke chose, and list each install and refusal in its report. | T | N1; UC-2; D-044; E-052 | Init | T-5 | PROPOSED |
| INIT-07 | The initializer shall offer an audit by a fresh agent. | D | N5; UC-8; E-007 | Init, Aud | DM-3 | PROPOSED |
| INIT-08 | The initializer shall refuse to create a code project inside an iCloud-synced folder, and name the folder it found. | T | N6; R7; D-008; E-063 | Init | T-7 | PROPOSED |
| INIT-09 | When Luke promotes a project to a higher tier, the initializer shall add only the missing documents and change no existing file. | T | N7; UC-10; D-044 | Init | T-8 | PROPOSED |
| INIT-10 | The initializer shall refuse a project with no elicitation record or no warden verdict. | T | N10; UC-17; D-032; E-081 | Init | T-21 | PROPOSED |
| HOME-01 | For a non-code project, the initializer shall write only Markdown files with no code blocks and lines of at most 100 characters, and create no git repo. | T | N10; UC-19; D-014; E-063 | Init | T-19 | PROPOSED |

## LIB, DASH and SAFE: library, dashboard and safety

| ID | Requirement | Method | Trace | Allocated | Verified by | Status |
|---|---|---|---|---|---|---|
| LIB-01 | The library shall keep each skill in one source location, from which every install is copied. | I | N3; UC-4; D-001; E-052 | Lib | I-1 | PROPOSED |
| LIB-06 | Each library script shall run on macOS with only the Python standard library, unless its skill says otherwise. | T | N6; D-019; E-038 | Lib | T-1 | PROPOSED |
| DASH-01 | The dashboard shall list every project under Luke's roots with its kind, tier, state, warden verdict and next step. | T, D | N1; UC-9, UC-17; D-021, D-038, D-041; E-083 | Dash | T-22, DM-1 | PROPOSED |
| SAFE-01 | Before a push, the privacy hook shall scan every file in the pushed commit for the project's and Luke's private terms and secrets, and block the push on a hit. | T | N4; UC-6; D-033; E-008 | Priv | T-3 | PROPOSED |
| SAFE-02 | The library's current files shall hold no credentials, private data or collaborators' work. | I, T | N4; R3; E-008 | Lib | I-4, T-3 | PROPOSED |
| SAFE-03 | No skill shall be installed outside this repo unless Luke has answered or waived its explain-back and its content is unchanged since. | T | N5; UC-5, UC-7; R2; D-044, D-045 | Lib, Init | T-5, T-23 | PROPOSED |
| SAFE-04 | Every AI-written file in the library and the dashboard shall carry a status line, except one-line import stubs. | I | N5; R2; **Claude's** (D-020) | Lib, Dash | I-4 | PROPOSED |
| SAFE-05 | No library skill shall change Todoist or Calendar, send a message or publish anything without Luke's approval in that session. | T | N4, N5; E-045 | Lib | T-6 | PROPOSED |

## Deferred until after G1 (D-020, D-027, D-036, D-044)

Each is reconsidered at G3 (closeout): kept, dropped or carried forward.

| ID | Requirement | Trace | Verified by | Status |
|---|---|---|---|---|
| LIB-02 | Each skill shall record its owner, source, status and review date. | N5; UC-7 | I-1 | DROPPED (D-060) |
| LIB-03 | The library shall record every repo where each skill is installed, and which version. | N3; UC-3 | I-2 | DROPPED (D-060) |
| LIB-04 | Third-party skills shall be linked from their source, not copied. | N3; R10 | I-1 | DROPPED (D-060) |
| LIB-05 | Project-specific values shall live in per-project settings, not in shared skill text. | N1; R4 | I-1, T-2 | DROPPED (D-060) |
| LIB-06W | Each library script shall run on Windows, or its skill shall state that it doesn't. | N6; D-019; E-038 | T-1W | DROPPED (D-060) |
| DASH-05 | The dashboard shall flag every installed copy that differs from the library. | N3; UC-4 | T-4 | DROPPED (D-060) |
| MAINT-01 | After three months untouched, the dashboard shall still launch and list the projects. | N6; UC-21; E-062 | DM-6 | DROPPED (D-060) |
| MAINT-02a | `/healthcheck` shall run each skill's checks and report failures. | N3; UC-21; E-061 | T-20 | DROPPED (D-060) |
| MAINT-02b | `/healthcheck` shall change no file. | N5; UC-21; E-061 | T-20 | DROPPED (D-060) |
| INT-01 | The timeline tool shall offer Calendar time blocks, written only after Luke approves. | UC-18; D-018; E-045 | T-18 | DROPPED (D-060) |
| INT-02 | The initializer shall offer GitHub milestones per gate, created only after Luke approves. | UC-2; D-018; E-046 | DM-7 | DROPPED (D-060) |
| INT-03 | The initializer shall write one rules file that Claude and ChatGPT both read. | UC-2; D-018; E-047 | I-8 | DROPPED (D-060) |
| WRAP-01 | When Luke says it is time to close (interest, demo, deadline, lesson learned), Claude shall propose a wrap-up that fits the time left and ends in a closeout. | N11; UC-20; D-031; E-067, E-079 | DM-8 | DROPPED (D-060) |
| WRAP-02 | On burnout signs, Claude shall ask once whether to wrap up, and start nothing without Luke's yes. | N5; UC-20; D-023; E-076 | DM-8 | DROPPED (D-060) |
| CLOSE-01 | The closeout shall be drawn only from recorded files, citing each by path. | N8; UC-12; D-028 | T-11 | DROPPED (D-060) |
| CLOSE-02 | The closeout tool shall write no closing statement, lessons or interpretation; it asks Luke and records the answers verbatim. | N5; UC-12; D-031; E-080 | T-11 | DROPPED (D-060) |
| CLOSE-03 | The closeout shall list every requirement with its final status, and every open decision. | N8; UC-12 | T-11 | DROPPED (D-060) |
| CLOSE-04 | The closeout shall offer each transferable workflow for harvest into the library. | N1; UC-5, UC-12 | DM-4 | DROPPED (D-060) |
| CLOSE-05 | The closeout tool shall propose a git tag and create none without Luke's approval. | N5; UC-12 | T-11 | DROPPED (D-060) |
| SAFE-06 | When refreshing installed copies, Claude shall show Luke each diff before writing. | N3, N5; UC-4 | T-4 | DROPPED (D-060) |

**Dropped:** DASH-02 and DASH-04 (D-021, the teaching mode); DASH-03 (D-044: installs belong to `/initialize` and the installer); STAT-01 to STAT-06 with tests T-9 and T-10 (D-037). Their text is in commit `c76d124`.

## Pending until the freeze lifts at G1 (W3)

These needs are recorded (E-077 to E-085 and the 10/9 addendum in [trace_items.md](trace_items.md)) and built, but have no requirement yet. Write them after G1:
- context loading before elicitation (D-039, E-086);
- the one-message dump (D-040, E-087);
- `/selftest` (D-030, E-078);
- the dashboard's tools, theme, states and shelves (D-034, D-038, D-041, D-042; E-083, E-088 to E-090).

## Test IDs

| ID | Test |
|---|---|
| I-1 | Inspect the library: one source per skill; installs are copies of accepted content (`install_skills.py`). |
| I-2 | Compare an install record with the repos on disk. |
| I-3 | Inspect one initialized project: status lines, explain-backs in SE documents, every date traced, every decision traced to Luke. |
| I-4 | Inspect the library and dashboard for secrets, private terms, collaborators' files and status lines; run `privacy_check.py` and `--all-history`. |
| I-6 | Inspect one elicitation record: verbatim dump and answers, every item with a source and basis, at most five questions per round, CNS sentences cited, no decision Luke didn't state, no invented numbers. |
| I-7 | Inspect one gated project: the verdict with E-id reasons in the record and on the dashboard; the suggested hours and Luke's budget both recorded. |
| I-8 | Inspect an initialized project: one rules file read by both Claude (through `CLAUDE.md`) and ChatGPT. |
| T-1 | Run the test suite and `/healthcheck` on macOS, with the system Python 3.9 and Python 3.14. |
| T-1W | The same on Windows (set aside, D-036). |
| T-2 | Initialize a scratch project: the files written, the skills installed, and no git action (`tests/test_initialize.py`). |
| T-3 | Plant a fake private term: a push to a local bare remote is blocked; remove it, and the push goes through; `--all-history` finds a removed leak (`tests/test_privacy.py`). |
| T-4 | Change an installed skill: each stale copy is flagged and each refresh shows a diff first. |
| T-5 | Try to install a `REVIEWED` skill, or one changed since acceptance: refused (`tests/test_initialize.py`). |
| T-6 | Run each skill where it could reach Todoist, Calendar, messages or publishing: it asks before acting. |
| T-7 | Initialize one scratch project per tier: each gets exactly its tier's documents; a code project in `~/Documents` is refused. |
| T-8 | Promote a Short project to Long: only SE-04 to SE-07 are added, and every existing file is byte-identical. |
| T-11 | Close a scratch project with seeded result files: the closeout cites only those files, lists every requirement and open decision, drafts no answer, and creates no tag (`tests/test_closeout.py`). |
| T-12 | Run `/elicit` on a scratch project with a scripted dump: every item's source exists in the dump or rounds, with a basis. |
| T-13 | Run `/elicit immediate` and `/elicit short` with scripted answers that stop adding items: each stops by its tier's rule, and records the reason and curve. |
| T-14 | `tests/test_prioritize.py`: the pick matches brute force with dependencies and Musts; an infeasible Must set reports its overrun; swings normalize. |
| T-15 | `tests/test_prioritize.py`: a dominant item is picked in every perturbed draw and a valueless one in none; the report names the seed and input hashes. |
| T-16 | `tests/test_gate_check.py`: a clear goal passes; an undefined, untestable or mostly-inferred goal is no-go; context items don't count as inferences. Plus inspection that a proposed rescope changed no file. |
| T-17 | `tests/test_timeplan.py`: suggestions rise with length and complexity, fall to shrink and no-go as availability drops or purpose is low, and calibrate from recorded actual hours. |
| T-18 | `tests/test_timeplan.py`: gate dates follow the budget and hours per week; outputs are files marked `PROPOSED`; the scripts have no network code. |
| T-19 | `tests/test_initialize.py`: a household project gets Markdown files with no code blocks, no line over 100 characters, and no `.git`. |
| T-20 | `tests/test_healthcheck.py`: a broken skill and script are reported, and nothing changes. |
| T-21 | `tests/test_initialize.py`: initializing from no record, from a record with no verdict, or from a NO-GO verdict without an override is refused. |
| T-22 | `tests/test_dashboard.py` and `tests/test_server.py`: projects, states, groups, shelves and next steps render; the page notices changes; forms refuse a bad token or another origin. |
| T-23 | `tests/test_install_skills.py`: only accepted, unchanged skills install, as copies; a change after acceptance withdraws the skill; foreign skills are left alone. |
| DM-1 | Luke starts a project from the dashboard and follows its next-step prompts to a gated project. |
| DM-2 | Initialize a real new project and note what was still done by hand. |
| DM-3 | Run `/se-audit` on an initialized set; the report is written (done for this project 10/9: `audit/se_audit_2026-10-09.md`). |
| DM-4 | Close one real project with `/closeout`, and note what Luke still wrote by hand. |
| DM-5 | `/elicit short` on Games-People-Play (done 10/8: 6 rounds, cap reached, 85 items). |
| DM-6 | Launch the dashboard after three months untouched. |
| DM-7 | Create GitHub milestones for one real project after Luke approves. |
| DM-8 | Close one real project through the wrap-up path. |

## Build status (10/9)

Evidence: [evidence/](evidence/), all tests passing on macOS at the commit named in the file. No Windows run (T-1W).

| Group | Built in | Automated tests | Still needs Luke or time |
|---|---|---|---|
| ELIC | `.claude/skills/elicit/` (`ACCEPTED`, D-045) | T-12, T-13 not automated; `test_context_pack.py` | |
| OPT | `elicit/prioritize.py` | T-14, T-15 | |
| WARD | `.claude/skills/warden/` (`ACCEPTED`, D-045) | T-16, T-21 | |
| TIME, TL | `.claude/skills/timeplan/` (`ACCEPTED`) | T-17, T-18 | actual hours on a time-equation suggestion (Test 1) |
| INIT, HOME | `.claude/skills/initialize/` (`ACCEPTED`, D-045) | T-2, T-5, T-7, T-8, T-19, T-21 | DM-2 (Test 1) |
| LIB-01, SAFE-03 | `dashboard/install_skills.py`, `accepted.json` | T-5, T-23 | |
| LIB-06 | stdlib scripts | T-1 (macOS) | T-1W |
| DASH-01, WARD-03 | `dashboard/` (DECIDED, D-034) | T-22 | DM-1 |
| SAFE-01, SAFE-02 | `.claude/skills/privacy/` (`ACCEPTED`, D-045), hook installed here | T-3 | `--all-history` finds 99 hits in older commits (open decision #4) |
| Deferred groups | `/closeout`, `/healthcheck`, `/selftest`, integrations | T-11, T-20 | after G1 |

**Luke's words** ([trace_items.md](trace_items.md), regenerated 10/9): of 66 live or deferred requirements, 45 trace to Luke's stated words, 7 rest on a decision only, and 14 are Claude's. The live ones that are Claude's: ELIC-03, OPT-02b, OPT-04, INIT-05 and SAFE-04, kept by D-020 and D-044.

**Coverage:** every use case in SE-02 has at least one live requirement, except UC-3, UC-12, UC-20 and UC-21, which have only deferred requirements until G1. UC-1 and UC-11 were dropped (D-021, D-037). There are 75 requirements:
- 46 live (`PROPOSED`): they serve the Must tier, apart from SAFE-04 and the LIB rules, which serve every tier;
- 20 deferred;
- 9 dropped.

Every test ID cited is defined.

---

**Explain-back (Luke):** Pick SAFE-03 and INIT-03. For each one, say in your own words what it guarantees, and which test would show it is false.

> *(Waived by D-029.)*
