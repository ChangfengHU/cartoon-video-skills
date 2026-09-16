# 新机器视频工作室安装器调研（2026-09-16）

## 结论

现有 `install-cartoon-video-studio.sh` 只完成两件事：安装 Codex 插件，并为八个远程 MCP 做 `initialize` / `tools/list` 后写入 `mcp-remote` 配置。它没有安装或验证 Node、FFmpeg、Chromium、HyperFrames、中文字体，也没有渲染一次 MP4；因此不能称为“新机器安装即可制作抖音视频”。

建议把安装器变成**可恢复的分阶段 bootstrap**，但不把系统包、浏览器登录、付费模型和用户凭据静默塞进机器：

1. `--dry-run` 只显示计划和缺口，不写配置、不下载二进制。
2. 默认安装用户目录下的可锁定 Node 22、项目本地 HyperFrames 及 Chromium；系统依赖以明确开关执行，不能无提示调用 `sudo` 或改动既有登录浏览器。
3. 每个 MCP 先实际探测，再做 keyed、原子、幂等的配置合并；同名但不同配置先备份并报告差异，自动保留已有非工作室服务器。
4. `studio doctor --json` 输出机器可执行的能力矩阵；安装结束只跑无账号、无付费、无上传的 3 秒本地合成与 MP4 验证。
5. 远端账户类能力单列为 `ready` / `needs_login` / `unreachable`，不以 `tools/list` 冒充可用。安装结果落到不含 token 的 receipt，供 Agent 先读 receipt/doctor 再开片。

这保留当前插件、资产 MCP 与 HyperFrames 的职责边界。没有导入任何下列仓库代码，也没有安装、启用付费服务或触碰系统浏览器。

## 当前安装器的实际检查

本次读取了发布端当前脚本 `https://skill.vyibc.com/cartoon-video-studio/release/install-cartoon-video-studio.sh`：

| 已做 | 未做 / 风险 |
| --- | --- |
| `codex plugin marketplace add`、`codex plugin add` | 不验证插件的技能镜像是否可加载，也不固定 marketplace revision。 |
| 八个 bridge 端点的 `initialize` 与 `tools/list` | 不调用任何业务工具，不能证明抖音账号、音色授权、生图浏览器或资产读取可用。 |
| `codex mcp add ... npx -y mcp-remote` | 同名条目直接失败；没有读取-比较-原子替换、备份、过期 token 更新或 post-write 验证。 |
| shell 结束时 `unset BOOTSTRAP_TOKEN` | `mcp-remote` 的启动参数仍带 bridge token；脚本本身也没有把它写进 Vault。应缩小本地配置可读范围，并不得在日志、receipt 或报错中打印 token。 |
| 30 天有效期提示 | 无到期时间、续期提示或 safe refresh，重新执行会因同名配置失败。 |

本仓库已有只读 `skills/cartoon-video-studio/scripts/doctor.py` 与 `references/runtime.md`，可检测 Node、FFmpeg、Python、HyperFrames、浏览器路径，但当前安装器未调用它；其 `launch_verified` 仍是 `false`，还不能证明 Chromium 真能启动。README 已如实说明运行时不随包捆绑。

## 外部候选核查

### Playwright：可锁定的 Chromium 获取和实际启动检查

