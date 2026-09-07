# 会成长的私有素材库

v0.5 首选 **`vyibc-cartoon-assets` MCP 管素材，Skill 管创作**。MCP 服务绑定私有 R2，读取旧 v1 记录，新增内容写 v2，不依赖某个 agent 的聊天历史。当前规模直接分页查询不可变记录即可，尚未引入 D1；以后可加可重建索引，不必改创作流程。服务器不自动搜歌、试听、判断授权或生成视频。

## MCP 操作顺序

1. `library_info` 核验账号/品牌和读写范围。配置不正确就报告，不能拿另一个用户或另一个品牌的库凑数。
2. `asset_search` 按 kind/query 查库。**每页即使没有命中也继续 next_cursor，直到 null**；这是分页关键字匹配，不是向量推荐。用 `asset_get` 看详情，`asset_feedback_list` 分页看历史反馈（含 v1）。
3. 来源不明的歌只用 `asset_register` 登记来源卡。实际文件用下面的 `upload`，通过私有鉴权上传；不把音频 base64 塞进上下文。MCP 不接受任意 R2 key 或其他 owner 参数，也不会根据一个 URL 自动抓取文件。
4. 对本片做新配乐研究、试听与权利核验后，使用 `freeze`：服务端 `project_freeze` 保存不可变作品选择，客户端下载并逐一验 SHA256，写 `ASSET_LIBRARY_LOCK.json`。只有该命令成功才能说“素材已下载并冻结”；仅 MCP 返回项目 ID 不表示本地文件已经准备好。新会话可用 `project_get` 找回选择。
5. 用 `asset_feedback` 追加使用、拒绝、失败或准确归属的用户反馈。不能把“这片不错”拆成所有素材逐一通过。新故事每次仍主动查新配乐。

接口客户端仅需 Python 3.9+ 标准库，支持 macOS / Linux ARM / Linux AMD；这不表示所有 TTS 模型或渲染引擎都跨架构通用。

```bash
python3 <skill>/scripts/asset_mcp.py call library_info
python3 <skill>/scripts/asset_mcp.py call asset_search --input <query.json>
python3 <skill>/scripts/asset_mcp.py upload --card <card.json> --file <已授权本地素材.wav>
python3 <skill>/scripts/asset_mcp.py download --id <asset-id> --output <新的本地文件路径>
python3 <skill>/scripts/asset_mcp.py freeze --selection <selection.json> --output <新的素材快照目录>
```

来源卡、反馈和选择格式沿用本文下方示例。新上传单文件上限20MB；旧库媒体仍可通过鉴权下载，客户端限制300MB。新同内容文件与相同来源卡自动去重；修改语义会得到新版本，使用 `supersedes` 指向旧卡。服务器用 R2 条件写拒绝覆盖，文件和卡不是跨对象事务：中断可能留下未引用文件，不会把它伪报成成功注册。

## 安装授权与降级

公开 endpoint：`https://cartoon-assets-mcp.2513120790.workers.dev/mcp`；**无凭据无法读取素材**。私有运行环境注入 `CARTOON_ASSETS_TOKEN`，或运行 `asset_mcp.py configure` 在隐藏提示中输入专用 token，保存在当前用户 `~/.config/vyibc-cartoon-assets/credentials.json`（0600）。凭据只访问指定品牌素材，不含 Cloudflare 管理权限。不要把凭据复制到公共 Skill、Plugin、发布记录或作品。环境可选 `CARTOON_ASSETS_MCP_URL`；不跟随跨站重定向。

原生 HTTP MCP 可用 URL + Bearer 环境变量；组合 Codex Plugin 自带 `asset_mcp.py stdio` 转接器，读取相同专用凭据。两种接法选一种，避免同一 MCP 重复出现。仓库提供 `install-asset-mcp.py`，只添加本服务配置，不覆盖其他 MCP、会话或全局规则。凭据丢失需由授权管理员重新提供，公共安装包不会自动领取主人私有库权限。

