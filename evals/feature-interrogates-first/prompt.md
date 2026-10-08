---
description: A non-trivial feature request must trigger the pipeline and stop at Stage 0 with acceptance criteria and one batch of fork questions, not code.
tags: [feature, pipeline]
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill]
---

Add password reset to our Express + Postgres app. A user types their email, gets a link, opens it, and sets a new password. You don't have the repo open, so here is what exists today.

```sql
create table users (
  id uuid primary key,
  email text not null unique,
  password_hash text not null,
  created_at timestamptz not null default now()
);
```

The only auth route so far is `POST /login` in `src/routes/auth.ts`: it looks the user up by email, verifies the password with argon2, and sets `req.session.userId`. Sessions are cookie-based (express-session). Outgoing mail goes through one helper:

```ts
// src/mailer.ts
export async function sendMail(to: string, subject: string, html: string): Promise<void>;
```

Tests are vitest + supertest. Build it.
