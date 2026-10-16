# Review: the `/start` pivot, 2026-10-10

**Status: PROPOSED.** Written by Claude under D-050 ("just start work and make me a review document to check your work rather than ask me questions on this pivot"). Nothing here is accepted until you say so. The decisions are D-047 to D-050 in [SE-00](SE-00_project_plan.md); your words from 10/10 are E-091 to E-100 in the elicitation record.

## In one minute

You asked for a streamlined gate: `/start small|medium|large`, about 15 minutes, fewer tokens, everything in the dashboard, and the dashboard as an application.

What exists now:
- **`/start`**: three stops (your dump → a few questions → one approval), then setup. Small is 1 round of up to 3 questions; medium is up to 2 rounds of 4; large saves your dump and hands off to the full gate in a chat.
- **Cheaper runs**: each Claude step is a separate, stripped `claude -p` call. Haiku asks the small questions, Sonnet judges and plans, and thinking is off where it isn't needed. A small run measured 2 calls and 26 to 44 seconds of Claude time.
- **The dashboard runs it all**: the Start form, the questions page, the approval page and the "set up" page. No copying prompts into Claude.
- **A Mac app**: `python3 dashboard/make_app.py` builds `/Applications/Games-People-Play.app` (with an icon; moved from `~/Applications` on 10/10 so it shows in Finder and Launchpad), a native window that starts the dashboard when it opens and stops it when it closes.
- **108 tests pass** (91 before, plus 17 for `/start`), and `/healthcheck` is 37 of 37. No accepted skill was changed.

## Try it on the website (about 15 minutes)

1. Open **Games-People-Play** from Applications or Launchpad. It is already installed; `python3 dashboard/make_app.py` rebuilds it.
2. In **Start a project**, pick your website folder under **Project** (or name a new one), choose **Small** and **Technical**, paste your brain dump, and press **Start**.
3. Answer the questions. Leave any blank, or press **Send and go straight to the plan**.
4. Read the verdict and plan. Tick any proposed change you want, type your hours, and press **Approve and set it up**.
5. Note the time from step 2 to step 4. The target is 15 minutes (E-095).

For an existing code folder like the website, `/start` writes only `elicitation/<date>/` (the record and `plan.md`) and one `.gitignore` line. Nothing else in the repo changes.

## Checklist: what to check

| # | Check | Where | Passes if |
|---|---|---|---|
| 1 | The app opens and shows your projects | the app | One window, no browser, your projects listed |
| 2 | Start to approval takes 15 minutes or less | your clock, on the website run | ≤ 15 min (E-095) |
| 3 | The questions are the ones that matter, and none leads you | the questions page | You'd have wanted to be asked them; none suggests its own answer |
| 4 | "Stated" items are really your words | `elicitation/<date>/items.md` | Every `stated` row quotes you, with a `dump P` or `R1.Q` source |
| 5 | The verdict and its reasons are fair | the approval page, or `verdict.md` | Each reason cites your items; concerns are kept apart from reasons |
| 6 | The plan is one you'd follow | the approval page, or `plan.md` | The first step takes under an hour; nothing you excluded is in it |
| 7 | Nothing is set up before you approve | the project folder | Only `elicitation/` exists until you press Approve |
| 8 | Quitting the app stops the server | Activity Monitor, or `pgrep -fl server.py` | No server left after Cmd-Q |
| 9 | The chat path works | a Claude Code chat in this repo: `/start small <folder>` | Same three stops, same files |
| 10 | The cost numbers make sense | the footer of each run page | A few cents at API prices per run |

## The choices Claude made for you (reverse any)

Each one is `PROPOSED`. To reverse one, say "C5: change it to …".

