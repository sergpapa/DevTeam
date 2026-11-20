---
name: retro
description: Self-improvement loop that turns recurring mistakes and friction into a durable fix (a CLAUDE.md rule, a new or updated skill, a hook, or an ADR), proposed item by item for the user's approval and never applied silently. Use whenever the user reports that a mistake keeps happening or asks how to stop it ("you did it again", "this is the third time", "what should change so this stops happening", "how do we prevent this", "make this a rule"), at the end of a rough slice, or on demand. Ends with a prune pass (only after approved changes are applied) that retires rules and skills the changes made stale.
---

# Retro — the self-improvement loop

The point is to stop re-learning the same lesson. A correction made only in chat is gone at the next chat change; a lesson written to a durable file is paid for once and applies forever after. This skill reviews recent work and routes each real lesson to the file that will surface it next time. It **proposes** changes and lets the user approve each — it never rewrites standards silently.

## Durable-lesson bar
A lesson earns a durable fix only if it passes all three tests:
- **Occurrence.** It happened 2 or more times, or once when it spent money, lost data, or shipped a defect past review.
- **Transfer.** A future session on a different task would act differently because of it. A fix that only helps the task just finished is not a lesson.
- **Not already handled.** A lesson that an existing rule already prevents is dropped. If an existing rule covers it but failed to stop the mistake, the lesson still clears the bar, and the proposal fixes that rule or converts it to a lower rung of the ladder, instead of adding a twin.

## Stage 1 — Gather
Look back over the work in scope (this session, a slice record in `docs/specs/`, or the range the user names) for candidates:
- Corrections the user made more than once, or a stated preference that isn't written down anywhere.
- Bugs whose root cause was a pattern rather than a one-off — a `/debug` run that ended "this is a class of mistake."
- A single costly hit: money spent, data lost, or a defect that got past review.
- Pipeline friction: a stage skipped that shouldn't have been, or one run that wasted time and should be gated.
- Wrong turns: a plausible approach that burned time before being abandoned — what earlier signal would have caught it?

Keep only what clears the durable-lesson bar. If nothing does, stop here and say so in one line.

## Stage 2 — Climb the cheapest-form ladder
For each lesson, stop at the first rung that can hold it. A test or a hook costs nothing per session and cannot be ignored; prose is re-billed in every session that loads it, and can be ignored.

1. **Test** — a test in the repo's suite that fails when the mistake comes back.
2. **Hook, lint rule or config gate** — a mechanical check that runs locally and blocks the mistake when it happens: a Claude Code hook, a linter rule, a pre-commit or tool config setting. A CI workflow is not this rung, because it bills on every push.
3. **Skill edit** — a line in the skill that runs at the moment the mistake happens, so it loads only then. Small, focused, named for its trigger.
4. **CLAUDE.md line** — only for behavior every session needs. Keep it tight; it is re-billed every session.

A proposal on rung 3 or 4 says in one sentence why a lower rung cannot hold it. Dedupe against what's already there: update the existing test, hook, skill or rule rather than adding a near-twin.

Project facts sit outside the ladder: a real decision goes to an `/adr`, project status to the roadmap's **Current state**. Never put project facts in CLAUDE.md. A lesson that fits no rung is dropped; not every annoyance earns a rule.

## Stage 3 — Propose
Show the user a short list: each lesson, its rung, its target file, and the exact change (the test to add, the hook to write, the line to add, the ADR to write). They approve, edit, or reject per item; apply only what's approved. Flag that changes to a skill or CLAUDE.md take effect next session, not retroactively.

## Stage 4 — Prune (only after the approved changes are applied)
Additions ratchet: every CLAUDE.md line and every skill description is re-billed in each session that loads it, so growth without retirement is a slow leak. Once the Stage 3 approvals are applied — never before, and never bundled into the Stage 3 approval batch — sweep the durable files for what the applied changes made stale:
- A CLAUDE.md rule now redundant: superseded by a new rule, absorbed into a skill, or guarding a mistake that no longer occurs.
- A skill whose trigger never fires anymore, or whose job a newer rule or skill now covers.
Propose each retirement with the reason it is safe to drop; the user approves, edits, or rejects per item, exactly as in Stage 3. No candidates → say so in one line. Never prune silently.

## When NOT to use
Mid-slice (finish it first), or when the run was clean — an empty retro is the correct outcome after a smooth slice, and saying so in one line beats inventing rules to justify the pass.
