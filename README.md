# Cartoon Video Skills

可复用的卡通角色品牌skill仓库。目前包含 **cartoon-xiaban（下班小人）v0.2.0**。

每个角色单独一个skill，隔离形象、声音候选和音乐偏好。当前包保留三根头发圆头角色、暖纸手绘画风、实际成片六姿态图集、表演示例代码、喜剧写作与配乐研究规则。

![下班小人表演图集](skills/cartoon-xiaban/assets/identity/acting-sheet-v2.png)

## 安装与使用

已发布，安装命令和包哈希见[RELEASE.md](RELEASE.md)。安装到Codex后可说：

> 使用 $cartoon-xiaban，以“AI替我省的时间去哪了”为题，先给3个具体喜剧梗概，再做一分钟内的手绘卡通视频。先试听配音和配乐，不更改角色。

或将仓库的skills/cartoon-xiaban目录安装到目标工具的skills目录。检查：

```sh
python3 skills/cartoon-xiaban/scripts/prepare_project.py --check-only
python3 skills/cartoon-xiaban/scripts/test_prepare_project.py
```

固定故事的可执行演示见skill内references/acting-recipe.md。它需要调用者提供音频、字体、GSAP与可选音效；不是下载即带TTS模型的视频生成产品。

## 当前状态

- 形象、画风和动画方向获认可，内容趣味仍须提升。
- 配音未定稿；不附带任何真人参考声音或合成本人音轨。
- BGM研究流程已写入，尚未选定曲目；没有声称已经实现抖音纯BGM提取或保证爆款。
- 不包含密钥、Cookie、私人行为、云端权限、模型权重、第三方音乐与字体。公开包不授予这些外部素材的使用权。

角色图由AI辅助创作，未做商标或全球相似性清查，不承诺独占。发布用于保存/安装此skill，不默示第三方音乐、模型或字体具有同样许可。未另行指定通用开源许可证。

打包与安装命令使用[ChangfengHU/skill-publisher](https://github.com/ChangfengHU/skill-publisher)，发布记录说明所用修订和本地安全调整。
