# looppool

An OMP skill for bounded implementation with repository checks and independent review.

Install this folder as `.omp/skills/looppool` for one project or `~/.omp/agent/skills/looppool` for the default profile. Install the reviewer templates, map their primary/fallback model aliases, and invoke `/skill:looppool <task and constraints>`.

Start OMP in a dedicated clean worktree with `omp --cwd <worktree>`; changing Python's cwd does not rebind isolated agents. The default loop is writer → checks → `reviewer_agents[0]`. Tests are changed by the writer with per-file AC rationale and checked from the actual diff; there is no pre-implementation test approval or freeze.

Set `multi_review=true` for independent configured reviews followed by a fresh `strong_reviewer_agent` judge. The same path is used once automatically when the default loop stagnates or immediately when its reviewer returns `NEEDS_EVIDENCE`. Reviews do not debate, and failed blocking checks cannot become `DONE`.

See [setup](references/setup.md), [configuration](references/config.md), and [protocol](references/protocol.md). [Fusion Harness](references/fusion-harness.md) is experimental, explicit-only, and requires multi-review.

Local Python tests cover orchestrator invariants; [pressure scenarios](tests/pressure-scenarios.md) state expected behavior. Neither is a claim that a particular external provider, Fusion Harness installation, Windows environment, or Klipboard Task 6 was integration-tested.
