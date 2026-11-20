# DevTeam roadmap

## Current state
2026-11-20. Plugin 2.3.0, pushed to `main`. Milestone **M1**: slices 1, 2 and 3 are done and released.

Pending that needs the user:
- Restart Claude Code so 2.3.0 loads. The next `/feature` run is the first live use of Stage 7 (the retro check); watch that it prints one `Retro:` line on a clean slice. Nobody has seen the 2.1.0 money-gate hook in a live session yet either.
- Slice 2 edited five skill descriptions (adopt, adr, debug, project, tdd). The 2026-10-08 eval baseline is no longer directly comparable for those five. A paid eval re-run (slice 11) needs its own approval with the cost stated. Slice 11 should also reword the `/retro` description, which still lists a CLAUDE.md rule first (see `docs/specs/retro-that-runs.md`).

Next action: slice 4 (config-protection hook).

## M1 — Close the gaps found in the 12-repo comparison
Source: the 2026-11-20 comparison of DevTeam against 12 agent/skill repos (superpowers, mattpocock/skills, compound-engineering, ECC, gstack, wshobson/agents, anthropics/skills, addyosmani/agent-skills, taste-skill, cloudflare/security-audit-skill, caveman, Claude-BugHunter). The user approved every slice below.

- [x] 1. **Money-gate precision.** CI rule fires only on writes; per-segment matching; paid-API rule only on network calls; every prompt names the command, what it does, and the cost class; local regression suite including the four 2026-11-20 false positives.
- [x] 2. **Plugin self-tests.** Strict frontmatter parse, name matches directory, "Use when" trigger present, 20 KB skill-size cap, double-encoding detector, free trigger-router test over the skill descriptions (no model calls).
- [x] 3. **Retro that runs.** `/feature` ends with a retro check (one line when nothing recurred); retro adopts the durable-lesson bar and the cheapest-form ladder (test or hook before prose).
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
- 2026-11-20: slice 1 done. 237-case suite (`sh tests/money-gate.test.sh`), all passing; two /code-review rounds; one test expectation corrected with user approval; heredoc bodies recorded as a known limit. Ordinary commands now cost ~70–90 ms in the hook instead of 500–850 ms.
- 2026-11-20: slice 2 done. 102 tests in `python -m unittest discover -s tests` (stdlib only, about 8 s on Windows): strict frontmatter, name/dir, trigger phrase, 1,024-character and 20 KB caps, UTF-8/BOM/mojibake, and a BM25 router over 35 prompt rows (3 marked as expected misses). Five descriptions gained missing words, with user approval. The score threshold and `none` prompts were dropped, with user approval, because a word matcher cannot separate them. `claude plugin validate .` misses both the 2.0.3 colon and a name/dir mismatch; the new suite catches both.
- 2026-11-20: slice 3 done. `/feature` gains Stage 7, an inline retro check after the commit that prints one `Retro:` line when nothing clears the bar. `/retro` gains the durable-lesson bar and the cheapest-form ladder (test, local hook or lint gate, skill edit, CLAUDE.md line). 30 pins in `tests/test_retro_contract.py`; full suite 132 of 132. New eval `retro-prefers-check-over-prose`, written, not run. /code-review found 2 important defects (a failed rule was screened out by the bar; recurrence across slices was invisible), both fixed test-first; 3 findings declined with reasons in the spec.
- 2026-11-20: slice 3's retro check proposed one fix and the user approved it: the encoding self-check now flags control characters (C0 except tab, LF, CR, plus DEL), after two decoded backspaces got into slice 3's files. Released as 2.3.0.
