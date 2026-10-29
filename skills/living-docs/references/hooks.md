# Optional Git hook and CI integration

Hooks are triggers, not the documentation engine. Keep them thin and delegate reasoning to the agent plus this skill.

## Cheap deterministic check

Use the included checker first:

```bash
bash /path/to/living-docs/scripts/freshness.sh --wiki-root docs
```

This is suitable for CI or pre-push because it does not call an LLM.

## Kilo fallback example

A simple hook can invoke Kilo only when existing code-grounded pages are stale:

```bash
#!/usr/bin/env bash
set -euo pipefail

SKILL_ROOT="/path/to/living-docs"
STALE=$(bash "$SKILL_ROOT/scripts/freshness.sh" --wiki-root docs --stale-only || true)

if [ -n "$STALE" ]; then
  kilo -p "Use the living-docs skill in sync mode. Review these potentially stale documentation pages against the current repository and update only what is necessary:\n$STALE"
fi
```

## Stricter fallback for new behavior

Freshness can only detect pages that already cite changed files. New source files or previously undocumented behavior may have no page to invalidate.

A stricter hook may also invoke an agent when a commit changes in-scope code but does not change `docs/`; the agent should be allowed to return a no-op.

Keep this optional because it can create unnecessary LLM calls for refactors, formatting, and implementation-only changes.

## Recommended placement

- `pre-push` or CI: deterministic freshness/lint gate.
- `post-commit`: optional asynchronous sync fallback for manual changes.
- same coding-agent conversation: preferred path for actual documentation updates.

Avoid blocking `pre-commit` on an LLM call; network/auth/model latency makes commits fragile.
