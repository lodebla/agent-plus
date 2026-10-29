---
name: grill-with-docs
description: "A relentless interview to sharpen a plan or design, which also creates docs (ADR's and glossary) as we go."
disable-model-invocation: true
---

Use the `grilling` and `domain-language` skills together. Load their `SKILL.md` files using the host's skill mechanism or the sibling skill directories.

Use `grilling` for the interview and `domain-language` for definitions and accepted synonyms. Consult the existing project glossary; otherwise use `docs/domain/glossary.md`, created only when a definition is established. Preserve accepted synonyms and context qualifiers; maintain this single canonical glossary.

Capture durable decisions and their rationale in the existing canonical project pages as they are settled. If a dedicated decision record is useful, follow the project's convention, defaulting to `docs/decisions/`. Keep the glossary about concepts; do not put implementation decisions or the interview transcript there. If `living-docs` is available, follow its documentation conventions without running a second interview or a full documentation sweep.

Document only decisions actually made by the user; recommendations and unanswered questions remain provisional. Confirm shared understanding before implementation, as required by `grilling`.
