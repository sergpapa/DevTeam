---
name: tdd
description: Rules for writing tests before implementation — how to write tests that catch real bugs instead of tests that merely pass. Use whenever writing or modifying tests, standalone or as Stage 2 of /feature.
---

# TDD rules

The point of writing tests first is that the tests encode the SPEC, uncontaminated by knowledge of the implementation. A test you couldn't fail is not a test.

## The red rule
Before writing any implementation, run the new tests and watch them fail — on an assertion or a missing symbol, not on a setup error. A test that passes before the implementation exists is broken; fix it before proceeding. Once tests are approved (test-guardian PRE pass), commit them; they are now the contract.

## The immutability rule
During implementation, tests are read-only. If a test seems wrong, stop and surface it to the user with your reasoning — never adjust, loosen, skip, or delete it to get to green. (Refactoring tests is allowed later, as its own reviewed step, never mixed into an implementation change.)

## Writing tests that catch bugs
- **Test behavior, not implementation**: assert on inputs → observable outputs/effects. Don't assert private state, call order, or call counts when a behavioral assertion exists — those tests break on refactors and pass on bugs.
- **Derive cases from the spec, then add hostile ones**: for each acceptance criterion, the happy path, boundaries (empty, zero, one, max, unicode, very long), invalid input, and error paths for anything that does I/O.
- **One behavior per test**, named for the behavior: `rejects_expired_tokens`, not `test_auth_2`.
- **Arrange–Act–Assert**, with real objects wherever practical. Mock only true externals (network, clock, payment providers, third-party APIs) — never the unit under test, and avoid mocking your own modules; use in-memory fakes or the real thing.
- **The tautology check**: for each test ask "what incorrect implementation would this catch?" If the answer is none — it asserts a mock's own script, compares a value to itself, or pins a magic constant that the implementation will copy — rewrite it.
- **Prefer few strong assertions** on outcomes over many shallow ones on structure.

## Where TDD applies — and where it doesn't
TDD fits logic, APIs, data transformations, and state machines. It fits exploratory UI badly: pixel-level look-and-feel is better iterated visually and judged by the design-reviewer agent. For UI features, TDD the behavior (rendering logic, state, form validation, routing) and leave aesthetics to visual review — do not write brittle snapshot tests as a substitute for design judgment.
