# Ingest workflow

Use `ingest` to turn durable knowledge from conversation or project artifacts into maintained documentation.

Good sources include:

- explicit statements from the user in the current conversation;
- accepted PR descriptions and review decisions;
- issues/tickets containing requirements;
- meeting notes;
- specifications and design notes;
- completed implementation plans;
- incident findings and operational lessons.

## Durable-knowledge test

Before writing anything, ask internally:

- Will another developer or agent benefit from knowing this later?
- Does it constrain implementation, explain a non-obvious choice, define project behavior, or prevent a repeated mistake?
- Is it sufficiently explicit to preserve without guessing?

If not, no-op.

## Classification

- desired behavior / requirement / business rule / explicit constraint → `intent`
- explicit rationale / trade-off / chosen alternative → `decision`
- implementation fact confirmed by repository evidence → `observed`

A single page may combine classes when it is clearer for humans, for example a feature page containing both intent and observed implementation.

## Steps

1. Read `docs/README.md` and relevant existing pages first.
2. Prefer enriching the existing canonical page over creating a duplicate.
3. Preserve the user's wording when precision matters, but rewrite into durable project documentation rather than conversation transcript.
4. Never promote speculation, brainstorming, or unchosen alternatives into intent/decision.
5. If the new knowledge supersedes an older decision or intent, preserve useful history and make the supersession explicit.
6. Add code sources only for claims that were actually verified against the repo.
7. Keep docs concise and linked; do not archive the whole conversation.

## Completed plans

When ingesting a completed plan, preserve durable requirements, constraints, decisions, and rationale in the existing canonical pages. Compare the plan with the final implementation and available execution evidence, including user corrections and decisions made during execution. Treat proposed, abandoned, or superseded steps as such; a checked box alone does not establish implemented behavior or an adopted decision.

Verify implementation claims against the repository. Keep any unresolved mismatch visible rather than presenting the initial plan as the final result. Transfer neither task checklists nor execution chronology into the knowledge base. The resulting pages must remain understandable without the plan.

Plain `ingest` does not delete its source. When the user also requests removal of the plan, first verify that all durable knowledge has been captured, update incoming links to the appropriate canonical pages, and then remove the plan. Unresolved questions may be retained as `TODO-VERIFY` in canonical pages, with enough context and provenance to investigate without the plan; uncertainty alone does not prevent deletion. If material evidence or uncertainty cannot be preserved adequately, keep the source and report what remains unresolved. Respect any project retention requirements.

Example request:

```text
Ingest this completed plan into the living docs, then delete the plan.
```

## Decision pages

Create a dedicated page under `docs/decisions/` when the rationale is important enough to survive implementation details. A lightweight decision record normally contains:

- context/problem;
- decision;
- rationale;
- alternatives, when known;
- consequences/trade-offs;
- links to relevant implementation/docs.

Do not require a formal ADR identifier unless the project wants one.
