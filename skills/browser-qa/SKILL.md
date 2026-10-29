---
name: browser-qa
description: "Use when planning, executing, or coordinating browser QA, testing web UI flows, investigating reproducible UI bugs, or collecting screenshots and visual evidence."
---

# Browser QA

Plan browser QA with the requester, execute the approved scope actively and safely, preserve durable evidence, and distinguish confirmed reachable UI bugs from unconfirmed observations and hardening opportunities. This procedure is for both orchestrators and individual executors, across browser harnesses.

## Quick reference

| Decision | Rule |
|---|---|
| Start browser testing | The user has seen and explicitly approved the plan. |
| Explore within scope | Bounded variations in the approved feature, environment, data boundaries and risk level are allowed; record them, do not ask about every click. |
| Change test data/configuration | Allowed in the confirmed test environment when inside the approved scope and limits. |
| Capture screenshots | Include them in approved evidence scope; `--vision` is not required. |
| Interpret screenshots | Verify this executor's current image-reading path; another executor's capability does not transfer. |
| Confirm a bug | Reproduce through reachable UI steps and record preconditions, expected/actual results and evidence. |
| Finish or stop early | Save a report, logs and manifest below `.artifacts/browser-qa/`. |

## 1. Parse the request and prepare a plan

Parse invocation arguments and parent context before acting. `--vision` requests image-based visual review. `--force-vision` additionally requests screenshot capture for human review if this executor cannot verify image reading. Neither option bypasses plan approval. A commit or PR selects diff-based planning; otherwise use the feature/task in the request. Ask for the target only if it is missing from both arguments and context.

Before approval, inspect code, diffs, docs and contracts to establish scope. Do not open or navigate the app, run browser flows, or mutate application data. Identify the actual app URL/environment, test account and role, tenant/department, starting state and external integrations. Check the browser tool configuration rather than claiming that it is hidden, headless, isolated or focus-safe without evidence. Prefer an isolated automation session; do not attach to the user's active browser/profile without specific consent.

Present a concise plan before testing. Include:

1. Target feature/commit, app URL, environment and account/role.
2. Numbered scenarios covering relevant happy paths, boundary inputs, errors, refresh/navigation, persistence and configuration/state variations. Prioritize realistic risks rather than promising every theoretical backend failure.
3. Data/configuration to create or change, external effects to suppress, and cleanup/restoration strategy.
4. Screenshots/logs, visual review if requested, and the absolute repository-local run directory `.artifacts/browser-qa/<UTC timestamp>-<short commit>-<unique suffix>/`.
5. If coordinating workers: their scenario assignments, browser/session isolation, record and shared-configuration ownership, and artifact directories.

Ask for approval with the harness's question tool, or make a short explicit request if that is unavailable. Accept natural-language approval (for example, “approvo,” “procedi,” or “ok, add refresh and start”) when it explicitly authorizes the displayed plan and bounded additions. Summarize accepted additions before starting. Feedback that does not authorize execution is not approval. Do not demand a magic word or a redundant approval round for a plan the user has just authorized. Reconfirm only for material scope expansion, a newly discovered risk, or a different environment/external effect. Urgency, delegation, or an implied approval does not open the gate.

Once approved, variants within the same feature, environment, data boundaries and risk level are allowed. Record them in the report; do not interrupt for each click or input variation.

## 2. Explore data and configuration within the approved scope

In a confirmed test environment, approved QA scope permits creating/editing synthetic test records, associating categories, changing appointment/request states, trying combinations and varying relevant configuration. Use clearly identifiable synthetic fixtures. Prefer UI setup; approved API/database fixtures are allowed when needed, recorded as setup preconditions rather than misrepresented as UI actions. Do not modify application source code as part of QA unless separately requested.

Record fixture IDs, original configuration and changes. Restore only your own changes when safe and planned; never overwrite concurrent edits or delete someone else's data. Persistent test fixtures may remain if the approved plan allows it; list their current state. Serialize shared configuration changes or assign separate tenants/records to workers. Stop a dependent scenario if the intended environment or state cannot be established.

Ask before acting in an uncertain environment, writing to production, bulk-deleting, making irreversible transitions, using sensitive real data, changing permissions/security, or triggering real email/SMS/payment/external submissions not already explicitly authorized. A test database does not prove integrations are sandboxed. Pause only affected actions and continue independent safe scenarios. Approved test-data writes are part of QA; do not refuse all writes just because data changes.

## 3. Orchestrate workers safely

