---
name: voice-production
description: 通过vyibc-voice查询豆包音色、短句试听、分角色分段配音及局部重做；输出真实音频与时长供视频排镜头，可复用已授权Cosy复刻音色；不承担转写或自动创建新克隆。
---

# 配音制作

需要连接 https://fleet.vyibc.com/mcp/voice ，使用Fleet既有管理员鉴权。先读tools/list和capabilities，不凭本文件推断上线版本。凭据由后端从金库service:doubao-tts读取；不在参数、提示词或工程中复制密钥。

选声先读角色已冻结的音色绑定；新角色通过list_voices按名称、语言文字、男女声、场景筛选，get_voice确认准确ID。官方目录收录不等于账号权限或使用许可。check_config默认仅检查配置存在；probe=true会产生短句合成调用与可能费用，只有本次voice_type的成功请求能证明该次权限。

## 真实生产

- 锁定文字后用synthesize提交segments：每段text、voice_type和speech_rate（可省略）。最多30段，每段180字符。speech_rate是供应商的-50..100整数单位，不是1.2倍浮点数；导演意图可用标点/断句表达，但本版没有传情绪API。
- 返回job_id立即保存，再通过status轮询，避免网络结果不明时重复提交。相同标准化内容复用任务。失败不会自动再次计费。
- result可返回部分成功音频；按段下载WAV、核对sha256和ffprobe时长，冻结到作品。临时链接携带限时访问票据，7天有效；不能把链接放公开索引。过期后可凭Fleet管理员身份访问不含ticket的同一音频路径。
- 音频时长来自PCM字节数，是真实时长；不是字幕逐字时间。短语字幕若按字数估算，记录estimated，不称ASR对齐。
- 局部返修用retry_segments，传job_id、稳定retry_key和segments中的index及所需文字/音色/语速改动。保留其他已完成段，新任务记录parent_job_id。未完成段必须明确选入；原任务仍活跃时不建并发重做。未知结果重试需要retry_uncertain=true，并可能再次计费。
- cancel只停止后续段，已在途请求可能完成并保存；不退款、不删除音频。卡住任务等待10分钟lease后，再检查状态决定是否明确重试。

按语音真实长度安排动作，试听自然度、重音、断句、末字和背景音乐遮蔽。文件可解码、合成成功或ASR相符都不等于配音质量通过；没听过的范围写pending。豆包MCP的synthesize不支持Cosy或情绪参数；已有Cosy音色走下述独立适配器。

## 安装与回滚

`python3 scripts/install.py --target-dir <明确的技能父目录>`；已存在且内容一致时不改写，用户改动时拒绝覆盖。
`python3 scripts/install.py --target-dir <同目录> --uninstall`只移除与源码完全一致的副本，不删除音频和服务。
`python3 scripts/test_install.py`验证幂等、修改保护和卸载。本技能不自行修改插件或客户端MCP配置。

## 私人称呼与已有 Cosy 音色

用户明确指定私人称呼时，先调用 vyibc-voice.resolve_voice；“Cosy 我的音色”读服务端金库 voice:cosy-my-voice，收藏男女声读 voice:favorite-aliases。只解析称呼，不推断性格、适用场景或其他偏好，不把私人ID写入公共skill。解析失败不得默认替换成大壹或重建克隆。

Cosy返回provider=dashscope；用 [已有Cosy音色适配](references/cosy.md)。这不是豆包MCP的synthesize功能。新克隆需用户授权与参考音频，另行操作，不因提到称呼再次付费注册。
