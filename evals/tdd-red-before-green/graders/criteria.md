---
type: llm
---

PASS if the reply presents the tests before the implementation, includes at least one hostile case (empty string, punctuation-only input, multiple consecutive spaces, or leading/trailing whitespace), and says the tests must be run and seen to fail before the implementation is written.
FAIL if the implementation appears before the tests, or every test is a happy-path case, or the reply never mentions running the tests red first.
