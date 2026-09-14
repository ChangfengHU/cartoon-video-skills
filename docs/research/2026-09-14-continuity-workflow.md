# V7 工作流开源核查

调研日期：2026-09-14。范围：参考锁、连续动作预检、实际 MP4 质量检查、版本证据。独立调研子 agent 完成；仅访问公开仓库与文档，未安装项目、未运行候选代码、未读取历史工程、未修改远端。下列 Linux ARM 判断是源码和依赖层推断，不是实际运行认证。仓库 API 与固定 commit 原始文件均已读取。

## 结论与融合

本地计划已经包含“角色参考锁 → 动作试片 → 实际 MP4 检查 → 版本证据”，不需要更换 HyperFrames。候选补足自动定位与可重复证据，不能判定角色好看、表演自然或包袱成立。建议借鉴 Manim 的连续帧基准和缺基准失败语义；按需接入 pixelmatch 作为局部回归指标；优先复用本地已安装 FFmpeg 做最终文件检测。参考锁与验收清单由本地业务流程维护，三个仓库都没有直接实现本角色的审美锁。

| 候选 | 已核实版本与维护证据 | 许可、依赖、平台判断 | 采用意见 |
|---|---|---|---|
| [ManimCommunity/manim](https://github.com/ManimCommunity/manim) | commit `485c226168e9c189512b22468de89b18dbc1780e`；API：未归档，最后提交 2026-09-14；pyproject 版本 0.21.0 | LICENSE 和 LICENSE.community 均为 MIT，分别含 3Blue1Brown LLC 和社区版权；Python ≥3.11，PyAV、Pango、Cairo、NumPy、SciPy、ModernGL 等原生依赖；ARM 是否有匹配 wheel、系统图形库须另验 | 借鉴测试设计，不引入整个数学动画引擎。迁移成本大且无角色审美判断能力 |
| [mapbox/pixelmatch](https://github.com/mapbox/pixelmatch) | commit `c6fee35afac3c52576b2cb424bd1061ab6a4bd06`；API：未归档，最后提交 2026-07-07；package 版本 7.2.0 | ISC，须保留 Mapbox 版权和许可；ES module，pngjs ^7.0.0；主算法纯 JS，ARM 风险较低，仍需核实 Node 版本与实际样本 | 可选轻量工具；先校准角色区域阈值与固定渲染环境，再决定接入。不能以全屏差异比例代替角色审美判断 |
| [FFmpeg/FFmpeg](https://github.com/FFmpeg/FFmpeg) | commit `639ee849526cfe61ceb312776335c245b98bd9d4`；API：未归档，最后提交 2026-09-14 | 主体 LGPL 2.1+，可选组件可转 GPL 或不可再分发组合；configure 明列 aarch64/arm64；C 工具链与编解码依赖取决于构建 | 优先使用已装 CLI；记录实际 `ffmpeg -version` 和 buildconf，不直接用调研 HEAD 替换本机版本 |

以上三项本地处理路径不要求账号或网络凭据；本次未调用服务、未发生候选安装。维护证据仅说明近期存在提交，不代表质量或长期支持承诺。

## 文档与源码证据

**Manim：**[官方测试文档](https://docs.manim.community/en/stable/contributing/testing.html)说明图形测试比较帧，视频编码差异可能妨碍跨系统直接比较。读取的[frames_comparison.py](https://github.com/ManimCommunity/manim/blob/485c226168e9c189512b22468de89b18dbc1780e/manim/utils/testing/frames_comparison.py)明确默认 `last_frame=True`，动态动画须设为 False；基准目录或文件缺失会报错，`--set_test` 才生成控制数据。直接启发：走路、拿取、转身等动作要看连续过程，单张结束帧无效；基准更新应单独记录，不能静默用新图覆盖旧图。[依赖](https://github.com/ManimCommunity/manim/blob/485c226168e9c189512b22468de89b18dbc1780e/pyproject.toml)、[原许可](https://github.com/ManimCommunity/manim/blob/485c226168e9c189512b22468de89b18dbc1780e/LICENSE)、[社区许可](https://github.com/ManimCommunity/manim/blob/485c226168e9c189512b22468de89b18dbc1780e/LICENSE.community)。

**pixelmatch：**[源码](https://github.com/mapbox/pixelmatch/blob/c6fee35afac3c52576b2cb424bd1061ab6a4bd06/index.js)要求等尺寸 RGBA 输入，可输出差异图；存在 threshold、抗锯齿排除和 windowSize 参数。默认阈值 0.1 不是本项目验收标准；windowSize 返回局部窗口最大差异数，不能当全屏总数使用。建议同时间点、同尺寸、同字体和渲染器比较，角色头发、脸、手等局部单独看；画面移动时像素差异会很大，不能据此直接判失败。[依赖](https://github.com/mapbox/pixelmatch/blob/c6fee35afac3c52576b2cb424bd1061ab6a4bd06/package.json)、[ISC 许可](https://github.com/mapbox/pixelmatch/blob/c6fee35afac3c52576b2cb424bd1061ab6a4bd06/LICENSE)。

**FFmpeg：**读取 [freezedetect](https://github.com/FFmpeg/FFmpeg/blob/639ee849526cfe61ceb312776335c245b98bd9d4/libavfilter/vf_freezedetect.c)、[blackdetect](https://github.com/FFmpeg/FFmpeg/blob/639ee849526cfe61ceb312776335c245b98bd9d4/libavfilter/vf_blackdetect.c)、[silencedetect](https://github.com/FFmpeg/FFmpeg/blob/639ee849526cfe61ceb312776335c245b98bd9d4/libavfilter/af_silencedetect.c)，确认按噪声、亮度或时长阈值输出冻结、黑场、静音的时间信息。用途是标记需复看的区间：漫画停顿、黑底字幕和叙事静音应允许人工解释，不应全部判错。检测必须针对交付的实际 MP4，HTML 预览不能证明编码文件正确。[官方滤镜文档](https://ffmpeg.org/ffmpeg-filters.html)、[构建平台分支](https://github.com/FFmpeg/FFmpeg/blob/639ee849526cfe61ceb312776335c245b98bd9d4/configure)、[许可组合说明](https://github.com/FFmpeg/FFmpeg/blob/639ee849526cfe61ceb312776335c245b98bd9d4/LICENSE.md)。

## 本地建议门禁（设计建议，未执行）

1. **参考锁：**清单登记角色图片实际路径、SHA-256、来源、用户认可状态与固定特征。缺有效参考时明确缺项，不能将新生成图标记成用户已认可。
2. **动作试片：**给每个关键动作记录起止秒、接触点与预期；渲染短 MP4，并看连续动作、关键接触前后帧。试片通过只覆盖对应动作，不能自动批准全片。
3. **实际 MP4：**保存媒体流/时长/尺寸检查、完整解码检查、音视频异常区间；复看全片并听配音和混音；把“命令成功”“技术通过”“连续动作通过”“审美通过”分开记。
4. **版本证据：**每轮独立目录保存源码/参考/输出 hash、工具版本、实际命令退出码、截图及其源 MP4 hash 和时间点、发现、返修项、复验结果。新版本不得沿用旧 MP4 的通过标签。
5. **回归基准：**先由实际观看建立合格样本，再加自动差异；缺证据记录为未验证。更新基准时写明原因和审阅依据，保留原文件。

## 未验证项与落地约束

- 未测试三个候选在本机 Linux ARM 的安装、性能、字体一致性、编解码可用性及误报率。
- 本次没有复制候选源码；若后续复制 Manim 或 pixelmatch 实现，必须随代码保留相应许可与版权。若后续安装，固定精确版本/commit 与锁文件，不依赖漂移 HEAD。
- FFmpeg 最终使用许可以实际构建选项为准，不能把仓库主体许可直接当成所有二进制的许可。
- 未验证自动评分对“三根头发”等角色特征的可靠性；连续动作自然度、角色一致性和喜剧节奏仍要记录实际视听审查。
