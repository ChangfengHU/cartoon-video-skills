# 音效和小物品来源

来源调查日期：2026-09-13。以下为获取入口与可参考实现，不是已开通账号或安装工具的声明。运行时核实可访问性、逐项许可及实际工具 schema。

## 音效

- Mixkit：https://mixkit.co/free-sound-effects/ 。通过搜索/页面查找具体动作或环境声，查看 https://mixkit.co/license/ 对应音效许可后取得文件。
- Freesound：https://freesound.org/ 。按动作、材质、时长和许可筛选。预览、原始音频下载与 API 使用条件分别核查；原件可能需要 OAuth，不能因预览可听就声称原件下载已通。
- 可参考现成 Node skill/CLI：https://github.com/MaksPyn/freesound-skill （MIT）。搜索、详情、预览、原件校验及归属记录；未随本skill捆绑，若当前已安装先读其SKILL和CLI帮助。采用代码前固定commit并保留LICENSE，凭据由环境/金库提供。
- MCP参考：https://github.com/timjrobinson/FreesoundMCPServer 。不能假设所有实现都有OAuth原件下载。

关键词示例：cardboard box opening、packing tape peel、paper rustle、wooden object drop、phone vibration。按场景变化，不固定素材或以下载量代替听感。

## SVG和小物品

- Lucide：https://github.com/lucide-icons/lucide ，ISC及完整LICENSE内的部分MIT来源声明；icons目录可找 package、shopping-bag、smartphone 等简洁轮廓。适合符号化道具，不直接等于手绘近景道具。
- Tabler Icons：https://github.com/tabler/tabler-icons ，MIT；可比较轮廓和填充版本。采用时保留许可，固定具体版本。
- OpenMoji：https://github.com/hfg-gmuend/openmoji ，图像采用 CC BY-SA 4.0；有更多彩色物品，但需处理署名及改编许可要求。无公开署名需求时优先另选合适许可素材，不默认使用。

通过官方仓库树核对实际文件路径再下载，不猜测CDN地址。下载原始SVG后保存对应LICENSE、上游commit与文件hash。SVG的代码许可/图像许可按项目具体声明核对。

## 获取后的工具与记录

沿用 media-use 的实际工具获取与变换。音频基本检查：

```sh
ffprobe -v error -show_format -show_streams -of json <项目内音频文件>
```

需要关键片段时用FFmpeg输出新的派生文件，保留源文件。SVG先读文本检查，再用项目已验证的渲染器预览。背景移除、图像改编和动画分别交对应媒体/角色/HyperFrames能力，不在这里重复实现。

本轮没有开通新素材账户、安装上游服务、下载模型或测试所有来源。获取失败必须记录实际失败步骤，不能通过来源列表或许可说明冒充已取得素材。

## 已附带的道具获取工具

```sh
python3 scripts/fetch_prop.py --source tabler --name package --output-dir <作品内新目录>
```

支持 tabler/lucide 的已知图标名，使用固定上游commit；无密钥、无付费、仅Python标准库。输出 original.svg、完整LICENSE、ASSET.json。目录已存在时停止；不存在的图标报HTTP错误，不替换其他图标。下载包含大小边界和SVG主动内容检查，但不替代实际渲染及品牌审查。需要查找图标名时使用上游目录搜索，此脚本不提供全库搜索或音效下载。
