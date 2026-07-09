---
name: feature
description: End-to-end TDD pipeline for building a feature or project — requirements → architecture → failing tests → implementation → verification → design review → code review → hygiene. Use for any non-trivial feature; skip for one-line fixes.
---

# Feature pipeline

You (the main session) are the orchestrator AND the implementer. Do not delegate implementation to subagents — you have the full conversation context; they do not. Delegate only the steps marked as agent launches, and skip any stage that does not apply (no UI → no design review; existing architecture fits → no architect). Announce which stages you are skipping and why.

## Stage 0 — Scope
Restate the request as concrete acceptance criteria (bulleted, testable). If a criterion is genuinely ambiguous AND the ambiguity changes what you'd build, ask now — never mid-pipeline. Write the criteria to `docs/specs/<feature-slug>.md`.

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

## Stage 4 — Verify
Run the full test suite, then `/verify` to exercise the changed behavior end-to-end in the real app — not just the tests.

## Stage 5 — Independent review (launch in parallel where possible)
- Launch **test-guardian** in POST mode.
- If anything user-facing changed, launch **design-reviewer**.
- Run `/code-review` (medium effort).
Fix confirmed findings; push back on incorrect ones with reasoning rather than blindly applying them. If a fix changes behavior, re-run Stage 4.

## Stage 6 — Hygiene & docs
Run `/hygiene`. Update README/docs if behavior or setup changed. Commit.

## Final report to the user
Lead with what was built and whether every stage passed. Include: acceptance criteria status, test count and coverage of the criteria, review verdicts, decisions recorded, and anything deferred or flagged. Report failures plainly — never present a partially-verified feature as done.
