# 角色级 MCP 索引调研（2026-09-16）

## 结论

为现有私有 R2、append-only 素材库补一个**可重建的角色当前版本视图**，并在同一 `vyibc-cartoon-assets` 服务上公开 `character_search`、`character_get`、`character_assets` 和 `character_history`。不另建 Fleet Media 数据源，也不让 Agent 读取需要网页登录态的 `/api/media/*`。

这不是把不可变事实迁移到数据库：R2 原始 records、`supersedes` 和文件 hash 仍为真相源。索引只是从它们派生、可整体重建的查询加速层。当前小规模可先发布 tenant-scoped 的 R2 `character-current.json`；只有确认 R2 列举/过滤已成为延迟瓶颈时，才以同样字段投影至 D1。

## 本地事实与缺口

本仓库已规定 R2 保存文件、D1 仅在目录需要时索引，且当前资产服务只绑定 R2：`skills/cartoon-video-studio/references/asset-management.md`。它也明确所有筛选仍要翻页，旧 ID 仍可查并沿 `supersedes` 判断后继。

角色长期字段已在 `technical.character_profile`，角色场景/推荐音色/参考图均已定义于 `skills/studio-character-workflow/references/contract.md`。当前 `asset_search` 逐页扫描再过滤，因此第一页空而有 `next_cursor` 时不能代表角色不存在；它不适合作为 Agent 的“当前角色配置”入口。

## 外部候选核查

### 1. Cloudflare MCP Server — 域专用、只读工具的实现边界

- 仓库：[cloudflare/mcp-server-cloudflare](https://github.com/cloudflare/mcp-server-cloudflare)，核对 commit `db9084730dd45ebb6ac4dd5d3181d189cc96e98d`（2026-09-16）。GitHub 元数据显示为活跃、未归档、Apache-2.0。
- 已查看源码：[`apps/workers-bindings/src/tools/d1.tools.ts`](https://github.com/cloudflare/mcp-server-cloudflare/blob/db9084730dd45ebb6ac4dd5d3181d189cc96e98d/apps/workers-bindings/src/tools/d1.tools.ts)。它以明确 Zod input schema 注册独立的 list/get/query 工具，标出 `readOnlyHint`，从 request context 取凭据，并把服务错误明确作为 MCP `isError` 返回。
- README 说明其域专用 MCP 走无状态 Streamable HTTP `/mcp`，认证/账户选择仍在请求或应用安全边界；一些功能可能需要付费 Workers 计划。
- 可借鉴：角色工具应是小而有类型的读接口；`character_search`、`character_get`、`character_assets` 设为只读，并复用当前 credential scope。错误应区分“不存在”“无权访问”“索引过期”。
- 不采用：不复用其 Cloudflare account/D1 管理工具或 OAuth 实现；它针对 Cloudflare 账户 API，不能替代租户私有素材授权，也不应暴露通用 SQL 查询。

### 2. Cloudinary Asset Management MCP — 资产查询与生命周期元数据

- 仓库：[cloudinary/asset-management-mcp](https://github.com/cloudinary/asset-management-mcp)，核对 commit `4ca3e0c4fb3ac36ce44990681912d6a9731bac5e`（2026-09-16）。GitHub 元数据显示为活跃、未归档、MIT；LICENSE 已核对为 MIT（Copyright 2025 Cloudinary）。
- 已查看源码：[`src/mcp-server/tools/searchSearchAssets.ts`](https://github.com/cloudinary/asset-management-mcp/blob/4ca3e0c4fb3ac36ce44990681912d6a9731bac5e/src/mcp-server/tools/searchSearchAssets.ts)。它把搜索、排序、字段选择和生命周期字段描述为单独的只读工具，并用 `readOnlyHint` / `idempotentHint` 标注；README 要求 Cloudinary API key/secret/cloud name，故不能直接接入本系统。
- 可借鉴：`character_assets` 的返回应按稳定分类和生命周期状态组织，而不让模型解析所有历史文件：`identity_reference`、`expressions`、`actions`、`scenes`、`voices`、`sfx`，并默认 `active`、默认排除 `retired`。`character_history` 才返回 supersedes 链。
- 不采用：不复用 Cloudinary SDK、Lucene 查询语言或其凭据模型；当前租户的 R2 private policy、20 MB upload 约束和追加式事实不可被它替代。

两者均仅作设计参考，本次没有安装、复制代码、启用 Cloudflare/D1 付费能力或发放新的凭据。

## 建议的派生记录与接口

每个 tenant 的 `character-current.json` 应由 records 全扫描生成，至少包含：

```json
{
  "schema_version": 1,
  "generated_at": "ISO-8601",
  "source_watermark": {"record_count": 0, "latest_record_id": "..."},
  "characters": [{
    "character_id": "xuman-campus-v1",
    "name": "许小满",
    "profile_asset_id": "...",
    "profile_version": 3,
    "status": "candidate_preproduction",
    "thumbnail_asset_id": "...",
    "assets": {"expressions": ["..."], "actions": ["..."], "scenes": ["..."]},
    "voice_asset_id": "...",
    "updated_at": "ISO-8601"
  }]
}
```

生成规则：只把有 `technical.character_profile` 的记录当角色档案；沿 `supersedes` 选择当前叶子；遇到分叉或损坏引用，输出 `index_warnings`，不猜一个“最新”；资产只在 `character_ids` / 明确关联字段与当前档案一致时关联；保留 `retired`，但默认不在 `character_assets` 返回。

接口最小契约：

| 工具 | 输入 | 返回 / 行为 |
| --- | --- | --- |
| `character_search` | `query?`, `status?`, `limit?`, `cursor?` | 当前角色的名称、ID、缩略图、版本、状态；搜索范围受 credential tenant 限制。 |
| `character_get` | `character_id` | 当前档案、人格、外观参考、推荐音色、场景关系、限制、索引水位；不返回私密文件 URL。 |
| `character_assets` | `character_id`, `categories?`, `include_retired=false` | 当前有效素材按类别分组；每项含 asset ID、状态、用途、版本，媒体仍通过现有鉴权下载工具获取。 |
| `character_history` | `character_id`, `cursor?` | 版本和 supersedes 链、停用原因；仅返修/旧片恢复时调用。 |

`asset_search` 保留为跨角色、按素材发现的工具，文档继续要求遍历 `next_cursor`。角色接口不应通过“自动翻到末页”隐藏索引陈旧或权限问题。

## 验收与未验证项

1. 用现有凭据调用 `character_search(query="许小满")`，必须一页命中当前版本；不能依赖 `asset_search` 的 cursor。
2. `character_get("xuman-campus-v1")` 的推荐声、场景和人格字段须与同一 profile asset 一致。
3. `character_assets` 默认不返回停用动作图；`include_retired=true` 时可追溯其替代关系。
4. 刻意制造 supersedes 分叉，验证返回 warning 而非静默挑选。
5. 验证无权限 tenant 得不到角色存在性、原始文件和可重放私有下载 URL。

未验证：当前 Fleet/asset MCP 的实际服务源码路径、现有写入流程能否在 record 登记后触发索引重建、目录规模和 R2 list 延迟。它们决定先用 R2 JSON 还是 D1 投影；本调研不能证明 D1 有必要。
