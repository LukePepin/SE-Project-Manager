---
name: se-audit
description: Independent audit of a project's SE document set by a fresh agent that never saw the drafting, at the project's tier (Short or Long), including whether each requirement traces to Luke's own words. Writes a ranked findings report. Use when a project's SE set has been drafted or reviewed, before a gate, or when Luke asks to "audit the docs".
argument-hint: "[project folder, defaults to the current repo]"
---

# SE audit (fresh agent)

**Status: ACCEPTED** (explain-back answered and skills authorized by Luke, 2026-10-08, D-029). AI-drafted by Claude on 2026-10-08 from Luke's direction (Games-People-Play D-015; INIT-07, UC-8). It is generalized from On-Edge's `.claude/commands/se-audit.md`.

"Independent" means the reviewer is not the session that drafted the documents.

## Steps

1. **Pick the tier** from the files: SE-04 or later present means Long; SE-00 to SE-03 means Short. An Immediate project has nothing to audit; say so and stop.
2. **Launch a fresh `general-purpose` agent** that sees only the repository, not this conversation. Give it the instructions below, with the tier filled in.
3. **Relay its report to Luke without softening it.**
   - Give the count of Blocker, Major and Minor findings, and the top three.
   - Do not fix anything until Luke says which findings to act on.

## Agent instructions

You are auditing a {Short|Long}-tier systems engineering document set for consistency, completeness and traceability. Be critical: the author has to defend every line.

**Read, in this order:**
- `docs/se/README.md`, then SE-00 (decisions, gates, risks), SE-01, and SE-02 onward to the last SE document present;
- the newest `docs/se/elicitation/<date>/`: `items.md`, `cns.md`, `verdict.md`, `reconciliation.md` (if present);
- `AGENTS.md` (project rules).

**Check each of the following, citing file and section for every finding:**
1. **Scope:** does anything exceed SE-01's Must tier or contradict its Won't list?
2. **Decisions:** is every `DECIDED (D-nnn)` or "D-nnn" citation backed by a decision-log row? Is any decision applied inconsistently?
3. **Luke's words:** does each requirement trace to a stated E-id, a decision, or a use case? List the requirements that trace only to inferred items, or to nothing (Claude-originated).
4. **Requirements:** is each one testable, with one "shall", a method and a test ID that exists?
5. **Coverage:** does every use case appear in at least one live requirement? Is every test ID defined?
6. **Warden:** does SE-00 carry the warden's verdict? If it was NO-GO, is there an override decision?
7. **Dates:** does every date come from Todoist, from Luke, or from an approved timeline proposal? Does anything invent a date?
8. **Status labels:** is any claim labeled `ACCEPTED` or `VERIFIED` without an answered explain-back, or a test and evidence file?
9. **Long tier only:** do SE-04 components, SE-05 interfaces and SE-06 tests line up with SE-03? Are evidence types (simulation, software, physical) kept apart, and are measures fixed before data collection?
10. **Length:** what can be cut? Is the charter at or under two pages?

**Write the report** to `audit/se_audit_<YYYY-MM-DD>.md`.
- Rank the findings **Blocker**, **Major** and **Minor**, each with a suggested fix.
- End with the five questions a skeptical reviewer would most likely ask.

---

**Explain-back (Luke):** Why must the auditor be a fresh agent, and what does it check that the warden doesn't?

> a fresh agent reads with a fresh pair of eyes, old agents make determination on history history which can fluxation, a fresh agent only sees whats written its unbiased and not prone to drift because it only relies on stated elements.
>
> *(Answered 2026-10-08 in the review packet.)*
