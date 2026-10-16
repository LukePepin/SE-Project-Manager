# Games-People-Play

**Closeout complete. Project done (10/10, D-054).** The closeout is in [SE-00](docs/se/SE-00_project_plan.md). Status: CLOSED, current to D-062 (2026-10-10).

Luke's Claude skill library and project gate. It gets a project out of Luke's head, decides whether the project is worth the time, sizes it, sets it up, keeps it private, and closes it out.

Where it stands, the gates and open decisions: [docs/se/SE-00_project_plan.md](docs/se/SE-00_project_plan.md). What changed on 10/10 and what to check: [docs/se/REVIEW_2026-10-10_start.md](docs/se/REVIEW_2026-10-10_start.md).

## Start a project: `/start` (D-047)

Three stops, about 15 minutes: **your brain dump → a few questions → one approval** (verdict, proposed changes, hours budget). Nothing is created before you approve.

| Size | For | Questions | Claude models | You get |
|---|---|---|---|---|
| `small` | an afternoon to a few evenings | 1 round, up to 3 | Haiku asks, Sonnet plans | a record and a `plan.md` |
| `medium` | a few weeks of evenings | up to 2 rounds of 4 | Sonnet (thinks when planning) | the same, with a longer plan |
| `large` | a semester or more | the full gate | your chat's model | `/elicit long` → `/warden` → `/timeplan` → `/initialize` with SE documents |

Run it from the app (below), or in a Claude Code chat: `/start small ~/Projects/My-Site`. Each Claude step is a short, stripped `claude -p` call on your Claude plan, not an API key. The numbers live in `.claude/skills/start/tiers.json`.

## The app

```bash
python3 dashboard/make_app.py
```

That builds **Games-People-Play.app** in `/Applications`, with its own icon: one window with your projects, the Start form, and each run's questions and approval. Open it from Applications, Launchpad or Spotlight. To keep it in the Dock, right-click its Dock icon while it runs and choose Options > Keep in Dock. It starts its own dashboard on a free port when it opens, and stops it when it closes. Python and page changes reach the app when you reopen it (⌘Q, then open). Rebuild with `python3 dashboard/make_app.py` only when `dashboard/app/` changes or this repo moves.

Without the app: `python3 dashboard/server.py --app` (an app-style window), or `--open` (a browser tab), or double-click `dashboard/open_dashboard.command`. On Windows, `dashboard\\open_dashboard.bat`. It reads `~/Projects`, `~/Research` and `~/School`, on this machine only, and follows your system's light or dark setting. Its pages:
- **Projects:** every project as a card, colored by state. Make your own folders (New folder) and drag cards into them; nothing moves on disk. Filter by text, state, kind and verdict, and sort by state, name or last activity; the filters are remembered.
- **A page per project:** the next step, goal and done-when, the plan as a checklist you can tick and add to, the warden's reasons, every document (open it in the app, in its own app, in Finder or in VS Code), open decisions, records, git, and notes. Buttons open the folder, a Terminal there, or VS Code.
- **Documents:** Markdown shown in the app, with a box to answer any open explain-back (saved word for word).
- **New project:** the `/start` form, then each run's questions and approval.
- **Library:** the skills and their review state. Answer a skill's explain-back and accept it, install accepted skills for every chat, and run the healthcheck.

A read-only snapshot needs no server: `python3 dashboard/build_dashboard.py --open`. All of it uses only the standard library.

## The other skills

| Skill | What you get |
|---|---|
| `/elicit`, `/warden`, `/timeplan`, `/initialize` | The full gate, for large projects (and what `/start` does in one pass for the rest) |
| `/privacy` | A pre-push hook that blocks private terms and secrets |
| `/se-audit` | A fresh-agent audit of the SE documents |
| `/closeout` | A wrap-up plan when interest runs low, then a closeout from the recorded files |
| `/healthcheck` | A monthly check that the library still works. It changes nothing |
| `/selftest` | Opt-in: five broad how-and-why questions to check that you understand a project |

## Tests

Most scripts use only the standard library. The prioritizer and the test suite need numpy, scipy and pytest:

```bash
python3 -m venv .venv
```

```bash
.venv/bin/pip install -e '.[dev]'
```

```bash
.venv/bin/python -m pytest
```

## Where things are

- `.claude/skills/`: the skills and their scripts; `/start`'s engine is `.claude/skills/start/engine.py`
- `dashboard/`: the server, the page, the installer, and the Mac app (`make_app.py`, `app/`)
- `docs/se/`: this project's own SE set (Short tier), the redacted trace (`trace_items.md`), and test evidence. The elicitation record (`elicitation/`) is git-ignored (D-035).
- `audit/`: fresh-agent audits
- `AGENTS.md`: the rules every assistant follows here; `CLAUDE.md` imports it
- `.privacy-terms.global` (git-ignored): private terms checked in every project (D-033)
