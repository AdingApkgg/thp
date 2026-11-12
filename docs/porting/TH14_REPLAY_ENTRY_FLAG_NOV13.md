# TH14 录像新开局标志修复 · 2026-11-13

GameSession::record_stage_entry 原先始终将阶段头 D8 写 0，现按真实入口参数写初次开局 1、换关 0。原版 446a4c 将 Supervisor+6f8 置 1，446a99 清零；4547b7..4547cc 将其 bit0 合并到阶段头 D8。实际执行这三段未修改指令，在六组旧字段值、两种入口共 12 例中验证仅改 bit0、保留其他位。当前阶段记录每次从零头构造，因此本修复使用 1／0，不制造其他保留位。

诊断夹具构造真实 GameSession、GameBattle 和 PlayerFrame，调用真实私有 record_stage_entry（仅夹具放宽访问权限）及正常权限 ReplayRecorder；没有拷贝录制函数实现。六种选择、五个 difficulty 值、两个 practice 参数、两种 initial 参数共 120 组受控元数据输入：旧实现初次 60 组 D8 错误，换关 60 组正确；候选全部 D8 相等。部分参数组合并非完整游戏可选流程，本组件不代表所有模式验收。构造使用空资源、未运行 Player 初始化或游戏循环，也不代表完整录像、存档、压缩／加密输出、浏览器下载或回放通过。

GameSession.cpp 候选以正常权限重新编译，140 个未变提供者及全部源码／对象哈希核验后复用，未更改布局。TH12／TH13／TH16 的旧／新 GameSession 对象各一对逐字节一致，仅映射诊断源文件路径。已通过候选与 Root 文件逐字节相同，采用原子替换，原版 ResourceCrypt 的用户修改保持不变。当前网站部署仍为旧发布 59a8cc4c，本修复尚未发布运行包。

继续读原版录制体还发现：非零 new-entry 时，4547d5／4547dc 将阶段头 +0c／+10 清零；当前路径直接复制 Player 的 x／y。现有 120 组仅断言 D8，且空资源 Player 坐标默认为零，不能掩盖此下一处位置字段缺口。下一步用非零受控坐标扩展原版／真实录制函数对照并修复，再检查其他阶段头字段。主线加载 RNG、三个僚机帧龄差及整作 1:1 仍开放。

证据位于 artifacts/th14/replay-entry-flag-nov13：native.json、result.json、build.json、current-provider-bindings.json、other-title-objects.json、integrated.json。工具为 tools/th14-replay-entry-flag-oracle-nov13.py 与 tools/th14-check-replay-entry-flag-nov13.mjs。全部进程已退出，无 GPU／音频设备、未复制游戏资产，completeGame=false。

后续复核：上述位置“缺口”已被原版 455f58 的录制激活写入否决，清零候选未合入。当前 480 组受控位置与原版两阶段生产相等；见 [位置生命周期复核](TH14_REPLAY_ENTRY_POSITION_LIFECYCLE_NOV13.md)。D8 修复保持，完整录像验收仍开放。
