# 角色常用场景与连续动作：独立开源调研

调研日期：2026-09-14。范围：资产组织、命名帧序列、场景组合；不安装引擎、不导入第三方角色素材、不改 Fleet UI、不生成图像。由独立调研 agent 执行，主 agent 同时处理现有生产与集成。

## 建议

沿用当前 HyperFrames、角色 profile 和资产 MCP。借鉴 PixiJS 的命名帧序列和逐帧锚点、Phaser 的按场景资源包及动作序列关系；本轮无需引入两个完整游戏引擎。场景资源包与角色身份分开，角色档案只引用适用场景；动作保存实际姿势帧、持续时间、接触点和起止姿势，渲染统一由主时间线驱动。

## 核验依据与版本

| 候选 | 固定源码 | 许可证与依赖 | 源码观察及适用性 |
| --- | --- | --- | --- |
| [PixiJS](https://github.com/pixijs/pixijs) | v8.6.6，`6f453df5e78fec090294eb57649a8aa9cbdc3825`，提交日期 2024-12-18 | [MIT](https://github.com/pixijs/pixijs/blob/6f453df5e78fec090294eb57649a8aa9cbdc3825/LICENSE)；[package.json](https://github.com/pixijs/pixijs/blob/6f453df5e78fec090294eb57649a8aa9cbdc3825/package.json) 依赖含 eventemitter3、earcut、@pixi/colord、@xmldom/xmldom 等；未声明 engines。 | [Spritesheet.ts](https://github.com/pixijs/pixijs/blob/6f453df5e78fec090294eb57649a8aa9cbdc3825/src/spritesheet/Spritesheet.ts) 的 `animations` 将名字映射为有序帧名，解析为纹理列表；帧支持 anchor。 [AnimatedSprite.ts](https://github.com/pixijs/pixijs/blob/6f453df5e78fec090294eb57649a8aa9cbdc3825/src/scene/sprite-animated/AnimatedSprite.ts) 支持逐帧时长、更新锚点、`autoUpdate` 和 `gotoAndStop`。适合借鉴动作资源结构，不负责创作中间姿势。 |
| [Phaser](https://github.com/phaserjs/phaser) | v3.90.0，`a9965625f49cf366584f454556b039e06e8adad6`，提交日期 2025-05-23 | [MIT](https://github.com/phaserjs/phaser/blob/a9965625f49cf366584f454556b039e06e8adad6/LICENSE.md)；[package.json](https://github.com/phaserjs/phaser/blob/a9965625f49cf366584f454556b039e06e8adad6/package.json) 运行依赖为 eventemitter3；未声明 engines。 | [PackFile.js](https://github.com/phaserjs/phaser/blob/a9965625f49cf366584f454556b039e06e8adad6/src/loader/filetypes/PackFile.js) 允许 JSON 资源包按 section 加载；[Animation.js](https://github.com/phaserjs/phaser/blob/a9965625f49cf366584f454556b039e06e8adad6/src/animations/Animation.js) 将帧、时长、帧率、循环分开；[AnimationState.js](https://github.com/phaserjs/phaser/blob/a9965625f49cf366584f454556b039e06e8adad6/src/animations/AnimationState.js) 的 chain/playAfterRepeat 提供动作连接机制。适合借鉴场景包与动作衔接语义，不应把完成事件驱动直接搬入可 seek 视频。 |

维护证据：通过 GitHub repository API 读取，两仓库均 `archived=false`；PixiJS `pushed_at=2026-09-13T09:47:22Z`，Phaser `pushed_at=2026-08-21T06:56:13Z`。此处固定的是已核验版本，不宣称它们是最新版本，也不把仓库最近 push 当成固定版本仍获维护的证明。

平台与费用：两者都是浏览器 JavaScript 2D 运行时，通常需要浏览器图形环境；源码与包下载无需账户或付费。若真正集成，需要另测当前 Chromium/GPU/无头渲染路径；Node 可用于构建与工具，但仅安装 npm 包不能证明能无头导出视频。第三方打包器、素材、编辑器的授权和付费条件不由引擎 MIT 授权覆盖。本次仅阅读代码与 metadata，未运行任何引擎实例。

## 与现有能力的差异和融合

本地依据：`skills/studio-character-workflow/references/contract.md` 已定义角色 profile、素材哈希、声音和远端预览证据；`skills/vyibc-character-design/references/asset-contract.md` 已定义身份锁、角色版本、各类资产及审美证据；`skills/cartoon-xiaban/character-profile.json` 的 `suitable_scenes` 目前是题材标签，不能替代实际场景素材。

- **角色身份**：保留稳定 `id`，独立 `display_name`；职业和某次故事定位放本集 override。旧 ID 可作 alias，改显示名不应复制成第二个角色。外观版本与动作版本分开记录。
- **场景包**：建议 `scene_id/version/style_id`、背景/前景/道具层引用、尺寸、地面线、角色可站区域、遮挡次序与预览资产 ID。办公室、客厅、地铁等每项必须落为实际本地文件并有哈希；场景包是可复用资源，不和某一人物永久绑定。Fleet 的场景预览应读真实鉴权资产，记录接口读回或浏览器证据。
- **动作包**：建议 `action_id/character_id/character_version`、有序 `frames[{asset_id,duration_ms,anchor}]`、`start_pose/end_pose`、循环规则、适用朝向和道具接触点。各帧共同画布或正确裁切偏移，脚底锚点坐标单位显式一致。姿势只给两个端点时，标记中间帧缺失，不能称连续动作已完成。
- **调度**：由 HyperFrames 绝对时间计算动作和帧索引；不要依赖独立 ticker、完成事件或累计 deltaTime。循环明确周期，非循环结束明确保持末帧；动作切换有起止姿势匹配或显式过渡段。若未来使用 Pixi，关闭自动更新并按确定性索引 `gotoAndStop`。
- **交付**：profile 引用 scene/action IDs；远端技术 metadata 引用同一资产，避免把每张动作帧加入 character_ids 后显示为多个角色。预览可用接触表和实际短循环视频，两者分别标注。复用当前版本/哈希失效机制，场景或动作改变使对应下游成片需要重验。

不采用完整 Phaser：当前无需物理、输入、游戏场景生命周期，引入第二时钟会增加确定性渲染成本。不立即采用 Pixi：当前 HTML/SVG/HyperFrames 已能选帧，缺口首先是姿势素材与接触点；只有确实出现大规模纹理性能问题时再做独立基准。以上是设计借鉴，没有复制上游源码；将来导入代码时须保留对应 MIT 原文及版权，并新增版本锁。

## 未验证和不能保证的质量

源码可以证明帧的组织与播放机制，不能保证人物一致性、动作流畅、剧情表演、透视、脚底稳定或镜头好看。两个静态姿势交叉淡入会形成重影，并不自动得到抬手、转身或迈步的中间运动。需要检查关键接触帧、连续播放、任意时间跳转和实际导出：脚不滑、道具不穿帮、手不突然换边、停顿与声音一致。场景和动作尚未产出的项目必须保持 pending，不以结构检查通过替代实际成片审美或用户认可。Fleet 预览和 HyperFrames 运行验证由生产侧另行记录，本调研不声称部署或浏览器验收成功。
