# 新增形象

一套角色一个skill，放在仓库skills/cartoon-<名字>。名称不要依赖具体故事。与现有风格一致不代表同一角色；换题材通常不需要新建角色。

最小内容：SKILL.md、独立brand_id的品牌JSON、已授权或明确候选的参考图、素材路径/SHA256/来源、外观比例/服装辨识点、姿势索引、声音候选或已验证ID、认可证据与状态。没有用户反馈时标candidate，不能继承其他角色的认可。

运行 scripts/register_character.py --source <完整角色skill目录> --id <唯一id> --name <显示名> --brand-file <相对JSON路径>。脚本验证路径、brand_id与资源哈希、阻止id/skill/brand冲突，将角色复制到相邻skills目录并原子更新目录。发布者随后运行仓库scripts/sync-plugin.py和validate-studio.py，更新插件版本与Hub固定源码快照。新增角色无需增加MCP或复制渲染运行时。

脚本失败不会提交目录；回滚新注册可移除新角色目录及characters.json对应条目，并重新同步打包。已发布角色改版保留版本，不覆盖已交付作品BRAND_LOCK。

新增角色还需 character-profile.json：id、profile_version、introduction、personality、speaking_style、emotional_range、suitable_scenes、casting_roles、comedy_engine、boundaries、editorial_status。遵循 [素材管理](asset-management.md)；旧角色外观认可不自动认可新增性格。缺档案者只保留候选状态。
