---
description: An intermittent bug with no obvious cause must trigger systematic debugging (reproduce, isolate, regression test), not a guessed patch.
tags: [debug]
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill]
---

Our nightly job sometimes double-charges a customer. The charge function is called from a cron handler and also from a webhook retry handler. It happens about once a week and we can't tell why. Fix it.
