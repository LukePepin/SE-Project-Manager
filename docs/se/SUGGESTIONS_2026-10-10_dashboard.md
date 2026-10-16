# Fifteen suggestions for the dashboard

**Status: PROPOSED.** Researched and written by Claude on 2026-10-10 at Luke's request: "do some research and create a list of the 15 best suggestions for a system like this in terms of functionality for the dashboard". Nothing here is built or decided. Pick any by number.

**How they were chosen.** They come from project-management practice and research that fits one person running many side projects: personal Kanban, GTD, PARA, Shape Up, Linear and Backstage, and studies of the planning fallacy, implementation intentions and quitting. They are ranked by how directly they guard against the risks this project already lists (R1 stalls, R11 false precision, R13 fatigue) and then by effort: S is under a day, M a few days, L more. Each source was opened during the research. Where a page showed only a summary, the caveats at the end say so.

**What already exists.** The dashboard already marks a project yellow after 14 quiet days and red after 30. `time_equation.py` already learns from recorded hours. SE-00 already keeps a decision log. The suggestions below that build on these say so.

## The list

| # | Suggestion | What it would do here | Why (the research) | Effort |
|---|---|---|---|---|
| 1 | **Stale nudge** | Builds on the 14/30-day colors. A quiet project's page asks one question: continue, shrink, park or close? It never closes anything itself. | Linear flags a project with a missing update after a set interval; projects mostly die quietly. [Linear: project updates](https://linear.app/docs/initiative-and-project-updates) | S |
| 2 | **"Stop for today" bridge** | A button on the project page asks for the next step and one line of context (prefilled from uncommitted git changes). The note heads the page next time and becomes the card's next step. | Forte's "Hemingway bridge": end every session knowing the next move, so restarting is cheap. [Todoist: Hemingway bridge](https://www.todoist.com/productivity-methods/hemingway-bridge) | S |
| 3 | **Guided weekly review** | One page steps through each active project: confirm the next step, tick steps, check the color. It shows the week ahead from Calendar and Todoist (read-only), then the parked shelf, and ends with "anything new?", which links to /start. | GTD's weekly review (get clear, get current, get creative) is what keeps the system trusted. [Todoist: weekly review](https://todoist.com/productivity-methods/weekly-review) | M |
| 4 | **Limit on active projects** | A cap on active cards (say 3). Starting a fourth asks which one to park first. | Personal Kanban's two rules are "visualize your work" and "limit work in progress". The board does the first; without the second it lets you start everything. [Personal Kanban](https://www.personalkanban.com/) | S |
| 5 | **Appetite and circuit breaker** | At approval, the budget becomes a fixed appetite. The card shows hours used against it. When it runs out, the project stops by default; going on means a new warden pass. | Shape Up fixes the time and flexes the scope; unfinished cycles end by default. [Shape Up: appetite](https://basecamp.com/shapeup/1.2-chapter-03), [circuit breaker](https://basecamp.com/shapeup/2.2-chapter-08) | S–M |
| 6 | **Kill criterion with a date** | /start records "if X isn't true by date D, close or shrink it." On D the project page shows it and asks you to judge it. | Annie Duke: set quitting criteria in advance, before sunk cost takes over ("would I start this today?"). [Epstein interviewing Duke](https://davidepstein.substack.com/p/annie-duke-quit) | S |
| 7 | **Your own estimate history** | Builds on the existing calibration. Closeout records estimated against actual hours by kind (code, research, coursework, household). The time suggestion then shows "you usually run ×1.6 on code". Later: 50% and 80% finish dates from your history. | The planning fallacy: people ignore how long their own past projects took; the fix is the outside view. [SPSP: Buehler](https://spsp.org/news-center/blog/buehler-planning-fallacy), [Spolsky: evidence-based scheduling](https://www.joelonsoftware.com/2007/10/26/evidence-based-scheduling/) | M (L with dates) |
| 8 | **"Parked, with a plan"** | A shelf between active and archived. Parking asks for a re-entry trigger and a review date ("when the semester ends, reopen and do X"). The weekly review brings it back on that date. | Masicampo and Baumeister (2011): a concrete plan for an unfinished goal stops it nagging at attention. [Secondary summary](https://bakadesuyo.com/2012/01/how-can-you-stop-worrying-about-that-stuff-yo/) | S |
| 9 | **Next step as a calendar block** | Turns the next step into "When [time/place], I will [action]" and proposes a Calendar block or Todoist task. Nothing is written until you approve (AGENTS.md). | Implementation intentions: a meta-analysis found d = .65 on reaching goals. [NCI: implementation intentions](https://cancercontrol.cancer.gov/brp/research/constructs/implementation-intentions) | S–M |
| 10 | **A premortem in the warden step** | One more question in /start: "It's six weeks from now and this failed. Why?" The top answers are kept as risks on the project page. | Klein's premortem brings out doubts that normal planning suppresses. It adds one line to a stage prompt, so per D-048 it needs a reason in the review. [HBR: premortem](https://hbr.org/2007/09/performing-a-project-premortem) | S |
| 11 | **Progress feed, with an optional weekly digest** | A timeline across projects of ticked steps, commits, notes and closeouts. Optionally, one stripped Claude call drafts "what moved this week" for you to edit. | Amabile and Kramer: seeing progress on meaningful work is the strongest everyday motivator. [HBR: small wins](https://hbr.org/2011/05/the-power-of-small-wins) | M |
| 12 | **Areas, apart from projects** | Ongoing responsibilities (coursework upkeep, the house) become Areas. They have no done-when and never turn red for lacking an end. | PARA: projects have outcomes, areas are ongoing; mixing them breaks the done and stale logic. [Forte Labs: PARA](https://fortelabs.com/blog/para/) | S |
| 13 | **Hill chart** | Drag each piece of the plan along a hill: uphill while figuring it out, downhill while doing it. A piece that hasn't moved since last time asks whether to split it. | Shape Up: a checklist can be 80% ticked and still stuck on an unknown; the hill shows it. [Shape Up: hill charts](https://basecamp.com/shapeup/3.4-chapter-13) | M |
| 14 | **Decisions across projects** | Builds on SE-00's log. Open decisions become decided (context, decision, consequences) from the app. A reversed one is marked "superseded by D-xxx". All of them are searchable across projects. | Nygard's architecture decision records keep the "why", including the superseded ones. [Cognitect: ADRs](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) | S–M |
| 15 | **A small manifest in each project folder** | State, area, appetite, kill date and next step live in a file in the project folder. The dashboard reads them instead of keeping its own lists. | Backstage keeps each service's metadata next to its code, so it travels with the repo. [Backstage: software catalog](https://backstage.io/docs/features/software-catalog/) | S–M |

## Claude's critique of the list

- **Strongest picks for your stated problem** (projects stalling, the gate costing too much): #2, #4, #6 and #5. Each is small, and each makes finishing or quitting a decision instead of a drift.
- **#3 is the most valuable and the most likely to be skipped.** A weekly review only works if it is short. Cap it at about 10 minutes, or it becomes the elicitation-fatigue problem again (R13).
- **#15 conflicts with today's build.** The dashboard folders added today live in one file in this repo (`dashboard/groups.json`), not in each project. A manifest would put the data in the project, which travels with it but adds a file to every repo, including your website. Decide before building #6, #8 and #12, because they would all store per-project data.
- **#9 and #11 touch outside services or Claude.** #9 needs your approval each time it writes to Calendar or Todoist. #11 adds a Claude call; keep it off by default.

## Considered and left out

- **Streaks and badges.** A broken streak counts as a setback, and setbacks weigh more than wins (Amabile and Kramer). They would also punish the burnout signs AGENTS.md already watches for.
- **Closing stale projects automatically** (GitHub's stale bot closes after 60 + 7 days). That breaks "the warden proposes and never applies"; #1 asks instead.
- **Cloud sync, a phone app, or a Notion or Linear backend.** They would move private project data off this machine, against the privacy model and the one-local-server rule.
- **Gantt charts, cross-project dependencies, burn-up reports.** Team overhead for one person; #7 and #13 give the useful signal more cheaply.
- **Betting-table meetings and status posts.** They assume an audience. The useful part, a deliberate go or no-go, is already the warden.

## Source caveats

- The two HBR pages (premortem, small wins) showed only their summaries, so they are cited for the core idea only.
- The Masicampo and Baumeister finding comes through a secondary summary; the APA page did not load.
- Studies of why open-source and side projects get abandoned showed only their abstracts, so no suggestion rests on them.
