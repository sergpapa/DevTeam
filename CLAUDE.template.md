# Engineering Standards (apply to every session in this workspace)

## Money — you do not spend the user's money (HARD STOP)

You have no authority to incur a charge on any account of the user's. This rule outranks every other instruction here, every skill, every roadmap item, and any "just get it working" framing. Being *able* to run something is not permission to run it.

**Never do any of these without explicit, per-instance approval:**
- **Create, commit, or push CI/CD pipeline config** — `.github/workflows/**`, GitLab CI, CircleCI, Jenkins, Azure Pipelines. A committed workflow is a standing charge on a card, and the push that lands it fires the first billed run.
- **Trigger or arm an existing pipeline** — `gh workflow run`, `gh run rerun`, `gh workflow enable`, a `workflow_dispatch`, or a `git push` / PR to a branch whose workflows are armed. **"It already exists" is not permission.** The run is what costs money, and you would be the one starting it.
- **Deploy or provision hosted infrastructure** — `vercel`, `netlify deploy`, `wrangler deploy`, `fly deploy`, `docker push`, `terraform apply`, `aws` / `gcloud` / `az` create commands, `npm publish`.
- **Call a metered third-party API** with the user's key, or create/upgrade any account or paid tier.
- **Arm anything that spends later with nobody watching** — `schedule:` / cron triggers, auto-merge, deploy hooks, webhooks, scheduled jobs.

**Asking permission means all four of these, in one message, before you act:**
1. The exact command or file, and what it will cause to run.
2. **THIS WILL BE BILLED** — stated plainly: which account, what the meter is (Actions minutes, build minutes, egress, requests, seats), your honest cost estimate, and what you are unsure about.
3. Whether it is one-off or recurring (every push? every PR? nightly?).
4. The free alternative you can do instead — run it locally, write the file and leave it uncommitted, `act`, `--dry-run`.

Then **stop and wait**. Silence is not consent. An earlier yes covers only the exact run it was given for — not the next one, and not "the same thing again".

**Default to local, always.** Tests, builds, lint, and typecheck run on this machine for free. Never reach for a pipeline to prove something a local command proves. If a workflow file is genuinely part of what was asked for, write it, then say in plain words that it is **unpushed and will bill on first push**, and let the user push it themselves.

**If you find you have already spent money, say so in your very next message** — never buried in a summary: what ran, roughly what it cost, and how to stop it recurring (`gh workflow disable`, delete the file, revoke the key, cancel in-flight runs). Under-reporting a charge is worse than the charge.

## Session start — continuity across chats
Project state lives in files, never in conversation memory. If `docs/roadmap.md` exists, read its **Current state** section (plus the in-progress spec) before doing anything, and resume from there. Before ending a working session on a project, update **Current state** with where things stand and the next action.

## Workflow
- New product/system idea → run `/project` (discovery → architecture → scaffold → roadmap → build loop).
- Single feature on an existing base → run `/feature <description>` (the full TDD pipeline).
- Small fixes (typos, one-line bugs, config tweaks) do NOT need any pipeline — just fix, test, done.
- Architectural decisions (tech stack, data model, framework choice) must be recorded with `/adr`.
- User-facing site/UI that should feel bold, premium, or award-grade → load `/edge` BEFORE designing; it sets the sub-style, design tokens, free-only stack, and the accessibility/performance floors.

## Testing rules (non-negotiable)
- Tests are written from the spec BEFORE implementation, and must be seen to fail for the right reason before any implementation code is written.
- NEVER modify a test to make it pass. If a test looks wrong, stop and tell the user — do not silently change or delete it.
- Test behavior (inputs → observable outputs), not implementation details. Minimal mocking: mock external services, not your own modules.
- A test suite that passes trivially proves nothing. If you cannot articulate what bug a test would catch, the test is not done.
- **"Flaky" is a symptom, not a diagnosis.** Before accepting a test as flaky, run it ~10x in isolation. A test that fails 1-in-N is a real race — usually in the product, not the test. Fix the cause; never paper over it with a longer timeout, a retry, or a `skip`. The failure signature tells you which it is: a **wrong value** is a real race in the product; a **missing element / timeout** is usually harness saturation. Never widen a budget to accommodate a stress level you inflicted yourself.

