---
name: adopt
description: Onboard an existing codebase into the dev-team pipeline — survey the code, reconstruct docs/brief.md, retroactive ADRs, and docs/roadmap.md with an honest baseline, so /project and /feature can take it from there. Use when pointed at a project that has code but none of the docs/ state files, whether the goal is new features, cleanup, or a refactor.
---

# Adopt an existing project

`/project` and `/feature` resume from repo state files (`docs/brief.md`, `docs/adr/`, `docs/roadmap.md`). An existing codebase has code but no state files — this skill reconstructs them from evidence. Adoption MAPS the project; it does not fix it. Every problem found becomes a roadmap item, not an on-the-spot edit.

If `docs/roadmap.md` already exists, this is not an adoption — run `/project` and resume.

## Stage 1 — Survey the code (evidence before opinions)

If Graphify is installed (`graphify --version` succeeds) and the codebase is non-trivial (~50+ source files), build the knowledge graph first: `graphify .` — code extraction is local tree-sitter, zero tokens. Then survey from `GRAPH_REPORT.md` and `graphify query`/`explain` instead of walking files by hand, opening only what the graph flags; the graph also supplies structure evidence for Stage 3's retroactive ADRs. Without Graphify (or on a small repo), read selectively — manifests, README, entry points, config, CI, directory shape; grep instead of full-file reads. Establish:
- **What it does**: user-facing surface (routes, screens, commands), the apparent core workflow.
- **Stack & structure**: languages, frameworks, DB, services, and the big structural decisions someone already made.
- **How to run it**: dev command, env vars/secrets it expects. Actually run it if possible.
- **Test reality**: run the suite. Record the honest baseline — runner present? passes? coverage of the core workflow? A suite that passes trivially counts as "no tests" for planning purposes.
- **Health flags**: build errors, dead directories, secrets in the repo, missing `.gitignore`, huge files. Note them; do NOT fix them yet.

## Stage 2 — Interview the owner (one batch)

Ask only what the code cannot answer, in ONE batch:
- Is this deployed/used today? By whom? What must not break?
- What is the goal of adoption — new features, cleanup/refactor, or rescue? What's the next thing they want done?
- Known pain points, half-finished work, and any "don't touch that" areas — and why.
- Anything surprising from Stage 1: "the code does X — intentional?"

## Stage 3 — Reconstruct the state files

- **`docs/brief.md`** — the `/discover` format, written retroactively from code + interview. Mark it: `> Reconstructed from existing code on <date> — describes what IS, plus the owner's stated direction.` Skip the landscape research unless the owner is questioning direction.
- **`docs/adr/`** — one retroactive ADR per standing decision a future reader would question (stack, data model, auth approach, hosting). Status: `Accepted (retroactive)`. Record the apparent rationale; where you're guessing, say so. Don't paper the walls — 3–6 ADRs is typical.
- **`docs/roadmap.md`** — the `/project` format. **Current state** is the Stage 1 baseline, stated honestly ("tests: 12 pass / 3 fail", "no CI", "core workflow works in manual run"). Then:
  - **Milestone 0 — Stabilize** (only if needed): whatever blocks the TDD pipeline, as slices — stand up test runner, pin down the core workflow with characterization tests, fix the build, `/hygiene` findings, secrets out of the repo. If the owner wants a refactor, the characterization tests are non-negotiable Milestone 0 items: they pin current behavior before anything moves.
  - **Milestone 1+**: the owner's actual goals, sliced per the roadmap rules (one `/feature` run each, shippable after each, riskiest first).

## Stage 4 — Handoff

Present the adoption report: what the project is, baseline health, the proposed roadmap, and any Stage-1 findings that need a decision (e.g. leaked secret → rotate). Get a nod on milestone order, then commit the `docs/` files as `Adopt project into dev-team pipeline`. From here the project is a normal `/project` resume; a fresh chat is the cheapest way to start Milestone 0.
