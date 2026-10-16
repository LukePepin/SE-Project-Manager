---
name: closeout
description: Wrap up and close a fully initialized project for any reason (interest running out, a finished demo, a deadline, or "I learned what I wanted"). It gathers closeout counts from recorded files, then asks Luke the closeout questions and records the answers verbatim. It never writes the closing statement for Luke. Use when Luke says "wrap up", "close this out", "I'm done with this", "demo's done" or "2 hours left", or when a project ends or is parked.
argument-hint: "[project folder] [actual hours]"
---

# Wrap up and close out

**Status: ACCEPTED** (Luke waived the follow-up explain-back, 2026-10-09, D-045: "skip the explain-back"). Its content is pinned; any later edit needs Luke's approval again (D-044). AI-drafted by Claude on 2026-10-08 from Luke's direction (Games-People-Play D-007, D-016, D-023, D-031; CLOSE-01 to CLOSE-04, TIME-03, WRAP-01, WRAP-02).

## 1. When to close (D-023, D-031)

A project can close for any of these reasons:
- Luke has about two hours of interest left;
- the demo is done;
- a deadline has arrived;
- Luke has learned what was wanted;
- the warden or the time equation says stop.

**When Luke says so,** go to step 2.

**When Claude sees burnout signs** (short or poor answers, long gaps, work shifting elsewhere), ask once: "Want to wrap this up?" Start nothing without Luke's yes (WRAP-02). If Luke says no, don't ask again that session.

**A closeout needs a fully initialized project:** an SE set, a goal line, or a household `plan.md`. `closeout.py` refuses anything else. A bare idea folder is closed informally, with one line in its notes.

## 2. Wrap-up plan (WRAP-01)

If time is short (for example, two hours of interest), propose a plan that fits and ends in the closeout:
- what is close to done and worth finishing, from the build order in `prioritization.md` if there is one;
- what gets parked, with one line each on why.

Luke approves the plan, then it runs. For a demo, deadline or "learned what I wanted", skip straight to step 3.

## 3. Closeout

1. **Draft it:**
   ```
   python <this skill>/closeout.py PROJECT --actual-hours A
   ```
   This writes `docs/se/closeout_<date>.md` (or pass `--out`; it never overwrites). The draft holds the closeout counts (not statistics in the D-037 sense): requirement statuses, decisions, elicitation items in Luke's words, suggested vs actual hours, result files and harvest candidates. It also lists the closeout questions with empty answers.
2. **Ask the closeout questions in chat, all in one message.** Put Luke's answers under them verbatim.
   - **Claude never writes the closing statement, the lessons or the interpretation**, not even as a draft to edit (D-031).
   - If an answer is thin, ask one follow-up that points at the record ("SE-03 shows R-2 never passed; was that the deadline?"). Don't supply the answer.
3. Go through the open-decision table with Luke: closed, dropped, or carried forward.
4. **Record the hours:** `time_equation.py record ...`. This calibrates future suggestions (TIME-03).
5. **Offer each harvest candidate** for the library, as a separate decision.
6. **Offer `/selftest` once** (opt-in).
7. With Luke's approval, move the closeout to where the tier puts it: SE-07 for Long, SE-00 for Short, the README for Immediate.
8. **The git tag is proposed, never created** without Luke's yes.

A household project uses its own `closeout.md` from the initializer: ask the same questions, write Luke's answers into it, and record the hours.

---

**Explain-back (Luke):** What two things can start a wrap-up, and what must the closeout never write for you?

> this shouldn't always be about 2 hours of interest if I want a demo wrapped or a deadline project or simply I've learned what I wanted I can close a project the wrapup needs a fully initalized project with all the proper documentation to review and hopefully some statisics it asks closeout questions like lessons learned etc, closeout never writes the inital message it will drive me to create a statement on the project, never drive one itself
>
> *(Answered 2026-10-08 in the review packet.)*

**Explain-back follow-up (Luke, D-044; waived by D-045):** What does /closeout need before it will run, and what will it never write for you?

>