| # | Choice | Default now | Where it lives |
|---|---|---|---|
| C1 | Questions per size | small: 1 round × 3; medium: 2 rounds × 4 | `.claude/skills/start/tiers.json` |
| C2 | Model per stage | small: Haiku asks, Sonnet plans; medium: Sonnet both | `tiers.json` → `models` |
| C3 | Thinking | off, except medium's plan (on, effort low) | `tiers.json` → `thinking` |
| C4 | Life context sent to Claude | a digest of 1,500 (small) or 3,000 (medium) characters from Docket, capacity first, last 7 days. It is never saved to disk | `tiers.json` → `context_chars`; `engine.context_digest` |
| C5 | **Medium writes a plan, not SE-00 to SE-03** | Both small and medium set up at the Immediate tier (README goal, `plan.md`). The full SE set is for large | `tiers.json` → `init_tier` |
| C6 | Large | saves `brain_dump.md` and hands off to `/elicit long` in a chat; it doesn't run in the app | `tiers.json` → `handoff` |
| C7 | Existing code project | gets only the record, `plan.md` inside it, and `**/elicitation/` in `.gitignore`. A **new** folder also gets `plan.md`, `README.md`, `AGENTS.md` and `CLAUDE.md` | `engine.approve` |
| C8 | The floor under the verdict | no stated Need → NO-GO; no stated Measure → at least SHRINK; more than half the items inferred → at least SHRINK. The floor only makes the verdict stricter | `engine.floor` |
| C9 | The approval form | proposed changes start unticked; the budget starts empty, with a "Use X h" button | `build_dashboard.approval` |
| C10 | How the app talks to Claude | the Claude Code CLI on your plan, not an API key (see below), capped at $0.50 API-price equivalent per call | `engine.run_claude` |
| C11 | The app | a native Swift/WebKit window; the server still listens on 127.0.0.1 inside it, unseen. Without Xcode tools, it falls back to a Chrome, Edge or Brave app window | `dashboard/app/`, `dashboard/make_app.py` |
| C12 | What the dashboard recommends | new ideas → `/start small`; old SE projects never gated → `/elicit` (unchanged, for G2) | `build_dashboard.recommend` |
| C13 | `/start` outside this repo | not installed for every chat until you accept it (SAFE-03). The app doesn't need it installed | open decision #17 |
| C14 | Dashboard freeze | set aside for this work, since you directed dashboard work (D-049). SE-03 stays frozen until G1 | `AGENTS.md` |

## Your question: the Claude app or API calls?

> "is it possible to interact with it over the claude application or is that API calls more expensive than the application" (E-098)

- **The Claude desktop chat can't be driven by another app.** The bridge is Claude Code's command line, `claude -p`. It signs in with the same Claude account, so its usage counts against your plan's limits, and there is no per-token bill.
- **API calls** need a separate API key and are billed per token on top of your plan. At the measured sizes, a small run would cost about $0.05 to $0.11 on the API. That's cheap, but it adds a key and a bill for no gain, so the app uses the CLI.
- The "API-price equivalent" in each run's footer is what Claude Code reports. It is a gauge, not a charge.
- **Caveats:** runs count toward your plan's usage limits, and headless use is for you on your machine. If the lab uses it, each person runs it on their own login.

## Token use: what changed, measured on 10/10

| Call | Input tokens | Output tokens | Time | API-price equivalent |
|---|---|---|---|---|
| Plain `claude -p`, Haiku, "say ok" | 32,923 | 68 | 3.2 s | $0.066 |
| The same, stripped (no tools, MCP, skills or CLAUDE.md; own system prompt) | 888 | 162 | 2.1 s | $0.0017 |
| A question round, Haiku, thinking **on** (`--effort low`) | ~2,300 | 12,952 (12,069 thinking) | 124 s | $0.082 |
| The same round, thinking **off** | ~2,300 | 1,591 | 15.6 s | $0.013 |
| **A whole small run**: Haiku questions + Sonnet verdict and plan | 14,041 | 5,343 | 44 s | $0.106 |
| **A medium run**, 1 round then plan (Sonnet ×2, thinking when planning) | 7,071 | 2,703 | 24 s | $0.083 |
| Home-Sweet-Home under the old gate | not measured | | ~3.5 h of clock | |

