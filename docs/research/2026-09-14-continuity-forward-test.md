# 独立前向验证：另一角色项目复用动作证据

所有资产均为本次 FFmpeg 创建的 **TEST ONLY 合成测试图案，不是真实角色作品、用户认可版本或审美通过证据**。仅阅读本次连续动作流程和两份脚本，没有读取历史工程、联网、安装或付费。

请求模拟：另一成年角色 B 项目复用一段已采样动作，随后更换输入图/成片；检查旧证据能否正确失效。输入以 action-input.txt 最小替身模拟图片字节变化，MP4 为实际可解码的两秒视频。

执行 `python3 studio-continuity-v7-research/forward-test/run_test.py` 可复现全部断言；脚本不修改主源码。`results.json` 保存完整返回结果。运行时会临时改写并恢复该目录内输入替身，因此静态读取 02/03 manifest 不等于重现其执行时文件状态，应使用 run_test.py。

|用例|期望/实际退出码|结果|
|---|---|---|
|01 完整证据|0 / 0|符合|
|02 输入实际换图，旧 hash|2 / 2|识别 stale file hash|
|03 更新输入 hash，保留旧预检摘要|2 / 2|识别 preflight no longer matches inputs|
|04 当前成片换为 v2，保留 v1 采样|2 / 2|识别 sample from old MP4|
|05 缺少真实连续采样 manifest|2 / 2|拒绝|
|06 model_assisted 冒充直接观察|2 / 2|拒绝|
|07 单状态且合理叙事停顿|0 / 0|符合：不会一概禁止停顿|
|08 states.at 从 1 改成 1.9，复用旧预检|2 / 0|漏检|
|09 只有一张真实采样图，frame_count 声称 4|2 / 0|漏检|
|10 states=[] 但填 hold_reason|2 / 0|漏检|

## 直接观察与真实采样

sample_motion 实际从 v1 MP4 trim [0,2] 后以 2fps 采样，生成 4 张 PNG，review_status 默认 pending。通过 view_image 直接看过 frame-0001 和 frame-0003：上方时间数字分别约 0.125 和 1.125，底部运动图案位置变化。这里只说明真实采样帧发生变化，不能外推为人物动作自然、连续播放听审或整片认可。

## 漏检的最小重现与建议

1. **动作时序变化没有绑定预检**：修改 sequence.states[1].at 后 inputs_digest 不变，旧短片和旧观察仍返回 evidence_complete。文档要求换时序后旧试片失效，但依赖调用者主动更新 inputs，检查器无法检测 manifest 内已可见的时序变化。建议预检摘要覆盖 range、states、contact、end_state 等影响动作的字段，或明确要求唯一权威动作计划文件必须在 inputs 中，且比对该文件与视图。
2. **连续采样数量仅相信声明值**：frame_count=4、files 仅一张真实 PNG，preflight 和 final 都返回 evidence_complete。建议检查实际文件数 >=2、等于 frame_count，且至少两条不同文件路径；final 分支也检查数量，避免一帧充当连续证据。
3. **空动作状态被当作停顿**：states=[] 且 hold_reason 非空即可通过。合理停顿应至少有一个 pose/gaze/at 起始状态，空列表不应借 hold_reason 绕过。

此外 direct_review 是记录声明，检查器不能证明观察者实际看过；不能把返回码 0 当自动视觉检测。此次文档/返回 note 正确说明该边界。

## 修复后复验

主 agent 修复检查器后，在合法基础夹具中新增 `preflight.plan_digest = plan_digest(seq)`；合理单状态停顿用例也为其合法新动作计划更新摘要。其他负例保持失效证据。原始结果保存为 `results-before-fix.json`，每例旧输出保存于 `before-fix/`，旧执行脚本保存在 `run_test-before-fix.py`。

再次运行同 10 例，期望退出码全部匹配（10/10）；08、09、10 均从错误通过变为候选，01 和 07 仍通过。当前 `results.json` 为修复后结果。

已把稳定的 10 例回归测试写入源码仓库 `tests/test_continuity_check.py`，执行 `python3 -m unittest discover -s studio-refactor/cartoon-video-skills/tests -p test_continuity_check.py -v` 全部通过。该单元测试使用明确标记的字节占位素材，范围限于证据关联；真实 MP4 采样和直接看图仍以本目录独立前向实验为准。空状态回归用例特意更新了 plan_digest，验证不能仅靠摘要过期顺带阻挡。
