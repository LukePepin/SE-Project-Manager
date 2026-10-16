# SE-01 Charter

**Status: DRAFT,** current to D-044 (2026-10-09). AI-drafted by Claude from Luke's direction. Explain-backs on SE documents are waived (D-029). Every behavior is `PROPOSED` unless it cites a D-nnn decision.

## 1. Problem

Luke has "a history of unfinished projects", often started "without clear goals, definitions purpose" (E-002, E-017). AI makes starting cheap; deciding whether a project is worth the time is the hard part (E-005, E-010). Each new project was also set up by hand, and AI drafts mixed Luke's words with Claude's guesses without marking which was which.

## 2. Goal (D-010, D-015)

A warden at the gate for every project, technical or household (D-014): get what Luke knows written down, judge whether it is worth the time, size it, set it up at the right tier, and close it out.

**Question:** does running a project through the gate end in more finished, worthwhile projects for the hours spent?

## 3. Scope

**Must** (D-015, plus `/elicit`, which D-032 requires before the initializer):
- [x] `/elicit`, with Luke's context loaded first (D-039)
- [x] the warden gate, which can say no (D-022)
- [x] the time equation and the timeline proposal: dates go to Todoist or Calendar only after Luke approves
- [x] the initializer: three tiers, code or household (D-006, D-014)
- [x] the dashboard: projects, states, next steps and shelves (D-034, D-038, D-041, D-042)
- [x] the security and privacy check (D-033)

Built and tested on macOS; not yet verified in real use (SE-00 gates).

**Should** (deferred by D-027 until after G1):
- the closeout tool and wrap-up (D-031);
- the self-test and health check (D-030);
- the integrations (D-018);
- the review rule as a Must-tier item (D-044; the rule itself, SAFE-03, stays enforced);
- the dashboard launching after three months untouched;
- library metadata (LIB-02).

**Won't:**
- teaching Claude's feature types (D-021);
- a library statistics toolkit (D-037);
- copying third-party skills;
- writing to Todoist, Calendar or GitHub, or pushing, without Luke's approval;
- a public marketplace;
- time taken from the thesis or coursework (D-004).

## 4. Boundary

**Inside:** Luke's skills, their scripts and templates, the dashboard, the elicitation records, and this repo's rules (`AGENTS.md`).

**Read, never written:** the Docket repo (`~/ChatGPT/Docket`), Google Calendar, and Todoist (D-039).

**Outside:** Claude Code, third-party skills, connectors and GitHub.

Repos live outside iCloud (D-008). Luke works on a Mac mini and a Windows PC (D-019). Other people's work and secrets never enter the library (SAFE-02).

## 5. Minimum evidence

1. The library's checks pass on macOS: 91 tests (`docs/se/evidence/`).
2. **Test 1:** one real Hands-on project (Home-Sweet-Home) runs from elicitation to closeout, with its actual hours recorded (G1, D-036).
3. **Test 2:** the four older projects are gated and reconciled (G2).
4. This project is closed with `/closeout` (G3).
5. Every skill installed outside this repo is `ACCEPTED` and unchanged since acceptance (SAFE-03, D-044).

Later, unscheduled: Windows (T-1) and a three-month launch (DM-6).

---

**Explain-back (Luke):** In 30 seconds, without notes: what does the library give you that copying a folder doesn't, and what result would make you stop the project?

> *(Waived by D-029.)*
