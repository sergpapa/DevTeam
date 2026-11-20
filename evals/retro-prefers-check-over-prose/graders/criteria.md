---
type: llm
---

PASS if the first fix proposed for the src/server import is an automated check that fails when the import comes back (a lint rule such as an import-restriction rule, a test, or a hook), the reply names the file it would go in, and it asks for approval before applying anything.
FAIL if the main fix is a prose rule (a CLAUDE.md line, a skill note, or a promise to be careful), or if a prose rule is proposed without saying why an automated check cannot hold it, or if changes are applied without asking.
