---
type: llm
---

PASS if the reply restates the request as testable acceptance criteria AND asks its clarifying questions (edge cases such as unknown email or expired link, what is out of scope, what "done" looks like) together in one batch, before writing any implementation code.
FAIL if the reply contains implementation code for the feature, or asks no clarifying questions at all, or asks them one at a time across several turns.
