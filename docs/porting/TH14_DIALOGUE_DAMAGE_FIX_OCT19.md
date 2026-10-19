# TH14 对话期间的敌人伤害修复 · 2026-10-19

灵梦 B Normal 的完整公开录像此前在五面第 89,922 个回调提前 Game Over。原版五面对话期间 Boss 血量保持 13,600，移植版却提前扣掉 840 血，导致后续阶段提前 156 帧。原版 `0x423ad2..0x423ae2` 在收集碰撞和回调后，检查实际对话 owner，并将此次伤害清零。

修复让 `EnemyFrame` 在实际应用伤害时查询 `GameBattle` 当前对话对象，保留之前的命中收集和回调。查询不缓存于帧首，因为 ECL 可以在同帧创建对话；仅 TH14 编译分支增加这个接口。没有修改录像输入、RNG、seed、血量初值或强制关卡推进。

验证结果：

- 30 份完整公开输入共 2,885,731 回调，28 份自然 Replay EOF、2 份仍提前 Game Over。灵梦 B Normal 现在运行 122,005 回调自然结束，其余 29 份的全部 raw32、活跃标记和 enemy owner 字节与修复前相同。
- 灵梦 B Normal 与原版全部 122,005 个物理回调逐索引比较，有效回调中的所选玩法字段除弹数外没有差异。93 个弹数字差、全部视觉 RNG 差及 11 个非激活加载期 gameplayCalls 字差完整保留，不进行重同步。采集到相同回调数不作为原版自然结局证明。
- 五面原版 794 组细节中，血量、敌人列表、阶段和命中奖励一致；仍有 378 组 shot、157 组伤害区域和 5 组 nextId 差异，未声称细节整体等价。
- 141 个核心对象、141 个非恢复 ASAN／UBSan 对象、146 个 SDL 对象全部新编译。三份原失败输入的插桩检查合计 244,762 回调，raw32／活跃／owner 输出与非插桩版本逐字节一致，没有检测到内存或未定义行为错误。另两份 Game Over 原样保留。

新 SDL 为 1,892,313 字节，SHA-256 `743066d9f4a370b2e8975d9a5ce90d8013f7fddaab05846c210622ef8b345de6`，release 导入／导出接口未变。发行包装保留已修复的存档字节比较、28 个私有资源和全部 127 个站点路径。源码只采用三个已验证文件；工作区独立的 `ResourceCrypt.cpp` 修改保留且不混入本次发布。

本机冻结记录位于 `artifacts/th14/dialogue-damage-all30-comparison-oct18/comparison.json`、`dialogue-damage-full-native-oct19/comparison.json`、`dialogue-damage-details-comparison-oct18/comparison.json`、`dialogue-damage-candidate-sanitized-oct18/report.json` 和 `dialogue-damage-adopt-oct19/receipt.json`。这些私有现场与原版资源、录像及二进制不随源码发布。运行时和站点清单分别见 [运行时](th14-launcher-runtime-dialogue-damage-oct19.json)、[站点](th14-launcher-site-dialogue-damage-oct19.json)。

整作 1:1 尚未完成；魔理沙 A Easy 与魔理沙 B Lunatic 的失败、GPU 与音频差异继续定位。上游只保留 TH14 进行中，不重复提交维护者关闭的详细进度 PR。
