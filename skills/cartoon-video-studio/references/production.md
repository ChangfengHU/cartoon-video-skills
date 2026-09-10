# 制作状态与角色交接

production_state.py 是本地任务账本，不是自动运行的云调度器。任务按实际项目依赖登记，名称自由；保持镜头级粒度。依赖必须先注册，因此无法新建环。状态更新有项目文件锁、原子替换、输入/输出SHA256、依赖run_id和历史快照。

```sh
python3 scripts/production_state.py --project /path/to/film add voice-03 --inputs lines/03.txt
python3 scripts/production_state.py --project /path/to/film add scene-03 --deps voice-03 --inputs scenes/03.html
python3 scripts/production_state.py --project /path/to/film begin voice-03
# 保存返回的run_id；提交远端后立即登记任务ID，重启时查询原任务
python3 scripts/production_state.py --project /path/to/film remote voice-03 --run-id ACTUAL_RUN_ID --provider doubao --job ACTUAL_JOB_ID
# 仅异步后端有job ID时登记remote；同步TTS不用伪造ID。实际成功后标remote-status succeeded。
python3 scripts/production_state.py --project /path/to/film finish voice-03 --run-id ACTUAL_RUN_ID --outputs audio/03.mp3
python3 scripts/production_state.py --project /path/to/film status
```

finish验证实际文件，不验证声音/画面美感。远端状态未知时 fail 可以记失败，但 begin 不允许重复提交；使用原run查询终态后再结束任务。远端提交到记录ID之间崩溃仍可能丢失ID：保存请求标识并向提供方查任务，不能声称恰好执行一次。同步调用也需保留请求时间与输入摘要，网络超时先查原请求。

修改输入后，status 的 reusable 为false；invalidate会标记相关下游过期，不删除文件。新产物用新目录/版本保留旧文件；同路径被外部覆盖只能检出变化，Git/R2版本或工程备份负责恢复原文件。脚本不会恢复被覆盖的媒体，也不会撤回已发布视频。

角色字段映射：cast.characters[].id 对应人物id；version对应本集冻结的brand版本；identityLocks/reference/assets关联品牌资源；character-profile.json保存长期性格和选角条件。本集role/职业/关系存cast，不改长期档案。新增注册前验证profile；品牌asset SHA256检查不代替设计skill逐张图检。候选制作允许，但明确candidate；长期默认和approved状态只依据用户真实认可。
