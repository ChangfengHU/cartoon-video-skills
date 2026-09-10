# 真实能力选择

此文件是路由约定，不是动态能力快照。执行前查看当前工具声明/连接状态。

## 找参考

已部署的 `vyibc-xiaohongshu` 入口为 `https://fleet.vyibc.com/mcp/xiaohongshu`，工具名带 `vyibc-xiaohongshu_` 前缀：`search({keyword,limit})`、`note_detail({url})`、`recommendations({limit})`、`login_status({})` 等。默认少量结果。只有需要当前账号推荐或用户明确提出时才读取个性化推荐。
优先使用客户端连接的 MCP。未出现在本轮工具列表时，先查看 Fleet Hub 注册表与正式端点的 `tools/list`，不要断言能力不存在，也不要盲猜工具名。直接 HTTP 调用须使用既有授权配置，凭据从 Vault/受控宿主进程读取，不写入请求示例、命令参数、项目文件或日志。
`note_detail` 提供图文/媒体地址，不是图像审美评估。下载少量候选后实际查看。保留公开笔记地址和作者署名，不公开复制会话凭据。小红书能力不可用时可继续用户提供参考的流程，不擅自运维 auto-parse。

## 生图

- **内置 imagegen**：本会话2026-09-09的获批大学生三视图与四表情来自这个工具。参考分别承载审美/服饰灵感；表情图使用定稿图锁身份。按所在环境的 imagegen skill 执行；不要声称它是自建 MCP 或自动可从服务器调用。
- **已有 `vyibc-image` MCP**：入口 `https://fleet.vyibc.com/mcp/image`；`list_fleet`、`generate_image`、`get_task`、`list_results`。当前核对的接口接收 `prompt` 或 `prompts`、单个 `referenceImageUrl`、`engine`、`nodes`；以实时 tools/list 为准，不伪造 `referenceImages` 参数。
- 单参考后端可用一张已批准角色图做表情/换装。多角色同框若需要多张独立身份参考，先核实引擎的多参考能力；不支持则明确标记待验证或切到用户允许且真实可用的后端。不能用女主参考生成所有配角，也不能把名字列表当身份约束。
- 并发时一个浏览器只跑一个任务。历史登录/机器数量不证明当前可用；保持实际节点限制。不在失败时安装依赖、移动登录或改 Fleet 配置。

## 资产和恢复

使用已有 R2 上传通路，验证下载状态、图片可解码/尺寸与内容摘要。真实参考图片与原创成果分开记录来源/授权。现有 `vyibc-cartoon-assets` 是品牌级素材库，未获授权不能把所有项目的新角色塞进去。
返回提供方、实际参考、任务/本地产物关联、版本和未验证项；`generated` 不等于 `approved`。
