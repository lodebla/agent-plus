# Trust and page metadata

## Knowledge classes

A page may contain one or more knowledge classes:

```yaml
knowledge:
  - observed
  - intent
  - decision
```

Use only classes actually present in the page.

### observed

Facts grounded in the current repository state: implementation behavior, APIs, schemas, configuration, data flow, deployment behavior visible from repo artifacts, and test-covered behavior.

Observed claims should cite source paths and should normally include `sources[]` metadata.

### intent

Explicit desired behavior, product rules, constraints, or requirements. Valid evidence includes direct user statements in the current conversation, accepted requirements/specifications, reviewed issues/PRs, existing product docs, or equivalent project-authoritative material.

Never convert observed implementation into intent by assumption.

### decision

Rationale for a deliberate choice. A decision should capture enough context to explain why the choice exists and, when useful, alternatives and consequences.

Never invent rationale from implementation. If rationale is absent, say so or use `TODO-VERIFY`.

## Recommended frontmatter

Keep metadata intentionally small:

```yaml
---
title: Session expiration
lastUpdated: 2026-10-14
knowledge:
  - intent
  - observed
verified_against_commit: 4d1a9e7
sources:
  - "src/Auth/SessionService.php | 0123456789abcdef0123456789abcdef01234567 | lines 20-88"
  - "tests/Auth/SessionServiceTest.php | 89abcdef0123456789abcdef0123456789abcdef | lines 14-72"
---
```

Each entry is a YAML string with the format `path | git blob hash | lines range`. `lines` is optional. This scalar format stays readable in renderers that display nested frontmatter objects as `[object Object]`. Do not use `|` in source paths. `freshness.sh` still reads the earlier mapping format for existing pages, but write the scalar format for new or updated pages.

Only `title` and `knowledge` are conceptually important. `sources` is strongly recommended for `observed` pages and optional for `intent`/`decision` pages.

`lastUpdated` is the editorial modification date in the native VitePress `YYYY-MM-DD` frontmatter format. Keep it separate from `verified_against_commit`, which records the source baseline last checked. Update `lastUpdated` when durable page content changes, not when only source hashes or the verification commit changes. VitePress uses Git history as a fallback for tracked pages without this field; untracked pages need an explicit date.

## Why `verified_against_commit` instead of “commit that contains this document”

A file cannot reliably embed the hash of the same Git commit that contains that exact file content: changing the file changes the tree and therefore the commit hash. This is self-referential.

Use:

```yaml
verified_against_commit: <HEAD at the time the page was verified>
```

This answers the useful question: “Which committed project baseline was current when this page was last checked?”

The actual commit that last modified the document is always available from Git itself:

```bash
git log -1 --format=%H -- docs/path/to/page.md
```

## Source hashes

For a source file, store the Git blob hash of the exact content that was inspected:

```bash
git hash-object src/Auth/SessionService.php
```

Put that hash in the second field of the readable source string. This works for both committed and uncommitted working-tree content.

The freshness checker compares the stored hash with the current content hash. A mismatch means “review this page”; it does not automatically mean the prose is wrong.

## Inline evidence

For non-trivial `observed` claims, prefer compact source references such as:

```text
The service rejects expired sessions before token refresh.
(`src/Auth/SessionService.php:44-61`)
```

Avoid citation noise on obvious prose. The goal is verifiability, not annotating every sentence.

## Uncertainty markers

Use:

```text
> TODO-VERIFY: <what cannot currently be established and what evidence is missing>
```

For a real conflict:

```text
> CONTRADICTION: Intent says 5 attempts; current implementation enforces 10. No test currently establishes which behavior is authoritative.
```

Do not leave a `CONTRADICTION` marker after the conflict has actually been resolved.
