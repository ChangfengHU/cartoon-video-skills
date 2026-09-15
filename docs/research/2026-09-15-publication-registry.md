# 发布登记：开源实现核对

检索日期：2026-09-14（工作区当前日期；目录名沿用主任务）。独立 subagent 负责公开资料与源码审阅；未读取本地凭据、未安装候选、未部署、未调用真实平台发布。先调用网页研究工具发现官方仓库/文档，再通过 GitHub API 固定默认分支 commit，通过 raw.githubusercontent.com 核对源码。以下不复制候选代码。

## 结论

采用设计借鉴，不引入完整产品依赖：将“已发布事实”与“Fleet 登记完成”分开，失败后只重放登记。Postiz 的补 release ID 接口最贴近本需求；Mixpost 的作品/账号关联表提示平台结果应按账号保存。两者均不能凭本次源码观察证明远端发视频与本地数据库之间具有 exactly-once 保障。

## 1. Postiz

- 真实仓库：[gitroomhq/postiz-app](https://github.com/gitroomhq/postiz-app)。固定审阅 commit：[3cbe20b86bf3b2243843d51bb63dcec8773babf7](https://github.com/gitroomhq/postiz-app/commit/3cbe20b86bf3b2243843d51bb63dcec8773babf7)，GitHub API 返回提交时间 `2026-09-12T08:00:18Z`，为近期维护证据，不等于稳定性认证。
- 许可证原文为 [GNU AGPL v3](https://github.com/gitroomhq/postiz-app/blob/3cbe20b86bf3b2243843d51bb63dcec8773babf7/LICENSE)。本次仅研究设计，不复制实现。后续若采用代码须单独评估义务并保留许可/署名。
- 源码观察：[posts.repository.ts L387-L410](https://github.com/gitroomhq/postiz-app/blob/3cbe20b86bf3b2243843d51bb63dcec8773babf7/libraries/nestjs-libraries/src/database/prisma/posts/posts.repository.ts#L387) 的 `updatePost` 一次写入 `PUBLISHED`、`releaseId`、`releaseURL`；`updateReleaseId` 限定组织与 `releaseId='missing'` 后补 ID，不调用平台发布。它是受状态约束的补写；重复同一补写可能不再匹配，不能直接称为返回一致结果的幂等 API。
- 源码观察：[posts.service.ts L877 起](https://github.com/gitroomhq/postiz-app/blob/3cbe20b86bf3b2243843d51bb63dcec8773babf7/libraries/nestjs-libraries/src/database/prisma/posts/posts.service.ts#L877) 有 `guardAgainstRepublish`，针对已发布对象要求显式 republish 或走 update。其 Temporal workflow ID 与终止策略并不单独证明平台不会重复发帖。
- 数据结构：[schema.prisma L398 起](https://github.com/gitroomhq/postiz-app/blob/3cbe20b86bf3b2243843d51bb63dcec8773babf7/libraries/nestjs-libraries/src/database/prisma/schema.prisma#L398) 关联组织、integration、tags 并保存平台 ID/URL；所阅 Post 模型无 `(integrationId, releaseId)` 唯一约束，因此本地登记仍需自建业务唯一键。
- 文档宣称：[Update Release ID](https://docs.postiz.com/public-api/posts/update-release-id) 用于连接已经发布但 ID 缺失的内容。与上述源码方向一致；未实际调用该 API。
- 环境/依赖：[package.json](https://github.com/gitroomhq/postiz-app/blob/3cbe20b86bf3b2243843d51bb63dcec8773babf7/package.json) 声明 Node `>=22.12.0 <23.0.0`、pnpm `10.6.1`，包含 Nest/Next/Temporal；Volta 又写 Node 20.17.0，存在配置差异待运行验证。[Docker Compose](https://github.com/gitroomhq/postiz-app/blob/3cbe20b86bf3b2243843d51bb63dcec8773babf7/docker-compose.yaml) 包含 PostgreSQL、Redis、Temporal 等服务，并列出平台 OAuth/API 配置项。适合服务器/容器部署；未在本工作区验证。自托管不代表平台 API 或可选 AI 服务免费；收费与审批条件未逐平台核对。

## 2. Mixpost

- 真实仓库：[inovector/mixpost](https://github.com/inovector/mixpost)。固定审阅 commit：[df57648b866310446703f5294350552b62735df5](https://github.com/inovector/mixpost/commit/df57648b866310446703f5294350552b62735df5)，GitHub API 返回 `2026-03-16T10:06:37Z`。该时间只证明此默认分支最新提交，不推断其他商业版本维护情况。
- 许可证：[MIT](https://github.com/inovector/mixpost/blob/df57648b866310446703f5294350552b62735df5/LICENSE.md)，版权 Dima Botezatu / Inovector；若未来复制代码需保留许可证与版权。本次无代码采用。
- 源码观察：[AccountPublishPost.php](https://github.com/inovector/mixpost/blob/df57648b866310446703f5294350552b62735df5/src/Actions/AccountPublishPost.php) 先请求 provider，成功后 `insertProviderData`。[Post.php L156 起](https://github.com/inovector/mixpost/blob/df57648b866310446703f5294350552b62735df5/src/Models/Post.php#L156) 在账号关联表写 provider ID、响应 data 并清 errors。远端成功与这次数据库写入之间存在失败窗口；所阅代码没有展示跨这两个系统的原子提交。
- 源码观察：[AccountPublishPostJob.php](https://github.com/inovector/mixpost/blob/df57648b866310446703f5294350552b62735df5/src/Jobs/AccountPublishPostJob.php) 跳过已进入 history 的作品、检查账号授权并对限流 release 重试；[PublishPost.php](https://github.com/inovector/mixpost/blob/df57648b866310446703f5294350552b62735df5/src/Actions/PublishPost.php) 通过 processing 状态避免常规重复调度，再批量执行账号任务。未见这些路径在每次平台调用前按已保存 provider ID 去重，不能把队列重试直接作为本需求的“仅补登记”。
- 环境/依赖：[composer.json](https://github.com/inovector/mixpost/blob/df57648b866310446703f5294350552b62735df5/composer.json) 要求 PHP ^8.2、Laravel contracts 10/11/12、Horizon、Guzzle、php-ffmpeg 等，属于 PHP/Laravel 服务器生态。账号授权检查为源码事实；所有平台 OAuth 配置、FFmpeg 系统安装、商业套餐与平台收费范围未在本次验证。

## 与本地需求的差异及融合建议

本地能力盘点由主 agent 执行，本报告不声称已审阅 Fleet 私有源码。按主任务给出的现有边界，本地已有工作室/角色/任务能力，要补的是发布结果登记与关联，而候选产品主责是管理社媒账号与执行发布；均未在上述源码中提供 Fleet 角色注册表和 task ID 对应能力。

| 需求 | 候选证据 | 本地融合决策 |
| --- | --- | --- |
| 已发布作品查询 | Postiz 保存状态、平台 ID、URL | 本地保存真实发布回执与来源；登记状态单列 |
| 角色及任务关联 | Postiz tags / Mixpost 账号 pivot，只是相近关系模式 | 使用本地稳定 character ID / task ID 外键或验证，支持多角色 |
| 登记失败恢复 | Postiz 有补 ID API；Mixpost 普通 queue retry 会进入发布逻辑 | 单独 registry-only 重放入口，禁止该入口调用发布器 |
| 重复回执去重 | 所阅实现不足以证明完整业务去重 | 用平台+账号+平台作品 ID 唯一键；无 ID 时要求稳定 receipt/job ID，不能用标题猜 |
| 集成成本 | 两套完整服务端/队列生态 | 不安装；只借鉴状态拆分和关联数据结构 |

建议先将成功发布回执持久化，再做 Fleet 登记与角色/任务关联；失败保存待登记记录，恢复时只重放登记。同一唯一键+相同事实返回已存在；事实冲突明确报错，禁止覆盖成另一视频。任务完成与发布登记可独立重试，避免登记错误触发整段“上传→发布”重跑。对平台响应丢失、结果不明的场景，记录 unknown 并做查询/人工核实，不能假设未发成功。

未验证项：候选项目未本地运行；未演练其并发、数据库故障、平台超时或 worker 崩溃；未核对所有 provider 的幂等能力；未验证所有角色/任务绑定的本地服务约束。主 agent 应以本地实现测试证明重复登记、冲突拒绝、角色/任务关联和登记失败后重试不调用发布动作。
