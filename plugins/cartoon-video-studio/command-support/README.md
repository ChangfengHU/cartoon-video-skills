# 角色指令 0.6.0

角色入口是预设提示词，不是只显示菜单名称。完整展开内容见 pi/ 或 claude/ 下对应 md；共用制作规则来自 studio/references/commands.md，人物数据来自授权素材库。

主入口：studio（菜单）、studio-xiabanxiaoren、studio-hongyi、studio-ali、studio-new、studio-help。
辅助入口：studio-revise、studio-check、studio-publish。

角色指令不带主题会调用独立研究能力主动选题，已有角色锁定身份；studio-new 默认设计新角色并制作视频，明确“只设计角色”则停止在角色交付。studio、studio-help 空参数只显示帮助；任何指令 help/--help/帮助只解释，不生成或发布。参数里的引用与讨论不构成执行授权。

## 客户端

- Codex：插件加载后 `$studio-ali`、`$studio-new`、`$studio-help`。这些是薄Skill入口，不声称支持裸 /studio-ali。
- Pi：安装模板到受信任项目 .pi/prompts，使用 `/studio-ali` 等。
- Claude Code：安装兼容模板到项目 .claude/commands，使用 `/studio-ali` 等；本包不是已验证的Claude插件manifest。
- 旧Codex CLI/IDE可选 codex-legacy 模板，安装至选定CODEX_HOME/prompts，使用 `/prompts:studio-ali`。官方已弃用该机制，桌面兼容性未验证。
- DSH/Hermes/OpenClaw本版未注册客户端菜单。

安装器目标必须明确，默认预览，--apply才写；冲突文件拒绝覆盖。这里只安装指令模板，完整Skill/MCP需事先安装与授权。

```sh
python3 command-support/install.py --client pi --target-dir /你的项目/.pi/prompts --apply
python3 command-support/install.py --client claude --target-dir /你的项目/.claude/commands --apply
```

## 配置与扩展

项目 STUDIO_DEFAULTS.json 可保存 source、topic、active_project、character_id、voice_policy_ref、尺寸/时长等。配置不能扩大权限，角色指令的固定人物不被全局默认覆盖。当前用户选声规则从私有配置读取，不发布个人ID或账号。

角色新建时是候选数据，不自动把全部候选加入菜单。正式采用后，在 scripts/build-commands.py 的 COMMANDS 里增加唯一稳定英文别名、中文说明与角色查询名，重新生成和同步、测试、发布，再由客户端更新加载。角色重命名保持旧别名兼容；同名歧义必须显式绑定，不猜测。普通角色新增的是薄入口，不复制角色制作技法。

所有入口来自同一生成器：python3 scripts/build-commands.py；发布前 --check 检查漂移。模板目录变化不意味着运行中的客户端自动刷新。

## 验证与卸载

本版验证文件生成、安装冲突与幂等、镜像与插件结构；客户端真实菜单、新会话执行、生成质量仍需运行验证。无付费生成或社交发布测试。
回退先核对本次文件与包内原版，只移除本次安装且未修改的命令文件，不删除配置目录；插件通过固定旧版本回退。素材和凭据不受影响。