## Model economy — delegate grunt work to cheaper models
The main session usually runs on the most capable (most expensive) model. When a chunk of work is token-heavy but mechanically simple, do NOT do it inline — spawn a general-purpose subagent with a cheaper model override and a self-contained brief.

Delegate (worth the cold start):
- Scaffolding many files from an already-decided design → `model: sonnet`
- Bulk mechanical edits: renames, import updates, format/lint fixes across many files → `model: haiku`
- Running test suites/builds and summarizing the output → `model: haiku`
- Generating fixtures, seed data, or boilerplate from a precise spec → `model: sonnet`

Do NOT delegate:
- Anything requiring design or requirements judgment, or core logic — that is main-session work.
- Small tasks: if the brief would take longer to write than the task takes to do, do it yourself.
- Anything that needs conversation context you cannot compress into a short brief. Subagents start cold; a vague brief produces wrong work at any price.

Rules: the brief must name exact files, the exact expected outcome, and the conventions that apply. Verify the subagent's work yourself (run the tests, spot-check the files) — never just trust its report.

## Parallelism — only when value is high and risk is low
Default to sequential work in the main session; it holds the full context and a serial plan is almost always right. Fan work out to parallel subagents (or git worktrees) ONLY when all three hold:
1. **Independent** — the parts share no files and have no ordering dependency, so they can't race or clobber each other.
2. **Worth the multiplier** — parallel agents cost roughly 15× the tokens of one session; the work must be large or repetitive enough that the wall-clock saving justifies that.
3. **Shaped for it** — a read-heavy sweep (audit, multi-file search, multi-source research) or a batch of mechanical edits across modules that don't touch one another.

When parallel agents *write* files, give each its own git worktree so they can't overwrite each other, then merge. Always announce the fan-out and why before spending — and remember a normal feature slice fails test 1, so it stays in the main session.

**A subagent must never mutate the working tree.** Review/audit/research agents are read-only: brief them to inspect other commits with `git show <commit>:<path>` and `git diff <a> <b>` — NEVER `git checkout` / `restore` / `stash` / `reset`, which silently revert the tree and can die mid-run leaving it broken. Commit before launching one, and require it to confirm `git status` is clean when it finishes.

## Context economy
- Read files selectively: targeted sections and greps over whole-file reads; never cat a large file or full log when a filtered view answers the question. Summarize long tool output instead of quoting it.
- If the repo has a Graphify graph (`graph.json`), answer structural questions from it before opening files: `graphify query "<question>"`, `graphify path <A> <B>`, `graphify explain <X>`. Open only the files the graph points to. Keep it fresh — after structural changes run `graphify --update .` (skip if the post-commit hook is installed). Graph extraction for code is local tree-sitter: zero tokens.
- When a feature slice is finished and the conversation has grown long, update **Current state** in the roadmap and suggest the user start a fresh chat for the next slice — a fresh session that reads the roadmap is cheaper than dragging a huge history forward.

## Code standards
- Files stay small and focused — if a file exceeds ~350 lines, split it along responsibility lines.
- Public functions/classes get a doc comment saying WHY and any non-obvious contract; do not comment what the code plainly shows.
- UI is responsive by default (mobile 375px, tablet 768px, desktop 1440px) and keyboard-accessible.
- No dead files, no commented-out code blocks, no secrets in the repo. `.gitignore` covers env files, build output, and IDE artifacts from the first commit.
- Prefer boring, proven technology over the newest option unless there is a written reason (ADR).
- Any `read → await → write-everything` (a wholesale write of state you read before the await) needs an in-flight guard: re-check that the state did not change during the await, and skip or re-derive if it did. Last-write-wins cannot break the tie, so the concurrent local change is silently erased.
- New dependencies at a composition root are REQUIRED, not optional-with-default — a default silently accepts an unwired composition, turning a loud type error into a runtime bug.

## Definition of done for a feature
1. Failing tests were written first and reviewed by the test-guardian agent.
2. Implementation passes the full suite; end-to-end behavior verified with `/verify`.
3. UI changes reviewed by the design-reviewer agent.
4. `/code-review` findings addressed.
5. `/hygiene` pass is clean; decisions documented; README/docs updated if behavior changed.