- 仓库：[microsoft/playwright](https://github.com/microsoft/playwright)，核对 commit `18205280b6112a4a08238195942c4fa30c199a62`（2026-09-16）；公开、未归档、Apache-2.0。已读取 [browser-chromium package](https://github.com/microsoft/playwright/blob/18205280b6112a4a08238195942c4fa30c199a62/packages/playwright-browser-chromium/package.json)，其 package 以安装脚本获取 Chromium，要求 Node >=20，许可证字段为 Apache-2.0。
- 官方 CLI 文档明确有 `playwright install chromium`、`install --with-deps`、`install-deps --dry-run`；后两项涉及系统依赖，不能放入无确认的默认路径。
- 借鉴：以锁定的 Playwright 版本将浏览器落在工作室控制目录，记录实际 executable path；doctor 用一次受超时限制的无 profile `--headless --version` 或 Playwright `chromium.launch()` 证明可启动。安装前先 run `install-deps --dry-run`，将缺少的 Linux 库清晰列出。
- 不采用：不把 Playwright 作为视频渲染器，也不使用它操控、复制或改写用户已登录浏览器 profile；HyperFrames 仍负责渲染。

### kajisho5/ffmpeg-skill：能力化 doctor 与 release smoke 语义

- 仓库：[kajisho5/ffmpeg-skill](https://github.com/kajisho5/ffmpeg-skill)，核对 commit `cecf37ca8194a83bacf5a564700112f73656c26d`（2026-09-16）；公开、未归档、MIT。已读 README、LICENSE 和其 `doctor` / `release-check` 说明。
- README 的源码/测试说明显示：`doctor --json` 将特性分为 `available`、`missing`、`unknown`，按单工具给出可用性与修复建议；`release-check` 在临时目录安装后执行 contract、doctor、测试。其 CI 覆盖多个 FFmpeg 版本和三个 OS。要求 FFmpeg 5+、Python 3.9+，并明确按实际编码器和滤镜而不是版本号判断。
- 借鉴：工作室 doctor 也返回稳定 JSON schema，分别报告 `required`、`optional`、`unknown`，例如 Node major、FFmpeg `libx264/aac/drawtext`、中文字体可解析、HyperFrames CLI、Chromium launch、可写工作目录与磁盘空间。3 秒 smoke 必须实际生成一个临时 1080×1920、30fps、含中文字符与 1 秒音频的 MP4，并用 `ffprobe` 回读编码、时长、帧率和分辨率。
- 不采用：不复制其 Python/FFmpeg 工具，也不把其 `subtitles` 等所有滤镜作为工作室的硬性前置条件；能力清单应由 HyperFrames 实际需要的版本锁定义。

### Yaw MCP：配置合并与冲突处理的产品模式（仅参考，不可复用代码）

- 仓库：[YawLabs/mcp](https://github.com/YawLabs/mcp)，核对 commit `1af6a19f617604b7d0611be4501257eddb2ec28b`（2026-09-16）；未归档、近期有提交。已读 `src/install-cmd.ts`、`src/client-config*.ts` 路径、测试目录及 `package.json`。
- `install-cmd.ts` 的源码注释明确列出期望语义：保留同容器的其他 MCP 条目；既有正确条目 no-op；不同条目在 TTY 提示、非 TTY 拒绝；提供 `--repair`（保留已有 string env）、`--force`、`--skip`、`--dry-run`；读写之间作 fingerprint 检查并用 atomic write，避免覆盖并发修改；dry-run 不打印完整配置以免泄露 sibling secrets。README 也说明 `--json` 的稳定结果字段和 `--list` 只读检查。
- 该仓库是 **Yaw MCP Source-Available License 1.0**，不是开源许可证；许可证禁止将该软件或衍生品作为竞争 MCP 管理产品提供给第三方。因此只借鉴可观察的交互/安全设计，不复制其代码、包或配置实现。

## 融合设计

### 命令与阶段

```text
install-cartoon-video-studio.sh [--bootstrap-token ...] [--runtime auto|check|skip]
  0. 解析参数、检查 OS/arch、生成不含密钥的 receipt 路径
  1. 安装/更新插件到已固定的 release revision，校验 manifest 与镜像 hash
  2. runtime ensure：Node 22、项目依赖锁、HyperFrames、FFmpeg、字体、Chromium
  3. bridge ensure：MCP initialize → tools/list → keyed config merge → post-write probe
  4. doctor --json：本地 runtime + 远端服务 capability 状态
  5. smoke：临时目录 3 秒无外部素材 HyperFrames render → ffprobe 回读 → 清理
  6. 输出 receipt：版本、检测时间、工具版本、browser path、MCP tool counts、状态和修复命令
```

`--runtime=auto` 只能下载/写用户可控目录；当系统级 FFmpeg、字体或 Linux 共享库缺失时，输出 exact recovery command 并返回非零 `needs_system_dependency`。`--runtime=check` 绝不写；`--runtime=skip` 仅供已有受管环境，仍须执行 doctor 和 smoke。任何失败都保留原有 MCP 配置，且返回阶段名、结构化 error code 与下一步。

### MCP 幂等更新契约

1. 解析目标客户端当前配置；配置无效时拒绝写入，报告文件和行列，不尝试“修复”用户 JSON。
2. 仅对八个本插件归属 key 比较标准化条目。完全一致即 no-op；同名不同内容时，保存 owner-only 备份、输出 redacted diff，并由 `--repair` 明确更新。绝不能删除不属于插件的条目。
3. 通过临时文件、文件权限和 rename 写入；写入前重新读取 fingerprint，变化则拒绝并提示重试。
4. 工具探测应在写前及写后各一次，核对端点、tool count 和需要的基础工具名；业务 read-only call 只对不消耗额度的端点执行。
5. token 只经 stdin 或短生命周期环境变量传递；不得拼进持久 receipt、shell history、stdout/stderr 或 Git。配置文件权限应为 owner-only；token 仍需依赖 bridge 到期机制，receipt 只存 `expires_at`。

### 可执行的 smoke 边界

烟测只使用安装器创建的临时目录和生成的纯色/文本/静音或合成音，不读取任何个人 profile、项目目录、平台内容、Vault、远端 TTS/生图或发布账号。成功条件是实际输出 MP4 并由 `ffprobe` 读回：H.264 视频、AAC 音频、1080×1920、30fps、约 3 秒、中文 glyph 可见。渲染后删除临时项目和 MP4，仅保留不含媒体内容的 receipt。

这证明基础渲染链路，不证明人物一致、剧情、配音效果、平台登录或成片审美；后者应由正式工作流及 `studio-quality` 实际检查。

## 采用顺序与未验证项

优先实施：1) locked runtime manifest + doctor JSON，2) MCP 配置的 read/compare/atomic update，3) 3 秒 smoke / ffprobe，4) receipt 与 refresh。Chromium system deps 和跨 OS 包管理器放第二批，因为 ARM Linux、macOS、Windows 的 install privilege、包名和浏览器可用性不同，必须分别验证。

尚未验证：安装器实际运行在全新 ARM Linux/macOS/Windows 的结果；所选 Node/HyperFrames/Playwright 的最终版本与下载大小；各系统包 manager 可用性和组织安全策略；MCP bridge token 的可续期接口及过期时间字段；Codex CLI 对重复 `mcp add` 的官方覆盖语义；端到端 3 秒 HyperFrames render。这些是实施与验收项，不能因本调研而宣称已具备。
