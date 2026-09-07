# 会成长的私有素材库

`scripts/asset_library.py` 用 Python 3.9+ 标准库访问 Cloudflare R2 REST。它管理实际文件、来源卡、反馈和作品快照；不自动搜歌、试听、判断法律授权或生成视频。无需 D1、SDK 或新模型。没有 R2 配置时，继续在本片目录保存同结构记录，不因未开通素材库阻塞已授权制作。

## 每片的循环

1. 先写剧情、情绪曲线和 `MUSIC_PLAN.json`，包括有意静音处。按剧情关键词查库，查看适用场景、过去的失败理由、批准状态和听过的区间。
2. **库里有歌也继续主动检索新 BGM 候选**。使用当次可用的浏览器/公开曲库，记录查询、日期、真实来源 URL 和新候选；未找到也记录原因。不能把“搜过旧索引”算成新音乐研究，不能总因已有文件而复用上次的曲子。
3. 按本片发布平台和用途重新核验许可，试听有差异的候选、比较无 BGM/A/B，依剧情选择。库内授权结论不自动适用于新平台、商业用途或素材再分发；元数据排序不等于听过。来源卡未知时保留原站链接，**不上传音轨**。
4. 选定文件下载到本片目录，校验 SHA256，冻结 `ASSET_LIBRARY_LOCK.json`；按真实音频排时间。角色/声线候选不自动成为默认。`plan_music.py` 仍只排序已核验的本地候选。
5. 使用后追加反馈：片名/项目、镜头与作用、试听范围、结果、评论者、观察时间、失败理由或下一次适用条件。用户说“这版可以”可记录对该成片的反馈，不能拆成对所有素材和默认声线的逐项认可。

## 权限和保存范围

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
