---
name: living-docs
description: Maintain a lightweight, code-grounded project knowledge base in docs/. Use it to initialize docs, synchronize docs with code changes, ingest durable intent/decisions from conversation or project artifacts, and lint consistency across docs, code, and tests.
argument-hint: init | sync | ingest | lint
---

# Living Docs

Maintain `docs/` as a living knowledge base shared by humans and coding agents.

The goal is not to generate a parallel documentation system. Humans and AI edit the same Markdown files. Git is the history. The skill adds only lightweight conventions that make the docs easier to keep current and safer for agents to trust.

## Core model

Every durable claim belongs to one or more knowledge classes:

- `intent` — what the project is supposed to do: explicit requirements, constraints, product rules, desired behavior.
- `observed` — what the current code, tests, schemas, configuration, or runtime-facing artifacts actually implement.
- `decision` — why a non-obvious design or architectural choice was made, including rejected alternatives and consequences.

Never infer `intent` or `decision` solely from implementation. Code can establish `observed`; explicit user statements, reviewed project documents, issues/PRs, or existing decisions can establish `intent` or `decision`.

## Trust rules

1. For implementation facts, executable code, tests, schemas, and configuration outrank prose documentation.
2. For rationale and product intent, explicit human/project evidence outranks inference from code.
3. When `intent` and `observed` disagree, do not silently choose one. Surface the mismatch as a possible bug, stale documentation, incomplete implementation, or changed requirement.
4. Prefer uncertainty over fabrication. Use `TODO-VERIFY` when evidence is insufficient.
5. Humans may edit any file under `docs/`. Never treat AI-authored text as protected or automatically regenerate over a human correction without evidence.

Read [Trust and page metadata](references/trust-and-metadata.md) when creating or materially changing documentation.

## Render-friendly source references

Store each source as a YAML string so Markdown renderers show readable text instead of `[object Object]`:

```yaml
sources:
  - "src/Auth/SessionService.php | 0123456789abcdef0123456789abcdef01234567 | lines 20-88"
```

Use the full `git hash-object` value in real pages. The freshness checker also accepts the earlier `path`/`sha` mapping format, but new or edited pages should use scalar strings. See [Trust and page metadata](references/trust-and-metadata.md) for the syntax.

## Editorial update dates

New pages and pages with materially changed documentation content must set the native VitePress frontmatter field `lastUpdated` to the current date as an unquoted YAML date (`YYYY-MM-DD`). Keep it distinct from `verified_against_commit`: update `lastUpdated` when the page's durable content changes, but not when only source hashes or the verified code commit change. Tracked legacy pages without this field use VitePress' Git timestamp; an untracked page has no Git fallback, so give it an explicit date when creating or editing it.

## Automatic behavior during normal coding work

When `docs/README.md` exists and the task modifies or reasons about project behavior:

### Before code work

1. Read `docs/README.md`.
2. Follow the smallest relevant links only; do not load the whole documentation tree.
3. Use relevant `intent` and `decision` knowledge as constraints on the implementation.
4. Verify `observed` claims against code/tests when correctness depends on them.

### After agent-made code changes

1. Inspect the code diff and the docs consulted for the task.
2. Run the `sync` workflow logically before finishing.
3. Use the current conversation as additional evidence for explicit `intent` and `decision` knowledge.
4. Update only docs whose durable meaning changed. A no-op is valid.
5. Update `lastUpdated` when durable page content changes; do not change it for source-hash or `verified_against_commit` refreshes alone.
6. Refresh source hashes for any `observed` page that was verified against changed source files, even when prose did not need to change.
7. Mention documentation changes in the final response.

This in-session update path is preferred over a later hook because the current agent has the richest context about intent and rationale.

Read [Automatic workflows](references/automatic-workflows.md) for details.

## Workflow selection

Honor an explicitly selected mode. Otherwise choose the primary workflow from the requested outcome and available sources; the user does not need to name a mode. Ask for clarification only when the ambiguity materially changes the work.

| Mode | Purpose |
| --- | --- |
| `init` | Create or normalize a minimal `docs/` knowledge base for a repository. |
| `sync` | Reconcile docs with code changes made manually, by another agent, or outside the current conversation. |
| `ingest` | Capture durable intent, decisions, constraints, or explanations from a conversation, PR, issue, meeting note, or other project artifact. |
| `lint` | Check freshness and semantic consistency across docs, code, tests, intent, and decisions. |

