# OMP setup

## Bind the session to the worktree

Prepare a dedicated Git worktree with HEAD and a clean initial state, then start OMP from that exact root:

```sh
omp --cwd /absolute/path/to/worktree
```

Do not start in checkout A and call `os.chdir("/path/to/worktree-B")` from eval. That moves only Python; isolated `agent()` calls remain bound to A. Looppool compares `Path.cwd()` with `PI_TOOL_BRIDGE_SESSION` and returns `STOP_CONFIGURATION` when the binding is absent or mismatched. It does not create or clean a worktree.

## Install agent definitions

Install the writer and all three reviewer templates from `../templates/` using this OMP version's agent-directory conventions:

- `looppool-writer` has no `model` frontmatter or per-agent model override: it inherits the active session model. Unlike the bundled `task` agent, it does not select `@task`.
- `looppool-reviewer-a` is the default single reviewer and a behavioral/edge-case specialist.
- `looppool-reviewer-b` covers integration/caller/lifecycle risks and joins multi-review.
- `looppool-reviewer-strong` is the fresh final-judge identity for multi-review.

At least two distinct names must be configured in `reviewer_agents`, even though the default path uses only the first. Map each reviewer's primary and fallback aliases to authenticated models; `/agents` can override each reviewer's model independently. Leave the writer's model override unset to preserve session-model inheritance:

```yaml
modelRoles:
  looppool_review_a: commandcode/deepseek/deepseek-v4-flash:high
  looppool_review_a_fallback: openai-codex/gpt-5.6-sol:xhigh
  looppool_review_b: commandcode/deepseek/deepseek-v4-flash:high
  looppool_review_b_fallback: openai-codex/gpt-5.6-sol:xhigh
  looppool_review_strong: openai-codex/gpt-5.6-sol:xhigh
  looppool_review_strong_fallback: commandcode/z-ai/glm-5.3-flash:max
```

Use selectors and credentials actually available to the user. Different aliases do not prove provider or model-family diversity. The judge uses the configured `strong_reviewer_agent` identity and therefore the same mapping/fallback chain on every fresh invocation; there are no separate judge-model settings.

## Configure provider recovery

OMP owns finite request retry, credential rotation, and provider switching for agent sessions. Configure only authenticated fallbacks that preserve role capability:

```yaml
retry:
  enabled: true
  maxRetries: 3
  maxDelayMs: 0
  modelFallback: true
  fallbackChains:
    commandcode/*:
      - openai-codex/gpt-5.6-sol:xhigh
    openai-codex/*:
      - commandcode/z-ai/glm-5.3-flash:max
```

OMP fallback runs first. Looppool sends no separate LLM readiness probes and gives agent handles no deadline. Run the orchestration eval with timeout `0`; do not add a finite outer timeout.

If an invoked role still returns an explicit subscription usage limit, Looppool reads the reset from error metadata or the read-only local usage database, announces the provider and retry time, waits, and recreates only that blocked invocation. With no reset, it announces the configured deterministic retry interval. Before retrying a failed writer, it restores the exact pre-invocation repository snapshot. Generic 429/5xx outages, timeouts, and schema failures are not quota waits. Keep the OMP process alive; recovery is not durable across process exit.

## Local validation

Run the executable regression suite:

```sh
cd ~/.omp/agent/skills/looppool/tests
python3 -m unittest -v
```

Then use a disposable worktree for one authorized smoke covering the configured roles and repository checks. Mocked adapters and pressure-scenario documents do not prove external provider routing, worktree attachment, Fusion Harness compatibility, Windows behavior, or Klipboard Task 6.
