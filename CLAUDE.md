# Engineering Standards (apply to every session in this workspace)

## Session start — continuity across chats
Project state lives in files, never in conversation memory. If `docs/roadmap.md` exists, read its **Current state** section (plus the in-progress spec) before doing anything, and resume from there. Before ending a working session on a project, update **Current state** with where things stand and the next action.

## Workflow
- New product/system idea → run `/project` (discovery → architecture → scaffold → roadmap → build loop).
- Single feature on an existing base → run `/feature <description>` (the full TDD pipeline).
- Small fixes (typos, one-line bugs, config tweaks) do NOT need any pipeline — just fix, test, done.
- Architectural decisions (tech stack, data model, framework choice) must be recorded with `/adr`.

## Testing rules (non-negotiable)
- Tests are written from the spec BEFORE implementation, and must be seen to fail for the right reason before any implementation code is written.
- NEVER modify a test to make it pass. If a test looks wrong, stop and tell the user — do not silently change or delete it.
- Test behavior (inputs → observable outputs), not implementation details. Minimal mocking: mock external services, not your own modules.
- A test suite that passes trivially proves nothing. If you cannot articulate what bug a test would catch, the test is not done.

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

## Definition of done for a feature
1. Failing tests were written first and reviewed by the test-guardian agent.
2. Implementation passes the full suite; end-to-end behavior verified with `/verify`.
3. UI changes reviewed by the design-reviewer agent.
4. `/code-review` findings addressed.
5. `/hygiene` pass is clean; decisions documented; README/docs updated if behavior changed.
