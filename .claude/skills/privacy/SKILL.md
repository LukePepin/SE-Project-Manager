---
name: privacy
description: The security and privacy check. A git pre-push hook blocks any push that would publish a project's private terms (names, ids, locations, collaborators' work) or secrets (keys, tokens, .env files). Use when setting up a repo that may be pushed or shared, when Luke asks "is anything private in here?", before a first push, or when the hook blocks a push.
argument-hint: "[repo folder, defaults to the current repo]"
---

# Privacy: nothing private gets published

**Status: ACCEPTED** (Luke waived the follow-up explain-back, 2026-10-09, D-045: "skip the explain-back"). Its content is pinned; any later edit needs Luke's approval again (D-044). AI-drafted by Claude on 2026-10-08 from Luke's direction (Games-People-Play D-015; SAFE-01, SAFE-02). It is generalized from I-Know-Puck's `scripts/check_public.py`.

`privacy_check.py` uses only the Python standard library.

## Set up a repo

1. **Install the hook.** This writes `.git/hooks/pre-push` and git-ignores `.privacy-terms`:
   ```
   python <this skill>/privacy_check.py --install-hook
   ```
   In a project other than Games-People-Play, copy `privacy_check.py` into the project first (for example to `scripts/`) and install from there, so the hook doesn't depend on a path on one machine (SE-00 R6). Only do this once the skill is `ACCEPTED` (SAFE-03).
2. **Ask Luke what must never be public**, using lens L16.
   - Terms that are private everywhere (Luke's locations, other people's names) go in the **global** file, `.privacy-terms.global` in the Games-People-Play repo (D-033). Every project's check reads it.
   - Terms private to one project go in that project's `.privacy-terms`.
   - Both use one term per line, as `term` or `term  # label`.
   - Never commit this file.
   - Never repeat its terms in chat or in any tracked file.

## Check

```
python <this skill>/privacy_check.py            # the working tree
python <this skill>/privacy_check.py --ref HEAD # one commit, as the hook does
```

A hit shows the file, line and label, never the private text itself. To fix one:
- edit the file; or
- move it to a git-ignored path; or
- if it is a deliberate exception, put `privacy: allow` on that line, and say so to Luke.

## Rules

- **Claude never pushes with `--no-verify`**, and never edits or removes the hook to get a push through. A blocked push goes to Luke.
- Branches named `private*` are never pushed.
- The hook checks the commit being pushed, not the whole history. Before a repo's first public push, also check older commits, and tell Luke what is found.

---

**Explain-back (Luke):** Where do a project's private terms live, why is that file never committed, and what do you do when the hook blocks a push?

> a global private term gitignored file should be in the games-people-play repo and for project specific privacy that data is in those repos properly marked
>
> *(Answered 2026-10-08 in the review packet.)*

**Explain-back follow-up (Luke, D-044; waived by D-045):** Why is a term file never committed, and what do you do when the hook blocks a push?

>
