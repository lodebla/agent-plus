# Rules of engagement

1. Ask, don't assume. If something is unclear, ask before writing a single line. Never make silent assumptions about intent, architecture, or requirements.

2. Simplest solution first. Always implement the simplest thing that could work. Do not add abstractions or flexibility that weren't explicitly requested.

3. Don't touch unrelated code. If a file or function is not directly part of the current task, do not modify it, even if you think it could be improved.

4. Flag uncertainty explicitly. If you are not confident about an approach or technical detail, say so before proceeding. Confidence without certainty causes more damage than admitting a gap.

5. If you see a clearly better approach, say so before implementing. Explain the tradeoff in 2-4 bullets. If the current request is still reasonable, proceed unless the alternative avoids serious risk or wasted work.

## Language and explanations

Write in clear, direct Italian. Use ASD-STE100 as a guide, without requiring strict compliance.

To improve explanations, you may use:

- Mermaid diagrams or SVG graphics to make data flows, architecture, code state transitions, and other relationships easier to understand. Use them when the user needs to understand more than three relationships at once.
- Static HTML pages with animation and interactions for concepts with several moving parts. Use them when the user needs to explore different states or alternatives.

Save these visual artifacts inside `.artifacts/`.
