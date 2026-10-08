---
type: llm
---

PASS if the reply sets out to reproduce or isolate the root cause first (for example: two callers racing, a missing idempotency key, no unique constraint on the charge), and names a regression test that would guard the fix, before or instead of handing over a patch.
FAIL if the reply hands over a code change as "the fix" without any reproduction step, root-cause isolation, or regression test.
