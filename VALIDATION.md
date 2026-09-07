# v0.4.0 Validation

Validated on 2026-09-07. This release preserves the v0.3.3 creative requirements and adds the private R2 asset-library workflow.

- Skill frontmatter validator passed using an existing Python environment with PyYAML; no dependency installation was needed.
- Brand integrity check passed: version 0.4.0 and all five bundled visual assets matched their declared hashes.
- Twenty deterministic tests passed: eight brand-snapshot tests, three music-planning tests and nine asset-library tests. They cover malformed/private inputs, safe output paths, immutable records and integrity checks.
- The public skill contains no personal voice recordings, synthetic personal voice samples, third-party music, fonts, model weights or credentials. Private R2 objects and index data are not included in the package.
- SOP sidecar remains optional, keeps `instruction+materials` as its public input, and describes runtime requirements without embedding secrets. The skill is not an independently deployed video-generation service.
- The published ZIP was downloaded again and matched SHA-256 `90d4a2a6eba5a60bfb2ec9f68ec3608b12820a6793346a7e0fe3964ba47fc2a8`. All 30 package files matched the frozen source byte-for-byte. The downloaded installer matched the repository installer and passed shell syntax validation.
- Real private R2 validation uploaded 13 authorized media files (five character images, five original sound effects and three provider-preset voice segments); every file was downloaded again and matched SHA-256. Four metadata-only records preserve three BGM sources and one public reference video. Eight audio durations were verified with FFprobe against the source manifests. These assets stay in the private library and are not in the public ZIP.

## Installation and session recovery

- The Codex installer stores a single skill under `~/.codex/skills/cartoon-xiaban` and creates the supported user-discovery symlink under `~/.agents/skills`.
- Updates preserve the existing named skill in a timestamped hidden backup. Unrelated skills are outside the update target. A conflicting independent discovery directory is preserved and reported before installation.
- Linux aarch64 validation used Codex CLI 0.153.4 and an existing Node 22.23.2 / HyperFrames 0.8.30 runtime. System Node 20 was retained; a task-scoped PATH selects the compatible runtime.
- The downloaded installer completed on macOS and Linux aarch64. Both installed trees contained the same 30 files and matched the frozen source tree hash `baebdc1fa68fe8cf8f16f683285e91802ea4dac5ce97323de028790fd371d9ba`. The existing macOS version was preserved in its timestamped backup.
- On Linux, all 20 tests passed from the installed directory. `skills/list` returned exactly one enabled `cartoon-xiaban` entry with user scope and all 11 existing rendering/media dependency skills. No global AGENTS file was retained or pre-existing authentication/configuration overwritten.
- One owned, completed non-interactive session was copied into the default Codex home, then found by `thread/list` and loaded to `idle` by `thread/resume`. No `turn/start` was sent. The original rollout and default authentication, configuration and pre-existing skill files remained unchanged.
- Non-interactive history requires `codex resume --all --include-non-interactive` in the picker, or a direct `codex resume <UUID>`. See the [official command reference](https://learn.chatgpt.com/docs/developer-commands?surface=cli) and [supported skill discovery locations](https://learn.chatgpt.com/docs/build-skills).

## Scope of these checks

These checks validate package integrity, client behavior, installation and history recovery. They do not guarantee the same perceived quality for every new video, natural voice performance, music rights, successful cloud calls without credentials, or performance on an unconfigured machine. No new creative video run is part of this release validation.

The earlier v0.2.0 fixed-story demonstration had zero lint/runtime/layout errors and 27/27 contrast checks, with four repeated-sprite and six intentional crop/edge warnings. Those are historical results for that demonstration; they are not new v0.4.0 render results.
