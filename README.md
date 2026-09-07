# Cartoon Video Skills

可复用的卡通角色品牌skill仓库。当前版本为 **cartoon-xiaban（下班小人）v0.4.0**；安装包地址与哈希见 RELEASE.md。

每个角色单独一个skill，隔离形象、声音候选和音乐偏好。当前包保留三根头发圆头角色、暖纸手绘画风、实际成片六姿态图集、表演示例代码、喜剧写作与配乐研究规则。

![下班小人表演图集](skills/cartoon-xiaban/assets/identity/acting-sheet-v2.png)

## 安装与使用

已发布，安装命令和包哈希见[RELEASE.md](RELEASE.md)。安装到Codex后可说：

> 使用 $cartoon-xiaban，以“AI替我省的时间去哪了”为题，制作约90秒手绘卡通视频，台词和表情要有情绪，按剧情重新找配乐，画面不放解释性页脚。

Codex 的实体安装目录为 `~/.codex/skills/cartoon-xiaban`，安装脚本同时创建 `~/.agents/skills/cartoon-xiaban` 符号链接供用户级发现，只有一份实体文件。已有同名版本先移入隐藏备份目录；发现目录发生独立安装冲突时停止并保留两边。安装后下一轮可用，若未刷新请重启 Codex。

或将仓库的skills/cartoon-xiaban目录安装到目标工具的skills目录。检查：

```sh
python3 skills/cartoon-xiaban/scripts/prepare_project.py --check-only
python3 skills/cartoon-xiaban/scripts/test_prepare_project.py
python3 skills/cartoon-xiaban/scripts/test_plan_music.py
```

固定故事的可执行演示见skill内references/acting-recipe.md。它需要调用者提供音频、字体、GSAP与可选音效；不是下载即带TTS模型的视频生成产品。

## 当前状态

- 形象、画风和动画方向获认可，内容趣味仍须提升。
- 配音未定稿；不附带任何真人参考声音或合成本人音轨。
- 配音后端可替换：已授权云 TTS、可用的 Mac mini、已验证 Linux 后端；跨机器可用私有 R2/SSH 传输。模型安装不作为成片前置条件，具体路由与失败处理见 skill 的 voice-routing.md。
- BGM按故事重新研究，再按场景意图选择；不绑定固定歌曲。附带可测试的元数据排序辅助脚本，不冒充自动听音、音乐搜索服务或通用纯BGM提取器。
- 默认约90秒，三层声音设计，说明性页脚关闭；需要署名的音乐在随片发布说明保留署名。另有九姿态候选，未覆盖已认可的六姿态。
- v0.4 增加私有 R2 素材库：保存素材、不可变索引记录、反馈与项目快照，支持下载后的哈希核验和并发追加。每片仍先分析剧情，再主动寻找新配乐、核验使用范围并试听；旧库不决定默认歌曲。
- R2 客户端使用 Python 标准库；渲染、TTS 和媒体服务是独立运行依赖。安装器不会安装模型、替换系统运行时或配置云端密钥。公共包只含客户端、文档与非敏感示例，实际素材和私有索引不进仓库。
- 不包含密钥、Cookie、私人行为、云端权限、模型权重、第三方音乐与字体。公开包不授予这些外部素材的使用权。

角色图由AI辅助创作，未做商标或全球相似性清查，不承诺独占。发布用于保存/安装此skill，不默示第三方音乐、模型或字体具有同样许可。未另行指定通用开源许可证。

打包与安装命令使用[ChangfengHU/skill-publisher](https://github.com/ChangfengHU/skill-publisher)，发布记录说明所用修订和本地安全调整。
