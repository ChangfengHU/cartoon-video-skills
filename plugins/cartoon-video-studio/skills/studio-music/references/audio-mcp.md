# 共用背景音乐与音效 MCP

服务 ID 是 `auto-parse-audio`，远程 Streamable HTTP 地址为 https://auto-parse-audio.2513120790.workers.dev/mcp 。本插件复用已有服务，不创建另一套音频库；它负责 BGM/音效检索、候选生成、标签、验收及复用，不提供 TTS、对口型、混音或视频渲染。

## 连接与适用范围

需要获取或补充 BGM、环境声、动作音效时使用。用户已提供合格音轨、仅改画面或只做本地混音时，不强制访问服务。先核对宿主实际工具列表；工具名前缀由客户端决定，以下为服务原始名称。安装包有依赖不等于已连接授权，ChatGPT 原有 `vyibc-flow` 云连接也不会自动获得这个独立 MCP。

缺连接时从 https://fleet.vyibc.com/#/hub?view=capabilities 搜索 `auto-parse-audio`，使用「安装与配置」的服务专用 Token。复用已有身份，不用 CF Token、金库管理员 Token，也不把密钥写进项目、提示词或公开包。连接失败只影响远程音频阶段；保留原有授权素材、Commons 检索及本地后期路线，明确说明实际使用哪条，不假装已查询云库。

## 素材流程

1. `audio_capabilities({})`：读取当前来源、模型和预算。不能因目录列有模型就假设启用；MiniMax、独立音效生成和原始文件直连均以实际状态为准。
2. `audio_library({q:"场景、情绪或标签",kind:"music",status:"approved"})`；音效/环境声用 `kind:"sound_effect"`。先复用合适的已验收素材，再扩大关键词或翻页，不重建已有条目。`audio_get_asset({id})` 核对真实时长、hash、来源、授权、有人声/循环等信息；标签不是听审证据。
3. 库内没有合适内容时，`audio_search({q,kind,provider:"openverse"})` 或 `provider:"wikimedia"`。核实来源及本次用途许可后才能 `audio_import({requestId,provider,sourceId,kind,tags,rightsAcknowledged:true})`。这是候选入库，不等于认可；聚合试听版不能称原始 WAV。不能向 import 传任意下载 URL。
4. 仍无合适素材时才考虑付费兜底：先 `audio_quote({model,prompt,title,seconds,tags})`，说明价格上限、用途及限制。得到用户费用确认后，`audio_generate` 使用相同参数，并提供稳定 UUID `requestId`、`confirmPaid:true`、`maxCostUsd`。本工作室音乐请求为 3–120 秒；需要更长音乐先检查实际能力，不伪造参数。无人声音乐不保证无缝循环。
5. 保存原任务 ID，用 `audio_jobs({id})` 查询。超时或 `needs_review` 保留原请求，核对结果，不换 ID 再扣费。`completed` 只代表候选保存成功。
6. 实际试听并核实本次用途授权；没有用户或已有明确人工验收证据时保持 candidate，不代替用户勾选认可。确认后才 `audio_review_asset({id,decision:"approved",qualityConfirmed:true,rightsConfirmed:true})`。用 `audio_update_asset` 补用途/情绪/标签；该接口会写入整组字段，先读取并保留已有字段，未知 BPM/人声/循环不编造。
7. 实际采用已验收素材时，`audio_use_asset({id,requestId,purpose})`，同一次使用保留原 UUID。记录服务 assetId、任务/使用 requestId、hash、许可、署名、标签及冻结到本工程的文件路径。新服务 ID 与原共享素材 MCP 的 ID 分开标记，不迁移或覆盖旧记录。

## 交给后期

媒体路径受 Bearer 鉴权，不是公开 R2 链接。通过宿主受保护的凭据配置下载原响应字节，完整校验 SHA256/大小并用 ffprobe 核对；没有安全下载通道则报告缺项，不能把私有 URL 直接塞进公开 HTML/播放器，也不能公开服务 Token 或原音频库。保存的音频仍受当前用途/供应商许可约束，人工 approved 不授予转售、公开素材分发或视频发布权。

本片 AUDIO.json/素材账本引用核验后的本地文件和来源记录，再交已有后期工具处理裁切、循环接缝、对白避让和混音。实际听审、技术检测、资产批准和最终影片发布分别判断。现有工程的冻结文件/hash 不因目录更新而替换；缺文件才补对应音频。