Resolve common ambiguities as follows:

- **"Update the docs"**: choose `sync` when code changes or current implementation are the source; choose `ingest` when a conversation, plan, or other project artifact supplies knowledge to preserve.
- **Completed plan**: choose `ingest` to preserve its durable knowledge. Verifying the final implementation is part of ingest, not a reason to run a separate full sync workflow. Follow the ingest reference for source retention or requested deletion.
- **"Check the docs"**: choose `lint`. Report findings by default; when the user also asks for corrections, apply documentation fixes supported by evidence. This does not authorize implementation changes.
- **Missing documentation**: choose `init` when the requested outcome requires establishing a knowledge base. A missing page alone does not require initialization; add it within the relevant workflow when useful.
- **Mixed request**: choose the primary workflow by the main requested outcome and incorporate only the necessary steps from other workflows. Do not automatically chain `init`, `sync`, `ingest`, and `lint`.

During normal coding work, keep the automatic maintenance behavior above: `sync` is primary after code changes, and explicit intent or decisions from the conversation enrich the same update without a second full ingest pass.

Load only the reference for the selected workflow. Consult another workflow reference only when a necessary secondary step requires its guidance:

- `init` → [references/init.md](references/init.md)
- `sync` → [references/sync.md](references/sync.md)
- `ingest` → [references/ingest.md](references/ingest.md)
- `lint` → [references/lint.md](references/lint.md)

## Domain vocabulary

Consult the project's existing glossary for the concepts involved in the task; the default location is `docs/domain/glossary.md`. Use preferred terms and recognize accepted synonyms, respecting any context in square brackets. Do not normalize away valid synonyms or create a glossary merely because this skill runs.

For a domain ambiguity that changes the requested behavior, or when definitions and synonym equivalences need to be established or revised, use [domain-language](../domain-language/SKILL.md). It owns terminology clarification and glossary updates; continue the selected Living Docs workflow for the surrounding documentation without duplicating that work. In report-only `lint`, report terminology findings without editing the glossary.

## Repository layout

Prefer a simple tree. Create only sections that are useful for the project:

```text
docs/
  README.md
  architecture/
  domain/
  features/
  flows/
  decisions/
  guides/
```

Do not create empty directory trees merely to satisfy a schema.

`docs/README.md` is the routing index for humans and agents. Keep it compact and link-oriented.

Put how-to and operational procedures together under `docs/guides/`. Do not create a separate `docs/runbooks/` category or generic baseline runbooks during `init`; add a guide only when a concrete project task or verified workflow needs it.

## What this skill deliberately does not require

- no database
- no registry file
- no schema-version machinery
- no separate AI-generated docs tree
- no audit log duplicating Git history
- no daemon or hosted service
- no mandatory Git hook

Git hooks, CI, and agent CLIs are optional triggers around this skill, not part of its core logic. See [references/hooks.md](references/hooks.md).

## Editorial pass

Aim for the shortest text that remains complete and clear, without a word limit. In `init`, `sync`, and `ingest`, revise the documentation passages created or changed by the task before finishing. In `lint`, report editorial problems in the reviewed scope; apply corrections only when requested.

- Lead with the main point; use direct sentences and consistent terms.
- Remove repetition, filler, and explanations superseded by verified evidence.
- Replace duplicated explanations with links to the canonical page, retaining enough local context to understand the page.
- Preserve necessary constraints, exceptions, rationale, source references, and unresolved uncertainty. Shortening must not change the meaning or erase useful distinctions.

Keep this pass within the task's documentation scope. Rewrite whole pages only when requested or needed to make the affected content coherent. Leave adequate text unchanged; do not invoke a separate cleanup skill or expand the review to the entire knowledge base.

## Finalization checklist

Before finishing any workflow:

1. Keep changes minimal and local to the affected concepts.
2. Preserve human-authored intent and rationale unless explicit evidence supersedes them.
3. Update `docs/README.md` only when navigation actually changes.
4. Ensure `observed` claims have usable source references when practical.
5. If a contradiction remains unresolved, make it visible rather than smoothing it over.
6. Do not create a documentation-only log entry; Git already records history.
7. Apply the editorial pass within the selected workflow's scope and edit permissions.
