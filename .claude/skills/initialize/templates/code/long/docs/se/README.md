# Systems engineering documents: {{name}}

**Status: DRAFT.** Initialized by Claude on {{date}} from Luke's elicitation ({{elicitation}}). Every behavior is `PROPOSED` unless it cites a D-nnn decision.

**Tier: {{tier}}.** {{tier_docs}}

## The V

```
 Elicitation record + CNS ................. Reconciled against Luke's own words
   Charter + ConOps (SE-01, SE-02) ...... Goal shown in real use
       Requirements (SE-03) ........... Requirement checks (the tests named in SE-03)
                   \                   /
                    Build increments
```

## Rules for every document

- **Status on every claim:** `PROPOSED`, `DECIDED (D-nnn)`, `REVIEWED`, `ACCEPTED`, `IMPLEMENTED`, `VERIFIED (test id, evidence file)`, `DEFERRED (D-nnn)` or `DROPPED (D-nnn)`.
- **Who writes:** Luke directs and decides; Claude drafts. Every claim traces to an E-id in the elicitation record, or is marked as Claude's.
- **Explain-back:** every drafted section ends with one, and is `ACCEPTED` only after Luke answers it in Luke's own words.
- **Scope changes** go through the SE-00 decision log.

---

**Explain-back (Luke):** Why is this project {{tier}} tier, and what would make you change that?

>
