# 连续表演与质量基线

适用于角色视频新制和实质动作返修；资料解读、静态卡片不机械套用。复用已有角色档案、PRODUCTION_PACK、production_state和release_check，不另建身份真相或调度服务。

## 先冻结认可的具体内容

读取当前作品与用户原话，REFERENCE_LOCK记录实际MP4路径/hash、选择依据、认可范围、需要保留的优点和仍有缺陷。人物图、日夜服装、场景与惯用手来自该角色的私有档案，不能把最后一个成功角色、音色、题材或镜头数变成全局默认。新片独立版本；用户赞扬旧片不自动批准新片。公共插件只包含规则和无私人内容的示例结构。

## 动作从意图设计

逐镜写意图、视线、起始状态、预备/接触/反馈/收束、结束状态与下一镜入口。静态反应或呼吸可以合理重复，注明叙事功能；不规定每秒切镜、不禁止一切重复，也不靠大量图片宣称表演丰富。保持有意义的停顿。

需要交互时，明确地面、手与物、身体与家具的接触位置。角色与椅子/桌面适合拆层时拆层；生成姿势的落脚线和身体尺度统一后再排帧。先在深浅底实际合成查看抠图，透明图查看器可能显示透明像素的RGB，不能仅凭其显示判断白底已清除。新衣装核对同一成年比例、脸型与光线。

连续镜头切换继承上一镜末表情与道具位置，避免下一镜又恢复默认笑脸。走路须有可区分的支撑腿/摆动腿和接触节奏，整图横移与高抬腿不能冒称自然步态。不合格动作先局部修；调用预算用尽仍不合格时如实交候选，不能改掉用户要求来声称通过。

## 先试难点，再合全片

选本片高风险动作而非固定数量：起身、走路、拿放物、躺卧、换装接镜、复杂表情等。渲染实际短MP4，连续查看起始、接触和终止；不能只验结束静帧。预检适配器本身也要检查动作是否播放、首末状态是否和完整时间轴一致。失败预检保留并明确标记。

`CONTINUITY.json` 是分镜与已有素材锁的证据视图，引用同一资产文件，不维护第二套角色身份。每组序列记录当前输入文件/hash、试片及连续采样、直接观察结果。使用 `studio-quality/scripts/continuity_check.py` 检查证据关联；换图、时序或影响动作的代码后更新 inputs，并让旧试片失效。只填写“pass”但没有当前文件证据不构成通过。

## 最终检查与局部返修

最终MP4需覆盖各镜头中点、镜头边界两侧，以及关键镜头内部的状态切换。用 `studio-quality/scripts/sample_motion.py` 从实际视频先trim再采样；输出路径为空，避免覆盖旧证据。黑场、冻结、静音检测只能定位区间，不能把喜剧停顿自动判坏。

声音沿用voice-production与speech-integrity：实际音频时长排镜头；原声、配乐、动作音效分别保留，接触音对齐接触而非整段随意铺。复用录音不声称新传了情绪参数。音频容器hash不同不一定音色改变；要复用听审必须另证实际解码音频相同，否则重新检查。

交付运行continuity_check的final分支和已有release_check，分开报告技术、连续动作、身份、字幕、表演听感与用户反馈。自动结果不生成审美分。可交候选及明确限制；社交发布仍需已有授权和相应检查。一次成功后可在另一故事上验证迁移性，未经验证不承诺未来质量保证。

## 执行契约

`continuity_check.py CONTINUITY.json --stage preflight|final --out result.json`：0表示已记录证据齐备；2表示候选/未验证/过期；1表示无效输入。preflight不代替final，不会生成素材、渲染或发布。

主要字段：

- reference：`path, sha256, selection_basis, feedback_scope, preserve`。
- sequences：`id, range:[start,end], intent, contact, end_state, states:[{at,pose,gaze}], inputs:[{path,sha256}]`。单状态停顿写hold_reason。
- 每序列preflight：`inputs_digest`由检查器提供的inputs_digest(inputs)计算，`plan_digest`由plan_digest(sequence)计算以包含时序与状态；`clip:{path,sha256}, sample:{path,sha256}, review:{status,method,finding,evidence:[{path,sha256}]}`。
- sample文件由sample_motion生成，路径相对项目根。不要把脚本默认pending改称自动视觉通过；direct_review表示实际看图/动作的观察，model_assisted或automated不能代替。
- final额外：`target:{path,sha256}, final_samples:[{path,sha256}]`；每份采样绑定当前target。

示例调用：`python3 sample_motion.py film.mp4 --project . --out qa/walk-v2 --start 12 --end 15 --fps 8`。采样频率由动作快慢选择，不是固定质量阈值。

步态与分层动作的候选拒用、支撑脚约束、显隐与审美区分见[专项返修](gait-and-layer-repair.md)，出现对应问题时必须加载。
