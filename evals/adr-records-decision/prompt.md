---
description: A stated architecture decision must be recorded as an ADR with context, decision, alternatives, and consequences.
tags: [adr]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

We decided to use Postgres instead of MongoDB for the new inventory service, because we need transactions that span orders and stock levels. Record this decision for the team.
