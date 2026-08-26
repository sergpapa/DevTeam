---
name: hygiene
description: Repo hygiene pass — file placement and size, dead code, gitignore coverage, secrets, naming, doc freshness. Use before committing a feature (Stage 6 of /feature) or on demand to clean up a repo.
---

# Repo hygiene check

Structural cleanliness review — this complements `/code-review` (which hunts logic bugs); do not duplicate its job. Apply mechanical fixes directly; report judgment calls (anything that deletes non-trivial code or moves public API) to the user instead of acting.

## Checklist
1. **Placement** — every file lives where the project structure (see architect output / ADRs / README) says its kind of file lives. No source files in the repo root that belong in `src/`; no test files mixed into source dirs if the project separates them.
2. **Size & separation** — files over ~350 lines: check whether they hold multiple responsibilities and propose the split. One module = one reason to change.
3. **Dead weight** — unused files, unused exports, unreachable code, commented-out blocks, empty directories, stray scratch files (`test2.js`, `old/`, `copy of ...`). Verify unused with a reference search before flagging.
4. **Gitignore** — `.gitignore` covers: env/secret files (`.env*` with `!.env.example`), dependency dirs, build output, coverage reports, caches, IDE/OS files (`.vscode/` per team convention, `.DS_Store`, `Thumbs.db`), logs. Check nothing already tracked should be ignored (`git ls-files` vs the patterns).
5. **Secrets** — grep tracked files for API keys, tokens, passwords, connection strings. Any hit is a critical finding: report immediately; if already committed, tell the user the key must be rotated (removing the file does not un-leak it).
6. **Naming & consistency** — one casing convention per file type; names say what things are.
7. **Comments & docs** — public functions/classes have doc comments (why + contract, per CLAUDE.md); README's setup/run instructions still match reality; specs and ADRs referenced by the change are up to date.
8. **Dependency sanity** — no dependencies in the manifest that nothing imports; lockfile committed.
9. **Billable automation** — inventory everything in the repo that spends real money when it runs: `.github/workflows/**` and other pipeline config (record each trigger — `push`, `pull_request`, `schedule`, `workflow_dispatch`), deploy hooks, cron/scheduled jobs, auto-merge settings, metered API keys wired into scripts. **Read-only: never run one, and never `gh workflow enable`/`run` it to find out what it does.** Flag hardest: a `schedule:` trigger (it bills with nobody watching) and any workflow committed without the user having approved the cost (say so plainly — it bills on the next push).

## Output
Billable findings (check 9) go FIRST, with the meter and trigger named — they outrank every other finding, and you report them rather than acting on them. Then applied fixes (one line each), then open judgment calls ranked by importance. If everything is clean, say so in one line.
