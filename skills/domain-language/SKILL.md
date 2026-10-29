---
name: domain-language
description: Clarify ambiguous project terminology and maintain a domain glossary with accepted synonyms. Use when domain terms are vague, overloaded, or contradictory, when identifying entities and relationships, or when mapping everyday, code, multilingual, or integration names to the same concept. Also use for glossary edits; ordinary use of an already clear term does not require terminology review.
---

# Domain Language

Give each domain concept a clear definition and a preferred name while recognizing its accepted synonyms. Synonyms are useful vocabulary, not mistakes to correct.

## Resolve language

Read the relevant entries in the project's existing glossary. If there is none, use `docs/domain/glossary.md`; create it only when the first durable definition is established. Reuse the existing location rather than creating a parallel glossary.

Use the glossary and current context to interpret the user's terms. Recognize accepted synonyms without interrupting the conversation. When a term has several plausible meanings that would change the work, ask a focused question with concrete alternatives. Do not question every vague phrase or repeatedly ask about an equivalence already established in the current context.

Check relevant project evidence and code when terminology depends on implemented behavior. Names, translations, shared types, or similar structures alone do not prove that two things are the same concept. Keep explicit user definitions distinct from observed implementation; surface material contradictions instead of silently changing either.

When a definition or equivalence is established by explicit user statements or clear project evidence, record it in the same task. If uncertain, state the open question in the conversation and leave accepted synonyms unchanged. Stay within the concepts involved in the task.

## Glossary format

Use one entry per concept: preferred term as the heading, a short definition, and a list of synonyms when useful. Add context in square brackets immediately after a synonym only when its meaning is context-specific. Synonyms may come from any language, everyday usage, code, or an integration; no separate categories or mapping tables are needed.

Illustrative format, not a definition to import into a project:

```markdown
## Cliente

Persona o organizzazione che acquista un servizio.

Sinonimi: acquirente, customer [API del partner].
```

A scoped synonym is accepted only in the stated context. If the same name denotes different concepts, keep separate definitions and make the distinction explicit; do not merge them into synonyms. Referring to the same concept does not imply identical fields, identifiers, or lifecycles. Keep data transformations and implementation details in the relevant technical pages, linked when needed.

Use the preferred term in newly written documentation where practical, and accept synonyms in conversation and existing interfaces. Do not rename code, database fields, APIs, or user-facing labels merely to normalize vocabulary.

## Documentation integration

Keep definitions concise, preserve existing human corrections, and follow the project's documentation metadata conventions. Link a newly created glossary from the documentation index when one exists. Do not create an empty index, a terminology registry, or an ADR for each word.

This skill works independently of `living-docs`. When both apply, maintain terminology here and let `living-docs` maintain the surrounding pages. Reading known definitions does not require running a new clarification workflow. During a report-only review, report terminology findings and proposed glossary changes without editing files.
