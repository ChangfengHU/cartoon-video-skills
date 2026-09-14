# 音效与道具素材 skill 交付记录

新增 studio-materials，复用已调研的音效来源，独立 subagent props_research 补查 Tabler/Lucide/OpenMoji 许可、固定commit和原始SVG。

Tabler MIT；Lucide ISC及完整LICENSE内MIT来源说明；OpenMoji CC BY-SA 4.0，仅参考未打包。自写fetch_prop.py无第三方代码依赖，按固定commit取原SVG和完整LICENSE，记录hash，禁止覆盖现有目录，限制响应大小并检查SVG主动内容。

实测：Tabler package 与 Lucide shopping-bag 下载成功；SVG XML解析、license内容与hash保存通过；同目录重跑拒绝覆盖。skill与工作室校验通过，19skills/5MCP，原426上游文件未变。已同步本机安装skill并备份两个路由文件，插件源码版本0.4.2。

尚未检查：道具实际渲染/手持动画及品牌融合；音效来源账号、下载与听审；完整安全审计。没有安装Freesound上游CLI、没有新建MCP、没有制作新片或部署Fleet。该skill提供取材流程和实测SVG下载助手，不宣称所有素材源自动连接。
