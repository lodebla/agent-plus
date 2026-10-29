# looppool configuration

Use commands inspected in the target repository. This example assumes its existing `test` and `typecheck` scripts are applicable.

```python
CONFIG = {
    "task": "Fix refresh-token rotation",
    "task_type": "fix",
    "spec": "Rotate a refresh token once; reject the old token after successful rotation.",
    "acceptance_criteria": [
        "A successful refresh returns a new token.",
        "The old token cannot be reused.",
        "Session behavior outside rotation is unchanged.",
    ],
    "project_context": "Auth state is owned by src/auth/session.ts.",
    "implementer_agent": "looppool-writer",
    "reviewer_agents": ["looppool-reviewer-a", "looppool-reviewer-b"],
    "strong_reviewer_agent": "looppool-reviewer-strong",
    "multi_review": False,
    "required_checks": [
        {"name": "tests", "command": "npm run test"},
        {"name": "types", "command": "npm run typecheck"},
    ],
    "optional_checks": [],
    "protected_paths": ["package-lock.json"],
    "max_iterations": 5,
    "stagnation_limit": 2,
    "evidence_rounds": 1,
}
```

When no required command applies, use `required_checks: []` and a nonempty `no_required_checks_reason` based on repository inspection.

## Review modes

| Key | Default and meaning |
|---|---|
| `multi_review` | `false`; checks then a fresh `reviewer_agents[0]`, with no judge for ordinary `PASS`/`FAIL` |
| `reviewer_agents` | At least two distinct configured agent names; all are used independently in multi-review |
| `strong_reviewer_agent` | `looppool-reviewer-strong`; fresh final-judge identity for multi-review, using that agent's normal OMP model/fallback mapping |
| `review_backend` | `native`; experimental `fh` is explicit-only and accepted only with `multi_review=true` |
| `fh_bridge_tool` | `fh_debate`; name of the explicitly installed experimental bridge |
| `evidence_rounds` | `1`; bounded read-only evidence follow-up available to the strong judge after multi-review |

Native multi-review performs one independent round and then invokes the strong judge. It has no peer discussion. A single-review `NEEDS_EVIDENCE` escalates immediately without a preliminary evidence round; only the strong judge uses `evidence_rounds`. The one automatic stagnation escalation uses the same multi-review path.

## Loop and repository settings

| Key | Default and meaning |
|---|---|
| `max_iterations` | `5`; global writer-invocation cap, never extended by escalation |
| `stagnation_limit` | `2`; consecutive unchanged candidates, repeated failed-gate signatures, or repeated blocker root causes before escalation/stop |
| `implementer_agent` | `looppool-writer`; write-capable role inheriting the active session model when no `/agents` override is set; a `BLOCKED` report returns `STOP_IMPLEMENTATION_BLOCKED` |
| `project_context` | `""`; concise relevant conventions and prior decisions |
| `protected_paths` | `[]`; exact repository-relative files the writer must not change |
| `check_timeout` | `900`; seconds for repository check subprocesses only |
| `review_diff_limit` | `24000`; review-diff character limit, with truncation reported |
| `check_output_limit` | `4000`; retained output-tail byte limit, with truncation reported |

Ordinary tests are not frozen or implicitly protected. The writer may add or repair them in the same iteration, but its required `test_changes` array must give a per-file AC/behavior reason for every test path changed in the actual diff (`[]` when none changed). Missing rationale becomes feedback for the next writer; it is not a rollback or approval phase. Use `protected_paths` only for genuinely immutable project infrastructure or explicit user constraints.

Required checks are always blocking. Optional checks may set `blocking` and require one authority attestation:

```python
"optional_checks": [
    {"name": "format-check", "command": "npm run format:check",
     "blocking": True, "local_read_only": True},
    {"name": "approved-audit", "command": "npm run audit:project",
     "blocking": True, "approved": True},
]
```

`local_read_only` means the exact existing command and invoked scripts were inspected and are relevant, local, nonmutating, and network-free. `approved` means existing user authority covers the action and cost. Discovery alone grants neither. Do not install tooling or authorize external mutation implicitly.

## Quota recovery

| Key | Default and meaning |
|---|---|
| `quota_auto_resume` | `true`; retry explicit subscription-usage limits only after OMP fallback is exhausted |
| `quota_usage_db` | `~/.omp/agent/agent.db`; read-only reset lookup; `""` disables it |
| `quota_reset_grace_seconds` | `5`; delay after a known reset |
| `quota_unknown_retry_seconds` | `900`; deterministic retry interval when no reset is known |

Agent handles intentionally have no Looppool deadline. Run the enclosing eval with timeout `0`. Generic 429/5xx errors, timeouts, and schema failures are not quota waits.

## Migration

Unknown keys fail preflight. Remove these obsolete options rather than carrying compatibility aliases:

- `test_writer_agent`, `test_repair_rounds`, `test_support_allowlist`: the implementation writer owns production and test changes; `test_changes` supplies rationale and review checks quality.
- `simplicity_model`, `simplicity_fallback_models`: configured reviewers assess simplicity with correctness, test quality, and scope.
- `max_fixes_per_iteration`: all concrete blockers are passed together.
- `debate_rounds`, `adaptive_debate`, `strong_discussion`: reviews are independent; multi-review has one round and a fresh strong judge.
- `judge_model`, `judge_fallback_models`, `strong_independent_review`: map the configured `strong_reviewer_agent` and its fallback in OMP.
- `agent_timeout`: agent calls have no Looppool deadline.
- `reviewer_c_agents`, `restore_best_on_failure`: no replacement; configure the supported roles and recover explicitly from reported checkpoints.
