---
name: discover
description: Requirements discovery at project conception — turn "I want an app that does xyz" into a concrete product brief before any architecture or code. Use for any new product idea, or when scope is fuzzy. Runs as Stage 0 of /project.
---

# Discovery

The most expensive bug is building the wrong thing. Do not architect, scaffold, or code until a brief exists. The output is `docs/brief.md`.

## Stage 1 — Interrogate the idea
Ask the user the questions that change what gets built, in ONE batch (not a drip-feed), and only the ones the idea leaves genuinely open:
- **Problem & user**: who has this problem, what do they do today instead, what does success look like for them?
- **Core workflow**: the single most important path through the app, start to finish.
- **Scope fence**: for each plausible feature — must-have for v1, later, or never? Push back to keep v1 ruthless: the best v1 is the smallest thing that proves the core workflow.
- **Constraints**: platforms (web/mobile/desktop), budget for paid services, existing systems/accounts to integrate, privacy or auth requirements, solo use vs. multi-user.
- **Taste**: products they admire (for design language) and products that get this problem wrong.

Propose defaults for anything they don't care about rather than asking; record them as assumptions.

Grill, don't survey. Follow up on vague answers until they are concrete enough to build from — "users can share things" is not an answer, "an owner can grant another account read-only access by email" is. When a choice genuinely forks the product (not just a preference), lay out the 2–3 options with their trade-offs and make the user pick, rather than accepting the first thing said. A shallow answer here becomes a wrong architecture three stages later, which is the most expensive place to discover it.

## Stage 2 — Research (web)
- Find 2–4 comparable products; note their table-stakes features, what users complain about, and what to deliberately NOT copy.
- Check feasibility of anything technically risky in the idea (API availability, platform limits, pricing of required services) — verify with a search, not from memory.
- Collect 1–3 design inspiration references if the product has a UI.

## Stage 3 — Write the brief
Write `docs/brief.md`:

```markdown
# <Product name> — product brief
Date: <YYYY-MM-DD>

## Problem
Who hurts, how, and what they do today.

## Core workflow
The one path that must be excellent, as a numbered user journey.

## v1 scope
**In:** …  **Later:** …  **Never:** … (with one-line reasons for Later/Never)

## Constraints & assumptions
Platforms, budget, integrations, auth/privacy; assumptions made on the user's behalf, flagged.

## Landscape
Comparable products — what to match, what to beat, what to avoid.

## Design references
Links/names + which aspect of each to borrow.

## Success criteria
3–5 checkable statements that mean v1 worked.

## Open questions
Anything unresolved that will need an answer before the relevant milestone.
```

Present the brief's key calls (scope fence, assumptions) to the user for a yes/no before handing off to the architect. The brief is the spec's parent: `/feature` specs and architect designs must trace back to it.