没有 MCP 时，保存本片本地候选与反馈并明确“尚未云端入库”。已获 R2 管理授权的维护人员可使用下述旧 `asset_library.py` 直接维护 v1；它不是给普通创作 agent 的默认接法。不要为了素材查询临时索取 CF 管理密钥。MCP 存素材与反馈，不会自动改写 skill；只有经过用户认可/评测的经验才提交有版本的 Skill 更新。

以下是沿用的创作规则、v1数据格式与维护工具说明。

## 每片的循环

1. 先写剧情、情绪曲线和 `MUSIC_PLAN.json`，包括有意静音处。按剧情关键词查库，查看适用场景、过去的失败理由、批准状态和听过的区间。
2. **库里有歌也继续主动检索新 BGM 候选**。使用当次可用的浏览器/公开曲库，记录查询、日期、真实来源 URL 和新候选；未找到也记录原因。不能把“搜过旧索引”算成新音乐研究，不能总因已有文件而复用上次的曲子。
3. 按本片发布平台和用途重新核验许可，试听有差异的候选、比较无 BGM/A/B，依剧情选择。库内授权结论不自动适用于新平台、商业用途或素材再分发；元数据排序不等于听过。来源卡未知时保留原站链接，**不上传音轨**。
4. 选定文件下载到本片目录，校验 SHA256，冻结 `ASSET_LIBRARY_LOCK.json`；按真实音频排时间。角色/声线候选不自动成为默认。`plan_music.py` 仍只排序已核验的本地候选。
5. 使用后追加反馈：片名/项目、镜头与作用、试听范围、结果、评论者、观察时间、失败理由或下一次适用条件。用户说“这版可以”可记录对该成片的反馈，不能拆成对所有素材和默认声线的逐项认可。

## v1 维护脚本权限和保存范围

运行环境注入 `CF_ACCOUNT_ID`、`CF_API_TOKEN` 和 `R2_BUCKET`；只有已授权建库时运行 `init`。不要把真实凭据写进命令参数、文件、公共包或日志。可用 `--auth-prompt` 在 TTY 隐藏读入 `{ "accountId": "…", "apiToken": "…" }`，也接受含 `forwarding` 的配置对象。脚本不会读取金库、创建令牌或扩权。已有令牌无权限时准确报告，不改用公共交付桶。

私有桶 `r2.dev` 必须关闭且不能有自定义域名，脚本在写入与下载前检查；不修改已有桶的公开设置。这个检查覆盖 R2 原生公开域名，**不能证明没有其他已配置 Worker 代理**，因此专用新桶不要再绑定公开 Worker。公开 CDN 只接收用户要公开交付的成片。R2 不是声线模型，也不隐含声音授权。

允许入库：有归档授权的生成图、原创算法音效、明确是服务商预置声线的合成片段。只入元数据：来源/权利未确认的曲目、公开参考成片。真人参考、本人克隆缓存、模型权重、账号会话和私人行为历史不属于本流程；本人声音另有明确归档授权后才扩展接口。当前脚本会拒绝 `personal_reference:true`、`voice_identity:user_clone`。公共 skill 不携带库里的私有文件或索引。

## 数据和并发

对象布局：

```text
xiaban/v1/records/<uuid>-<json-sha256>.json
xiaban/v1/feedback/<uuid>-<json-sha256>.json
xiaban/v1/blobs/<uuid>/<file-sha256>.<ext>
xiaban/v1/indexes/<uuid>-<json-sha256>.json
```

每次导入、反馈与索引快照都用独立 UUID+SHA256 对象，不覆盖历史。`records/` 和 `feedback/` 是事实来源，`index` 分页重建 JSON 视图；没有会被两个任务互相覆盖的共享 `index.json` 或 `latest`。索引是采集时点的快照，不是跨所有对象的事务快照；并发写入后重新运行 `index` 可纳入新记录。反馈如果引用本次尚未列出的新记录会报错，刷新即可。命名中的哈希会在读取时校验。

