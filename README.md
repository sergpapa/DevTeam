# DevTeam — an agent team for Claude Code

A lean, credit-efficient development pipeline: **3 agents + 4 skills**, orchestrated by the main Claude Code session.

## Design philosophy

The main session is the orchestrator AND the implementer (backend + frontend). It has the full conversation context; subagents start cold and must re-read everything, which costs credits and loses information. So:

- **Agents** (separate context windows) exist only where isolation is a *feature* — a reviewer that hasn't seen the implementer's reasoning can't be biased by it.
- **Skills** (process checklists loaded into the main session) handle everything that is knowledge rather than a fresh pair of eyes. They cost almost nothing.
- **Built-ins are reused**, not duplicated: `/code-review` (logic-bug review), `/verify` (end-to-end verification), `/security-review`, and plan mode already cover the "code reviewer", "QA", and part of the "architect" roles.

Sources for this shape: Anthropic's [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) (use the simplest structure that works), [multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) (multi-agent ≈ 15× token cost — only worth it when isolation or parallel reading pays for itself), and [Claude Code best practices](https://www.anthropic.com/engineering/claude-code-best-practices) (TDD workflow with tests committed before implementation).

## The team

| Member | Kind | Model | Job | When it runs |
|---|---|---|---|---|
| main session | — | your choice | Orchestrates, implements front + back, writes tests | always |
| `architect` | agent | inherit | Requirements → stack, structure, data model, contracts, ADR drafts | project kickoff / structural features |
| `test-guardian` | agent | sonnet | Audits tests: fail-first, spec coverage, tautologies (PRE); weakened tests, gamed implementations (POST) | Stage 2 & Stage 5 of `/feature` |
| `design-reviewer` | agent | sonnet | Visual consistency, UX heuristics, responsiveness, accessibility — from screenshots when possible | after UI changes |
| `/project` | skill | — | System-level pipeline: discovery → architecture → walking skeleton → roadmap → build loop; resumes from `docs/roadmap.md` in any new chat | new app/system, or resuming one |
| `/discover` | skill | — | Requirements discovery: interrogate the idea, research the landscape, write `docs/brief.md` | project conception / fuzzy scope |
| `/feature` | skill | — | The pipeline: scope → architecture → red → green → verify → review → hygiene | any non-trivial feature |
| `/tdd` | skill | — | How to write tests that catch bugs, not tests that pass | whenever writing tests |
| `/adr` | skill | — | Record decisions in `docs/adr/` | any stack/structure decision |
| `/hygiene` | skill | — | File placement/size, dead code, gitignore, secrets, doc freshness | before committing |

Plus `CLAUDE.md` — the standards every session loads automatically (testing rules, code standards, definition of done).

## Usage

```
/project I want an app that tracks my climbing training and suggests sessions
```
takes an idea from conception to v1 across as many chats as it needs.
```
/feature Users can reset their password via an emailed link
```
runs one slice's pipeline. For questions of structure only: "launch the architect agent to design X". For a cleanup pass: `/hygiene`.

## Continuity across chats (why there is no top-level orchestrator agent)

Nothing conversational survives a chat change — not the main session's context and not a subagent's, so an "orchestrator agent" would lose its memory exactly when you need it. Durable state therefore lives in repo files, which every new session reads for free:

- `docs/brief.md` — what we're building and why (from `/discover`)
- `docs/adr/` — every decision and its reasoning (from `/adr`)
- `docs/roadmap.md` — milestones, checked-off slices, and a **Current state** section updated at the end of every session (from `/project`)
- `docs/specs/` — acceptance criteria per feature (from `/feature`)

CLAUDE.md instructs each new session to read **Current state** before doing anything, so "changing chats" costs one file read, not a re-explanation. (`claude --resume` can also reopen a previous conversation, but treat that as a convenience — the files are the source of truth.)

## Roles deliberately NOT built as agents

