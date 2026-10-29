# Sources and attribution

Agent Plus is a curated collection by [lodebla](https://github.com/lodebla), assembled from the author's installed skills, two personal skill imports, upstream projects, and local adaptations. It is not an official release of any source project. Upstream names and trademarks remain their owners'.

## Provenance limits

The personal imports did not retain a source manifest or original upstream commit IDs. **The pinned commits below are references checked for attribution and licensing, not claims about the revision originally imported.** Some local files differ from those references. An exact source or dependency version is stated only when verified; missing metadata is not replaced with a guessed author.

The collection license covers original contributions only. Third-party material retains the licenses and notices bundled in `licenses/` and inside the relevant skill directory. Skill-local notices travel with individual Skills CLI installations.

## Public upstreams

| Source | Bundled skills or material | License and reference |
| --- | --- | --- |
| [Matt Pocock — skills](https://github.com/mattpocock/skills) | `wayfinder`, `codebase-design`, `improve-codebase-architecture`, `setup-matt-pocock-skills`, `grilling`, `research`, `prototype`, `retro`; TDD support material | [MIT at `a496f5513d4a4cf889bc48e189e579f4b0bdf6aa`](https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/LICENSE). Copyright (c) 2026 Matt Pocock. See `licenses/matt-LICENSE.txt`. |
| [Jesse Vincent — Superpowers](https://github.com/obra/superpowers) | `brainstorming`, `dispatching-parallel-agents`, `finishing-a-development-branch`, `receiving-code-review`, `systematic-debugging`, `verification-before-completion` | [MIT at `2ce8aa15d05bd57213e6f746f953aafb7ded7a8b`](https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/LICENSE). Copyright (c) 2025 Jesse Vincent. See `licenses/superpowers-LICENSE.txt`. |
| [Vercel — Skills](https://github.com/vercel-labs/skills) | `find-skills` | [MIT at `92a9a34ac3bf88e695e468b90c7bf32f163d32c8`](https://github.com/vercel-labs/skills/blob/92a9a34ac3bf88e695e468b90c7bf32f163d32c8/LICENSE). Copyright (c) 2026 Vercel, Inc. See `licenses/vercel-LICENSE.txt`. |
| [DietrichGebert — Ponytail](https://github.com/DietrichGebert/ponytail) | `ponytail`, `ponytail-review`, `ponytail-audit` | [MIT at `7801d061243d7b753bad0e0b3c057cd250b11755`](https://github.com/DietrichGebert/ponytail/blob/7801d061243d7b753bad0e0b3c057cd250b11755/LICENSE). Copyright (c) 2026 DietrichGebert. See `licenses/ponytail-MIT.txt`. |
| [Fable Wise, in get-fable](https://github.com/imMamdouhaboammar/get-fable/tree/36920932251ffc619da6073eb02cb35a9a2f2dbf/skills/fable-wise) | `feynman`, `hate` | [Skill package MIT at `36920932251ffc619da6073eb02cb35a9a2f2dbf`](https://github.com/imMamdouhaboammar/get-fable/blob/36920932251ffc619da6073eb02cb35a9a2f2dbf/skills/fable-wise/LICENSE). Copyright (c) 2026 LilMGenius. See `licenses/fable-wise-MIT.txt`. The parent repository has a different root license; this attribution relies on the nested package's explicit MIT license, not that root license. |
| [Paul Bakaus — Impeccable](https://github.com/pbakaus/impeccable) | `impeccable`, including launcher, agent definitions, and references | [Apache-2.0 at `5e745ace7e151feb2a93d360d0281fe39448b857`](https://github.com/pbakaus/impeccable/blob/5e745ace7e151feb2a93d360d0281fe39448b857/LICENSE). Upstream identifies version 4.8.0. See `licenses/impeccable-LICENSE.txt` and the skill's `NOTICE.md` and `THIRD_PARTY_NOTICES.md`. Do not describe this version as MIT. |

### Impeccable's source credits and bundled dependency

- **Anthropic's frontend-design:** Impeccable's upstream README credits [Anthropic's original skill](https://github.com/anthropics/skills/tree/ca45fc496a3436251f191354091d557da31c15b5/skills/frontend-design), licensed [Apache-2.0](https://github.com/anthropics/skills/blob/ca45fc496a3436251f191354091d557da31c15b5/skills/frontend-design/LICENSE.txt). Historical Impeccable notices name “2025 Anthropic, PBC”; that credit is retained in the bundled third-party notices.
- **ehmo's platform-design-skills:** Impeccable's current NOTICE attributes the iOS and Android references to [this MIT source](https://github.com/ehmo/platform-design-skills/tree/dc2be825d8b439caea78e9eaa8fb3ac23b0ff3e9). The original copyright line is `Copyright (c) 2026` without a holder name; the notice identifies the author as ehmo. See `licenses/ehmo-LICENSE.txt`.
- **ehmo's typecraft-guide-skill:** [Historical Impeccable attribution](https://github.com/pbakaus/impeccable/blob/5613891aa64f92ba2982338c0436b76d67bcdb8e/NOTICE.md) credits typography contributions from [this source](https://github.com/ehmo/typecraft-guide-skill/tree/8099648409ec73980bd693ac8d15fd3e3230072d). Its MIT license text matches the bundled ehmo notice. The historical credit is preserved without claiming every historical addition remains in this snapshot.
- **modern-screenshot:** the vendored `skills/impeccable/scripts/modern-screenshot.umd.js` comes from [qq15725/modern-screenshot](https://github.com/qq15725/modern-screenshot). The [MIT license checked at `792d6db7411839c62940a6e930161f8e376e817f`](https://github.com/qq15725/modern-screenshot/blob/792d6db7411839c62940a6e930161f8e376e817f/LICENSE) names `Copyright (c) 2021-present wxm`. The exact version of the bundled UMD file is not established. See `licenses/modern-screenshot-LICENSE.txt` and the copy inside the Impeccable skill.

## Personal sources and local adaptations

The following came from the owner's local skill collection/imports. No independently verified public upstream repository was recorded for these packages; this is not a claim that an unknown third party authored them, nor an invented public-source credit.

| Skill | Local provenance and adaptation |
| --- | --- |
| `domain-language` | The owner's chosen domain-language workflow; canonical glossary, accepted synonyms, and human clarification of material ambiguities. Preserved instead of the removed `domain-modeling`. |
| `living-docs` | Imported personal package, including references, templates, freshness script and tests. Provides the durable documentation model around domain-language, distinguishing intent, observed implementation, and decisions. |
| `browser-qa` | Consolidates the imported `mike-bot` package and the previous `running-browser-qa` workflow. Renamed to one active skill, including artifact paths and environment variables; keeps functional QA separate from verified visual capability. No public author is inferred from the name `mike-bot`. |
| `grill-with-docs` | Imported personal adaptation combining `grilling`, the owner's `domain-language`, and Living Docs conventions. Not presented as an unmodified Matt Pocock skill. |
| `test-driven-development` | The owner's customized TDD instructions, retained instead of replacing them with upstream `tdd`. Bundled `writing-good-tests.md` matches [Matt Pocock's `tdd/tests.md` at `5beb35b040e3de97e54fa9e386d7e42d15c295c2`](https://github.com/mattpocock/skills/blob/5beb35b040e3de97e54fa9e386d7e42d15c295c2/skills/engineering/tdd/tests.md); Matt's MIT notice is included. |
| `looppool` | Local OMP-specific orchestration package with implementation, references, templates and tests. Its model/provider aliases and project/task references are configuration examples, not portable runtime guarantees. |
| `clipboard-extension-visual-lab` | Locally developed, project-specific recipe for the ClipBoard Manager extension. It is included as a documented example, not a replacement for generic browser QA; its application fixture is external. |

Additional adaptations carried in this collection:

- `brainstorming` no longer requires `writing-plans`; an approved architectural design ends in an actionable handoff rather than a mandatory separate planning skill.
- `wayfinder`, `codebase-design`, `improve-codebase-architecture`, and `setup-matt-pocock-skills` align domain terminology with the owner's `domain-language` and durable documentation with `living-docs`. They do not require the removed `domain-modeling` or a parallel root `GLOSSARY.md` convention.
- `feynman` and `hate` match the Fable Wise bodies at the cited reference, with different frontmatter. They are **not attributed to Matt Pocock**.
- Six files in the supplied Impeccable variant differ from the pinned audit snapshot. They carry prominent file-level notices; the exact original import revision is unknown. Agent Plus adds those notices and the missing distribution license/attribution files without changing their executable behavior.

## Deliberate exclusions

The Orca skills `orca-cli`, `orchestration`, and `computer-use` are not distributed here. Their global installation in the originating environment is unchanged. Removed/duplicate skills, imported project-specific packages that were never activated, and plugin/system-provided skills are not silently reinstated by this collection.