上传前检查对象不存在，上传后读回验证 SHA256。REST 没有在这里使用已证实的 CAS/条件写，因此检查并非原子锁；依赖随机唯一键避免正常并发碰撞，不承诺防御拥有直写权限的人改动对象。两次主动导入同一素材会生成两条记录，调用者先查库避免重复。一次失败可能留下尚未引用的完整 blob；不自动删除，不伪报回滚。原文件不被覆盖；下载拒绝符号链接、目录越界和已有路径。每个文件上限 300 MB。

## 可执行用法

以下命令中的路径由当前作品目录提供；环境里的凭据只用于本次操作。

```bash
python3 <skill>/scripts/asset_library.py verify-private
python3 <skill>/scripts/asset_library.py index --output <新的私有index.json>
python3 <skill>/scripts/asset_library.py search --index <index.json> --kind sfx --query "通知"
python3 <skill>/scripts/asset_library.py add --card <card.json> --asset-root <作品目录> --file assets/sfx/notification.wav
python3 <skill>/scripts/asset_library.py add --card <只有来源卡的card.json>
python3 <skill>/scripts/asset_library.py feedback --input <feedback.json>
python3 <skill>/scripts/asset_library.py freeze --selection <selection.json> --output <新的本片素材快照目录>
python3 <skill>/scripts/asset_library.py index --output <新的index.json> --publish
```

`add` 来源卡最小示例（根据实际证据填写，不能原样当授权）：

```json
{
  "schema_version": 1,
  "kind": "sfx",
  "title": "原创通知声",
  "source_type": "original_algorithm",
  "source_url": "project://episode-identifier/mix_audio.py",
  "tags": ["通知", "轻巧"],
  "use_cases": ["消息弹出时单次点声"],
  "review_status": "candidate_not_individually_approved",
  "audition": {"status": "not_listened", "ranges": []},
  "license": {
    "status": "user_authorized_generated",
    "scope": "本用户私有素材库保存；新片仍需核对用途",
    "evidence": "本任务用户授权与原创算法来源记录",
    "archive_allowed": true
  }
}
```

`kind` 为 image/sfx/voice/bgm/reference。来源卡可增加作者、实际时长、生成器与参数、许可 URL、署名位置、失败原因及测得的数据；未测 BPM 不填。`license.status: unknown` 配合 `archive_allowed:false` 只能保存来源卡。voice 文件还须 `voice_identity:provider_preset`。文件哈希、大小与 R2 key 由脚本计算，不信任手填。若要纠正旧卡，新增一条带 `supersedes` 的记录并保留旧记录；当前检索会显示两条，由编辑者判断。

反馈格式：`asset_id`（add 返回的完整 id）、`project`、`outcome`（used/rejected/user_approved/user_disliked/technical_failure）、`reason`、`reviewer`（用户或编辑者，准确归属）、`observed_at`；可加 scene、audition_range、failure_reason。反馈独立保存，不篡改旧卡的批准状态。

冻结选择格式：`project`、`story_intent`、`platform`、`selected` 数组。每项有 `asset_id`、`reason` 和 `project_review:{status:"verified_for_project",allowed_platforms:[...],evidence:"...",checked_at:"..."}`。选择 BGM 还必须附 `new_music_research:{performed:true,checked_at:"...",queries:[...],source_urls:[...],new_candidates:[...]}`；结果为空时附 `no_new_candidate_reason`。这里验证的是记录完整性，不验证人是否真的听过、许可是否真实有效。另记录各候选 `audition` 和剪辑区间，交付说明诚实列出听看边界。

## API依据与验证

2026-09-07 核对 [List Objects 分页](https://developers.cloudflare.com/api/resources/r2/subresources/buckets/subresources/objects/methods/list/) 和 [R2 managed domain](https://developers.cloudflare.com/api/resources/r2/subresources/buckets/subresources/domains/subresources/managed/methods/list/)。使用 `result_info.is_truncated/cursor`；对象路径保留斜杠。单测运行 `python3 -m unittest discover -s <skill>/scripts -p 'test_*.py'`，覆盖权利门槛、越界/符号链接/覆盖、哈希污染、分页、并发追加、重新选用时的新研究和冻结记录。