The biggest saving is the stripping: about 37× less input per call. Thinking off made a Haiku round about 8× faster and 6× cheaper.

**Variance.** A later small run (after the prompt edits) took 6 s for questions but 59 s and about 26,000 input tokens for the plan, about $0.18. Rerunning that same plan call took 20 s and about 3,700 tokens. The difference is structured-output retries: when the JSON fails validation, the CLI retries and resends everything. Each call is now capped at $0.50 API-price equivalent (`--max-budget-usd`), and the record logs each call's turns (2 is normal). Expect $0.05 to $0.20 per small run.

**More suggestions, not built:**
- **S1. Prefer the app over a chat for `/start`.** In a chat, every turn also carries the chat's own large system prompt and history. The app sends each step only what it needs.
- **S2. For large projects, run the chat on Sonnet** (the model picker) unless a step needs deep judgment. Most of `/elicit` is careful bookkeeping, not hard reasoning.
- **S3. Drop the life context for small runs** (`context_chars: 0`) if the first few runs show the questions don't use it. It saves about 400 input tokens a call, and it keeps your calendar out of small runs.
- **S4. Check quotes mechanically.** A short Python check that each `stated` item's quote really appears in your dump or answers would catch a model misquoting you. That is cheaper than a model check.
- **S5. In everyday chats,** start a fresh chat per task and `/compact` long ones. The history, not the model, is usually most of the bill.

## Devil's advocate: strongest objections first

