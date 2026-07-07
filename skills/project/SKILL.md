---
name: project
description: Whole-system pipeline — take a product idea from conception to a working v1 across many sessions: discovery → architecture → scaffold → roadmap → repeated /feature slices. Use when starting a new app/system, or resuming one (it picks up from docs/roadmap.md).
---

# Project pipeline

`/feature` builds one slice; this skill builds the system. It is designed to survive chat changes: ALL state lives in repo files (`docs/brief.md`, `docs/adr/`, `docs/roadmap.md`, `docs/specs/`), never in conversation memory. Any new session can resume from the files alone.

## Resuming (run this check first, always)
If `docs/roadmap.md` exists, this is a resume: read the roadmap's **Current state** section, the in-progress slice's spec, and any ADRs newer than the last session note. Announce where the project stands and continue from the next unchecked item. Do NOT re-run discovery or architecture on a resume unless the user is changing direction — if they are, record the change as a superseding ADR and update brief + roadmap before coding.

## Stage 0 — Discovery
Run `/discover` → `docs/brief.md`, approved by the user. Skip only if an approved brief already exists.

## Stage 1 — Architecture
Launch the **architect** agent with the brief. Present the stack and structure choices to the user; record accepted decisions with `/adr`. Disagreements between brief and design go back to the user, not silently resolved.

## Stage 2 — Walking skeleton
Scaffold the repo per the architect's structure: tooling, test infrastructure, linting, `.gitignore`, README stub, and the thinnest possible end-to-end path (e.g. one page hitting one endpoint returning one DB row). Verify the skeleton runs and an (empty) test suite executes. Commit. Everything after this is `/feature` slices on a working base.

## Stage 3 — Roadmap
Write `docs/roadmap.md` from the brief's v1 scope:

```markdown
# Roadmap
## Current state
<2–5 lines: last updated <date>, what works now, what is in progress, next action.>

## Milestone 1 — <name> (goal: <user-visible outcome>)
- [ ] <feature-slice — one /feature run, independently testable>
- [ ] …
## Milestone 2 — …
```

Slicing rules: each item is one `/feature` run (roughly one session or less); each leaves the app shippable; order by risk — the scariest/least-certain slice goes first, not last. Get a nod from the user on milestone order.

## Stage 4 — Build loop
For each unchecked slice: run `/feature <slice>`. After it completes:
1. Check the box and refresh **Current state** (date, what works, next action).
2. Note any deviation from brief/architecture in the roadmap and, if it was a real decision, an ADR.
3. Commit with the slice name.

End of every working session — even an interrupted one — update **Current state** with an honest "where I stopped and why". That line is what the next chat resumes from.

**Context engine checkpoint:** once the codebase outgrows targeted greps (~50+ source files), suggest setting up Graphify: `graphify .` builds the knowledge graph (local tree-sitter, zero tokens) and `graphify hook install` keeps it fresh on every commit. Note it in **Current state** so later sessions know the graph exists. From then on, structural questions go to the graph first (see CLAUDE.md context economy).

## Milestone boundaries
At each milestone's end: run the full suite, `/verify` the milestone goal end-to-end, run `/security-review` if the milestone touched auth/input/secrets, `/hygiene`, and give the user a milestone report (goal met?, deviations, what's next).
