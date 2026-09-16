# 卡通视频工作室

`cartoon-video-studio` 0.4.1：一个插件，多套独立角色，共用制作能力。原“下班小人视频工作室”保留安装ID，中文名称升级为卡通视频工作室。

## 内容

- 工作室入口：cartoon-video-studio；选择角色、冻结工程、组织制作与授权发布。
- 角色：cartoon-xiaban（三根头发的下班小人）、cartoon-hongyi（红衣侧辫女生）。各有素材、声线、动作与认可参考，后续角色可独立加入。
- 共用10个skills：hyperframes、general-video、hyperframes-core、hyperframes-cli、hyperframes-animation、hyperframes-keyframes、hyperframes-creative、hyperframes-audio、hyperframes-registry、media-use。
- 5个HTTP MCP声明：vyibc-cartoon-assets、vyibc-image、vyibc-douyin、vyibc-youtube、vyibc-voice。分别负责素材、生图、授权发布、音频转写等；当前工具能力以服务返回为准。

角色、视觉风格和故事形式独立。两名现有角色均属暖纸手绘，不表示工作室只能做办公室或情感独白。

## 安装与更新

```sh
codex plugin marketplace add ChangfengHU/cartoon-video-skills
codex plugin add cartoon-video-studio@personal
```

保留现有personal marketplace来源；如果有同名冲突，先核对来源，不能覆盖其他人的市场。已有安装需刷新该GitHub来源并重新安装插件，随后新线程读取新版skills。Fleet能力广场展示固定源码快照，不代表客户端自动升级。

从 Fleet 能力广场复制的工作室授权安装命令会在 Linux x64/ARM64 的用户目录锁定 Node 22、HyperFrames 0.8.33、受管 Chromium 和 MCP 启动器；缺少 FFmpeg/中文字体时只在可用的 Debian/Ubuntu 包管理器上补齐。它还会实际渲染并 ffprobe 回读一段 1080×1920、30fps 的临时 MP4，再写入不含 token 的安装回执。`--runtime check` 只诊断，`--runtime skip` 仅供已受管环境，`--repair` 才会轮换本插件已有 MCP 条目。此冒烟结果不代表云端账号已登录、配音/生图已获授权或成片审美通过。Claude 客户端安装仍未验证；安装器不会下载 TTS 模型、启用付费服务或修改既有浏览器登录。

## 授权

MCP使用客户端环境变量：CARTOON_ASSETS_TOKEN、VYIBC_IMAGE_TOKEN、VYIBC_DOUYIN_TOKEN、VYIBC_YOUTUBE_TOKEN；豆包为DOUBAO_API_KEY。安装不会获取机主账号权限，不在公开JSON内粘贴Key。同端点已有连接优先复用。

资产服务0.1插件原有stdio桥接脚本保留供独立调用；0.2插件改用同一官方HTTP端点及客户端环境授权，避免对角色目录中的Python桥接路径形成依赖。只在需要时连接相关服务。

## 扩展角色

将完整角色skill交给 `skills/cartoon-video-studio/scripts/register_character.py`，按其 `--help` 提供唯一id、显示名和相对品牌JSON路径。脚本验证素材哈希、目录安全和冲突，再注册目录。随后运行：

```sh
python3 scripts/sync-plugin.py
python3 scripts/validate-studio.py
python3 -m unittest discover -s tests
```

canonical来源在skills/，插件skills/由脚本镜像；不手工维护两套不同版本。更新插件版本后发布GitHub，并更新Fleet固定快照，不为每个形象重复部署MCP。

## 发布原则

发布文案聚焦剧情、互动、话题；优先使用无需公开署名的授权音乐。已有曲目要求署名时不能擅删，先换曲或履行许可。AI和虚构声明按内容保留。用户明确授权才发布，R2交付和安装插件本身不等于公开发布授权。

抖音MCP自定义封面目前实验性，实际遇到失败；话题仅保证文案文本。失败/不确定/正式回执分别记录，不能盲目重投。详情在工作室发布规范。

## 回滚与范围

0.1.0源码快照为12a9206e5b1959a1adc5d4e7147829e9968057fa。需要回滚时将市场来源固定到该提交并重新安装；不要删除作品目录或账号凭据。卸载只通过客户端移除cartoon-video-studio插件，独立安装的同名skills不自动删除。

本次验证插件镜像、目录扩展/冲突/哈希、公开结构及Hub展示；未为验证而再生成视频、付费生图或发布旧作品。HyperFrames第三方许可见plugins/cartoon-video-studio/THIRD-PARTY.md。

## 0.3 制作流程

18个skills：工作室、两套角色、独立vyibc-character-design、studio-director、studio-music、studio-quality、voice-production，以及10个既有HyperFrames/媒体skills。新增配音MCP，共5个连接。选题研究是独立可选输入，不属于每片必经步骤。

镜头任务账本保存依赖、文件哈希、远端任务ID和历史；脚本不自动调用云任务，也不保证崩溃窗口内恰好提交一次。质检汇总不产生用户认可。资产服务1.1新增范围内标签/角色/BPM/许可筛选和不可覆盖的修订，保留旧素材ID；R2目录没有迁移D1，不扩大原凭据权限。

角色设计组件按character-design.lock.json固定来源；本地包不捆绑参考图远端文件、不新增付费服务、不自动改浏览器登录。新增编导/配乐/质检可独立读取。

恢复：按Git提交恢复插件文件并重新安装；工作室任务invalidate仅标记过期，不删除媒体。素材修订可重新选择旧ID。线上Worker代码回滚须保留后续无关更新，服务认证和R2数据不跟随代码回滚删除。

## 0.6.0 角色指令

主入口 studio、studio-xiabanxiaoren、studio-hongyi、studio-ali、studio-new、studio-help；辅助返修/检查/发布。每个入口包含实际预设，角色制作未给主题时调用独立研究，新角色默认完成视频。Codex使用 $名称，Pi/Claude项目模板使用 /名称。详见 [安装与完整预设](plugins/cartoon-video-studio/command-support/README.md)。原有20个制作Skill保持职责，新增9个薄入口；不是9套重复制作流程。
