# Lenses: what the probe rounds look for

**Status: PROPOSED.** AI-drafted by Claude on 2026-10-08. The lenses come from the DoDI 5000.87 Capability Needs Statement definition, its User Agreement and its program strategies, plus classic elicitation gaps.

A lens is **covered** when a **stated** item in `items.md` is tagged with it, or Luke answered its open question with "n/a". Inferred items and open Questions don't count. **Context items** (from Docket, Calendar or Todoist; D-039) also cover the "what else is going on" lenses: L5, L6, L7, L10, L12 and L13. Never ask Luke a question the context already answers. At most, confirm one number the hours budget depends on ("Calendar shows about 6 free hours a week: is that right?"). In Short and Long, L7, L8 and L10 can't be closed by "n/a": record a "none yet" Question instead (SKILL.md Stage 2).

Replace <the deliverable> and any "it" with the deliverable's name. When several lenses are uncovered, ask them in table order. Ask the open question first. Use the follow-ups only after Luke answers, and never put a candidate answer into an open question.

| ID | Lens | Source | Immediate tier? | Open question | Follow-ups |
|---|---|---|---|---|---|
| L1 | Mission deficiency | CNS | yes | What goes wrong today, or what can't you do, that this project fixes? | When did you last hit it? What happened? What happens if this never gets done? |
| L2 | Enhancements to what exists | CNS | | What do you already have that does part of this? | What's missing from it? Why not just extend it? |
| L3 | Interoperability | CNS | | What other tools, repos, people or services does this have to work with? | What breaks if one of them changes? |
| L4 | Legacy interfaces | CNS | | What existing files, formats or habits have to keep working unchanged? | Which of those could you give up? |
| L5 | Operating environment | CNS | | Where and when will it be used: which machines, what setting, what state are you in? | What's different on the other machine? |
| L6 | Users | UA | | Who will use the result? Who else is affected by it? | What does each of them need from it? |
| L7 | User involvement | UA | | How much time can you give to reviewing it while it's built, and when? | What usually gets skipped when you're busy? |
| L8 | Feedback cadence | UA | | When I hand you a finished piece of <the deliverable>, what would you check before deciding to keep using it? | How often do you want that check? When will you answer the explain-backs? |
| L9 | Test approach | Strategy | | What would convince you it works? What would a skeptic need to see? | What would show it's broken? |
| L10 | Cost | Strategy | yes | How many hours can this take before the next fixed date, and what is it competing with? | If the answer is a date: how many hours by then? What gives way if it runs over? |
| L11 | Support after delivery | Strategy | | Once <the deliverable> exists, who fixes it when something breaks or a tool it uses changes? If nobody touches it for three months, what must still work? | |
| L12 | Stakeholders and sponsors | Classic | | Who has a say: advisor, lab, collaborators, a course? | What does each of them want from it? Have they told you that directly? Who could block it? |
| L13 | Hard constraints | Classic | | What can't change: dates, money, rules, privacy, platforms? | Where does that constraint come from? |
| L14 | Failure and stop | Classic | yes | What result would make you stop or shrink the project? | What's the worst way it could go wrong? |
| L15 | Alternatives | Classic | | What else could solve this, including doing nothing? | Why not that? |
| L16 | Privacy | Classic | | What in or near this project must never become public? | Who else's material passes through it? |
| L17 | Out of scope | Classic | yes | What will this deliberately not do? | What will people assume it does that it won't? |
| L18 | Success measures | Classic | yes | Months from now, what would tell you it was worth it? | What's the least you'd accept (threshold)? What would be great (objective)? When should we check whether it still earns its time? |

## Generic follow-ups (any lens)

- What else?
- Can you give me an example?
- How would you know?
- What happens if that doesn't happen?
- Where does that come from: you, someone else, or a rule?
- Is that a must, or a nice-to-have? (closed: ask it only after the open questions)

## Leading questions to avoid

| Don't ask | Ask instead |
|---|---|
| Would a dashboard help with that? | How do you want to find that out? |
| So the main goal is saving time, right? | What matters most about this? |
| You'll want it on both machines? | Where will you use it? |
