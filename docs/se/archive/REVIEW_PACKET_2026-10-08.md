# Review packet

**Archived 2026-10-09 (audit, Length):** superseded by SE-00, which now holds the current state and open decisions.

**Status:** first round answered by Luke on 10/8 and applied (D-025 to D-034). What remains is below, most important first. Nothing in it blocks daily use.

## Done from your answers

- **Merged** `elicit-front-end` into `main` (D-025).
- **Removed the classmate's name** from the SE documents (D-026). It remains only in the git-ignored global term file, and in older commits' history.
- **The warden's W1 to W3 are applied** (D-027):
  - 17 Should-tier requirements are deferred to after G4, leaving 39 Must-tier ones to verify.
  - The attic is the first real test.
  - SE-03 is frozen; new needs (E-077 to E-085) live in the elicitation record.
- **Claude's defaults are accepted** (D-028), and open decisions #2, #3, #5, #6, #7, #9 and #11 are closed.
- **All 9 skills are ACCEPTED** (D-029). The explain-backs on this project's SE documents are waived.
- **What you asked for in your explain-backs is built:**
  - `/selftest` is now a check of your understanding at the how-and-why level, opt-in. The library check is `/healthcheck` (D-030).
  - `/closeout` closes for any reason, needs a fully initialized project, gives statistics, and only asks questions: it never writes your statement (D-031).
  - `/initialize` refuses anything that wasn't elicited and warden-gated (D-032).
  - Privacy has one global, git-ignored term file here, plus each project's own (D-033).
  - The dashboard can create projects, add notes, and show each project's next skill with a Copy button (D-034).
  - The warden now spells out when its judgment is stricter than its checks, and what it may never do.
  - Timeplan records hours at each gate, not only at the end.

## Settled on 10/8 (second round)

- **The repo stays private.** Elicitation records are git-ignored (D-035), and the privacy check passes, so pushes are no longer blocked.
- **The monthly Todoist task:** added by Luke.
- **Test 1** is the attic; **Test 2** is gating the four older projects. The Windows run is set aside (D-036).

## Still open

Nothing. The statistics toolkit is project-dependent (D-037), which was the last open item. Next up: Test 1, the attic.

## Known limits

- The prioritizer prints a harmless HiGHS solver line while it runs.
- The privacy hook checks the commit being pushed, not older history. The classmate's name is still in this repo's earlier commits; rewriting history would be your call before any public push.
- The dashboard counts requirements only where SE-03 uses the status vocabulary.
- The build order's hours and scores were Claude's guesses; your recorded hours will correct the time equation.