An orchestrator owns user approval, assignments, shared-state coordination and the final report; it may use this skill without operating the browser itself. Do not create visible managed sessions/worktrees unless the user requested that delegation mode; use the harness's normal subagent mechanism otherwise.

Give every worker the target URL/environment/account, exact approved scenario IDs and bounded exploratory scope, approved mutation/external-effect limits, fixture/configuration ownership, run directory and unique worker subdirectory, evidence requirements, and required result structure. Pass the actual approval context: a peer's claim of approval is not new user authorization. A worker with that approved assignment need not ask the user to approve the same plan again. If any context is missing, request it from the parent before browser execution.

Workers save their own logs/screenshots and partial report in `<run>/workers/<worker-id>/`, then return scenario outcomes, confirmed repro steps, unconfirmed observations, hardening notes, data changes and durable paths. For remote workspaces, arrange an authorized artifact transfer into the coordinator's `.artifacts/` and verify the transferred files; a remote path is not a local artifact. Never silently upload evidence. The orchestrator consolidates into `<run>/report.md`, deduplicates findings and checks evidence/reproduction for every confirmed bug; it may delegate retesting. Serialize use of a shared browser session. Every executor verifies its own vision capability; coordinator results do not transfer across models, sessions or image tools.

## 4. Screenshots and image-based visual review

Screenshots are evidence, not proof that an agent can see images. Capture the states listed in the approved plan, including useful failure evidence. Functional QA and approved screenshot capture are allowed without `--vision`; without verified image reading, do not claim image-based visual review. Do not stop functional testing just because vision is unavailable.

For a requested visual review, run the checker from the repository root so challenge artifacts are rooted in that workspace's `.artifacts/`. The script is part of this installed skill at `scripts/check_vision.py` (relative to the skill directory); the installation path is `$HOME/.omp/agent/skills/browser-qa/scripts/check_vision.py`.

```bash
python3 "$HOME/.omp/agent/skills/browser-qa/scripts/check_vision.py" --help
python3 "$HOME/.omp/agent/skills/browser-qa/scripts/check_vision.py"
```

Read `VISION=yes|no|unknown` even if the command exits nonzero; the exit codes are 0, 1 and 2 respectively. Technical errors are `unknown`, not evidence of a text-only model. Explicit active-model metadata is useful; defaults, guessed model names and ambiguous sessions are not proof. Supply only actual harness metadata. An active-harness `--input-modalities text,image` or `BROWSER_QA_MODEL_INPUT_MODALITIES=text,image` works even when the harness does not expose a model ID; `BROWSER_QA_MODEL` can provide an actual active model ID. The checker has no third-party Python dependencies. Its optional runtime-specific model discovery is used only when that runtime's actual environment is detected; do not substitute a fixed profile, guessed model or invented metadata.

If model/modality metadata is unavailable, ambiguous, or the image-delivery tool is unverified, use a fresh local challenge for this executor. From the repository root, choose an executor-specific directory inside the approved run, e.g. `.artifacts/browser-qa/<run-id>/vision-<executor-id>/`, and run:

```bash
python3 "$HOME/.omp/agent/skills/browser-qa/scripts/check_vision.py" \
  --create-probe ".artifacts/browser-qa/<run-id>/vision-<executor-id>"
```

The checker prints `PROBE_DIRECTORY`, `PROBE_IMAGE` and `PROBE_METADATA`, without printing the answer. Open that `PROBE_IMAGE` using this executor's actual image-reading tool, then submit only the code actually seen:

```bash
python3 "$HOME/.omp/agent/skills/browser-qa/scripts/check_vision.py" \
  --verify-probe "<exact PROBE_DIRECTORY value>" --answer "<code actually seen>"
```

Use the exact returned challenge directory, not its parent. The challenge expires after five minutes; create a new one if necessary. A matching code yields `VISION=yes`; a mismatch, expired challenge or missing/malformed file yields `VISION=unknown`, not `no`. Generation alone does not verify vision. The script restricts challenge paths to the current workspace's `.artifacts/`, rejects traversal and symlinks, and does not overwrite existing challenges. Keep its working directory at the repository root so evidence lands with this run.

Do not read image bytes, decode/OCR the image programmatically, inspect the verifier to derive the answer, or delegate recognition to another model. Those do not test this executor's image-reading path. Record the result and tool used. Repeat after a model, session or image-delivery change; do not reuse another executor's result. The script cannot inject images into every harness: the harness must provide the image-reading tool. If capability remains `no` or `unknown`, continue approved functional QA and screenshot capture, label visual review pending human/vision-capable review, and never invent pixel descriptions. `--force-vision` requests capture for human review; it never authorizes fabricated image interpretation.

