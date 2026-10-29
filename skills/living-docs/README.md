# Living Docs skill — v0.1

A lightweight Agent Skill for maintaining human- and AI-edited project documentation in `docs/`.

## Design goals

- plain Markdown in the repository;
- no separate generated-docs tree;
- no database, registry, daemon, or mandatory hook;
- prefer same-session updates when a coding agent changes behavior;
- fallback sync for manual/external changes;
- distinguish `intent`, `observed`, and `decision` knowledge;
- deterministic freshness via source blob hashes;
- semantic lint across docs, code, and tests;
- use lint to surface contradictions and candidate test gaps;
- Git remains the history and audit trail.

## Install

Personal/global installation for Agent Skills-compatible tools:

```bash
mkdir -p ~/.agents/skills
cp -R living-docs-skill ~/.agents/skills/living-docs
```

Or commit it with a repository, for example:

```text
.agents/skills/living-docs/
```

Exact skill discovery paths vary by host. The skill itself is host-neutral.

## Suggested repository instruction

Add this to `AGENTS.md` (or the equivalent host instruction file):

```text
When docs/README.md exists, consult the smallest relevant Living Docs pages before changing project behavior. After code changes, use the living-docs skill to update affected docs in the same task. Treat current conversation statements as evidence for explicit intent/decisions, but never infer intent solely from code.
```

## Explicit usage

| Mode | Purpose |
| --- | --- |
| `init` | Create or normalize a minimal `docs/` knowledge base for a repository. |
| `sync` | Reconcile docs with code changes made manually, by another agent, or outside the current conversation. |
| `ingest` | Capture durable intent, decisions, constraints, or explanations from a conversation, PR, issue, meeting note, or other project artifact. |
| `lint` | Check freshness and semantic consistency across docs, code, tests, intent, and decisions. |

Natural-language examples:

```text
Use the living-docs skill in init mode.
Use the living-docs skill in sync mode for the current branch diff.
Use the living-docs skill to ingest the decisions from this conversation.
Use the living-docs skill to ingest this completed plan, then delete the plan.
Use the living-docs skill in lint mode and identify test gaps.
```

## Freshness checker

```bash
bash scripts/freshness.sh --wiki-root docs
bash scripts/freshness.sh --wiki-root docs --stale-only
bash scripts/freshness.sh --wiki-root docs --json
```

The checker only treats pages containing `knowledge: observed` as source-grounded pages that should normally have `sources[]`. New `sources` entries are scalar strings (`path | git blob hash | optional lines`) so they remain readable in rendered frontmatter; the older path/sha mapping form is still accepted.

## v0.1 non-goals

- dependency graph / AST impact propagation;
- hosted documentation portal;
- vector search / RAG;
- automatic schema migrations;
- formal requirement registry;
- automatic unit-test generation without user request;
- mandatory post-commit updates.

Those can be added only if real usage shows they are needed.
