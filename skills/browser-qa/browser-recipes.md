# Browser QA Recipes

Use the browser APIs actually available in the current harness. The examples use Playwright-style `page` objects and Node filesystem access where available; translate names to the actual API rather than assuming Playwright, a hidden/headless browser, or a specific filesystem. Run only after the approved plan. Create the durable run directory and pending report before navigation.

## Durable run setup and event capture

Use an absolute repository-local `.artifacts/browser-qa/<UTC timestamp>-<short commit>-<unique suffix>/` path. A delegated executor writes inside its own `workers/<worker-id>/` directory. Browser-server and repository filesystems may differ: copy generated artifacts into the repository filesystem and verify them before claiming they are durable. Browser page evaluation cannot access Node filesystem APIs; persist through the outer tool runtime.

Configure and test a project-specific sanitizer for sensitive personal data before attaching event listeners. Do not use an identity function or assume token-pattern redaction is a complete privacy filter. If safe sanitization cannot be established, record the limitation and omit unsafe event text/paths rather than persist them.

```js
const fs = await import('node:fs/promises');
if (typeof projectPersonalDataSanitizer !== 'function') {
  throw new Error('A project personal-data sanitizer is required before event capture');
}
const sanitizePersonalData = projectPersonalDataSanitizer;
// Set from the approved absolute repository-local run/worker directory, not browser-server cwd.
const runDir = approvedRunDirectory;
await fs.mkdir(runDir, { recursive: true });
const startedAt = new Date().toISOString();
const logs = [];
const network = [];
const screenshots = new Set(); // Register planned names before attempting capture.
const outcomes = []; // { id, outcome: 'PASS' | 'FAIL' | 'BLOCKED' | 'NOT_RUN' }
let report = '# QA Report\n\nStatus: pending; no scenarios executed.\n';
let status = 'IN_PROGRESS';
let visualReview = 'NOT_REQUESTED';
let writeQueue = Promise.resolve();
let evidenceError = null;

const redactSecrets = (raw) => String(raw)
  .replace(/\bBearer\s+[^\s,;]+/gi, 'Bearer [REDACTED]')
  .replace(/(["']?[\w-]*(?:password|passwd|secret|token|api[_-]?key)["']?\s*[:=]\s*)(?:"[^"]*"|'[^']*'|[^\s,;&}]+)/gi, '$1[REDACTED]');
const sanitizeUrl = (raw) => {
  try {
    const url = new URL(raw);
    if (!['http:', 'https:'].includes(url.protocol)) return url.protocol;
    return sanitizePersonalData(redactSecrets(url.origin + url.pathname));
  } catch { return '[invalid URL]'; }
};
const redact = (raw) => sanitizePersonalData(redactSecrets(String(raw)
  .replace(/\bhttps?:\/\/[^\s"'<>]+/gi, (value) => sanitizeUrl(value))));

const saveEvidence = (complete = false) => {
  writeQueue = writeQueue.then(async () => {
    const files = ['report.md', 'console.jsonl', 'network.jsonl', ...screenshots];
    const errors = [];
    const contents = {
      'report.md': report, // Preserve safe reproduction details; sanitize before assigning.
      'console.jsonl': logs.map((event) => JSON.stringify(event)).join('\n'),
      'network.jsonl': network.map((event) => JSON.stringify(event)).join('\n'),
    };
    for (const [name, text] of Object.entries(contents)) {
      try { await fs.writeFile(`${runDir}/${name}`, text + '\n'); }
      catch (error) { errors.push({ path: `${runDir}/${name}`, message: String(error) }); }
    }
    for (const name of files) {
      try { await fs.stat(`${runDir}/${name}`); }
      catch (error) { errors.push({ path: `${runDir}/${name}`, message: String(error) }); }
    }
    try {
      const path = `${runDir}/manifest.json`;
      await fs.writeFile(path, JSON.stringify({
        startedAt, updatedAt: new Date().toISOString(), commit: shortCommit,
        status, outcomes, visualReview,
        evidenceStatus: complete && !errors.length ? 'COMPLETE' : 'INCOMPLETE',
        files, errors,
      }, null, 2) + '\n');
      await fs.stat(path);
    } catch (error) {
      errors.push({ path: `${runDir}/manifest.json`, message: String(error) });
    }
    evidenceError = errors.length ? errors : null;
  });
  return writeQueue;
};
const recordConsole = (event) => {
  logs.push({ ...event, timestamp: new Date().toISOString() });
  if (['warn', 'warning', 'error', 'pageerror'].includes(event.type)) void saveEvidence();
};
const recordNetwork = (event) => {
  network.push({ ...event, timestamp: new Date().toISOString() });
  if (event.event === 'requestfailed' || event.status >= 400) void saveEvidence();
};
const onConsole = (message) => recordConsole({ type: message.type(), text: redact(message.text()) });
const onPageError = (error) => recordConsole({ type: 'pageerror', text: redact(error.message) });
const onRequest = (request) => recordNetwork({ event: 'request', method: request.method(), url: sanitizeUrl(request.url()) });
const onResponse = (response) => recordNetwork({ event: 'response', status: response.status(), method: response.request().method(), url: sanitizeUrl(response.url()) });
const onFailure = (request) => recordNetwork({ event: 'requestfailed', failure: redact(request.failure()?.errorText ?? 'unknown'), method: request.method(), url: sanitizeUrl(request.url()) });

await saveEvidence(); // Persist the pending report and empty log files first.
page.on('console', onConsole);
page.on('pageerror', onPageError);
page.on('request', onRequest);
page.on('response', onResponse);
page.on('requestfailed', onFailure);
// Navigate only now, after the plan was approved and listeners are attached.
```

