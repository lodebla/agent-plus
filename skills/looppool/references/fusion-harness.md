# Experimental Fusion Harness bridge

Select `review_backend="fh"` only when the user explicitly requests Fusion Harness, and set `multi_review=true`. Presence of an extension does not select it automatically.

This is a bridge contract, not a claim of shipped or tested integration. The configured `fh_bridge_tool` (default `fh_debate`) must exist in the host and accept the current invocation contract in `orchestrator.py`. Inspect the installed extension API before the writer runs; a missing/incompatible bridge is a setup stop, never a silent native fallback.

FH supplies exactly one independent review round—no peer debate:

```python
response = await bridge({"prompt": material, "rounds": 1})
```

The response must be `{"history": [{"round": 0, "positions": {"reviewer-name": review}}]}` with each review conforming to the active `REVIEW_SCHEMA`. Reviewers must be independent, read-only, and evidence-based. The adapter then invokes a fresh final judge through the configured `strong_reviewer_agent` and its normal OMP model/fallback mapping; only that strong-judge stage may perform the bounded native evidence follow-up.

Bridge lookup proves only callable availability, not schema compatibility. Snapshot mutation checks and native success rules still apply: failed blocking checks cannot become `DONE`, unresolved evidence remains unresolved, and all concrete blockers are returned together. Record the actual extension/version and observed result before claiming compatibility. Python mocks, pressure scenarios, and unrelated platform runs are not FH integration evidence.
