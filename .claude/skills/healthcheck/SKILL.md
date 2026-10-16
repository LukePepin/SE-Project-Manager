---
name: healthcheck
description: Check that the Games-People-Play library still works (skills well-formed, scripts compile, dashboard builds, tests pass) without changing anything, then propose fixes for Luke to approve. Use for the monthly maintenance check, after a tool like Claude, Python or Todoist changes, after months untouched, or when Luke asks "does this still work?".
argument-hint: "[--no-tests]"
---

# Health check: does the library still work?

**Status: ACCEPTED** (Luke waived the follow-up explain-back, 2026-10-09, D-045: "skip the explain-back"). Its content is pinned; any later edit needs Luke's approval again (D-044). AI-drafted by Claude on 2026-10-08 from Luke's direction (Games-People-Play E-061, E-062; MAINT-01, MAINT-02). It was called `/selftest` until D-030 gave that name to the knowledge check.

1. Run `python3 .claude/skills/healthcheck/healthcheck.py` from the repo root. It writes nothing.
2. Show Luke the table. For each failure, propose one fix with the diff. **Apply nothing until Luke approves** (SAFE-06).
3. If the test suite was skipped because there is no `.venv`, give the setup commands from `README.md`. Don't install packages unless Luke says so.
4. Monthly: the Todoist task "Games-People-Play: monthly health check" (D-036) is the reminder. Claude never creates it.

---

**Explain-back (Luke):** waived (D-029).

**Explain-back follow-up (Luke, D-044; waived by D-045):** What does /healthcheck check, and why does it never fix anything by itself?

>
