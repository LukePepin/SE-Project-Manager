---
name: initialize
description: Start a project at the right tier (Immediate, Short or Long), as a code repo or as a household folder of printable Markdown. It writes the tier's documents from the elicitation record, adds one rules file for Claude and ChatGPT, and installs only accepted library skills. Use after /elicit and /warden, when Luke says "start a project", "set up", "initialize" or "make the SE docs", or to add the missing documents when a project moves up a tier.
argument-hint: "[target folder] [immediate|short|long] [code|household]"
---

# Initialize a project

**Status: ACCEPTED** (Luke waived the follow-up explain-back, 2026-10-09, D-045: "skip the explain-back"). Its content is pinned; any later edit needs Luke's approval again (D-044). AI-drafted by Claude on 2026-10-08 from Luke's direction (Games-People-Play D-006, D-014, D-015, D-018; INIT-01 to INIT-08, HOME-01, INT-03, SAFE-03).

`init_project.py` uses only the Python standard library.

## Order

1. **`/elicit`** writes the elicitation record.
2. **`/warden`** writes `verdict.md`.
3. **`/timeplan`** suggests the hours.
4. **This skill.** It does no ideation (D-032): `--from` must point at an elicitation record holding a warden `verdict.md`. Without one the script refuses. A NO-GO verdict also stops it, unless Luke has logged an override decision.

## Steps

1. **Confirm with Luke** the target folder, the tier (from the time suggestion; Luke picks) and the kind: `code`, or `household` for a project with no code (the attic, packing to move).
2. **Run the script:**
   ```
   python <this skill>/init_project.py TARGET --name NAME --tier TIER --kind KIND --from ELICITATION_FOLDER [--skills elicit]
   ```
   - Existing files are never overwritten. Running it again at a higher tier adds only the missing documents.
   - A code project inside iCloud (`~/Documents`, `~/Desktop`, iCloud Drive) is refused.
   - Skills that aren't `ACCEPTED` are refused.
3. **Fill the documents** from `cns.md`, section by section:
   - Every claim cites an E-id, or is marked as Claude's.
   - Copy the warden's verdict line and the time suggestion into SE-00.
   - Dates come from Todoist, from Luke, or from an approved `/timeplan` proposal.
   - Log as decisions only what Luke stated.
4. **A household project** gets `plan.md` (and, at Short or Long, `checklist.md` and `closeout.md`). Keep them printable: short lines, no wide tables, no code.
5. **Report** what was written, skipped, installed and refused. Then offer, without doing any of them:
   - `git init` (code projects only);
   - the privacy hook (`/privacy`);
   - the timeline (`/timeplan`);
   - a fresh-agent audit (`/se-audit`).

---

**Explain-back (Luke):** What four things will the initializer refuse to do, and why does each one matter?

> doesn't do the ideation, it accepts approved elict and warden'd projects.
>
> *(Answered 2026-10-08 in the review packet.)*

**Explain-back follow-up (Luke, D-044; waived by D-045):** The initializer refuses four things: which three besides "no ideation"? (Hint: iCloud, the warden, and skill status.)

>
