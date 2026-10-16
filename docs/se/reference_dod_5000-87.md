# Reference: DoD Software Acquisition Pathway (D-011)

**Status: DRAFT.** Moved here from SE-02 §8 on 2026-10-09 (audit, Length). Background for `/elicit`; not a requirement.

Labmates' prior work pointed to defense acquisition. Of its pathways, the **Software Acquisition Pathway (DoDI 5000.87, 2020)** fits best: it is built for software and it iterates. Its planning phase produces a Capability Needs Statement (CNS), an acquisition strategy and an architecture concept. Execution then delivers a Minimum Viable Capability Release (MVCR) within a year, with value assessments at least once a year after that.

The heavier front-loaded requirements process, JCIDS, was disestablished by an August 2025 DoD memo. The lesson for this library: capture needs at a high level, stop on a rule, and iterate. Don't try to write everything down before starting.

| Software pathway | Here (`PROPOSED`) |
|---|---|
| Draft CNS, written by the operational community | Elicit Stages 0 to 3: dump, extract, probe, stop. Luke is the operational community |
| The sponsor approves the CNS before execution | Luke answers the explain-back on `cns.md`; part of G0 (passed 10/8) |
| User Agreement: committed user involvement and feedback roles | Luke's committed review time and explain-back cadence (the habit SE-00 R2 says is being skipped) |
| Planning phase: CNS, acquisition strategy, architecture concept, prototypes | The Short tier's SE-01 to SE-03, with an optional spike |
| Entry to execution: CNS, UA, test strategy, cost estimate | The SE-03 test IDs and the hours budget H (D-016) |
| MVP and MVCR | The MVCR candidate is the robust set from Elicit Stage 5, delivered by the next gate |
| Value assessment, at least once a year | `/closeout`, plus G1's stop rule: "does running the gate take longer than the project?" |

**Taken:** the CNS, the User Agreement, MVCR, value assessment, and threshold and objective values for each measure.
**Not taken:** the paperwork, contracting, decision authorities, and the joint-staff routing. **Naming:** DoD's "ICD" (Initial Capabilities Document) is not this set's ICD (SE-05, Interface Control Document). Use "CNS" for needs.

Sources: DoDI 5000.87 (esd.whs.mil); DAU Adaptive Acquisition Framework, Software Acquisition pages (aaf.dau.edu/aaf/software); Breaking Defense, 2025-08, on ending JCIDS. Check the current issuance before citing it: a business-systems sub-pathway was added in 2022 for a later revision.
