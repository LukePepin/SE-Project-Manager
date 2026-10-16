---
name: selftest
description: Check Luke's own understanding of a project at the systems level, by asking a few broad questions on the how and why (purpose, architecture choices and trade-offs, evidence, lessons) and never on implementation details. Luke's answers are recorded verbatim and given feedback from the project's documents. Use when Luke asks to "test me", "selftest" or "do I understand this?", before a demo or lab meeting, or as part of a closeout.
argument-hint: "[project folder, defaults to the current repo]"
---

# Selftest: do you understand your own project?

**Status: ACCEPTED** (Luke waived the follow-up explain-back, 2026-10-09, D-045: "skip the explain-back"). Its content is pinned; any later edit needs Luke's approval again (D-044). AI-drafted by Claude on 2026-10-08 from Luke's direction.

Luke's definition (D-030): it "checks user knowledge of the project in broad scopes, never specific details about implementation but large scale systems engineering and technology questions, the high level lessons that should be brought on, I never care what function said hello world but I do care about the how and why".

It is **opt-in**. Luke doesn't want to be quizzed by default, so run it only when asked, or offer it once at a closeout or before a demo.

## Steps

1. **Read the project:**
   - its SE documents (or `plan.md` for a household project);
   - the elicitation record's `cns.md`;
   - the warden verdict;
   - any closeout draft.
2. **Write 5 questions, one from each area.** Each must be answerable in two or three sentences without opening a file. Never ask about function names, file layout, syntax or settings.
   - **Why:** what problem it solves and why it was worth the time.
   - **How, at block level:** the main parts and how they fit together, or the steps for a household project.
   - **Trade-off:** one choice that was made, and what was given up for it.
   - **Evidence:** how you know it works, and what that evidence does not show.
   - **Lesson:** what you would carry into the next project.
3. **Ask all five in chat, in one message.** Wait for Luke's answers.
4. **Give feedback per answer.** Say what matches the documents and what is missing or contradicts them, citing the file and section. Never give a score. Never write the answer for Luke; point to where it is.
5. **Record** `docs/se/selftest_<date>.md` (or `selftest_<date>.md` in a household folder): the questions, Luke's answers verbatim, and Claude's feedback marked `PROPOSED`.
6. If an answer shows that a document is wrong rather than Luke, propose the document change. Apply nothing without Luke's yes.

---

**Explain-back (Luke):**

> checks user knowledge of the project in broad scopes, never specific details about implementation but large scale systems engineering and technology questions, the high level lessons that should be brought on, I never care what function said hello world but I do care about the how and why
>
> *(Answered 2026-10-08 in the review packet.)*

**Explain-back follow-up (Luke, D-044; waived by D-045):** What kind of question will /selftest never ask you, and what does it do when your answer contradicts the project's documents?

>
