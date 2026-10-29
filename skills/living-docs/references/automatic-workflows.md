# Automatic workflows

## Preferred path: same-session maintenance

When an agent changes the code inside an active conversation, update Living Docs before finishing the same task.

This path is preferred because the current conversation may contain evidence that is unavailable to a later sync agent:

- explicit product intent;
- reasons for a design choice;
- alternatives that were considered and rejected;
- user corrections and clarifications;
- the boundary between deliberate behavior and incidental implementation detail.

Use that context as evidence for `intent` and `decision`, while still verifying implementation facts against the repository.

## Fallback path: external/manual changes

When code changes without an in-session docs update, a Git hook, CI job, or manual command may:

1. run deterministic freshness checking;
2. invoke an agent only when review is needed;
3. ask that agent to use this skill in `sync` mode.

A later sync agent may safely update `observed` knowledge from code, but must not invent missing intent/rationale.

## Avoid duplicate work

If the in-session agent updated docs and refreshed source hashes, the later freshness check should normally be clean and the hook/CI can no-op.

## Recommended coding-agent instruction

A repository can add a small instruction to `AGENTS.md` or an equivalent host-specific file:

```text
When docs/README.md exists, consult the smallest relevant Living Docs pages before changing project behavior. After code changes, use the living-docs skill to update affected docs in the same task. Treat current conversation statements as evidence for explicit intent/decisions, but never infer intent solely from code.
```
