---
name: test-driven-development
description: Use when implementing features or bug fixes test-first, changing executable behavior, or applying red-green-refactor. Guides small behavioral tests, verified failures, minimal implementation, and safe refactoring.
---

# Test-Driven Development

Work in small cycles: one observable behavior, one failing test, enough code to pass, then a small refactor if useful. Prefer tests that catch real regressions and survive changes to internal structure.

## Choose the test boundary

Read the relevant code, existing tests, project test commands, and applicable decisions. Use the project's glossary for names; the default is `docs/domain/glossary.md`. Use `domain-language` when a material domain ambiguity needs resolving, not simply to consume established vocabulary.

Test through an existing public interface at the highest practical boundary that detects the behavior reliably. A function or module's public contract can be the right boundary; every test need not drive the UI. Describe what the chosen boundary covers and any important gap.

Proceed when the task, accepted design, or project conventions already establish that boundary. Ask only when unresolved choices would materially change the contract, architecture, or testing scope. Consult `codebase-design` if available when interface design itself needs discussion.

Read [writing-good-tests.md](writing-good-tests.md) when writing or changing tests or test doubles.

## Red, green, refactor

1. **Red:** write one focused test for a required behavior. For a bug, reproduce the reported failure. Derive expectations from the requirement, a worked example, or an independent fixture.
2. **Verify red:** run that test before implementation. Confirm it fails because the required behavior is missing or wrong. Import errors, broken fixtures, unavailable services, and unrelated failures are setup problems, not a valid red. If it already passes, investigate whether the behavior already exists or the test misses the failure.
3. **Green:** implement only what the behavior requires. Run the test again and confirm it passes. Avoid speculative features and changes outside the task.
4. **Refactor:** while green, improve names, remove duplication, or simplify the affected code without changing behavior. Re-run the relevant tests after each meaningful change. Wider restructuring belongs to a separately scoped review or task.
5. Repeat for the next behavior, including meaningful boundary and failure cases. Do not write an entire imagined test suite before learning from the first cycle.

## Completion and limits

Run the affected tests and the applicable project checks before claiming success, including the project suite when required by its conventions or the risk of the change. Follow the project's runner and test-environment instructions. Report what ran, results, and any blocked checks or existing failures; a passing focused test does not prove the full suite passed.

Use tests for meaningful executable behavior, not to assert source wording, cosmetic edits, or documentation against itself. For a behavior-preserving refactor, existing regression tests may already provide the needed coverage.

If implementation predates the test, preserve existing work and establish useful regression coverage; do not delete user changes to manufacture a test-first history. State that the work was not test-first. When execution is blocked, describe the limitation and do not claim a verified red or green.
