# v0.5.0 Validation

2026-09-07: no new video generation or quality-iteration loop was started.

- 20 existing Skill tests + 12 service tests passed. Independent review reproduced
  two defects (truthy but incorrectly typed rights/research fields, and an async
  file error escaping the HTTP handler); both were fixed and regression checked.
- Production Worker `cartoon-assets-mcp`, private R2 binding only, no CF admin
  credential at runtime. Final deployment version `3efc313d-89fc-4272-b374-f44c6090e0f2`.
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

### Fresh187 acceptance and distribution

- Public publisher package, source Skill, local installed Skill,187 installed
  Skill, bundled Plugin Skill and a separate GitHub installation all have31
  files and the same relative-path/hash tree digest:
  `e7169e518923d64925f9097f8ae11b03230151316494e7e1ff9305379aab2252`.
- GitHub source release `af46442e093d63548cd79b1b53359e50998bc86b` was fetched
  through skill-installer into a new directory.187 also installed the actual
  `cartoon-video-studio@personal` Plugin from GitHub in an isolated Codex home;
  Codex resolved its MCP working directory and relative client arguments.
-187 default uses one canonical Skill plus one standalone MCP entry, not both
  plugin and standalone copies simultaneously. Its scoped credential belongs to
  claude with0600 mode. Prior configuration values remained intact; CLI added
  the new MCP and trust records for the two new acceptance workspaces. No global
  AGENTS file, TTS model change or old-session deletion was made.
- First fresh task `01a07d21-5289-74f3-93d3-a581f028df90` correctly completed
  MCP queries and project recovery but reported download failure because its
  shell sandbox had no network. It did not falsely report a verified file.
- Second **new** task `01a07d23-7d50-7610-b21f-e94121996068` used task-scoped
  network permission with workspace-write; global sandbox settings were not
  changed. It read the installed Skill, completed all search/feedback pages,
  recovered the previous project, downloaded52844bytes and independently
  matched SHA256 `72923e69d03bbaba0c0d59e07bf021c11ecf3508761f97fedff04d5d9ce064c0`.
  It retained the requirement to research new music even when old tracks exist.
  This was not a video, listening or aesthetic-quality acceptance run.

### Fleet registration

- Fleet hub contains all three entries: Skill `cartoon-xiaban`0.5.0, MCP
  `vyibc-cartoon-assets`1.0.0, Plugin `cartoon-video-studio`0.1.0.
- Public registry shows the MCP's **eight live-discovered tools**, not only a
  fallback count. Both Fleet origins report15 MCPs /6 Skills /2 Plugins with
  no broken dependencies. The existing20 capability entries remain unchanged.
- Fleet's protected administrator configuration may resolve the dedicated
  scoped asset token; anonymous token retrieval returns401. Public registry
  does not expose that token or its Vault locator. No CF management token is
  used for asset access. Standard JSON/SSE discovery compatibility was added.
- Formal custom domain: `https://cartoon-assets-mcp.vyibc.com/mcp`.
  Exact DNS/Worker-domain absence was checked before creation. Anonymous access
  still returns401. Existing workers.dev clients continue to work. The domain
  enables same-account Worker-to-Worker discovery without broad Fleet fetch
  flags or service-binding changes; private R2 public access remains disabled.
- Fleet source change was deployed content-only and verified without changing
  existing runtime bindings/configuration. Fleet version
  `563018e3-b3e4-4840-8e03-10bddc1bb3ad`.

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


## Studio 0.3 / asset service 1.1 — 2026-09-10

- 15 Python tests: character registration, task invalidation, original cloud-job recovery, input/output changes, scoped paths, quality-state separation and Unicode SSE decoding.
- 14 asset-service tests: existing tenant isolation/rights/legacy records, additional structured filters and immutable revisions preserving media/rights.
- 11 imported character-design tests; 17 skills mirror exactly, both character profiles and frozen design component verified. No new image/voice/video generation in this software release; new-story aesthetic stability remains untested.
- Live asset MCP: 9 tools, filtered existing Investigations track; revision e6b3fe917fde432be5c95d740f5f154332268201e0cfe992ca31244252ceef34 adds hongyi association. Original b4353c01eab26bc044b52f282cc9ba31700bd0affd055f170e106f233b133239 remains unchanged; rights/object preserved. Friendly and workers.dev health200, unauthenticated401, authenticated tools/list200.
- Deployment8252f2f9-78a5-43bc-b3a6-796da3a7d6ce replaces3efc313d-89fc-4272-b374-f44c6090e0f2. The initial exact /settings comparison failed after upload; its old transient response was not retained, cause not established. Independent version-resource comparison proves bindings and script_runtime identical; only script changed. Complete code readback matched. SDK bootstrap in live prefix preserved.
- Old Python SSE splitter failed on Unicode line separators embedded in JSON strings. Bundled client now splits only real SSE LF lines/events and has regression coverage.
- Catalog remains R2 within existing authenticated scope. No D1 index, global usage sorting, principal broadening or automatic background media-health scan. Revisions can fork; retirement does not revoke old frozen selections.
- Task ledger is local orchestration evidence, not a daemon. Agent executes external work. The submission-to-ID-recording crash window is not exactly-once. Stored pass statements do not prove actual listening/viewing or user approval.
- Rollback: restore a Git commit for plugin source; restore the previous Worker code/version only after checking later deployments. Keep R2 records and authentication bindings. Re-select prior immutable asset ID rather than deleting corrections. Install updates do not prove a running client hot-reloaded.
