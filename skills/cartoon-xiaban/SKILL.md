---
name: cartoon-xiaban
description: "复用下班小人（三根头发圆头角色）的暖纸手绘形象、角色表演、喜剧分镜和声音设计，制作一分钟内卡通短视频。用户提到下班小人、这套小人或调用本 skill 时使用；新角色另建品牌 skill。"
---

# 下班小人 · 手绘卡通品牌

这是一个角色品牌包，不是所有视频的通用规范。「下班小人」是便于调用的暂定名称，用户尚未正式命名。用户希望以后建立多套独立角色、音色、画风和专属音乐的 skill；本包只管理这一套。

## 先确定使用的版本

读取 [assets/brand.json](assets/brand.json)，查看角色参考与六姿态图集。v0.2 已保存实际成片中获认可的动画方向与实现；内容趣味和配音仍需优化，BGM 已进入选曲阶段、尚无定稿。不能把生成成功、方向认可、最终确认混为一谈。

沿用当前包，不因为新选题重设计角色。用户指定新角色或新品牌时，读 [references/new-brand.md](references/new-brand.md)，另建 skill。用户本次明确要求可以覆盖默认值，但一次试验不自动改写长期品牌。

## 制作入口

1. 阅读 [references/visual-identity.md](references/visual-identity.md) 与 [references/story-and-motion.md](references/story-and-motion.md)。用参考图约束新姿势，先保证人物是同一个，再设计新场景。
2. 新故事先读 [references/comedy-writing.md](references/comedy-writing.md)：先有值得讲的误会、升级和反转，再排动画，不复读示例结论。声音读 [references/voice-and-music.md](references/voice-and-music.md)；研究抖音配乐读 [references/music-research.md](references/music-research.md)。声线身份、台词表演、音乐作用分别决策。
3. 为新作品建立独立目录并冻结品牌快照：

   ```bash
   python3 <本skill目录>/scripts/prepare_project.py --output <尚不存在的项目目录> --topic "这次的主题"
   ```

   脚本复制随包保存的参考素材、品牌档案和制作规则，写入 `BRAND_LOCK.json` 与 `BRAND_BRIEF.md`；拒绝覆盖已有目录。`--check-only` 只核验包内素材、哈希和状态，不调用云服务。
4. 做视频先加载可用的 `hyperframes` 入口 skill；用户指定 Remotion 时遵从。引擎未安装就先说明依赖，不能声称本包自带渲染器或 TTS 模型。成功机制和可运行示例见 [references/acting-recipe.md](references/acting-recipe.md)，运行环境见 [references/local-runtime.md](references/local-runtime.md)。示例 `scripts/build-demo.mjs` 是一个固定故事的实现，不是所有新选题套用的模板。
5. 按实际音频时长排镜头，交付可播放 MP4。先看过画面、检查转场与声画同步，再说完成；技术检查通过不代表用户已经认可观感。

默认是一分钟以内中文竖屏故事，可被本次用途覆盖。拿不到声音服务权限时报告具体错误，不自动购买、开通服务、换成人声或下载大模型。

## 本品牌的创作重点

- 小人是会反应、会做选择的主角，而不是大标题边上的装饰。用表情、动作、道具和喜剧停顿讲故事。
- 「可爱地说很累的成人心事」是目前方向；微丧但不绝望，有自嘲和一个具体的小解法。音色像卡通男孩，不意味着角色故事必须是真实儿童经历。
- 每片一个值得看的矛盾。AI 焦虑是首集例子，不是永久选题；以后可写拖延、消费、工作、人际等合适主题，不复读同一结论。
- 参考优秀作品可以借鉴揭示顺序、动作节奏和信息差，不复制角色造型、文案或音乐，不声称能保证爆款。

## 定稿与复用

新生成的角色图、声音、音乐先进入作品目录的候选区。只有用户明确认可后才晋升为默认，并更新 `assets/brand.json` 的版本、状态、文件和来源；保留旧版本，不用新素材覆盖旧作品。

配音服务的预置音色不是我们独占的音色；生成的角色也不承诺法律意义上的全球唯一。保存来源、授权范围与合成标记。skill 不保存 API Key、Cookie、账号会话或个人行为明细；这些仍由运行环境管理。
