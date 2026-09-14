# 工作室角色命令适配评审（2026-09-14）

范围：`studio`、`studio-xiabanxiaoren`、`studio-hongyi`、`studio-ali`、`studio-new`、`studio-help` 的客户端入口、发现性、私有映射和更新。独立子 agent 只读核对既有研究及官方资料；仅写本文，未安装客户端、未生成图片、未调用 Fleet、未复制外部代码。已有同日固定版本研究适用，无需再派重复子 agent。

## 结论

保留一个公共命令目录和后台提示词契约，生成各客户端薄入口。六个产品名可以相同，但不能声称所有客户端都原生支持 `/studio`。Codex 用 `$studio` 等技能名；Claude 项目入口和 Pi 模板可提供 `/studio`；Codex 旧兼容入口为 `/prompts:studio`。插件安装与命令文件部署是两层，Fleet 回执应分别记录。

| 客户端 | 当前证据与推荐适配 | 发现性和限制 |
| --- | --- | --- |
| Codex | 官方仍推荐 Skills；每个角色需独立可发现 Skill 包装，或明确只提供 `$studio` 加参数。旧 prompts 已弃用，仅按需兼容。 | `/skills` 或 `$` 发现；`agents/openai.yaml` 可带显示名、短说明、默认提示词。不能用提示词正文声称注册了原生 `/studio-*`。修改后检查客户端实际加载清单；旧 prompts 文档要求重启。 |
| Claude Code | `.claude/commands/studio.md` 仍创建 `/studio`，新建也可采用 `.claude/skills/studio/SKILL.md`。插件技能使用 `/插件名:技能名`。 | 精确无前缀短命令需部署项目/个人包装入口；不能仅安装 namespaced 插件就宣称已有短命令。正文、description 和 argument-hint 保持一致。 |
| Pi | 固定 commit 的模板源码以文件名构造命令，读取 description/argument-hint，支持 `$ARGUMENTS`。 | `/` 自动补全；项目 `.pi/prompts/*.md` 需工作区受信任，目录发现非递归。全局、包或显式路径亦可；禁用模板发现的实例不能保证可见。无需仅为静态命令引入 extension。 |

官方依据：[Codex Skills](https://learn.chatgpt.com/docs/build-skills)、[Codex 旧 prompts](https://learn.chatgpt.com/docs/custom-prompts)、[Claude Code Skills](https://code.claude.com/docs/en/skills)。上述官方页在本次实际打开，属滚动文档，不具有固定 commit，不能称为已固定客户端版本。尚未验证各 Fleet 机器所装版本和实际菜单。

Pi 仓库为 `earendil-works/pi`，MIT，复用已有固定 commit `ceea48f5d5d12fd7915dfefba2835ccd55f23bb9` 的 [模板文档](https://github.com/earendil-works/pi/blob/ceea48f5d5d12fd7915dfefba2835ccd55f23bb9/packages/coding-agent/docs/prompt-templates.md) 和 [模板源码](https://github.com/earendil-works/pi/blob/ceea48f5d5d12fd7915dfefba2835ccd55f23bb9/packages/coding-agent/src/core/prompt-templates.ts)。本地证据位于工作区 `command-research-20260914/pi-{revision.json,LICENSE,prompt-templates.md,prompt-templates.ts,extensions.md}`；源码实际观察到 basename 去除 `.md`、frontmatter 元数据及模板查找展开。Node 客户端入口无需新服务凭据或费用，但实际制作依赖原有工具、账号及服务。完整依赖树、客户端运行和热更新效果未实测。现有研究未导入第三方代码，本方案采用接口契约，无需引入 Pi 运行时或新 MCP。

## 后台提示词与帮助分支

1. 公共目录至少记录 `name`、`description`、`argument_hint`、`action`、`character_alias`、`route`、`preset_ref`；公共 preset 保存可共享制作默认，私有策略另存。入口只引用公共契约和 alias，不复制完整角色身份材料。
2. `studio-help` 必须先进入独立只读分支：列命令、当前客户端准确语法、参数示例和实际安装状态，然后终止。不得随后加载“无参数自主制作”的总规则，不调用生图、配音、渲染、入库或发布。`studio --help`、各角色入口 `--help`/`帮助` 亦应在路由前返回帮助；命令出现在引用或讨论中不算执行授权。
3. `studio` 无参数按用户确认的业务默认执行；帮助要展示该默认。角色命令明确本次角色选择，`studio-new` 明确创建流程。显示“已安装入口”和“私有角色可用”两个状态，不能因命令存在就宣称已有阿狸资产。
4. Codex 的显式调用策略可在 `agents/openai.yaml` 配 `allow_implicit_invocation: false`；Claude 的入口可用 `disable-model-invocation: true`。这些是减少误触的客户端控制，不能替代正文 help 早退出及执行授权判断。Pi 模板是提示词展开，并非有确定性权限边界的 handler。

## 角色 ID 私有映射

`xiabanxiaoren`、`hongyi`、`ali` 作为公共可读 alias；运行时从用户私有注册表解析到角色 ID、锁定版本、认可参考、voice policy。公开包与公开 Fleet release 不含私人 ID、图像、历史会话、token 或资产下载地址。部署同步公共代码；有授权的私有配置另走私有通道，回执只带状态/哈希等必要信息。

解析失败必须标记具体 alias 不可用，不临时猜 ID、不随机换角色、不自动新建一个同名角色。`ali` 的身份与版权/授权材料以用户私有档案为准，不能仅凭名称判定是某公共 IP 或已获许可。显式角色入口与工程既有角色锁冲突时记录并处理冲突，不能静默改掉角色。

## 动态新增与 Fleet 更新

现有 `scripts/build-commands.py` 固定五个功能入口；直接在多个目录手工追加角色容易漂移。建议由一份受验证 catalog 驱动生成六个入口、文档、Codex 包装 Skill 和客户端模板。新增角色入库成功后先增加私有 alias 映射，再显式生成允许公开的别名入口；任意私人角色名不要自动提交公共仓库。大量或私有角色也可通过通用 `studio` 加角色参数访问，避免公共菜单无限增长。

生成器应拒绝重复/保留名及路径字符，维护自己生成文件的清单；删改别名时仅清理清单中旧文件，禁止递归删除用户命令目录。先生成、校验引用、执行 `--check`，再形成固定 commit/版本及产物校验和。部署记录每机器：客户端种类/版本、安装路径、发布版本、校验和、入口文件状态、私有映射状态、是否需要 reload、新会话发现验证结果。部分失败保留逐机状态，不能把仓库 push 或单机安装称为 Fleet 全同步。

热更新按实机版本核对：Pi 已有扩展文档确证 `/reload` 针对自动发现扩展，但本次未验证每种 prompt 安装方式的刷新，保守用新会话发现测试；Claude 滚动文档有技能动态加载与插件 reload 机制，但既有版本未核对；Codex 不对未测热更新作承诺。

最低必要验证：六个生成入口及实际客户端语法清单一致；help 分支只读早退出；alias 缺失不进入制作；新增/删除 alias 后生成产物无漂移；不同客户端的 `$ARGUMENTS` 得到原样业务输入；至少一个实际新会话发现测试并留回执。静态检查通过只能证明文件契约，不能证明点击入口不会误触或已经生产出视频。
