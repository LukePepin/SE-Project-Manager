# Systems engineering documents: Games-People-Play

**Status: DRAFT,** current to D-050 (2026-10-10). AI-drafted by Claude from Luke's direction. Explain-backs on SE documents are waived (D-029). Every behavior is `PROPOSED` unless it cites a D-nnn decision.

**Games-People-Play** (formerly Project Initializer, D-005) is a warden at the gate for Luke's projects, technical and household (D-014). Its parts:
- **`/start`:** small and medium projects in one pass, three stops, about 15 minutes (D-047); large ones go through the four skills below;
- **`/elicit`:** loads Luke's context, takes one brain dump, and writes the record;
- **`/warden`:** go, shrink or no-go;
- **`/timeplan`:** suggested hours and a proposed timeline;
- **`/initialize`:** three tiers (D-006), or a printable household folder;
- **`/closeout`:** closes a project from its record;
- **`/privacy`:** a pre-push hook;
- **`/se-audit`, `/healthcheck`, `/selftest`:** an independent audit, a library check, and an opt-in knowledge check;
- **the dashboard:** the application (D-049): projects, states and next steps, and every `/start` run, in a Mac app window.

It is side work, behind the thesis and coursework (D-004), and itself a **Short-tier** project (D-003). Where things stand: [SE-00](SE-00_project_plan.md), "Where the project stands".

## The V

```
 Elicitation record + CNS ................. Reconciled against Luke's own words (trace_items.md)
   Charter + ConOps (SE-01, SE-02) ...... Goal shown: Test 1 and Test 2 (G1, G2)
       Requirements (SE-03) ........... The I, T and DM tests in SE-03
                   \                   /
                    Build (skills, dashboard)
```

Read each dotted line as "verified by". SE-04 to SE-07 are added only if the project is promoted to the Long tier, by a decision.

## Document set

| Document | State |
|---|---|
| [SE-00](SE-00_project_plan.md) plan, gates, risks, decision log | Current to D-044 |
| [SE-01](SE-01_charter.md) charter | Current to D-044 (520 words) |
| [SE-02](SE-02_conops.md) ConOps | Current to D-044 |
| [SE-03](SE-03_requirements.md) requirements and tests | Current to D-044; frozen until G1 (D-027) |
| [trace_items.md](trace_items.md) | Redacted trace of the elicitation record and SE-03, regenerated 10/9 |
| Elicitation record `elicitation/2026-10-08/` | Git-ignored (D-035). 6 rounds (cap reached), 90 items (82 in Luke's words), CNS, reconciliation, verdict |
| [audit/se_audit_2026-10-09.md](../../audit/se_audit_2026-10-09.md) | Fresh-agent audit: 2 Blocker, 12 Major, 11 Minor, all addressed by D-044 |
| [reference_dod_5000-87.md](reference_dod_5000-87.md) | The DoD framework behind `/elicit` (D-011) |
| [archive/](archive/) | The 10/8 review packet, now superseded by SE-00 |

**Schedule:** none in Todoist yet (open decision #1). Fixed date: Wed 10/14 lab meeting.

**Tests:** `.venv/bin/python -m pytest` (setup in the top-level `README.md`). Evidence: [evidence/](evidence/).

## Rules for every document

- **Status on every claim:**
  - `PROPOSED`: not yet decided;
  - `DECIDED (D-nnn)`: in the SE-00 decision log;
  - `REVIEWED`: Luke has seen it, and an explain-back is pending;
  - `ACCEPTED`: Luke answered the explain-back, or waived it (D-045). For a skill, its content is also pinned by a hash, and any later change undoes acceptance (D-044);
  - `IMPLEMENTED`: the code exists;
  - `VERIFIED (test id, evidence file)`: a recorded test shows it;
  - `DEFERRED (D-nnn)` or `DROPPED (D-nnn)`: kept for later, or removed, by a decision.
- **Who writes:** Luke directs and decides; Claude drafts.
- **Keep evidence types separate.** A skill file that exists is not a skill that works, and a run on one machine is not a run on both.
- **Scope changes** go through the SE-00 decision log.

---

**Explain-back (Luke):** Why is this project Short tier and not Long, and what would have to happen for you to promote it and add SE-04 to SE-07?

> The architecture of the systems is not an important feature of the development and I don't need to actively be in it.
