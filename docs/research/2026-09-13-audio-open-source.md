# 音乐与音效能力开源对比

日期：2026-09-13。用户要求在方案设计时独立委派 subagent 检索开源实现。本轮已实际委派 `audio_open_source_research`，主 agent 同时检查本地 studio-music 和额外候选。

## 当前能力与问题

现有 studio-music 已规定按剧情规划、抖音线索查询、许可记录、A/B 试听、最终音乐连续性和资产登记。缺口主要在可验证的多源获取适配器、统一试听产物和流程执行证据，不能再靠新增文字规则宣称质量稳定。已有 HyperFrames 音频处理和资产 MCP 应继续复用。

## 候选比较

| 候选 | 核查证据 | 可借鉴部分 | 限制与决定 |
| --- | --- | --- | --- |
| [MaksPyn/freesound-skill](https://github.com/MaksPyn/freesound-skill) | README、MIT 标记和 scripts/freesound.js 源码 | Node CLI，搜索过滤、详情、试听与原件分别下载、归属记录、原件校验 | 最先评估的 Freesound 适配候选。预览与原件授权不同；需凭据及 API 使用条件验证。未运行 |
| [timjrobinson/FreesoundMCPServer](https://github.com/timjrobinson/FreesoundMCPServer) | subagent 阅读 README/实现，MIT | 现成 MCP 搜索和音频元数据接口 | OAuth 原件下载未实现，不当成全链路下载方案 |
| [JimCline/game-audio-kit](https://github.com/JimCline/game-audio-kit) | MIT；subagent 检查 build_audition.py，项目自称实验 POC | manifest 驱动的可播放 A/B HTML 与选择记录 | 优先借鉴试听交互；源码有转单声道、未统一响度、缺失文件跳过等行为。我们应保留声道、同对白同响度比较、缺失显式失败。GPU 生成与新付费服务不接入 |
| [sonilo-ai/skills](https://github.com/sonilo-ai/skills) | 官方仓库，MIT；subagent 阅读 sfx-prompting | 音效按画面材质、动作和事件节点设计；音乐/音效/ducking 分工 | 借鉴方法；依赖 Sonilo 服务，开源 skill 不代表服务免费或已获授权，不自动启用 |
| [kajisho5/ffmpeg-skill](https://github.com/kajisho5/ffmpeg-skill) | 仓库 README 和 MIT 信息 | 结构化 FFmpeg 参数、错误结果和验证路径 | 与 HyperFrames/audio 现有职责重叠，参考接口与检测方式，不整体替换 |

这些仓库的许可证指代码，不代替音频文件或第三方服务的许可。引用时依据的是本次读取的在线默认分支；尚未导入代码，因此未冻结供应链版本。实际采用前必须固定 commit 并保存 LICENSE。

## 融合后的实施方案

1. 继续用 studio-music 组织剧情需求、候选比较与实际成片听审；独立平台 MCP 提供抖音线索。
2. 搜索层优先评估现成 Freesound CLI/MCP，统一为 source adapter。Mixkit/Incompetech/Pixabay 的自动访问方式分别验证，不能先宣布全都接通。
3. list_sources 分别报告 search、preview、original_download、auth、availability；get_audio_detail 区分素材许可、API 使用条件和允许归档范围。原件不可用不能悄悄用试听压缩版代替。
4. prepare_audition 借鉴 game-audio-kit 生成对比页面，加同画面/同对白、响度匹配、原声道保留、hash、来源和试听片段边界。页面生成成功不等于有人已试听。
5. 音效 cue 至少包含动作、材质、接触时间、强度和空间位置；按可见动作触发，不能按均匀时间切段或用一串提示音替代表演。
6. 导入和标签更新复用资产 MCP 与 R2/D1；新增音频字段而非另建冲突素材库。下载执行需有大小限制、超时和幂等标识；未知结果不盲目重试。
7. 混音与分析复用 FFmpeg/HyperFrames 执行环境，新增结构化检查产物；技术通过与主观听审状态分开。

## 首个验证切片

先用已有合法本地音乐和音效验证 A/B 页面、对白混合、缺失素材报错及资产记录，再验证一个远程来源的搜索→试听→原件→归档闭环。这样能分别定位素材源授权问题和本地工具质量问题。后续再扩展来源。

## 实际检查范围与未验证项

- 完成：本地 skill 阅读；GitHub 搜索；上述候选的文档/部分关键源码检查；主 agent 与 subagent 结果融合；AGENTS 规则落盘。
- 未完成：第三方仓库安装或运行、凭据配置、商业 API 授权核验、远程素材下载、A/B 真实听审、性能/安全完整审计、新 MCP 开发及 Fleet 发布。
- 本记录是设计依据，不是已接入能力清单。没有安装模型、调用新付费服务或变更现有成片。