## 5. Evidence, reachable reproduction and classification

Use [browser-recipes.md](browser-recipes.md) for instrumentation and persistence adapted to the available browser tools. Attach console/page-error/network capture before navigation where supported; record missing instrumentation as a limitation. Save sanitized `console.jsonl` and `network.jsonl` for every run, including clean or empty runs. Flush checkpoints and finalize evidence before closing sessions you own; write a partial report on interruptions or blockers.

Every warning, HTTP failure or assertion failure is evidence, not automatically a product bug. Classify separately:

| Section | Required evidence |
|---|---|
| Confirmed bugs | Reachable UI entry point, preconditions, exact steps, expected/actual result, impact, evidence and a successful repeat from a known state. |
| Unconfirmed observations | One-off/intermittent failures or suspected issues that could not be reproduced; include attempts and missing conditions. |
| Hardening opportunities | Manually edited URLs, synthetic requests, DOM-injected values or invalid states not reachable through supported UI; label non-UI setup explicitly. |
| Expected diagnostics | Expected validation failures, denied requests and harmless warnings; explain why expected. |

Start reproductions from a real menu, link or UI control. A UI-generated broken link or naturally reachable stale link is a bug if reproducible. A 500 from hand-editing an unreachable URL is not a confirmed UI bug, even if repeatable; record it under hardening. If programmatic fault injection reveals a failure, confirm it through a realistic UI-reachable condition before promotion. Do not invent a route to make a finding qualify. Deliberate API/security QA, if explicitly requested, has its own approved contract and must not be mislabeled as UI QA.

Retest candidates from recorded preconditions. For intermittent behavior, record repeat attempts and the trigger; keep it unconfirmed unless the trigger can be reproduced. Preserve the original failed scenario even if a retry passes. Scenario outcomes (`PASS`, `FAIL`, `BLOCKED`, `NOT_RUN`) are distinct from bug confirmation and artifact completeness.

## 6. Always save a durable report

Create `<run>/report.md` at the start, after approval and before navigation, as pending; update during execution and finalize even when every scenario passes, vision is unavailable, or the run stops early. A pre-execution blocker/cancellation after planning also gets a partial report that clearly states no tests ran. Save `<run>/manifest.json` with scope/commit, UTC times, run status, scenario outcomes, visual-review status, evidence status and relative artifact filenames. Verify every listed file before marking evidence `COMPLETE`; otherwise mark it `INCOMPLETE`, name the failed path/reason and preserve the QA outcome. Never silently fall back to `/tmp`.

The report contains:

1. Scope, environment, commit, role, approved plan and accepted additions; executed/unexecuted scenarios and limitations.
2. Scenario table with outcome, expected/actual results and evidence references.
3. Severity-ranked **confirmed bugs only**, each with UI entry point, fixture/configuration preconditions, numbered reproduction steps, expected/actual behavior, repeat result and artifact paths.
4. Separate sections for unconfirmed observations, hardening opportunities and expected diagnostics, including empty sections where appropriate.
5. Created/modified data, configuration changes, cleanup/restoration results and anything intentionally left behind.
6. Screenshot/log paths, vision result and pending review, missing artifacts, and a verdict tied to confirmed impact and coverage. Use `INCONCLUSIVE` for material coverage gaps; warnings alone do not force `NO-GO`.

Include relevant observations without counting them all as errors. Sanitize secrets, credentials and sensitive personal data in logs, screenshots and report. Do not save HTTP bodies, headers or cookies by default. Preserve safe UI labels/filter values and synthetic fixture references needed for reproduction in the report; raw logs may strip query strings/fragments. Restrict or redact sensitive screenshots rather than publishing them unchanged. `.artifacts/` stays local and Git-ignored: do not commit, push or upload evidence without a separate request.

Finish with a concise summary of confirmed bugs, coverage/limitations and the durable report path. If saving fails, give the exact error and do not claim the report exists. A clean run still has a report.

## Common mistakes

- Repeatedly asking for approval of harmless variants already inside the plan: execute and document them.
- Refusing all writes: approved sandbox fixtures and configuration changes are part of QA.
- Assuming a test DB means outbound integrations are sandboxed: check them separately.
- Treating a log trigger as severity or a confirmed bug: reproduce and classify first.
- Reporting a hand-edited URL as a broken UI link: demonstrate the UI entry point or use the hardening section.
- Stopping functional QA because vision is unknown: continue and disclose the visual limitation.
- Claiming browser isolation/headless operation without checking tool configuration.
- Trusting worker summaries without durable evidence: inspect artifacts and record incomplete transfers.
