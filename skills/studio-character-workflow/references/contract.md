# 项目与资产契约

项目简报至少包含角色来源方式、交付范围和参考/风格约束；`example_video`决定是否创建视频阶段。不要把具体名字/数量/秒数固定在工作流。简报的voice_policy_path指向项目内策略文件，stage_inputs按阶段列出额外输入（角色档案、实际请求参数、被调用skill版本清单、素材哈希清单等）；初始化将这些交给生产账本，后续内容或政策改变会使下游不可复用。不要只把剧本文字算作任务输入。

`CHARACTER_WORKFLOW.json`（schema_version=1）在项目私有目录：
- `voice_policy` 是 `{path,sha256}`，JSON含 `excluded_voice_ids` 数组。由当前用户/工作室提供；未配置写空数组及来源说明，不偷用其他用户偏好。默认从当前项目配置读取，或通过有授权的金库key `studio:voice-selection-policy`解析后保存非秘密策略。不得把token写入报告。
- `references[]`：`id, source_url, platform, role, used_for_generation, image:{path,sha256}, usage_status`。`usage_status=recorded_at_generation`仅用于真正保存实际请求的情况，另带`request_receipt:{path,sha256}`；历史补录用`retrospective`。`preview_asset_id`指向鉴权私有原图/截图资产。
- `characters[]`：`id, profile:{path,sha256}, reference_ids, assets:[{path,sha256}], voice:{provider,model,voice_id,preview:{path,sha256},selection_reason}, visual_review:{path,sha256}`。声音metadata是推荐，不改收藏别名；未生成预览不称已试听。
- `example_video`可为null，或`{file:{path,sha256},release_report:{path,sha256}}`。release report仍执行原检查器，不因用户已认可画面就伪造完整听审。
- `delivery`：`receipt:{path,sha256}`、`browser_evidence:[{path,sha256}]`。实际接口读回/浏览器采样应保存目标asset ID或URL，不能复用别的项目截图。

通用检查器验证项目内路径与哈希，排除音色、实际文件与证据是否齐备；遇到补录回执标pending。输出不是审美分数或自动批准。

远端角色约定：`technical.character_profile`保长期人物；`technical.references[]`在原有来源字段上加 `preview_asset_id, preview_caption, usage`，UI通过同源鉴权 `/api/media/assets/<id>/file`读图；参考不填character_ids以免重复成新人物卡，可用technical.related_character_id建立关联。`kind=reference`及`license.status=user_authorized_private_reference`仅用于用户要求保存在私有库的第三方参考，`scope=private_reference_only`、`personal_reference=true`、`archive_allowed=true`，不允许用作公开发布素材。

`technical.voice_recommendation`含provider/model/voice_id/display_name/preview_url/reason与实际验证状态；`technical.voice_selection_policy`记录该角色适用的排除策略与来源。`technical.example_video={url,title}`绑定实际MP4。`technical.approval_evidence`分列角色外观、具体视频及声音的认可范围；未来版本不继承旧片检查。长期工作室策略可放私有配置，不存公共插件的用户偏好。