1. **R9 fired again, on purpose.** The dashboard is now an app with background jobs: about 900 more lines across the engine, server, page, Swift app and tests. Mitigation: one engine, shared by the app and the chat skill; the app is a thin window around the same stdlib server. If you feel it growing, the warden's old advice holds: stop adding to it.
2. **A cheaper gate can wave a bad project through** (R15). The small gate is one Haiku round and one Sonnet judgment. The floor is mechanical, but it only checks that the right kinds of items exist. Suggestion: for the first three real runs, ask whether the full gate would have said something different.
3. **G1 is still open, and this pivot could become a way not to finish** (R1). Home-Sweet-Home has no closeout yet. Suggestion: run the website through `/start small`, close it with `/closeout`, and decide whether that, plus Home-Sweet-Home, passes G1 (open decision #19).
4. **It leans on newer CLI flags** (R14): `--json-schema`, `--tools ""`, and `--settings` with `alwaysThinkingEnabled`. A Claude Code update can break a run. You'd see the error and a Retry button, not silent damage, but `/healthcheck` doesn't run a live call yet.
5. **"Stated" is still the model's call.** Python stores your words verbatim, and an item can be `stated` only with a `dump P`/`R1.Q` source (the engine downgrades any other to inferred). But whether the quote matches is not checked (S4).
6. **Prompt rules are not guarantees.** On 10/10, Sonnet called you "his" in a plan. The prompts now say to use your name or "they", and the follow-up run used neither "he" nor "his" anywhere in its record. One clean run is not proof.

## Not verified

- Windows; the app's fallback launcher (no Xcode tools); the Copy button inside the native app window.
- A machine where `claude` isn't logged in. The error path is tested with a fake; the real message is untested.
- Two runs at once, a 20,000-character dump, and a missing Docket in a live run (all covered only by unit tests).
- That 15 minutes holds for you. The Claude time is under a minute, but your reading and typing is the real cost, and it is unmeasured until the website run.

## What changed

- **New:** `.claude/skills/start/` (SKILL.md, engine.py, tiers.json, prompts/ask.md, prompts/plan.md), `dashboard/make_app.py`, `dashboard/app/GamesPeoplePlay.swift`, `tests/test_start.py`, and this file.
- **Changed:** `dashboard/server.py` (Start, run and approval routes, background steps, app mode); `dashboard/build_dashboard.py` (the Start form, run pages, `/start` recommendations); two old tests updated for the new recommendations; `README.md`, `AGENTS.md`, `docs/se/README.md`, and SE-00 (D-047 to D-050, R14, R15, open decisions #17 to #19).
- **Unchanged:** all nine accepted skills (their pinned hashes still match).
- **Git:** committed on branch `start-streamline`, not merged, not pushed.

## To accept or change it

- **Accept `/start`:** answer the explain-back at the bottom of `.claude/skills/start/SKILL.md`, or waive it, and tell Claude. Claude then sets it `ACCEPTED` and runs `install_skills.py --accept start`, so it works in every chat.
- **Reverse a choice:** "C5: medium should write SE-00 to SE-03", for example.
- **Merge:** say "merge start-streamline".

---

## Addendum: the dashboard pages (D-052, same day)

Your direction: "different pages for each project, display more information, link to the file system remove the old skill flow at the top, make a light/dark mode that changes with the system setting, generally make the layout better and have me do a lot more inside the application". Built on branch `dashboard-pages`, not merged. 116 tests pass (8 new).

**What you can now do in the app:**
- Open any project's page from its card: the next step and its prompt, goal and done-when, the plan, the warden's reasons, documents, open decisions, records, git (branch, uncommitted files, recent commits, remote) and notes.
- **Tick plan steps** and add new ones. This edits the checklist lines in `plan.md` and nothing else.
- **Open things:** the folder in Finder, a Terminal there, VS Code, any document in its own app, or "Show in Finder".
- **Read documents** in the app, rendered, and **answer explain-backs** there. Your answer is saved verbatim under the prompt, marked "Answered <date> in the dashboard".
- **Library:** answer a skill's explain-back, then press **Accept** (two steps, so you see your answer first). That sets it `ACCEPTED`, pins it, and lets Install put it in every chat. This is how open decision #17 (`/start`) can close in the app.
- Run **the healthcheck** from the Library.
- Light and dark follow your system setting, and the skill-flow bar at the top is gone.

**Choices to check (reverse any):**
- **C15. Open never runs a program.** Folders, documents, images, PDFs and data files open. Anything else (`.command`, `.sh`, `.app`) is only shown in Finder.
- **C16. The app only touches** paths inside a project on the dashboard, or this library.
- **C17. In-app acceptance needs a written answer.** There is no "waive" button; a waiver still goes through a chat, so accepting stays a deliberate act (risk R2).
- **C18. Large projects:** a large `/start` in an existing folder now shows on the dashboard (it used to be invisible).

**Not verified:** the Open buttons inside the native app window (tested with a fake opener and in the browser pane). Windows Terminal and VS Code paths. A document over a few hundred KB.

**To see it:** quit the app (⌘Q) and reopen it. The app runs this repo's code, so there's nothing to rebuild, but it has to be on the `dashboard-pages` branch or merged.

## Addendum 2: folders, filters and the suggestions list (D-053)

- **Folders** are dashboard groups. Use New folder, drag a card onto one, or pick a folder on the project page. Rename, reorder (↑ ↓) or remove a folder from its header; removing one returns its projects to their root folder. They live in `dashboard/groups.json`, which is git-ignored.
- **Choice C19: nothing moves on disk.** A project's absolute path is written into its records, the archive list and Claude's memory, so moving the folder itself would break links. Dragging a card into a *different* root (from ~/Projects to ~/Research) is refused for the same reason. Say so if you want real moves instead.
- **Filters:** text search (name, next step, tags, folder), state, kind and verdict chips, and sort by state, name or last activity. They are remembered in the app between visits.
- **Tested:** 118 tests (2 new). The drop and the filters were exercised in the browser pane with synthetic drag events, because the pane's mouse drags don't produce native drag events. A real mouse drag in the app window is untested.
- **The 15 suggestions:** [SUGGESTIONS_2026-10-10_dashboard.md](SUGGESTIONS_2026-10-10_dashboard.md).
