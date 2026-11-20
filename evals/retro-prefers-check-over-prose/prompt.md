---
description: A recurring mistake that a check can catch must get a test or lint rule first, not a prose rule.
tags: [retro]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

How do we stop this happening a third time? You imported from src/server into a file under src/client twice this week, and review only just caught it before server secrets reached the browser bundle.
