---
name: elicit
description: Get everything about a project out of Luke's head before any SE document is drafted. It first loads Luke's life context (the Docket repo, plus Google Calendar and Todoist when connected) so it never asks what else is going on; one message is the whole brain dump. The steps are a verbatim brain dump, tagged items (stated vs inferred), probe rounds until saturation, swing weights, prioritization under an hours budget, and a Capability Needs Statement. Use when Luke starts or rescopes a project, says "elicit", "brain dump", "interview me", "requirements" or "what am I missing", or before running the project initializer.
argument-hint: "[immediate|short|long] [project folder, defaults to the current working directory]"
---

# Elicit: get the project out of Luke's head

**Status: ACCEPTED** (Luke waived the follow-up explain-back, 2026-10-09, D-045: "skip the explain-back"). Its content is pinned; any later edit needs Luke's approval again (D-044). AI-drafted by Claude on 2026-10-08 from Luke's direction (Games-People-Play D-010 to D-013), then revised the same day after a scripted scratch test and the first real run.

Target: `$ARGUMENTS`. The first word is the tier (`immediate`, `short` or `long`). If it is missing, ask for it. The rest is the project folder. The default is the current working directory.

**Framework.** This is the planning phase of the DoD Software Acquisition Pathway (DoDI 5000.87), cut down for one person. It produces the draft **Capability Needs Statement (CNS)** and **User Agreement**. Take the ideas, not the paperwork. Never call the needs document an "ICD": in Luke's SE sets, ICD means the SE-05 Interface Control Document.

Luke is usually the user, the sponsor, the developer and the tester at once. When others will use the result (a lab tool, a shared library), they are the operational community, and Luke is relaying them. Mark what Luke relays as second-hand (see Stage 1).

**Goal.** Capture everything that is cheap to capture now and expensive to discover later. Stop when new questions stop finding new things. It is not "everything", because no one can get everything.

Record formats, including the status line every file starts with: [records.md](records.md). Question bank: [lenses.md](lenses.md). Optimizer: [prioritize.py](prioritize.py).

## Rules for every stage

1. **Verbatim first.** Luke's words go into the record unedited:
   - the dump goes in `dump.md`;
   - every answer in a round, or in Stages 4 and 5, goes in `rounds.md`.

   Never put a paraphrase in their place. Control words ("done", "no, that's all") are not dump text.
2. **Stated or inferred.** Every item cites its source: `dump P3`, `R2.Q4`, `S4.Q1` or `S5.Q2` when Luke said it, `inferred from E-007` when Claude did. An inferred item stays inferred until Luke confirms it.
3. **Don't lead.** Within a message, open questions come before closed ones. An open question never carries a candidate answer. Ask "what else?" before "would X help?".
4. **At most 5 questions per round.** Each yes/no confirmation counts as one question. One round per message, then wait.
5. **No decisions by Claude.** Log a decision only when Luke states one, as "By: Luke, <date>". Everything else is `PROPOSED`.
6. **Nothing outside the folder.** No Todoist writes, no messages, no git init, commit or push (SAFE-05, INIT-05).
7. **Privacy.** Never record credentials, cookies or tokens. If the dump identifies a specific person other than Luke (by name, by initials, or by a role only one person holds, such as "my advisor" or "the PI"), or includes unpublished thesis material, ask in the next round whether it stays in the record.
8. **Never invent numbers or levels.** Luke supplies:
   - the hours budget and each item's hours;
   - the scores;
   - the swings;
   - each measure's worst and best levels.

   Claude may propose a range or wording, labeled inferred. Luke confirms or changes it before it is used.
9. **One place per round.** A round with any open question is asked entirely in chat, with its closed questions marked "(yes/no)" or listing their options. Use AskUserQuestion only for a round of closed questions (swing ranking, batch confirmations), or when AskUserQuestion is the only question. Mixing the two made Luke answer the box and miss the chat (dogfood, 10/8).
11. **Name the thing.** In every question, say the deliverable's name ("the dashboard", "the `/elicit` skill") instead of "it", "this" or "an increment".
10. **Non-answers.** An "n/a" or "nothing new" given to a question about an *item* leaves that item as it was. Ask it at most once more, in a later round. An answer that doesn't fit the question is recorded as whatever it is, with its own source. The question then counts as unanswered and may be asked once more.

## Tier scaling

| Tier | Stages | Lenses that must be covered | Round cap | Stop reasons possible | Hands to the initializer |
|---|---|---|---|---|---|
| Immediate | 0, 1, one probe round, 3 | the Immediate set in [lenses.md](lenses.md) | 1 | covered, cap reached, stopped by Luke | `goal.md`: a goal line and a "done when" line |
| Short | 0 to 4; 5 if Luke gives a budget; 6 | all | 6 | saturated, cap reached, stopped by Luke | `cns.md` → SE-01 to SE-03 |
| Long | 0 to 6, plus external stakeholders (advisor, committee, lab): interview them or read their documents | all | 10 | saturated, cap reached, stopped by Luke | `cns.md` → SE-01 to SE-07, with a value-assessment schedule |

The caps are `PROPOSED` values. Luke can raise one for a session, and the record notes it.

