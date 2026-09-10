# 角色资产清单 v1

使用项目已有角色清单；没有时采用 `cast.json`。检查器只验证结构，不上传、不下载、不判定美感。

```json
{
  "schemaVersion": 1,
  "projectId": "campus-story",
  "style": {"id": "soft-3d", "description": "统一的柔和三维材质与比例"},
  "characters": [{
    "id": "hero", "version": 1, "name": "女主", "role": "protagonist",
    "species": "human", "age": 20, "brief": "清纯微丧的大学生",
    "identityLocks": ["脸型", "发型", "服装"],
    "references": [],
    "requiredAssets": ["turnaround", "expressions"],
    "assets": [{
      "kind": "turnaround", "url": "https://example.com/hero-v1.png",
      "sha256": "填写真实64位摘要", "provider": "实际引擎",
      "prompt": "完整实际提示词", "inputReferences": [],
      "views": ["front", "side", "back"],
      "technical": {"status": "pending", "evidence": "尚未下载核对"},
      "visual": {"status": "pending", "evidence": "尚未看图"}
    }],
    "approval": {"status": "draft", "evidence": "待用户评审"}
  }],
  "lineups": []
}
```

上例是未完成草稿，缺少表情图且摘要为说明文本，应被检查器拒绝；不要把它复制为已完成记录。
完整有效样例见 `campus-approved.json`。`role` 可为主角、配角、反派、路人等任意明确职责；非人类无需强行添加人类年龄。每个角色ID在此清单中只有一个选中版本，旧版本另存原资产，不覆盖。
`references` 元素：`{url, purpose}`，明确是身份、造型、表情还是风格。URL无密钥、用户名密码、片段或签名令牌，公开交付使用可恢复的稳定资源地址。
`requiredAssets` 按用户要求和戏份设置，不能为了检查通过删掉承诺的交付物。`assets.kind` 在单角色选中版本中唯一；扩展装束用明确名称如 `costume-winter`。
`technical` 与 `visual`：`pending | pass | fail`；任何 pass/fail 需非空真实 evidence。`approval.status`：`draft | approved | rejected`；approved/rejected 必须引用真实用户反馈，不由模型自动批准。
`lineups` 元素包含 `{members:[{characterId,version}], asset:{...同资产字段,kind:"lineup"}}`。完整演员组交接需一张包含全部选中角色的比例对照图；切勿以另一版本合影替代当前版本。可追加角色子组合影，但不自动满足整组检查。
不应自动纳入背景路人时，单独保存其简化设计任务，不偷偷省略当前请求的必需角色。同框比例可为有意夸张，但须符合共用画风和故事设定。
`node scripts/character-check.mjs cast.json --approved` 要求所有必需资产技术与视觉通过、角色获用户批准，多角色还须完整且已通过的同框图。技术检查和视觉证据由调用者提供，脚本不会证明填写的证据为真。
