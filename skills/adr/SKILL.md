---
name: adr
description: Record an architecture/technology decision as an Architecture Decision Record in docs/adr/. Use whenever a decision is made about stack, structure, data model, dependencies, or any choice a future reader would ask "why did they do it this way?" about.
---

# Architecture Decision Records

Create `docs/adr/NNNN-short-kebab-title.md` (NNNN = next number, zero-padded, starting 0001). One decision per file. Keep it under a page — an ADR nobody reads is worse than none.

```markdown
# NNNN. <Decision title as a statement, e.g. "Use PostgreSQL for primary storage">

Date: <YYYY-MM-DD>
Status: Accepted | Superseded by NNNN | Deprecated

## Context
What problem forced a decision, and the constraints that shaped it (2–5 sentences).

## Decision
What we chose, stated plainly.

## Alternatives considered
Each rejected option with the one real reason it lost.

## Consequences
What this makes easier, what it makes harder, and what would trigger revisiting it.
```

Rules:
- Never rewrite history: a changed decision gets a NEW ADR that supersedes the old one; update the old ADR's Status line only.
- Write the honest reason ("team knows it", "cheapest managed option"), not a retrofitted technical justification.
- If `docs/adr/` doesn't exist yet, create it with this skill's template as `docs/adr/0000-template.md` alongside the first real ADR.
