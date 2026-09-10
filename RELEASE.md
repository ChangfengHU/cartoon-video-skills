# 0.3.0 — 2026-09-10

新增独立角色设计集成、编导/配乐/质检skill、镜头级恢复账本和人物档案；资产MCP1.1增加结构化过滤与追加修订。插件17skills、4MCP；未自动安装CLI/模型或授予账号。

验证：13个Python测试、14个资产服务测试、11个角色设计测试通过；素材哈希与插件镜像校验通过。单元测试不证明新故事创作品质，多角色新图和下一部成片仍需实际验收。部署读回证据单独记载，不能用本文件代替线上验收。

# cartoon-video-studio 0.2.0 — 多角色工作室

保留插件ID，升级中文名为卡通视频工作室。包含13个skills、2个独立角色和4个HTTP MCP声明；新增形象注册、品牌隔离、共用HyperFrames指令、运行环境检查和发布规范。安装命令及授权方式见README。

本版不更新旧的独立cartoon-xiaban ZIP安装器；那个安装器仍为0.5.0单角色发布。新工作室从GitHub插件安装，不能将两种发布渠道混为同一版本。HyperFrames二进制和服务授权不捆绑。

验证：插件manifest校验、426个共享文件哈希、canonical/plugin镜像、角色注册成功/冲突/坏哈希/越界路径检查。桌面客户端重新安装及新角色实际生图成片不在本版验证范围；Fleet上线证据另见发布记录。

---

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
