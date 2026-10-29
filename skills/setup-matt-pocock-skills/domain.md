# Domain Docs

Use `domain-language` for terminology and `living-docs` for the surrounding project knowledge base. Keep one canonical documentation layout shared by humans and agents.

## Before exploring

- Read `docs/README.md` when present and follow only the links relevant to the task.
- Consult the project's existing glossary. Without an existing location, the default is `docs/domain/glossary.md`.
- Read relevant decision pages in the project's existing location, defaulting to `docs/decisions/`.
- In a multi-context project, follow the existing context-specific documentation links. Do not create another glossary hierarchy or a separate glossary-map format.

If those pages do not exist, proceed without scaffolding empty directories or files. Create a glossary only when a durable definition is established; create a decision page only when the rationale is useful and is not already captured in a canonical page.

## Domain language

Use preferred terms in new documentation where practical and recognize accepted synonyms, including their context qualifiers. Do not interrupt ordinary use of established vocabulary or rename code merely to normalize wording.

Invoke `domain-language` when an ambiguity materially changes the work, or when a definition or synonym equivalence must be established or revised. It owns terminology clarification and glossary updates. Merely reading existing definitions does not require a new clarification workflow.

## Durable intent, observed behavior and decisions

Follow `living-docs` conventions to maintain the relevant canonical pages. Explicit user or project evidence establishes intent and rationale; code and tests establish observed implementation. Surface disagreements instead of silently choosing one.

For a durable architectural choice, preserve the reason, genuine alternatives and consequences in the existing relevant page. Use a separate page under `docs/decisions/` only when useful, and link existing explanations rather than duplicating them. Keep implementation decisions out of the glossary.

## Decision conflicts

If a proposal contradicts an existing decision, identify the page and explain why reopening it may be justified. Do not silently overwrite accepted rationale. Report terminology and documentation findings without editing pages during report-only reviews.
