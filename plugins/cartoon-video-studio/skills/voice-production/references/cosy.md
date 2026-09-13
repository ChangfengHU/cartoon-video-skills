# 已授权 Cosy 音色复用

先用resolve_voice读取本人的绑定，冻结到本次作品VOICE_ALIAS.json（至少voice_id/model）。声线保持不变；约10秒试音认可不等于新生成整片也已认可。已授权整片替换时直接逐句制作与检查，无需重复审批。

运行 `python3 scripts/cosy_synthesize.py --voice-file <本片绑定.json> --segments <台词.json> --output-dir <作品内新目录>`。segments是包含index/text/instruction的JSON数组；凭据仅由DASHSCOPE_API_KEY子进程环境注入，可选DASHSCOPE_WORKSPACE_ID。服务授权不随插件安装获得。

实际请求使用cosyvoice-v3.5-plus与input.instruction（单数），每句的导演意图由适配器真正发往供应商；不能把它当成精确情绪强度控制，豆包大壹的旧适配器也不因此支持同参数。不默认倍速。

先保存submitted记录再请求；相同文件和请求成功则复用。结果不明不自动重试，保留请求ID或失败状态供核对；确认需重做时使用新输出目录并冻结其他成功片段。无下载TTS模型、无自动注册新音色。生成后下载WAV、核对哈希和真实时长，交给工作室按实际时长排镜头。

依据当前源音频做无剧本提示独立ASR，记录漏字/错读，必要时仅重配对应句；混音后再次从实际MP4提取音轨复核。详见studio-quality的speech-integrity和工作室release-evidence。不得把合成成功、逐句instruction、识别一致写成主观听审通过。

适配器兼容供应商返回的OSS HTTP音频链接：仅对aliyuncs.com子域升级为HTTPS，保留完整签名查询；不能因音频链接协议而重新提交已付费TTS。接口字段参考：[官方HTTP文档](https://help.aliyun.com/en/model-studio/cosyvoice-tts-http-api)。

WAV长度以实际可读PCM字节数除采样率、声道和位深计算；供应商流式WAV的0xffffffff声明长度不能当作真实时长。适配器保留原响应哈希并重写有效WAV头，再与FFprobe交叉核对。
