---
name: retro
description: Self-improvement loop — turn recurring mistakes and friction from recent work into a durable fix (a CLAUDE.md rule, a new/updated skill, or an ADR). Use at the end of a rough slice, when the same correction keeps recurring, or on demand so lessons compound instead of being re-learned.
---

# Retro — the self-improvement loop

The point is to stop re-learning the same lesson. A correction made only in chat is gone at the next chat change; a lesson written to a durable file is paid for once and applies forever after. This skill reviews recent work and routes each real lesson to the file that will surface it next time. It **proposes** changes and lets the user approve each — it never rewrites standards silently.

## Stage 1 — Gather
Look back over the work in scope (this session, or the range the user names) for lessons that will *recur*:
- Corrections the user made more than once, or a stated preference that isn't written down anywhere.
- Bugs whose root cause was a pattern rather than a one-off — a `/debug` run that ended "this is a class of mistake."
- Pipeline friction: a stage skipped that shouldn't have been, or one run that wasted time and should be gated.
- Wrong turns: a plausible approach that burned time before being abandoned — what earlier signal would have caught it?

Keep only the recurring ones. A single typo is not a lesson; a habit is. If nothing recurred, stop here and say so.

## Stage 2 — Route each lesson
Send each to the cheapest durable home — and dedupe against what's already there (update the existing rule/skill rather than adding a near-twin):
- **Behavior that should apply every session** → a line for `CLAUDE.md`. Keep it tight; it's re-billed every session, so rule bloat has a real cost.
- **A repeatable multi-step process** → a new skill, or an edit to an existing one. Small, focused, named for its trigger.
- **A project-specific decision or fact** → an `/adr` (a real decision) or the roadmap's **Current state** (project status). Never put project facts in CLAUDE.md.
- **Nothing durable fits** → drop it. Not every annoyance earns a rule.

## Stage 3 — Propose
Show the user a short list: each lesson, its target file, and the exact change (the line to add, the skill to create, the ADR to write). They approve, edit, or reject per item; apply only what's approved. Flag that changes to a skill or CLAUDE.md take effect next session, not retroactively.

## When NOT to use
Mid-slice (finish it first), or when the run was clean — an empty retro is the correct outcome after a smooth slice, and saying so in one line beats inventing rules to justify the pass.
