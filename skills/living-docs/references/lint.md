# Lint workflow

`lint` checks whether the project knowledge base is still trustworthy and useful. It combines deterministic freshness checks with semantic reasoning across documentation, code, and tests.

Do not modify code or tests during lint unless the user explicitly asks to fix findings. Documentation-only safe fixes may be applied when clearly requested; otherwise report first.

## Phase 1 — deterministic freshness

Run:

```bash
bash <skill-root>/scripts/freshness.sh --wiki-root docs --json
```

Treat a source-hash mismatch as “needs review”, not proof that the page is wrong.

## Phase 2 — semantic checks

Check the relevant knowledge graph for:

### 1. Contradictions

Look for conflicts among:

- `intent` vs `observed`;
- docs vs tests;
- docs vs current implementation;
- decision records vs current architecture;
- two documentation pages describing the same concept differently.

Do not automatically choose a winner when authority is unclear.

### 2. Intent coverage

For important `intent` claims, identify whether the repository contains observable implementation and/or tests that support them.

Classify findings such as:

- intent appears implemented and tested;
- intent appears implemented but untested;
- intent appears contradicted by implementation;
- intent has no identifiable implementation evidence;
- evidence is ambiguous.

### 3. Test gaps

When an intent is precise and testable but no test appears to encode it, report a **candidate unit/integration test**.

Example:

```text
Intent: account locks after 5 failed attempts.
Observed: implementation uses threshold 5.
Tests: no assertion covers the threshold.
Candidate test: after the fifth failed login, assert account is locked; after four, assert it is not.
```

Do not manufacture requirements just to create tests.

### 4. Stale meaning

A page can be semantically stale even if its cited file hashes have not changed, for example when behavior moved to another module. Use code search and recent diffs when a claim looks suspicious.

### 5. Duplicates and orphans

Report duplicated concepts, contradictory parallel explanations, dead links, and important pages that are difficult to discover from `docs/README.md`.

### 6. Unresolved uncertainty

Report meaningful `TODO-VERIFY` and `CONTRADICTION` markers that remain unresolved.

## Output

Prefer a compact report grouped as:

- Freshness
- Contradictions
- Intent vs observed
- Test gaps
- Navigation / duplicates
- Uncertainty

For each finding include the affected doc, evidence, why it matters, and the safest next action.

Do not create a persistent lint log by default. Git and the current review/CI output are sufficient. Persist a report only if the user asks.
