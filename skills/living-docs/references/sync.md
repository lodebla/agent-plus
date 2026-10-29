# Sync workflow

Use `sync` to reconcile documentation with code changes made manually, by another agent, or outside the current conversational context.

## Inputs

Prefer, in order:

1. a user-specified diff/base range;
2. changed files reported by the freshness checker;
3. staged or working-tree diff;
4. a recent commit range or merge-base when the user asks to reconcile a branch.

## Steps

1. Read `docs/README.md` and only the relevant linked pages.
2. Inspect the code diff and identify changed behavior, interfaces, configuration, schemas, tests, or architecture.
3. Find pages whose readable `sources[]` entries reference changed files. The freshness checker also accepts legacy mapping entries with `path` and `sha` keys.
4. Also consider whether new code introduces a concept that is not referenced by any existing page. Do not rely only on `sources[]` for additions.
5. Re-read current source files at HEAD/working tree before updating prose. The diff is a change set, not the full truth.
6. Update `observed` knowledge to match current implementation.
7. Do not create or change `intent` or `decision` merely because code changed. If code appears to violate or redefine them, surface the mismatch.
8. If prose remains correct but a cited source changed, refresh the source hash after re-verification.
9. Update `verified_against_commit` to current `HEAD` when the page has been meaningfully re-verified.
10. Update `docs/README.md` only when pages are added, removed, renamed, or navigation materially changes.
11. A no-op is valid when the code change does not alter durable documentation.
12. Update `lastUpdated` when durable page content changes; refreshing only source hashes or `verified_against_commit` does not change the editorial date.

## Conflict handling

When code conflicts with an `intent` claim:

- preserve the intent;
- document current observed behavior separately;
- add a concise `CONTRADICTION` marker if the mismatch matters;
- recommend a test when the intent is testable but not currently encoded.

When code conflicts with an old `observed` claim, update the observed claim unless evidence suggests the code itself is unintended.
