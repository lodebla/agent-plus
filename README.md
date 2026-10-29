# Agent Plus

A personal collection of agent skills curated and adapted by [lodebla](https://github.com/lodebla). Use it as an installable skills library or as a starting point for a new project.

This is a collection, not a new agent runtime or an official distribution of any upstream project. Sources, local adaptations, and third-party license notices are documented in [SOURCES.md](SOURCES.md).

## Install skills

### Skills CLI

Requires Node.js/npm. Preview the available skills:

```sh
npx skills add lodebla/agent-plus --list
```

Install interactively in the current project:

```sh
npx skills add lodebla/agent-plus
```

Add `-g` for user-level installation. Review the selection and target agent before accepting; installing skills with names you already use can replace your existing versions. Manual-invocation-only metadata is preserved in the bundled files; how an agent handles that metadata depends on its runtime.

The Skills CLI installs skill directories, **not the root `AGENTS.md`**. Copy that file separately if you want these project rules.

### OMP: persistent native skills

Clone the repository, then copy only skill directories that do not already exist. Run from the clone:

```sh
git clone https://github.com/lodebla/agent-plus.git
cd agent-plus
mkdir -p "$HOME/.omp/agent/skills"
for skill in skills/*; do
  name=${skill##*/}
  target="$HOME/.omp/agent/skills/$name"
  if [ -e "$target" ] || [ -L "$target" ]; then
    printf 'Keep existing skill: %s\n' "$name"
  else
    cp -R "$skill" "$target" || exit 1
  fi
done
```

This does not overwrite or merge an existing skill. To upgrade an existing skill, compare it first and move its old directory to a backup **outside active skill discovery** before copying the replacement. Reload skills or start a new OMP session after installation.

In the originating devbox, `$HOME/.omp` points to `/persist/omp`; the native skill directory is therefore `/persist/omp/agent/skills/`. On other machines, persistence depends on their filesystem and runtime configuration.

## Start a new project

Use GitHub's **Use this template** button, or:

```sh
gh repo create OWNER/NEW-PROJECT --template lodebla/agent-plus --private --clone
cd NEW-PROJECT
```

The new project includes the rules in [`AGENTS.md`](AGENTS.md) and the skill library under `skills/`. Install the skills for your agent with `npx skills add .` or the OMP copy instructions above; merely having `skills/` in a repository does not guarantee your agent discovers it.

For an existing project, merge the rules deliberately into its existing `AGENTS.md`; do not overwrite project-specific instructions. The rules are written in English and ask the agent to explain things in Italian. Visual explanations belong in `.artifacts/`.

## What is included

- **Clarification and planning:** `brainstorming`, `grilling`, `grill-with-docs`, `wayfinder`, `research`, `prototype`.
- **Shared understanding:** `domain-language`, `living-docs`, `feynman`.
- **Design and implementation:** `codebase-design`, `improve-codebase-architecture`, `test-driven-development`, `systematic-debugging`, `impeccable`.
- **Review and verification:** `ponytail`, `ponytail-review`, `ponytail-audit`, `receiving-code-review`, `verification-before-completion`, `browser-qa`.
- **Coordination and lifecycle:** `dispatching-parallel-agents`, `finishing-a-development-branch`, `looppool`, `retro`, `hate`, `setup-matt-pocock-skills`, `find-skills`.
- **Project-specific recipe:** `clipboard-extension-visual-lab`, for the ClipBoard Manager extension. Its selectors, build commands, and messages are not generic browser QA instructions; use `browser-qa` for unrelated projects.

These are alternative entry points, not a mandatory sequence. Read each skill's requirements before using it. This collection keeps the author's custom TDD and domain-language workflows; it is not a complete installation of Matt Pocock's upstream workflow.

## Runtime requirements and limits

- Skills are instructions; they do not install their tools, models, browsers, permissions, or plugins.
- `browser-qa` needs the browser tooling described in its instructions. Its vision helper requires Python 3; visual interpretation requires verified image input support, not just screenshot capture.
- `living-docs` uses Git and Bash for source freshness checks. It does not automatically initialize a project's documentation.
- `looppool` requires OMP's eval/tool environment and explicitly configured agents/providers. It is not a standalone Python application.
- `impeccable` includes its upstream launcher and reference files. Its engine can be downloaded by the launcher; review the upstream requirements before running it.
- `clipboard-extension-visual-lab` requires its original extension project, Xvfb, Chromium, Quasar, and Playwright.
- Some instructions refer to OMP APIs or `skill://` paths. Other agents may need an explicit path/tool adaptation; installing the Markdown does not make those APIs available.
- Orca-specific skills (`orca-cli`, `orchestration`, `computer-use`) are intentionally excluded. No Orca installation is required merely to install this collection.
- Engram's `learn`, `review`, and `coach`, and the devbox-provided `devbox-sessions`, are not copied from their plugins/system installation.

## Attribution and licensing

See [SOURCES.md](SOURCES.md) for provenance and [LICENSE](LICENSE) for the licensing scope. Preserve the notices in `licenses/` when redistributing upstream-derived material. Local versions may differ from the linked upstream projects; an upstream reference is not a claim that these files are an unmodified release.
