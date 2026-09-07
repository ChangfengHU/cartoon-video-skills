# v0.5.0 Validation

2026-09-07: no new video generation or quality-iteration loop was started.

- 20 existing Skill tests + 12 service tests passed. Independent review reproduced
  two defects (truthy but incorrectly typed rights/research fields, and an async
  file error escaping the HTTP handler); both were fixed and regression checked.
- Production Worker `cartoon-assets-mcp`, private R2 binding only, no CF admin
  credential at runtime. Version `585a4dd1-c05c-4a7b-a9d4-cdf79fca5ba5`.
- Anonymous access returns401, disallowed browser Origin403, missing media404.
  MCP initialize / notification / tools-list / library-info handshake passed;
  exactly eight tools. Code tests verify read-only permissions and namespace
  isolation. These tests are not a complete third-party penetration audit.
- Independent full pagination: all17 legacy records and all9 legacy feedback
  preserved. One original notification SFX received a provenance-preserving v2
  record for real integration validation: total18 records. This does not add
  personal voice samples or imply fresh artistic approval.
- Real media import, identical retry/dedup, feedback and project freeze passed.
  A newly constructed client recovered the project and hash-checked its media.
  Independent reviewer downloaded legacy character art and original SFX and the
  v2 SFX; SHA256 and sizes matched. Public URLs do not expose these files.
- Project fixture ID: `6e5456bf549b0375b8863028e56bac9edf322126daa03610d26acf81ed9ad962`.
- Skill and Codex Plugin manifest validators passed. Publisher-generated ZIP was
  SHA256-verified by actual macOS and187 Linux ARM installations. The previous
  named Skill was backed up, not deleted.187's global MCP entry was added using
  Codex CLI after a private backup of config.toml; other entries were preserved.
- Source/public package contain no service secret, personal reference audio,
  user clone, private catalog or third-party music. The public Plugin uses a
  Python-standard-library scoped client, not a CF management credential.

Independent verification artifacts are retained in the private operator task;
the historical v0.4 results below are not new video-generation claims.

## Historical v0.4.0 Validation

Validated on 2026-09-07. This release preserves the v0.3.3 creative requirements and adds the private R2 asset-library workflow.

- Skill frontmatter validator passed using an existing Python environment with PyYAML; no dependency installation was needed.
- Brand integrity check passed: version 0.4.0 and all five bundled visual assets matched their declared hashes.
- Twenty deterministic tests passed: eight brand-snapshot tests, three music-planning tests and nine asset-library tests. They cover malformed/private inputs, safe output paths, immutable records and integrity checks.
- The public skill contains no personal voice recordings, synthetic personal voice samples, third-party music, fonts, model weights or credentials. Private R2 objects and index data are not included in the package.
- SOP sidecar remains optional, keeps `instruction+materials` as its public input, and describes runtime requirements without embedding secrets. The skill is not an independently deployed video-generation service.
- The published ZIP was downloaded again and matched SHA-256 `90d4a2a6eba5a60bfb2ec9f68ec3608b12820a6793346a7e0fe3964ba47fc2a8`. All 30 package files matched the frozen source byte-for-byte. The downloaded installer matched the repository installer and passed shell syntax validation.
- Real private R2 validation uploaded 13 authorized media files (five character images, five original sound effects and three provider-preset voice segments); every file was downloaded again and matched SHA-256. Four metadata-only records preserve three BGM sources and one public reference video. Eight audio durations were verified with FFprobe against the source manifests. These assets stay in the private library and are not in the public ZIP.
- Final R2 acceptance found 17 records, 13 media objects, nine feedback entries and one immutable index snapshot (40 objects total). Three concurrent imports retained every record. A character image and an original notification sound were downloaded and frozen in an `ASSET_LIBRARY_LOCK.json` with matching SHA-256 and sizes. Native `r2.dev` access was disabled and no custom domains were configured. The current REST index rebuild uses serial reads and can take minutes; it is not a low-latency catalog service.

## Installation and session recovery

- The Codex installer stores a single skill under `~/.codex/skills/cartoon-xiaban` and creates the supported user-discovery symlink under `~/.agents/skills`.
- Updates preserve the existing named skill in a timestamped hidden backup. Unrelated skills are outside the update target. A conflicting independent discovery directory is preserved and reported before installation.
- Linux aarch64 validation used Codex CLI 0.153.4 and an existing Node 22.23.2 / HyperFrames 0.8.30 runtime. System Node 20 was retained; a task-scoped PATH selects the compatible runtime.
- The downloaded installer completed on macOS and Linux aarch64. Both installed trees contained the same 30 files and matched the frozen source tree hash `baebdc1fa68fe8cf8f16f683285e91802ea4dac5ce97323de028790fd371d9ba`. The existing macOS version was preserved in its timestamped backup.
- An independent GitHub installation through the standard skill-installer, pinned to source release commit `22b1153eb795ed5dd2ba929c50e91d1d6838d02e`, produced the same 30-file tree and passed the SOP contract checks.
- On Linux, all 20 tests passed from the installed directory. `skills/list` returned exactly one enabled `cartoon-xiaban` entry with user scope and all 11 existing rendering/media dependency skills. No global AGENTS file was retained or pre-existing authentication/configuration overwritten.
- One owned, completed non-interactive session was copied into the default Codex home, then found by `thread/list` and loaded to `idle` by `thread/resume`. No `turn/start` was sent. The original rollout and default authentication, configuration and pre-existing skill files remained unchanged.
- Non-interactive history requires `codex resume --all --include-non-interactive` in the picker, or a direct `codex resume <UUID>`. See the [official command reference](https://learn.chatgpt.com/docs/developer-commands?surface=cli) and [supported skill discovery locations](https://learn.chatgpt.com/docs/build-skills).

## Scope of these checks

These checks validate package integrity, client behavior, installation and history recovery. They do not guarantee the same perceived quality for every new video, natural voice performance, music rights, successful cloud calls without credentials, or performance on an unconfigured machine. No new creative video run is part of this release validation.

The earlier v0.2.0 fixed-story demonstration had zero lint/runtime/layout errors and 27/27 contrast checks, with four repeated-sprite and six intentional crop/edge warnings. Those are historical results for that demonstration; they are not new v0.4.0 render results.
