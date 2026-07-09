---
name: debug
description: Systematic debugging — reproduce, isolate the root cause, fix the cause not the symptom, and prove the fix with a regression test. Use whenever behavior is wrong and the cause isn't already obvious; skip for typos and mistakes you can already see.
---

# Systematic debugging

A bug you can't reproduce, you can't fix — you can only guess, and a guess edits the symptom while the cause survives. Work the phases in order; do not jump to a fix because one looks plausible. Per the working method, never surface a hypothesis as the diagnosis: a cause is confirmed only when you have seen it produce the failure and seen the fix remove it.

## Phase 1 — Reproduce
Get a deterministic repro before touching any code. Capture the exact inputs, environment, and the smallest sequence of steps that still fails; write down observed vs expected precisely. If it fails only intermittently, hunt what differs between a passing and a failing run (timing, order, data, cached state) — that variance is the lead. No repro → stop and get one (a failing input, logs, the user's exact steps); do not "fix" blind.

## Phase 2 — Isolate the root cause
Narrow until you can point at the line and say why it's wrong.
- **Bisect the space.** Which layer (UI, state, network, DB), which module, which call — halve the search each step. For a regression, `git bisect` or diff against the last known-good commit.
- **Read real values at the boundary** where correct becomes wrong — instrument with a log/breakpoint rather than assume. Check each assumption against actual output; the bug is usually an assumption you were sure of.
- **Separate trigger from cause.** The trigger is what the user did; the cause is why the code mishandles it. Ask "why" down the chain until the answer is code you can change, not another symptom.
Stop when you can state it in one line: "input X reaches line Y, which does Z, and Z is wrong because W."

## Phase 3 — Fix the cause
Fix W, not the symptom. A real root-cause fix should also kill any sibling symptoms of the same cause — if it only silences this one call site, you found a symptom, keep going. Follow the CLAUDE.md code standards. Resist "while I'm here" scope creep: note unrelated issues, don't fold them into this change.

## Phase 4 — Prove it
Write a test that reproduces the bug — the minimized Phase-1 repro — following `/tdd`. Run it against the **unfixed** code and watch it fail for the right reason, then apply the fix and watch it pass: that ordering is the proof the test actually guards this bug. This is the one sanctioned exception to tests-before-code — the repro test may be written after diagnosis, but it must still be seen to fail before the fix lands. Then run the full suite (a fix that reddens another test isn't done) and `/verify` the affected flow end-to-end. Leave the regression test in — it is the receipt.

## Report
State the root cause in one sentence (cause, not symptom), the fix, the regression test now guarding it, and anything you deliberately left unfixed. If the bug was an instance of a wider class of mistake, that is a `/retro` lesson — say so.
