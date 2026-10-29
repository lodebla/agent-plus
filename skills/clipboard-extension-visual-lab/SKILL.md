---
name: clipboard-extension-visual-lab
description: "Screenshot and slow-motion QA of the ClipBoard Manager browser extension (Quick Armory, Tooltip, popup, Settings) in a headed Chromium on Xvfb, including seeding history and inspecting transitions"
---

# ClipBoard Manager extension visual lab

Use when you need to see how the extension UI really renders or animates (Quick Armory HUD, content-script Tooltip, popup, Settings) in `kilpboar_with_antgravity`.

## Setup
1. Display: `Xvfb :99 -screen 0 1600x1000x24 -nolisten tcp` as a named service; export `DISPLAY=:99`. Extension service workers need headed Chromium (headless shell does not load extensions).
2. Build: `npx quasar build -m bex -T chrome` (~5 s) → `dist/bex-chrome`. When several agents share the tree, serialize build + run with `flock /tmp/uxlab/build.lock …`; never rebuild while Playwright E2E is running (it reads `dist/`).
3. Script (Node, outside the repo): `createRequire(<repo>/package.json)` then `require("@playwright/test").chromium.launchPersistentContext("", { headless: false, deviceScaleFactor: 2, args: ["--disable-extensions-except=<dist>", "--load-extension=<dist>"] })`. Extension id from `context.serviceWorkers()[0].url()`.

## Seeding and driving
- Seed from the popup page (`chrome-extension://<id>/www/index.html`): `chrome.storage.sync.set({ settings: {...} })`, `chrome.runtime.sendMessage({ type: "clipboard:replace-history", data: { items } })`, slots via `clipboard:assign-quick-slot`. Images: draw on `OffscreenCanvas`, `convertToBlob`, FileReader data URL.
- Page fixture: `tests/e2e/fixtures/test-page.html` (file://). Open overlays by sending to the tab from an extension page: `chrome.tabs.sendMessage(tab.id, { type: "quick-armory:toggle" | "toggle-tooltip" })`.
- Shadow roots: Armory host `#clipboard-manager-quick-armory-host` (`.quick-armory-app`), Tooltip host `#clipboard-manager-tooltip-host`.

## Seeing motion
- Slow all CSS transitions and Web Animations: `const cdp = await context.newCDPSession(page); await cdp.send("Animation.enable"); await cdp.send("Animation.setPlaybackRate", { playbackRate: 0.08 });` then press keys and screenshot every ~700 ms.
- Stitch frames with PIL into one strip and read it, instead of reading many PNGs.
- Measure geometry stability by reading `getBoundingClientRect()` of the panel after each step.

## Pitfalls
- A broken (mid-edit) build makes `waitForEvent("serviceworker")` time out: rebuild first.
- `-webkit-line-clamp` on a grid item is blockified and ignored in current Chromium: clamp an inner element.
- Electron E2E (`playwright.electron.config.ts`) rebuilds `dist/electron` unless `ELECTRON_E2E_SKIP_BUILD=1`; don't run it concurrently with the lab.
