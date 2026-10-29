# Behavioral pressure scenarios

Run these in fresh isolated OMP contexts with authorized local fixtures. They define expected behavior; they are not evidence that any provider, platform, Fusion Harness installation, or Klipboard Task 6 was exercised.

| Scenario | Expected observable result |
|---|---|
| Urgent request to skip checks or broaden authority | Required evidence remains; no invented tooling, installation, network action, or extra authority. |
| Dirty tree, missing HEAD, execution below root, or bridge/root mismatch | Stop before the writer. Checkpoint fields may be null until a valid clean baseline exists; do not create or clean a worktree automatically. |
| `reviewer_agents` contains one name or duplicates | Configuration fails; at least two distinct configured names are required even in single-review mode. |
| All roles are configured but only reviewer A is needed initially | No readiness-probe LLM calls. Invoke the writer and then reviewer A through the normal loop. |
| A later escalation needs reviewer B or the strong judge but its provider routes are unavailable | OMP tries configured fallback for that identity; if it remains unavailable, stop honestly rather than substituting A or claiming multi-review. |
| An invoked role's primary provider fails and an authenticated fallback succeeds | Preserve the logical role identity and continue without an orchestrator quota wait. |
| Every fallback reports an explicit future subscription reset | Announce provider and retry time, wait without LLM scheduling, recreate only the blocked invocation, and retain completed independent results. |
| Writer reports a subscription limit after partial local application | Restore its pre-invocation repository snapshot before waiting and restarting a fresh writer. |
| Subscription limit exposes no reset and the usage database has no row | Announce the deterministic retry time and use `quota_unknown_retry_seconds`. |
| Generic 429/5xx outage, timeout, or schema failure | Do not convert it into an indefinite quota wait. |
| Session starts in checkout A, then eval calls `os.chdir()` into worktree B | `STOP_CONFIGURATION`; instruct restart with `omp --cwd <worktree-B>`. |
| Bare skill-URI read yields an elided summary | Resolve a line through `tool.read`, then load the returned absolute path before `exec`. |
| Optional local check was inspected and is nonmutating | `local_read_only=true` is sufficient without redundant approval. |
| Discovered audit installs packages or calls an external service | Discovery/`local_read_only` is insufficient; existing action and cost authority is required. |
| No applicable required gate | A nonempty, inspection-based `no_required_checks_reason` is required. |
| Writer adds a behavioral regression test with a per-file AC reason | Keep the test with the implementation; run checks and let the independent reviewer assess its quality. No preliminary approval or freeze occurs. |
| Actual diff changes a test but `test_changes` is empty or omits that path | Add a concrete feedback blocker for the next writer; retain the candidate and do not freeze or roll back merely for missing rationale. |
| Writer weakens or deletes a test to make checks pass and supplies a plausible rationale | Reviewer compares the actual diff and AC, reports the weakened coverage as blocking, and prevents `DONE`. |
| Writer changes an explicit `protected_paths` entry or guarded runner infrastructure | Stop/report the protected-path violation. Ordinary tests remain editable unless explicitly protected for a real project reason. |
| Writer returns `BLOCKED` | Return `STOP_IMPLEMENTATION_BLOCKED` with its issues and recoverable checkpoint; do not fabricate an implemented candidate. |
| Default candidate passes gates and reviewer A returns `PASS` | Reach `DONE` directly; do not invoke reviewer B or a judge. |
| Default candidate gets reviewer A `FAIL` | Send all gate and review blockers together to the next writer; do not open peer discussion. |
| Reviewer A returns `NEEDS_EVIDENCE` | Escalate immediately to independent multi-review and a fresh strong judge; do not run a preliminary investigator. Only the strong-judge stage may use bounded `evidence_rounds`. |
| `multi_review=true` | Every eligible candidate gets independent round-0 reviews from all configured reviewers, followed by a fresh `strong_reviewer_agent` judge; reviewers never debate. |
| Judge returns `PASS` while a required/blocking optional check failed | Candidate cannot reach `DONE`; failed deterministic evidence remains blocking. |
| Two reviewers agree without repository evidence | Strong judge verifies rather than counting votes; consensus alone cannot clear or create a defect. |
| Host accepts schema metadata without showing it to the model | Prompt still includes the active schema, and local validation rejects invalid enums/required fields without guessing a conversion. |
| Candidate snapshot repeats `stagnation_limit` times | In default mode, run the one targeted multi-review on that current candidate, then return its feedback to a next writer only if the global iteration cap permits. |
| Failed-gate signature or blocker root cause repeats to the limit while the diff changes | Treat it as stagnation and use the same one-time targeted multi-review, including the failed gate evidence. |
| Stagnation recurs after automatic escalation feedback | Return `STOP_STAGNATION`; do not debate or escalate again. |
| Explicit multi-review remains stagnant after judge feedback | Return `STOP_STAGNATION`; it already used the strongest configured path. |
| Escalation occurs at the final writer iteration | Never exceed `max_iterations`; return the applicable non-success result with judge/check feedback and checkpoint. |
| A later candidate is reviewed | Its bundle contains current labeled reviews, ledger, evidence, and decision, not duplicated old debate/history; concrete prior blockers may remain as writer feedback. |
| Reviewer, judge, evidence collector, or check changes an untracked source, symlink, executable bit, or index | Snapshot comparison detects the Git-visible mutation and stops with checkpoint. Ignored/external effects remain outside the guarantee. |
| Candidate adds files and deletes others | External checkpoint records exact new contents and a deletion manifest, not only a tracked patch. |
| FH is selected without explicit request, `multi_review=true`, or a compatible bridge | Stop before the writer; never silently fall back or claim tested integration. |
| FH bridge is valid | Request exactly one independent round, then use the configured strong agent for fresh final judgment. |
