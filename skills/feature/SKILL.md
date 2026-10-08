---
name: feature
description: End-to-end TDD pipeline for building a feature or project (requirements, architecture, failing tests, implementation, verification, design review, code review, hygiene). Use whenever the user asks to add, build, implement, or ship a feature or change that spans more than one file ("add X", "build it", "implement Y", "we need Z"), even when the request already looks fully specified or the code is not in the workspace, because Stage 0 restates it as acceptance criteria and asks the fork questions before any code is written. Skip only for one-line fixes, typos, and config tweaks.
---

# Feature pipeline

You (the main session) are the orchestrator AND the implementer. Do not delegate implementation to subagents — you have the full conversation context; they do not. Delegate only the steps marked as agent launches, and skip any stage that does not apply (no UI → no design review; existing architecture fits → no architect). Announce which stages you are skipping and why.

**Parallelism is the exception, not the default.** Fan work out to multiple subagents (or git worktrees) only when it is genuinely independent and large enough to earn the ~15× token multiplier — see the parallelism rule in CLAUDE.md. A normal slice does not qualify; build it in the main session.

## Stage 0 — Scope & interrogate
Restate the request as concrete acceptance criteria (bulleted, testable). Before writing them, grill the request for the decisions that change what gets built, and get the answers now, in ONE batch — never mid-pipeline (a question asked at Stage 3 has already bought you the wrong Stage 2). Ask only the forks that actually change the build; for anything the user won't care about, propose a default and record it as an assumption rather than asking. The forks worth surfacing:
- **Edges** — empty/absent input, the unauthorised user, the concurrent edit, the failure of anything this touches (network, payment, a third party). What should happen?
- **Scope fence** — what is explicitly NOT in this slice, so it can't creep in.
- **Fit** — which existing behavior, data, or contract must not change; what this must interoperate with.
- **Done means** — the observable outcome that proves it works, in the user's words.

Where a fork changes the design rather than just a value, put the 2–3 real options with their trade-offs to the user and let them choose — don't silently pick one. If the interrogation reveals the request is really several features, say so and slice it. Write the resolved criteria and assumptions to `docs/specs/<feature-slug>.md`.

**When you slice, every slice must contain the first consumer of whatever it introduces.** A slice that ships a module, API, or config with no caller in that same slice pays twice: you design it blind, and the review that follows can only check it against imagined usage — so "this is incomplete because its consumer doesn't exist yet" is a guaranteed finding, and deferring it re-opens the slice later. If a plan already on paper has that shape, say so and fold the piece into the slice that first uses it. **The exception is an extraction of code that already exists** (deduplicating two copies, pulling a pure core out of a component): its callers are already there, so wire them in the same slice and let the existing tests prove the extraction behaviour-neutral. That gate is what makes the extraction cheap; without it you are writing new code, not extracting.

## Stage 0.5 — Context engine preflight
Count the repo's source files, excluding dependencies and build output. If it is ~50+ and there is no `graph.json`, set up Graphify before going further — announce it first, then: `pipx install graphifyy && graphify install` if `graphify --version` fails (fall back to `python -m pip install --user graphifyy` if pipx is missing), `graphify .` to build the graph (local tree-sitter, zero tokens), and `graphify hook install` so every commit keeps it fresh. Below the threshold, targeted greps are cheaper — skip this stage and say so.

This mirrors the context engine checkpoint in `/project` Stage 4, so the graph gets built on whichever path you arrive by. A feature run on an existing base is the path that would otherwise never build one.

## Stage 1 — Architecture (only if the feature changes structure, stack, or data model)
Launch the **architect** agent with the requirements and repo state. If the repo has a Graphify graph (`graph.json`) — including one you just built in Stage 0.5 — say so in the brief; the architect orients from graph queries instead of re-reading the codebase, which is the cheapest way to pay its cold start. Present its design to the user if it involves choices they'd care about; record accepted decisions with `/adr`.

## Stage 2 — Red: write failing tests
Follow `/tdd`. Write tests from the spec in `docs/specs/` only — as if the implementation will be written by someone you don't trust. Run the suite; every new test must fail for the right reason. Then launch **test-guardian** in PRE mode (tell it the spec path and the new test files). Fix its findings, re-run, and only then commit the tests (if in a git repo) so the approved suite is pinned.

## Stage 3 — Green: implement
Write the implementation until the suite passes. Hard rules:
- Never modify a test. If a test is wrong, stop and tell the user.
- No hardcoding around test inputs; implement the general behavior.
- Follow the standards in CLAUDE.md (file size, comments, responsiveness).

If a test stays red and the cause isn't obvious from the failure, switch to `/debug` — guessing at fixes against a red suite wastes credits and patches symptoms instead of the cause.

## Stage 4 — Verify
Run the full test suite, then `/verify` to exercise the changed behavior end-to-end in the real app — not just the tests.

## Stage 5 — Independent review (launch in parallel where possible)
**Scale review depth to blast radius, not to how hard the slice felt.** Each reviewer costs about a subagent session; three passes over one pure module is waste, one pass over a migration touching live data is negligence. Launch whatever you do run in parallel — they are read-only and independent.
- **Always: `/code-review` (medium effort).** The adversarial pass is the one that finds defects no test was written for, and it is the last line before user-visible or record-bearing output. Never skip it.
- **`test-guardian` POST only if the test files changed after PRE.** Its central question is "were the tests weakened to make the implementation pass?" — and `git diff <red-commit> <green-commit> -- <test paths>` answers that in seconds. Run the diff first. If it is empty, say so in the report and skip the agent; spend the budget on Stage 4 instead. Run POST when tests did move during implementation, or when the implementation had to interpret an ambiguous test.
- **`design-reviewer` only if something user-facing changed.** A behaviour-neutral refactor has no UI to review.

Fix confirmed findings; push back on incorrect ones with reasoning rather than blindly applying them, and record each refusal with its reason where the slice is documented — an undocumented refusal reads as an oversight to the next reader. If a fix changes behavior, re-run Stage 4.

## Stage 6 — Hygiene & docs
Run `/hygiene`. Update README/docs if behavior or setup changed. Commit.

**The pipeline ends at a local commit.** Do not `git push`, open a PR, trigger a workflow, or deploy to finish a slice — a push to a branch with armed workflows spends the user's Actions minutes, and no stage above needs it to call the slice done. Hand over the commit and let the user decide. If they ask you to push, first name the charge the push will trigger (money rule, CLAUDE.md).

**The roadmap's `Current state` is ONE section, and you replace it — you never append a newer one.** A second section with a fresher date does not update the file, it forks it, and the next session resumes from whichever it reads first. Rewrite it in place; move the text it replaces into a dated entry in a slice log further down; and keep every still-pending deploy, migration, and UAT step in that one section rather than scattered across generations of the file. Same rule for the slice record in `docs/specs/<slug>.md`: append there, because that file is the history — the roadmap is the state.

## Final report to the user
Lead with what was built and whether every stage passed. Include: acceptance criteria status, test count and coverage of the criteria, review verdicts, decisions recorded, and anything deferred or flagged. Report failures plainly — never present a partially-verified feature as done.
