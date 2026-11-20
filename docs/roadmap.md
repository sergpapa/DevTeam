# DevTeam roadmap

## Current state
2026-11-20. Plugin 2.0.3. Working on milestone **M1 — Close the gaps found in the 12-repo comparison**, slice 1 (money-gate precision). Spec: `docs/specs/money-gate-precision.md`.

Pending that needs the user: every paid eval run (slice 11) needs its own approval with the cost stated. Nothing is pushed until the user says so.

Next action: finish slice 1 (tests → implementation → review → commit), then slice 2.

## M1 — Close the gaps found in the 12-repo comparison
Source: the 2026-11-20 comparison of DevTeam against 12 agent/skill repos (superpowers, mattpocock/skills, compound-engineering, ECC, gstack, wshobson/agents, anthropics/skills, addyosmani/agent-skills, taste-skill, cloudflare/security-audit-skill, caveman, Claude-BugHunter). The user approved every slice below.

- [ ] 1. **Money-gate precision.** CI rule fires only on writes; per-segment matching; paid-API rule only on network calls; every prompt names the command, what it does, and the cost class; local regression suite including the four 2026-11-20 false positives.
- [ ] 2. **Plugin self-tests.** Strict frontmatter parse, name matches directory, "Use when" trigger present, 20 KB skill-size cap, double-encoding detector, free trigger-router test over the skill descriptions (no model calls).
- [ ] 3. **Retro that runs.** `/feature` ends with a retro check (one line when nothing recurred); retro adopts the durable-lesson bar and the cheapest-form ladder (test or hook before prose).
- [ ] 4. **Config-protection hook.** Block edits to lint, formatter, and test-runner config and `--no-verify` / hooks-path bypasses.
- [ ] 5. **Skill content.** Terms section in `docs/brief.md` used by later stages; `/debug` built around a failing loop, plus the layer-ordering trap; rationalization tables in `/tdd` and `/debug`; characterization-first evidence strategy for legacy code in `/tdd` and `/adopt`; test-guardian POST checks for new suppressions, skips, and deleted tests; per-slice test seams as a Stage 0 default.
- [ ] 6. **Refute pass.** `/feature` Stage 5 review findings go to a fresh agent briefed to refute them; each ends confirmed, needs-validation (names the missing fact), or rejected.
- [ ] 7. **Routing hint hook.** UserPromptSubmit keyword match that names the DevTeam skill a prompt calls for; no model call.
- [ ] 8. **Stop-hook contract.** A `/feature` slice cannot end without test-guardian PRE and red-test evidence, unless the user waives it.
- [ ] 9. **Always-on context trim.** Cut `CLAUDE.template.md` (1,860 words) by moving detail into the skills that use it.
- [ ] 10. **Free measurement.** Committed transcript-counting script (per machine), skill value ledger, check of the real `/debug` and `/hygiene` runs.
- [ ] 11. **Eval cases.** Sharpen debug, hygiene and retro so the base model fails them; should-stay-quiet pairs; Plain-style case with a control prompt and fidelity checks; a `/project` case; a script that flags Δ=0 cases. Writing is free; running needs approval.

Deferred, with reasons recorded in the comparison: autonomous plan executor (needs an ADR, ~15x tokens), browser design gate and copy-lint for `/edge` (wait until `/edge` is used).

## Slice log
- 2026-11-20: roadmap created from the 12-repo comparison.
