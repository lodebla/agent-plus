# looppool protocol

## Preflight and target

Stabilize the task, task type, SPEC, and observable acceptance criteria before implementation. Validate a dedicated, initially clean Git worktree with HEAD, applicable repository commands, and the configured role names. Python's cwd must equal the OMP eval-to-agent bridge root; `os.chdir()` cannot rebind task isolation. A missing or mismatched `PI_TOOL_BRIDGE_SESSION` stops before any writer.

An empty required-check list needs `no_required_checks_reason`. Optional commands need existing approval or an inspected `local_read_only` attestation; command discovery grants neither. Unknown/removed configuration keys fail. When Fusion Harness is explicitly selected, validate its callable bridge and `multi_review=true` before the writer runs.

Looppool does not spend LLM calls on readiness probes. OMP handles credential rotation, prioritized models, finite request retry, and finite provider fallback when a role is actually invoked.

Capture an initial checkpoint outside the repository. Snapshot comparisons cover Git-visible regular-file bytes, symlink targets, modes, and index identity. Ignored artifacts and external side effects are outside this mutation detector.

## Implementation and tests

Each iteration dispatches a fresh `implementer_agent` labeled `looppool implement iteration N`. It receives the target, project context, current candidate, protected paths, and all concrete feedback from the preceding checks/review. It uses existing project primitives, avoids unrelated refactors, and does not commit.

The implementer schema permits `IMPLEMENTED` or `BLOCKED` and requires:

- `summary`
- `changed_files`
- `criteria_addressed`
- `checks_run`
- `remaining_issues`
- `test_changes`: an array of per-file AC/behavior reasons, or `[]`

The writer may create, repair, or remove ordinary tests with production changes. There is no preliminary Test Writer, validation approval, or test freeze. After the writer returns, Looppool derives changed test paths from the actual candidate diff and compares them with `test_changes`. Missing rationale is a concrete feedback item for the next writer, not a rollback. Independent review checks that changed tests defend observable AC and were not weakened merely to pass.

Explicit `protected_paths` and infrastructure guards still block forbidden mutations. Ordinary test paths are not protected solely because they are tests. A crashed/failed writer is restored to its exact pre-invocation snapshot before any retry; repository rollback cannot undo external mutations. A valid `BLOCKED` report returns `STOP_IMPLEMENTATION_BLOCKED` with its evidence and checkpoint.

## Checks and default review

After every retained candidate, run required checks and authorized optional checks, retaining bounded output. Required checks always block completion; configured blocking optional checks do likewise. Ordinary gate failures go directly to the next writer; repeated equivalent failures trigger the stagnation multi-review instead of another blind retry.

The default (`multi_review=false`) dispatches only `reviewer_agents[0]`, labeled `looppool review round 0 NAME`. The fresh reviewer receives the exact diff, implementer report (including `test_changes`), check results, SPEC, and AC. It independently assesses behavior, callers, regressions, changed-test quality, simplicity, efficiency, and scope. It returns `PASS`, `FAIL`, or `NEEDS_EVIDENCE` under the active `REVIEW_SCHEMA`.

`PASS` reaches `DONE` only when all blocking checks pass and no other blocker remains. `FAIL` returns every concrete gate and review blocker together to the next writer. A single-review `NEEDS_EVIDENCE` escalates immediately to multi-review on the current candidate; it does not run a preliminary investigator or consume `evidence_rounds`.

No judge runs for an ordinary decisive single review.

## Multi-review and judge

With `multi_review=true`, all configured reviewers inspect the current material independently in round 0. They do not see or debate peer opinions. Each may find any defect while retaining its configured emphasis. Their evidence requests are preserved for the judge rather than opening reviewer discussion.

A fresh final judge is then invoked through `strong_reviewer_agent` with the same configured OMP model and fallback mapping as that identity. It receives the current candidate, check results, labeled independent reviews, finding ledger, and current evidence. Only this strong-judge stage may perform bounded read-only follow-up under `evidence_rounds`; it then adjudicates every current finding. Consensus alone is not evidence, and there are no peer-discussion rounds.

Native review uses `_run_native_review(cfg, material, multi=...)`; `_review_round` is round 0 only. Explicit Fusion Harness review also means multi-review: the bridge executes exactly one independent round, then the native fresh strong judge adjudicates it. See [Fusion Harness](fusion-harness.md).

Review history is compact: retain the current candidate's labeled reviews, ledger, evidence, and decision. Feedback to a later candidate carries concrete blockers, not duplicated obsolete debate transcripts. All blockers are passed together; there is no per-iteration finding cap.

## Stagnation

Track three consecutive signals: unchanged candidate snapshots, repeated failed-gate signatures, and repeated blocker root causes. Reaching `stagnation_limit` in the default path triggers one targeted multi-review of the current candidate, even if checks failed. Feed its concrete judge/check feedback to the next fresh writer and reset the counters.

That automatic escalation is available once. If stagnation reaches the limit again after its feedback, return `STOP_STAGNATION`. With explicit `multi_review=true`, the candidate already had multi-review, so unresolved stagnation after judge feedback stops without another review tier. Escalation never increases `max_iterations`; exhausting that global writer cap returns `STOP_MAX_ITERATIONS`.

## Completion, mutation, and recovery

`DONE` requires the same unchanged candidate to satisfy all blocking checks and the applicable decision: single reviewer `PASS`, or strong judge `PASS` after multi-review. A judge cannot overrule failed checks. Missing test-change rationale, unresolved evidence, invalid structured output, or a reported blocker prevents success.

Every reviewer, evidence collector, judge, and check phase is compared against repository snapshots. Unexpected Git-visible mutation stops with evidence and a checkpoint rather than reviewing a silently changed candidate. This is detection, not an OS sandbox.

Checkpoints remain outside the repository and record HEAD, tracked patch, exact changed/untracked file contents, modes/symlink targets, and deletions. Recover into a separate worktree at the recorded HEAD after inspecting the manifest; never apply blindly over live work. Looppool does not automatically restore an older “best” candidate. Every `STOP_*` and runtime error is non-success and should report the current recoverable state; before a valid baseline exists, checkpoint fields may be null with a setup explanation.

Submodules and paths beneath symlink directories are unsupported. Visible generated files count as mutations; do not change ignore rules to hide them. Command timeouts terminate the shell process group, but host cancellation of an agent is not guaranteed.

## Quota recovery

After OMP's configured fallback is exhausted, only an explicit subscription usage-limit signal enters deterministic recovery. Looppool obtains a reset from error metadata or the read-only usage database, announces the provider and exact retry time, waits through the grace period, and recreates only the blocked invocation. If no reset exists, it announces a deterministic probe time from `quota_unknown_retry_seconds`.

Generic 429/5xx outages, timeouts, and schema/semantic failures do not become quota waits. Quota recovery is process-local, so the OMP/eval process must remain alive. Run the orchestration eval with timeout `0`; no in-process setting can revive an externally terminated process.