## Stage 0: Context, then the dump

**Context first (D-039).** Before asking Luke anything, load what else is going on in Luke's life, so no question asks it.

1. Create the record folder:
   - `docs/se/elicitation/<YYYY-MM-DD>/` in the project;
   - for a Hands-on project with no `docs/se/`, `elicitation/<YYYY-MM-DD>/`;
   - if today's folder exists, add `-2`.
2. **Docket.** Run:
   ```
   python <this skill>/context_pack.py <record folder> --project <project folder>
   ```
   It copies the current parts of Luke's Docket repo (`~/ChatGPT/Docket`) into `context.md`: areas and goals, parked items, the last two weeks of confirmed decisions, and the latest weekly and monthly reviews' capacity, allocation and next actions. It git-ignores `context.md` in a code project.
3. **Google Calendar**, if a calendar connector is available. Read only the next 4 weeks.
   - Append a `## Calendar` section to `context.md`: fixed commitments (title, day, time) and booked hours per week.
   - Never copy descriptions, confirmation numbers, links, locations or attendees.
   - Never create or change an event.
4. **Todoist**, if a Todoist connector is available. Read only:
   - Append a `## Todoist` section: open projects, and tasks due in the next 4 weeks, with priority and due date.
   - Without a connector, say once that the Todoist picture is the Docket weekly review snapshot, and give its age.
   - Never create, complete or change a task.
5. **Read `context.md` fully.** If Docket is missing, say so in one line and carry on without context.

**Then the dump.**

6. **If the project has `brain_dump.md`** (typed in the dashboard), that is the whole dump: copy its text into `dump.md` word for word and go to Stage 1. Ask nothing first.
7. Otherwise, ask once, in one short message: tell me everything about this project, in any order: what it is, why it matters, what bugs you today, what you've tried, who's involved, what worries you, and what done looks like. Type it or paste a voice transcript.
8. **Luke's next message is the dump. Sending it means done (D-040).** Don't ask "anything else?" or wait for a "done". Write `dump.md` right away: Luke's text verbatim, split at paragraph breaks, labeled `P1`, `P2`…, with the sentences of a long paragraph numbered (`P1.S7`) without changing a word. Anything Luke adds later is appended as a new paragraph.

## Stage 1: Extract

Write `items.md`, one row per item. Rows follow [records.md](records.md).

- **Types:** Need, Constraint, Assumption, Stakeholder, Alternative, Risk, Measure (how success is judged), Out (out of scope), Decision (stated by Luke only) and Question (unresolved). A deficiency ("what goes wrong today") is a Need tagged L1.
- **Wording:** quote Luke's words where they are short enough.
- **Lenses:** tag each item with every lens it covers. One item may cover several lenses.
- **Second-hand:** when Luke relays what someone else wants ("the PI wants…"), the basis is still `stated`. Add `via <who>` to the Source.
- **Context:** add only the facts from `context.md` that bear on this project (competing commitments, free hours, related goals, deadlines, people involved). Use basis `context` and a source like `context: docket_memory.md § 2026-10-05 …`, `context: calendar` or `context: todoist`. Context is never `stated`: Luke didn't say it in this elicitation.
- **Hard constraints are not measures.** A "must" or "must not" is a Constraint, even when it also sounds like a goal.

Show Luke only a summary: counts by type, stated, inferred and context, the context that matters most (two or three lines), and the uncovered lenses. Show the full table only on request.

## Stage 2: Probe rounds

