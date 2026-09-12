# 制作与验收证据

适用于完整视频制作、修改，以及为既有作品替换配音的试听。单纯测试账户或音色接口可以只做连通性检查，但不能据此回答“达到旧片效果”。未完成检查可交候选，不额外等待用户审批；不能称质量通过、晋升默认或自动发布。

## 在生成前锁定对照

用户指“之前那条”时，从实际作品标题、来源地址、下载文件哈希、时长确认版本；工程目录名或旧 manifest 不能替代作品身份。记录用户认可的范围，整体满意不能扩成声线、所有素材均被认可。不要仅凭旧模型信息反驳用户对自己配音来源的说明；无法核实的制作来源保留未知。

模型、声线或参考发生变化时，从认可片挑有代表性的短句进行同文案对照。用原片理解停顿与反应，不要求新故事机械复制秒数。记录整体响度处理、是否含音乐、是否拉伸速度等干扰因素。角色身份、声音身份、表演、混音分别判断。

## 生成到排镜的约束

逐句记录台词、说话对象、意图、重音、情绪转折、句前句后停顿，保存实际发送给服务的非敏感参数。导演意图与真正受支持并发送的参数分开；没有映射的要求标明通过分段、剪辑实现或仍未实现。不能把一条“更生动”指令当成逐句表演。不要将某服务的情绪字段泛用到另一服务。

先验证关键短样片：声音是否自然、动作是否有刺激和反应、角色道具是否一致。发现明显退步先局部返修，不用扩整片掩盖。相邻句保持语境；有必要时连句生成并保留可编辑停顿。音频冻结后再排动作字幕；替换音频使受影响镜头、混音、成片及其验收失效。

## 交付前执行

建立作品私有 `RELEASE_CHECK.json`，运行：

```sh
python3 <工作室skill>/scripts/release_check.py <作品>/RELEASE_CHECK.json
```

退出 0 仅表示证据记录完整；2 表示仍是候选；1 表示文件或结构错误。它不能自动证明好听、好看、质量稳定或用户批准。原有 qa_summary.py 保持兼容，不能代替此检查。用实际工具发现的问题覆盖自报 pass；模型复核与可测证据矛盾时不采用其“通过”。

格式：`profile` 为 `audio` 或 `video`；`target` 含 `path, sha256, duration_seconds`。路径相对报告目录，文件必须在作品内。`reference` 为 `{required:true,path,sha256,source,selection_basis}`；确无参考时 `{required:false,reason}`。不把私人音频或声线标识放入公共 skill。

`checks` 每维度一条，含 `dimension, status, target_sha256, finding, reviewer, method, evidence:[{path,sha256}], ranges:[[start,end]], coverage`。status 为 pass/fail/pending；method 为 automated/direct_review/model_assisted；coverage 为 sampled/whole。声明 whole 必须时间覆盖完整；抽查只能声明 sampled。reference 维度还含 `reference_sha256`。无需字幕或确无参考时对应维度可 not_applicable，并给 reason；不得豁免实际要求。

音频维度：technical、intelligibility、performance、reference。视频另加 editorial、identity、composition、motion、mix、captions、ending。各维度不能以平均分抵消；ASR 对词归 intelligibility，不归 performance。感知维度需实际直接复核记录；工具或模型辅助不能单独清除待听审。无法直接听音时保留 pending，继续可做的测量及候选交付。

检查开场、中段升级、关键转折、连续动作、音乐变化、字幕边界和结尾。范围随作品确定，不硬编码切镜频率、统一语速、停顿阈值或角色数量。自动脚本只校验证据完整和版本一致；语义准确与审美仍需真实检查。

修改后保留旧版和差异记录。用真实失败案例验证检查器不会误放行；用新的独立创作任务验证流程可复用。旧片返修、单元测试或字段完整不能证明跨作品稳定。
