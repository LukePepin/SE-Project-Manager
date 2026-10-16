# Rules for every assistant: Games-People-Play

**Status: DRAFT,** current to D-050 (2026-10-10). Written by Claude from Luke's decisions in `docs/se/SE-00_project_plan.md`.

Claude reads this through `CLAUDE.md`, and ChatGPT and other agents read it directly (D-018). This is Luke's skill library and project gate. Most projects start with `/start small|medium|large` (D-047): dump, a few questions, one approval, in about 15 minutes, in the dashboard app or a chat. Large projects use the full gate, `/elicit` → `/warden` → `/timeplan` → `/initialize`. Plus `/privacy`, `/se-audit`, `/closeout`, `/healthcheck` (does the library work?) and `/selftest` (does Luke understand a project? opt-in).

- **Luke decides; assistants draft.** Log a decision in `docs/se/SE-00_project_plan.md` only when Luke states it, with "By: Luke" and the date. Everything else is `PROPOSED`. Assistants may propose changes to the goal, the Must tier or the boundary, but never make them.
- **Status on every claim:** `PROPOSED` → `REVIEWED` → `ACCEPTED` (Luke answered the explain-back) → `IMPLEMENTED` → `VERIFIED (test, evidence)`. Off the path: `DEFERRED` and `DROPPED`, each by a decision.
- **Stated or inferred.** In an elicitation record, only Luke's words are `stated`. Never present an inference as Luke's.
- **The warden proposes and never applies.** It may deny a project outright; a rescope waits for Luke's yes (D-022).
- **Dates** come from Luke's Todoist, from Luke, or from a `/timeplan` proposal Luke approved.
- **No push, no Todoist, Calendar or GitHub writes, no messages** without Luke's approval in that session. Never push with `--no-verify`; the pre-push hook runs `/privacy`.
- **Only `ACCEPTED`, unchanged skills leave this repo** (SAFE-03, D-044). Acceptance pins a skill's content in `.claude/skills/accepted.json`; editing an accepted skill means setting it to `REVIEWED` and asking Luke to approve it again (an explain-back, or Luke's waiver, D-045). After Luke approves, run `python3 dashboard/install_skills.py --accept NAME --by "Luke, explain-back <date>"`.
- **The dashboard is the application** (D-049): `/start` runs in it, and `dashboard/make_app.py` wraps it as a Mac app. Keep it one stdlib server; the `/start` engine (`.claude/skills/start/engine.py`) is shared with the chat skill, never copied. SE-03 is frozen until G1 (W3): record new needs in the elicitation record. `/initialize` takes only elicited and warden-gated projects (D-032); a `/start` record counts, since it holds the warden's `verdict.md`.
- **Token use** (D-048): a `/start` stage is one stripped `claude -p` call (no tools, MCP, skills or CLAUDE.md; thinking off unless `tiers.json` says so). Don't add context to a stage without a reason in the review.
- **Privacy:** `.privacy-terms.global` (git-ignored, here) holds Luke's private terms for every project; each repo keeps its own `.privacy-terms`. Never print or commit either (D-033).
- **Closeout never writes Luke's statement, lessons or interpretation.** It asks, and records the answers verbatim (D-031).
- **Wrap-up:** a project can close for any reason Luke gives. On burnout signs (short answers, long gaps, other work taking over), ask once whether to wrap up (D-023, D-031).
- **Tests:** `.venv/bin/python -m pytest` (see `README.md`).