`projectPersonalDataSanitizer(text)` is caller-provided and must cover the actual environment's names, email addresses, fiscal codes and sensitive identifiers before event capture. Apply the same policy to report text, screenshot content and persistence error messages; synthetic fixture references may remain when safe. Do not save response bodies, request/response headers, cookies, credentials or sensitive personal data. URL logging removes query strings and fragments; retain safe UI filter labels and synthetic fixture references separately in reproduction preconditions.

Wrap scenario execution in `try/finally`. Checkpoint after each scenario and candidate finding: update `report` with executed steps and observations, update `outcomes` with actual assertion results, then `await saveEvidence()`. In `finally`, finalize or mark the report partial, set status from coverage and confirmed findings, `await saveEvidence(true)`, report `evidenceError`, detach only your listeners and close only sessions you own. Do not lose the original test error because persistence failed. Bound waits for pending requests and disclose unfinished requests. A directory-creation failure must be reported with its exact path; never claim evidence was saved.

If the harness exposes only console/network listing tools, fetch all available events after each scenario and before closing, save them locally, and disclose that live or pre-navigation capture was unavailable. Preserve actual timestamps and event types; do not fabricate history. Empty event lists still produce both JSONL files.

## Browser setup and scenario patterns

Prefer a dedicated isolated browser session/tab when available. Do not attach to the user's active browser/profile without explicit consent, and do not claim isolation or headless operation without checking the actual tool configuration. Attach listeners before the first navigation where supported; after leaving/reopening a page, reattach and collect events in the same executor context. Use the harness's normal browser-tool API; do not assume handles or APIs such as `tab.$`, `tab.ref`, `page`, `goto`, or `waitForSelector` exist unless the current tool provides them.

For a Playwright-style API, a minimal instrumented tab could look like this:

```js
const logs = [];
page.on('console', (message) => logs.push(`[${message.type()}] ${redact(message.text())}`));
page.on('pageerror', (error) => logs.push(`[pageerror] ${redact(error.message)}`));
const requests = [];
page.on('response', (response) => {
  requests.push(`${response.status()} ${response.request().method()} ${sanitizeUrl(response.url())}`);
});
await page.goto(targetUrl); // Only after approval; listeners are already attached.
await page.waitForSelector('#items li'); // Wait for rendered state where this API supports it.
```

- **Read UI state:** use a supported accessibility snapshot, locator text, or read-only DOM evaluation (for example, `page.evaluate(() => document.querySelector('#total')?.textContent)`). Record exact safe UI text/values rather than paraphrases.
- **Boundary input:** prefer actual user interactions (`locator.fill`, keyboard input or the harness's fill/type tools) to test what a user can enter. A value assigned through page evaluation or DOM injection is synthetic setup, not proof of a reachable UI bug; classify it under hardening unless reproduced through supported UI actions.
- **Rapid repeat:** use the actual button/input action twice (for example, a supported double-click or two deliberate clicks) and wait a bounded interval for relevant responses; compare deltas rather than absolute IDs when server-side state persists.
- **Failure responses:** record status, method and sanitized URL. Never persist response bodies, headers or cookies by default. Expected validation/denial responses are diagnostics unless a reachable UI behavior demonstrates a defect.
- **Preconditions:** re-establish the recorded starting state for each scenario through UI or approved fixtures where safe. Do not assume a fresh page reload resets server state; compare counts/deltas when persistent state is intentional.

## Screenshots and visual evidence

Screenshots require approved evidence scope, not `--vision`. Image-based visual interpretation requires this executor to verify its own image-reading path, as described in `SKILL.md`.

```js
const name = 'screenshot-S03-save-error.png';
screenshots.add(name); // Record the intended artifact before capture.
await page.setViewportSize({ width: 1280, height: 800 });
await page.screenshot({ path: `${runDir}/${name}` });
await fs.stat(`${runDir}/${name}`);
await saveEvidence();
```

For a tool that returns a temporary path, copy it with the outer runtime's filesystem API into `runDir` and verify the destination. Keep planned filenames in the manifest even if capture/copy fails, and record the failure. Redact sensitive UI data before durable capture or use synthetic fixtures; do not leave an unredacted screenshot as the reported artifact. A screenshot is evidence that an image was captured, not evidence that the executor can interpret it.

## State setup and report evidence

Create/edit fixtures and configuration through the UI where practical. Approved API/database setup is allowed in the confirmed test environment: record synthetic fixture IDs, original values, changes and cleanup. A JavaScript-injected value, synthetic request or manual URL may help diagnose robustness, but is not a confirmed UI bug unless that state can be reproduced through a supported reachable UI action.

The caller supplies the approved scope, scenario table, data changes and classified findings to `report`; event arrays do not automatically imply bugs. Include all report sections required by `SKILL.md`, including empty sections for no findings. Add scope/environment/role and worker metadata to the manifest where appropriate, without secrets. Verify every referenced screenshot, log, child report and transferred artifact; include child relative paths in the coordinator's manifest.

- **Confirmed bug:** reachable UI entry point, preconditions, numbered steps, expected/actual behavior, successful repeat, severity and durable evidence.
- **Unconfirmed observation:** observed failure, attempted repeats and why confirmation is missing.
- **Hardening opportunity:** non-UI setup and reproducible synthetic input, explicitly outside confirmed UI bugs.
- **Expected diagnostic:** sanitized event and why it is expected.
- **Scenario coverage:** `PASS`/`FAIL`/`BLOCKED`/`NOT_RUN`, distinct from confirmation and artifact completeness.
- **Verdict:** tie confirmed impact to coverage; material gaps may require `INCONCLUSIVE`.

The durable report and manifest are required even if no events or screenshots exist. Sanitize secrets and personal data. `.artifacts/` stays local and Git-ignored: do not commit, push or upload evidence without a separate request.