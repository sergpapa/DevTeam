# Retro that runs: every slice ends with a lesson check

## Why
The 30-day usage count on 2026-11-20 shows `/retro` called 0 times against 139 `/feature` runs. It only runs when someone remembers it, so lessons from slices die in chat. When it does run, nothing steers it toward the cheapest fix: it routes lessons straight to prose (a CLAUDE.md line or a skill edit), which is re-billed every session and can still be ignored. A test or a hook costs nothing per session and cannot be ignored.

## Decisions (user, 2026-11-20)
- **Where:** an inline step in the main session at the end of `/feature`, after the Stage 6 commit and before the final report. No subagent.
- **Bar:** a lesson qualifies if it happened 2 or more times, or once when it spent money, lost data, or shipped a defect past review. It must also change what a future session on a different task would do, and not already be covered by an existing rule.
- **Ladder:** test, then hook (or lint rule or config gate), then skill edit, then CLAUDE.md line. ADRs and the roadmap stay a separate route for project facts.
- **Testing:** free unittest pins on the skill wording, plus one new eval case that is written but not run.

## Acceptance criteria
1. **/feature ends with a retro check.** `skills/feature/SKILL.md` has a section headed "Retro check", placed after the Stage 6 section and before "Final report". It says:
   - it runs in the main session, with no subagent;
   - what it reads: the slice record in `docs/specs/<slug>.md` (test-guardian and review findings, refusals) and the user's corrections in this session;
   - it applies `/retro`'s durable-lesson bar;
   - when nothing qualifies, its whole output is one line beginning `Retro:`, for example `Retro: nothing recurred.`;
   - when something qualifies, it runs `/retro` from Stage 2 with those lessons, and nothing is applied without the user's approval.
   The "Final report" section includes the retro line.
2. **/retro states the durable-lesson bar.** `skills/retro/SKILL.md` has a "Durable-lesson bar" section with three tests: occurrence (2+ times, or once if it spent money, lost data, or shipped a defect past review), transfer (a future session on a different task would act differently), and not already covered (if an existing rule covers it and still failed, the proposal fixes or converts that rule instead of adding a twin). The old line "A single typo is not a lesson; a habit is" is gone, and so is Stage 1's "Keep only the recurring ones", because both contradict the one-costly-hit clause. Stage 1 keeps what clears the bar instead.
3. **/retro climbs the cheapest-form ladder.** Stage 2 of `skills/retro/SKILL.md` is a numbered list in this order: 1 test, 2 hook (lint rule or config gate), 3 skill edit, 4 CLAUDE.md line. It says to stop at the first rung that can hold the lesson. A proposal on rung 3 or 4 states in one sentence why a lower rung cannot hold it. Project facts go to an ADR or the roadmap, outside the ladder. A lesson that fits no rung is dropped.
4. **Proposals name their rung.** Stage 3 says each proposal names its rung along with the target file and the exact change.
5. **New eval case** `evals/retro-prefers-check-over-prose/`: a prompt about a mistake that recurred and that a test or lint rule could catch, written the way a user asks and never naming the skill. Graders: `skill-fired.md` (`tool_used`, Skill `retro`) and `criteria.md` (`llm`): PASS only if the first fix proposed for the mistake is an automated check (test, lint rule, hook) that names its file and asks before applying; FAIL if the main fix is a prose rule, or a prose rule is proposed without saying why an automated check cannot hold it. Its first sentence is a router case that routes to `retro`. It is not run in this slice.
6. **Pinned.** `tests/test_retro_contract.py` fails if any of criteria 1 to 4 is removed or reordered: the Retro check section missing or in the wrong place, the one-line `Retro:` output gone, the approval rule gone, the bar's clauses gone, the ladder reordered, or the why-not-lower rule gone.
7. **Docs.** README's `/feature` row lists the retro step, and its `/retro` row says `/feature` runs the check at the end of every slice.

## Scope fence
- The `/retro` description is not edited. `/feature` calls retro by name, so routing does not depend on it, and editing it would break the eval baseline for one more skill.
- No hook is written. Slice 8 (Stop-hook contract) is where enforcement lives.
- `CLAUDE.template.md` is not edited. Slice 9 trims it.
- No paid eval run. Running the new case waits for slice 11 approval.
- `/debug`, `/project` and `/adopt` are unchanged. `/project` gets the check through `/feature`.

## Assumptions (proposed defaults, not asked)
- The retro check runs after the commit, so its proposals never block or change the slice's commit. Approved changes go in a separate commit.
- Pins match on short phrases and heading order, not whole sentences, so the wording can be edited without breaking them as long as the rule stays.

## Slice record
- 2026-11-20, test-guardian PRE: FAIL, fixable. 1 test was green before any work (ADR, roadmap and "drop" already sat in Stage 2). 7 of 12 pin groups would pass a wrong implementation, mostly through negation: a bare `approv` matches "no approval needed". Other gaps: the eval graders and prompt frontmatter were barely pinned, the ladder accepted a fifth rung, and a `###` heading counted as a section. Fixed before the red commit: each rule is now pinned as one sentence holding all its parts, with a negation check where a negated sentence would still match; the ladder must be exactly 4 contiguous rungs; sections are level-2 headings with code fences stripped. It also found that Stage 1's "Keep only the recurring ones" contradicts the one-costly-hit clause; criterion 2 now covers it.
