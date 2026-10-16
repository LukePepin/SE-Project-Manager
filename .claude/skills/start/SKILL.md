---
name: start
description: Start a project in about 15 minutes, from brain dump to an approved plan, with three stops (the dump, a few questions, one approval). Sized small, medium or large; small and medium run the whole gate (elicit, warden, time suggestion, setup) in one pass on cheaper models, and large hands off to the full /elicit → /warden → /timeplan → /initialize gate. Use when Luke says "start", "new project", "I want to do X", "/start small|medium|large", or "/start continue <record>". The same runs are in the dashboard.
argument-hint: "[small|medium|large] [project folder or name] [--kind code|household] | continue <record folder>"
---

# Start: from brain dump to plan in three stops

**Status: ACCEPTED** (Luke reviewed and accepted it, 2026-10-10, D-057: "I reviewed it ... I accept it install outside this repo"; the explain-back below was not answered). AI-drafted by Claude on 2026-10-10 from Luke's direction, D-047 to D-050. The review is `docs/se/REVIEW_2026-10-10_start.md`.

Luke's direction (D-047, 10/10): "/start [tier] small/medium/large which updates the numbers of rounds and questions", "limit token usage", "15min is perfect". Most of Luke's projects are small or medium. The full gate stays for large ones.

Engine: [engine.py](engine.py). Tier settings (rounds, questions, models, context size): [tiers.json](tiers.json). Stage prompts: [prompts/](prompts/).

## Why this skill is thin

The engine does the work. Each Claude step is a separate, stripped `claude -p` call on Luke's plan: no tools, no MCP, no skills, no CLAUDE.md, thinking off for small projects, a cheap model where it is enough (Haiku asks, Sonnet judges), and JSON out. Python writes every record file, so Luke's words are stored verbatim by code, never retyped by a model. In this chat, **relay; don't redo the engine's work**: don't read the record files back into this chat, and don't write questions or plans yourself.

## Steps

`E` below is `python3 <this skill>/engine.py`.

1. **Size and folder.** The first word of `$ARGUMENTS` is the size (`small`, `medium`, `large`). If it is missing, ask once with the three sizes: small = an afternoon to a few evenings, medium = a few weeks of evenings, large = a semester. Then the folder: an existing folder, or a new name under `~/Projects` (ask only if unclear). Kind is `code` unless it is a physical or life project (`household`).
2. **The dump.** If Luke hasn't given it, ask once: everything about the project, in any order. Luke's next message is the whole dump (D-040). Save it word for word to a file in the scratchpad, then:
   - existing folder: `E new --project DIR --kind K --tier T --dump-file FILE`
   - new folder: `E new --root ~/Projects --name NAME --kind K --tier T --dump-file FILE`

   For **large**, the engine saves `brain_dump.md` and stops: tell Luke to run `/elicit long DIR` (the full gate). Stop here.
3. **Questions.** Run `E step RECORD`. It prints the questions. Show them to Luke exactly as printed, numbered, in one message, and wait. Write Luke's answers word for word as JSON `{"R1.Q1": "...", ...}` to a scratchpad file, then `E answer RECORD --answers-file FILE` (add `--stop` if Luke says to skip to the plan). Run `E step RECORD` again: more questions (medium only) or the plan.
4. **One approval.** `E step` prints the verdict, reasons, proposed changes (W1…), goal, done-when, steps and the suggested hours. Show them, then ask in **one** AskUserQuestion box: which proposed changes to approve (multi-select), and the hours budget (the suggestion is one option; Luke's own number goes in "Other"). On NO-GO, the box asks: stop, or override (Luke gives the reason).
5. **Set up.** `E approve RECORD --budget H --accept W1,W2 [--override "Luke's reason"]`, or `E stop RECORD`. Report what was written, in two lines, and offer (don't do) `git init` for a new code folder and `/privacy` before any push.

`/start continue RECORD` picks up wherever a run stopped (the dashboard's runs too): `E show RECORD`, then the matching step above.

## Rules

- **Luke decides.** Nothing is set up before step 5. Proposed changes are applied only when Luke approves each one. The engine's checks can only make the verdict stricter (WARD-02).
- **Verbatim.** Luke's dump and answers go to the engine unedited. Never paraphrase them.
- **Nothing outside the folder.** No git, Todoist, Calendar, GitHub or messages (SAFE-05). In a git repo the engine adds `**/elicitation/` to `.gitignore`, so the record stays private (D-035). An existing code project gets only the record and its plan.
- **Errors.** If a step prints an error, show it in one line and offer to retry (`E step RECORD`).

---

**Explain-back (Luke):** Where are your three stops, what makes a run cheap (name two things), and what is the one thing /start never does before you approve?

>
