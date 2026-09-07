# cartoon-xiaban v0.5.0

Published using [ChangfengHU/skill-publisher](https://github.com/ChangfengHU/skill-publisher).

```bash
bash <(curl -fsSL 'https://skill.vyibc.com/install-cartoon-xiaban.sh?ts=20260907112558') codex
```

- Package: https://skill.vyibc.com/cartoon-xiaban/release/cartoon-xiaban-20260907112558.zip
- SHA256: `23e12dd029748bdaab9d54a9f146ad0c505feefb177e518c7e9e357fb321ad0f`
- Companion MCP 1.0.0: https://cartoon-assets-mcp.vyibc.com/mcp (the packaged workers.dev endpoint remains compatible)
- Composite Codex Plugin: `cartoon-video-studio` 0.1.0; see README for installation.

Skill manages creative decisions; MCP manages private assets, feedback and frozen
project selections across sessions. No CF management credential, personal voice,
private index or third-party music is distributed. The MCP requires separately
issued tenant/brand-scoped authorization. The old direct R2 script remains an
operator fallback. All existing creative quality/acting/music requirements remain.

New media <=20MB per authenticated upload; paginated keyword search, not semantic
ranking. Existing v1 data remains intact. No D1 introduced at the current scale.
No video or TTS model is installed by this release. Public installation does not
grant access to the owner's private material library.

## Historical v0.4.0 release (superseded)

## Published installer

```bash
bash <(curl -fsSL 'https://skill.vyibc.com/install-cartoon-xiaban.sh?ts=20260907105344') codex
```

Omit `codex` for the tool-selection menu. Codex installation keeps the canonical directory at `~/.codex/skills/cartoon-xiaban` and creates a symlink at `~/.agents/skills/cartoon-xiaban` for user-level discovery. The skill is available on the next turn; restart Codex if discovery has not refreshed.

Installing updates this named skill only; an existing installation is moved to a timestamped hidden backup first. An independent, conflicting discovery directory is preserved and reported before installation. The installer does not install models, replace system Node or configure cloud credentials.

- Package: https://skill.vyibc.com/cartoon-xiaban/release/cartoon-xiaban-20260907105344.zip
- SHA-256: `90d4a2a6eba5a60bfb2ec9f68ec3608b12820a6793346a7e0fe3964ba47fc2a8`
- Publisher: https://github.com/ChangfengHU/skill-publisher
- Publisher base revision: `e8a2f02c69af68ecd5b9247707d5b04b4ccb3612`
- Local publisher adjustments: required runtime upload credential, archive SHA-256 verification, recoverable named-skill backups and a single-copy Codex discovery symlink. The upstream publisher repository was not pushed or changed remotely.
- Reviewed SOP contract included; it is optional adapter metadata, not an independently deployed video-generation service.

v0.4.0 includes the v0.3.3 direction for approximately 90-second stories, richer acting, scene-driven music research and clean frames. It adds a Python-standard-library private R2 client for immutable records, feedback and project snapshots. Existing music in the library does not replace fresh music research and listening for each story.

No personal audio, reference voice cache, private behavior records, credentials, third-party tracks, model weights, fonts or actual private library indexes are in the public package. Voice candidates remain unapproved by default; a voice selection for one private project does not change the public default.

Repository: https://github.com/ChangfengHU/cartoon-video-skills

Release date: 2026-09-07. Publication uses runtime credentials from the private vault. Package download, content hashes, installation and the GitHub remote commit are verified independently; detailed scope is recorded in [VALIDATION.md](VALIDATION.md).