- **Orchestrator** — the main session with the `/feature` skill *is* the orchestrator. A subagent can't orchestrate: it can't see your conversation or steer the main loop.
- **Backend / frontend engineers** — one implementer with full context beats two specialists split across the API boundary, which is where integration bugs live.
- **QA tester** — covered by test-guardian + `/verify` + `/code-review`.
- **DB/cloud & deployment experts** — architecture-time concerns (the architect covers them) until you have a real deployment target. When you do, add a `deploy` skill encoding *your* pipeline (provider, environments, rollback steps) — a generic deployment agent guessing at your infra would waste credits. Same trigger for a dedicated DB agent: complex migrations on a live database.
- **Designer (generative)** — the design-reviewer *judges*; generating design is best done in the main session (iterating visually with screenshots), optionally seeded with inspiration examples passed to the reviewer as the reference design language.

## Credit-efficiency rules of thumb

- Skip pipeline stages that don't apply; `/feature` says to announce skips.
- Small fixes bypass the pipeline entirely (CLAUDE.md says so).
- Reviewer agents run on Sonnet; only the architect inherits your (likely bigger) main model, and it runs rarely.
- Launch Stage-5 reviewers in parallel — one round-trip instead of three.
- Grunt work gets offloaded to cheap models: CLAUDE.md instructs the main session to spawn Haiku/Sonnet subagents for token-heavy mechanical work (scaffolding, bulk edits, running test suites) instead of burning top-model tokens on it. Judgment work never gets delegated — a cold subagent can't be trusted with decisions.

### Session habits (the biggest levers — these are yours, not the model's)
1. **One chat per feature slice, not marathon sessions.** Every message re-sends the whole conversation; a 200-message chat makes each new turn expensive. The roadmap's Current state section exists precisely so fresh chats are cheap — use them.
2. **Work in bursts.** The prompt cache lives ~5 minutes; replies inside that window reprocess history at ~10% cost, while a reply after a long idle gap pays full price for the entire history. Batch your thoughts into fewer, fuller messages rather than a drip of one-liners.
3. **Match the model to the session.** Routine implementation sessions run fine on Sonnet (near-Opus at coding, much cheaper); save the top model for architecture, gnarly debugging, and design sessions. If you adopt this, pin the architect agent to `model: opus` so design quality never depends on the session model.
4. **Point at files, don't paste them.** Pasting a big file or log into chat puts it in the permanent (re-billed every turn) history; naming the path lets Claude read just the relevant part once.
5. **Keep the tool surface lean.** Every MCP server's tool definitions load into every session's context whether used or not — only keep servers you actually use. Same for CLAUDE.md: it's loaded every session, so it must stay tight.
6. **Right-size the reviews.** `/code-review` at medium effort for routine slices; the ultra (cloud, multi-agent) tier only for release-critical branches. Run `/fewer-permission-prompts` once to cut approval round-trips.

## Installation

This repo is a Claude Code **plugin** and its own **marketplace**. To install it, run inside Claude Code:

```
/plugin marketplace add <github-user>/DevTeam
/plugin install devteam@devteam
```

That makes the team available in **all** your projects. Skills installed via plugin are namespaced: `/devteam:project`, `/devteam:feature`, `/devteam:adr`, etc. (`/help` lists them). The agents keep their names.

When the repo gets updated, pull the new version with `/plugin marketplace update devteam`.

**The standards file is a separate step.** Plugins can't ship a `CLAUDE.md`, so copy this repo's [CLAUDE.md](CLAUDE.md) into `~/.claude/CLAUDE.md` (global — applies to every project) or merge it into a project's own `CLAUDE.md`. If you use the plugin install, the skill names it references are the namespaced ones (`/devteam:feature` instead of `/feature`).

### Alternative: standalone global install (no namespacing, this machine only)

Copy `agents/*` to `~/.claude/agents/` and `skills/*` to `~/.claude/skills/`, and merge `CLAUDE.md` into `~/.claude/CLAUDE.md`. Skills keep their short names (`/feature`), but you won't get marketplace updates — re-copy after changes. Note that same-named files in `~/.claude/` override the plugin versions, so pick one method, not both.

### Local development

Test changes to the team without reinstalling:

```
claude --plugin-dir ./DevTeam
```

then `/reload-plugins` after edits.
