# 按角色自动选声

## 输入与排除

读角色定位、年龄感、性格、适用场景、表达节奏，以及当前项目/工作室voice_policy.excluded_voice_ids策略。先排除禁用voice ID；别名或旧作品绑定不能绕过排除。私人偏好和禁用列表保留在租户配置/作品记录，不复制到公共技能。未找到适用策略时说明未知，不能猜测收藏意味着推荐。

## 供应商边界

- vyibc-voice MCP当前通过capabilities核实真实支持；若只支持豆包，不宣称已统一托管阿里云、Cosy或克隆管理。
- 豆包其他合适音色：准确ID + 模型/resourceID + 本次合成成功才能证明本次调用可用。无情绪API就不填写虚构emotion参数。
- Qwen预置声：核对官方音色表与模型组合。例如qwen3-tts-instruct-flash-2026-01-26支持Cherry、Serena；实际发送input.instructions、optimize_instructions才可称使用指令控制。效果强弱需听音，不能视参数存在即通过。
- Cosy现有授权复刻/设计声：需明确voice ID、模型、授权范围、目标用途；不能把“已有用户私人声”自动绑定新女性/男性角色。不得自动注册新克隆。
- Cosy版本不通用。官方文档当前注明v3.5-plus/flash无系统预置声；不要将v3预置ID传入v3.5已有克隆适配器。其他版本先核查兼容API再调用。

## 自动选择与冻结

以角色表达需求选择足够合适的候选，自主确定推荐，不要求用户做A/B选择。记录选择理由是基于目录描述、真实模型听审还是人类听审，不能混写。先用包含正常介绍与情绪转折的短句合成，核对时长/解码/首尾/重音。发现问题只返修受影响候选，不扩大无目的试音。

推荐记录至少包含：provider、model、voice_id、display_name、角色依据、controls_sent、availability（实际请求时间/结果）、preview_file/URL/hash/duration、授权依据及未知范围、listening_method/status、版本和被替代绑定。目录可见、调用成功、许可和主观质量是四个不同字段。

角色推荐可调整；历史作品冻结自己的voice binding。新版本推荐不代表旧作品音轨需要替换。保留用户收藏别名原义，不给收藏添加性格或适用场景等偏好标签。

## 凭据与产物

供应商凭据仅从固定金库键读取并注入子进程环境，不写入skill、请求日志、URL或公共角色metadata。供应商限时签名音频URL不直接公开；下载核验后按用户授权上传自有试听文件。保留提交记录与request ID；结果不明不自动计费重试。

## 官方来源

核查日期2026-09-14；再次执行时检查模型/音色兼容性是否更新。
- https://help.aliyun.com/zh/model-studio/qwen-tts-voice-list
- https://help.aliyun.com/zh/model-studio/cosyvoice-voice-list
- https://help.aliyun.com/zh/model-studio/realtime-tts-user-guide
- https://help.aliyun.com/zh/model-studio/non-realtime-tts-user-guide

这是工作流说明，不表示插件安装已经给账户开通供应商或新付费服务。

## 已封装Qwen预置声执行器

`python3 scripts/qwen_synthesize.py --text-file <单段纯文本.txt> --voice <已核验ID> --model <已核验instruct模型> --instructions-file <导演指令.txt> --output-dir <全新目录>`。

调用前由agent读取当前项目voice_policy.excluded_voice_ids并过滤；脚本只执行明确绑定，不自行选声或回退。凭据从DASHSCOPE_API_KEY子进程环境注入，可选DASHSCOPE_WORKSPACE_ID；金库访问由agent完成，公共脚本不绑定用户金库服务。需要系统ffprobe，无额外模型下载。

当前适配器限定中文单段1–500字、明确Qwen3-TTS-Instruct-Flash模型与voice、真实input.instructions。输出原始audio.wav、raw_sha256、ffprobe时长/音轨、请求正文、request_id和状态receipt.json；公共receipt不保存供应商签名下载链接或密钥。已接受请求的临时下载URL保存在独立0600文件download-private.json，仅供下载恢复，禁止公开打包或打印；阿里aliyuncs.com子域的HTTP音频URL仅升级为HTTPS，保留签名参数，其他HTTP拒绝。要求输出目录全新，已有目录一律拒绝，以免覆盖或重复计费。请求/下载失败保留failed或unknown状态；不自动重试、不自动换音色。需要局部重做时由agent明确创建新版本目录。

验证范围：mock HTTP、请求字段、成功落盘、失败状态、下载失败保留request_id、已有输出拒绝、阿里OSS协议升级和私有文件权限均有测试。2026-09-14公共脚本实际短句验收：首轮请求被接受后下载失败，保留unknown且未自动重试；修复HTTP阿里OSS到HTTPS下载后，在明确授权的新版本目录实调Cherry成功（2.72秒，原始hash与ffprobe回执齐全）。这证明该模型/音色本次端到端可用，不等于所有音色或主观听感通过。
