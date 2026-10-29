# Init workflow

Use `init` when a repository has no useful `docs/` knowledge base yet, or when the user explicitly wants Living Docs conventions introduced.

## Steps

1. Inspect the repository narrowly: README, package/build files, source roots, tests, schemas, configuration, routes/entrypoints, deployment files, and existing documentation.
2. If `docs/` already exists, preserve it. Do not replace human structure just to match this skill.
3. Create or update `docs/README.md` as a compact routing index.
4. Create only sections justified by actual project knowledge. Typical sections are `architecture`, `domain`, `features`, `flows`, `decisions`, and `guides`.
5. Build a minimal first-pass overview of the codebase. Prefer a few useful concept pages over one page per source file.
6. Classify claims:
   - code-derived facts → `observed`
   - explicit requirements/constraints → `intent`
   - explicit rationale → `decision`
7. For `observed` pages, add readable scalar entries in `sources[]` with paths, `git hash-object` values, and optional line ranges for the significant files actually inspected.
8. Set `verified_against_commit` to current `HEAD` when available.
9. Do not infer product requirements or architectural rationale from code.
10. Do not create audit logs, registries, placeholder trees, or generated-only folders.

Operational procedures are guides. Keep them under `docs/guides/` with task-specific names such as `testing.md` or `environment.md`. Do not create a separate `docs/runbooks/` folder, starter runbooks, or generic testing/deployment procedures by default. Add a procedure only when the repository or user request provides a concrete need and evidence.

## Suggested initial pages

Only when supported by the repo:

- `docs/architecture/overview.md`
- one or more major feature/domain pages
- existing deliberate decisions under `docs/decisions/`
- a task-specific operational guide when a real workflow is evidenced by scripts/configuration or requested by the user

Keep `docs/README.md` short enough that an agent can use it as a routing map without loading the whole wiki.