A lens is **covered** when either of these holds:
- a **stated** item is tagged with it (inferred items and open Questions don't count);
- Luke answered its open question with "n/a".

In Short and Long, L7 (review time), L8 (feedback cadence) and L10 (hours) feed the User Agreement and Stage 5. For them, "n/a" is not enough. If Luke has no answer, record a Question item, "none yet", which covers the lens and goes into the CNS's open questions.

**Choosing the round.** Pick at most 5 questions, in this priority order:
1. **Uncovered required lenses**, in the order of the lenses table, using each lens's open question.
2. **Inferred items and open Questions** to confirm, change, drop or answer. Batch yes/no confirmations with AskUserQuestion.
3. **Vague items.** A Need with no Measure gets "how would you know?". A Measure with no numbers gets its **threshold** (least acceptable) and **objective** (what would be great).

Then put the open questions first in the message (Rule 3), all in one place (Rule 9).

Append each round to `rounds.md`: the questions, Luke's answers verbatim, and the new, confirmed and dropped items by type. Update `items.md`.

## Stage 3: Stop

Stop when **one** of these holds, and record which:
- **Saturated** (Short, Long): two rounds in a row added no new **stated** Need, Constraint, Stakeholder or Assumption (Claude's inferences don't count, so Claude can't keep a session going). Every required lens is covered. Every Measure has a threshold and objective, or Luke has said there are none. While a Measure lacks them, the next round includes that question.
- **Covered** (Immediate): after the dump and one round, every Immediate lens is covered.
- **Stopped by Luke:** record "stopped, not saturated" and list the uncovered lenses.
- **Cap reached:** record "cap reached, not saturated" and list the uncovered lenses.

End the rounds section of `rounds.md` with the discovery curve: new items per round and the running total. A curve still climbing at the stop is itself a finding. Items added later, in Stages 4 and 5, are counted in a separate line under the curve.

For Immediate, write `goal.md` (format in [records.md](records.md)) and finish.

## Stage 4: Weight (swing weights)

Log every question and answer in `rounds.md` under `## Stage 4`, as `S4.Q1`, `S4.Q2`…

1. **Pick the measures.** The value measures are the stated Measure items, never Constraints.
   - Two to six measures are workable. With one, its weight is 1: skip to Stage 5.
   - With more than six, ask Luke to merge some.
   - If Luke wants to weight a Constraint, ask whether it is really a must. If it isn't, change it to a Measure first.
2. **Set the levels.** Each measure needs a worst and a best level in words, from Luke (Rule 8).
3. **Rank the swings.** Ask: "Picture every measure at its worst. You can move one to its best. Which one?" Repeat for the rest, using AskUserQuestion.
4. **Score the swings.** The top swing is worth 100. Ask what each of the others is worth, from 0 to 100. If the points contradict the ranking, ask once.
5. **Write the files:** `weights.md` (measure, worst, best, rank, swing, normalized weight) and `weights.csv` (`measure,swing`).

## Stage 5: Prioritize (Next Release Problem)

Log questions and answers in `rounds.md` under `## Stage 5`, as `S5.Q1`…

1. **Get the budget.** If L10 did not give an hours figure, ask: "How many hours can you give this before the next gate?" If Luke gives none, write "Stage 5 skipped: no hours budget" under `## Stage 5` in `rounds.md` and in `cns.md`, and go to Stage 6.
2. **List the candidates.** They are the stated Needs that are buildable pieces, one row each in `items.csv` (format in [records.md](records.md)).
3. **Get the inputs.** Luke gives:
   - each item's hours;
   - its dependencies;
   - the Musts ("which of these would make the project pointless if cut?");
   - a 0 to 10 score per measure.

   Scores Claude proposes are marked inferred in `items.md` until Luke confirms each row.
4. **Run the optimizer** with a Python that has numpy and scipy. In Games-People-Play that is `.venv/bin/python`, or `.venv\Scripts\python` on Windows:
   ```
   python <this skill>/prioritize.py items.csv weights.csv --budget H --out prioritization.md
   ```
5. **Read the results to Luke:**
   - The **robust** items (picked in at least 90% of perturbed draws) are the MVCR candidate.
   - **Contested** items are Luke's call. The weights alone do not settle them.
   - Exit code 2 means **the Must set does not fit the budget.** Say so plainly: cut the Must tier or raise H.

## Stage 6: CNS and User Agreement

Write `cns.md` from the record only. Every sentence cites E-ids, or a question id (`R2.Q3`, `S4.Q1`) when Luke's answer made no item. A section with nothing recorded says "none recorded" and repeats in the open questions.

Sections:
- mission deficiency;
- enhancements to what exists;
- interoperability and legacy interfaces;
- operating environment;
- constraints;
- out of scope;
- the MVCR candidate, with threshold and objective values (if Stage 5 was skipped: "not set: no hours budget", plus the Musts if Luke named any);
- the **User Agreement**: who the users are (first-hand, or relayed by Luke), how much review time Luke commits (L7), and the explain-back and feedback cadence (L8);
- the **value assessment**: when to check that the project still earns its time (L18). The default is at closeout;
- open questions, including second-hand needs worth checking with the person who holds them.

End the file with an explain-back prompt, which is exempt from the citation rule. The next step is the initializer for the tier. Every SE claim it writes cites an E-id.

## Reconcile (when an SE set already exists)

This stage runs only when the project had `SE-03` or an `SE-02` inventory before this run. After Stage 3 (or 6), write `reconciliation.md`:
- For every requirement in SE-03, and every row of the SE-02 inventory, list the E-ids that support it. If none do, mark it **Claude-originated, unconfirmed**.
- List the stated items that no requirement covers.
- Put the counts at the top.
- Propose edits as a list. Do not rewrite the SE set.
- Then run `python <this skill>/trace_table.py <record> <SE-03> docs/se/trace_items.md --terms <project>/.privacy-terms <library>/.privacy-terms.global`, so the trace survives in git while the record stays ignored.

## Finish

Report:
- the folder;
- item counts by type, and stated vs inferred;
- rounds and the stop reason;
- weights;
- the MVCR candidate;
- open questions.

Commit nothing.

---

**Explain-back (Luke):** What stops this skill from putting words in your mouth, and what would the discovery curve look like if it stopped too early?

> 1. This skill doesn't put words in my mouth since its a dump first then clarify, it doesn't make any suggestions until the user empty out everything they have, then we seek clarification some words in mouth may be good i.e the warden posing a direction.
>
> *(Answered 2026-10-08.)*
>
> Second half (review packet): "an early stopped discovery looks like a cliff high level of build than rather than a closeout a quick snap to the current answer?"

**Explain-back follow-up (Luke, D-044; waived by D-045):** Before asking you anything, what does /elicit now read, what will it never copy or change, and why can a context item never count as something you said?

>
