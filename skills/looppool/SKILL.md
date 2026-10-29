---
name: looppool
description: Use when a non-trivial code change is too risky for one-pass implementation, when repeated defects need independent scrutiny, or when provider outages or worktree isolation have disrupted autonomous iteration.
---

# looppool

Looppool is a bounded implementation loop for OMP. By default, one fresh writer implements and repairs the candidate, deterministic checks run, and one fresh reviewer decides whether concrete feedback is needed.

## Before execution

- Stabilize the task, SPEC, and observable acceptance criteria (AC).
- Start OMP at a dedicated, initially clean Git worktree with `omp --cwd <worktree>`. `os.chdir()` cannot rebind isolated agents.
- Inspect repository test/lint/type/build commands. Required checks are blocking; optional checks need existing approval or an attested, inspected `local_read_only` command.
- Configure at least two distinct `reviewer_agents`, an `implementer_agent`, and `strong_reviewer_agent`. The default uses the first reviewer; the others are available for multi-review. Configure reviewer models and fallbacks through OMP; leave the model unset on the default `looppool-writer` to inherit the active session model.

Read [setup](references/setup.md), construct [CONFIG](references/config.md), and follow the [protocol](references/protocol.md). Fusion Harness is [experimental and explicit-only](references/fusion-harness.md).

```python
source = await tool.read({
    "i": "Resolving Looppool orchestrator",
    "path": "skill://looppool/orchestrator.py:1",
})
exec(read(source["details"]["resolvedPath"], offset=1, limit=10000))
result = await looppool(CONFIG)
display(result)
```

Run this eval with timeout `0`. Looppool gives agent handles no deadline. OMP model/provider fallback runs first; only explicit subscription-limit failures enter deterministic quota waiting.

## Loop

1. A fresh writer returns `IMPLEMENTED` or `BLOCKED`. It may repair tests with the implementation and must explain every changed test path in `test_changes`; `BLOCKED` returns `STOP_IMPLEMENTATION_BLOCKED`.
2. Required and authorized optional checks run.
3. Normally, `reviewer_agents[0]` independently checks AC, actual diff, test quality, regressions, and simplicity. No judge runs for an ordinary `PASS` or `FAIL`.
4. Feedback includes all concrete gate and review blockers. The next fresh writer repairs the candidate within `max_iterations`.

`multi_review=true` instead runs the configured reviewers independently and sends their evidence to a fresh judge using `strong_reviewer_agent`; there is no peer debate. A single-review `NEEDS_EVIDENCE` escalates immediately to multi-review; only the strong judge uses the bounded evidence rounds.

Repeated unchanged candidates, failed-gate signatures, or blocker root causes trigger one targeted multi-review of the current candidate, even when checks failed. Its feedback gets one further implementation opportunity within the global cap. Further stagnation stops; explicit multi-review stops on unresolved stagnation without another escalation.

## Completion and recovery

`DONE` requires one unchanged candidate with all required checks passing, no blocking authorized optional check, and the applicable reviewer decision (`PASS` directly, or judge `PASS` after multi-review). Review cannot overrule failed gates.

Read-only phases are checked for Git-visible file, symlink, mode, and index mutation. Writer crashes roll back to the pre-invocation snapshot; retained candidates and external checkpoints support manual recovery. These checks are not an OS sandbox and cannot undo external side effects. Every `STOP_*` or error remains a non-success result with checkpoint and evidence.
