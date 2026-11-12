# TH14 录像坐标清零候选被后续写入否决 · 2026-11-13

前轮根据 4547d5／4547dc 判定初次阶段头应保留零坐标，判断过早。原版 455ed0 的录制激活分支随后执行 455f58..455f70，无条件把实际 Player+5ec／+5f0 写回阶段头 +0c／+10；new-entry 只控制之前的全局块复制条件，不阻止该坐标写入。因此不能把构造时的临时零值当作最终录像坐标。

先保存清零候选和针对构造片段的结果：八组原版初次／换关、非零／边界坐标输入，加六自机选择×五 difficulty 值×两 practice 参数×两 initial 参数×四坐标的 480 组真实 GameSession／Recorder 受控输入。仅按构造后状态比较时，当前 240 组不同、候选 0；这只是错误阶段的局部通过，未合入 Root。

补上实际原版录制激活写入，再比较同一批已经保留的完整阶段头，不重跑 GameSession：当前 480 组位置零差异，清零候选 240 组错误。八组原版两阶段位置生产均执行未修改指令、无替代函数，并逐字节检查 256 字节对象中只有坐标八字节按各阶段契约变化。候选和当前的所有其他阶段头字节相同；这是编辑影响范围检查，并非将其他字段当成已经对原版通过。

结论：拒绝清零候选，保留当前复制 Player 坐标的实现。前一轮已通过的 D8 新开局标志修复保持；GameSession.cpp SHA256 仍为 0e0fb1e1d4174acbf13652f6118351f8732272f444882e57b690dcd63bce8be9。此次没有修改生产源码或部署。当前坐标组件不代表完整普通开局、首次激活时刻、实际 Player 初始化、整份录像压缩／加密／保存／重开或跨关通过。

私有结果：artifacts/th14/replay-entry-position-nov13/result.json 为早期清零片段比较；lifecycle-qualified.json 为后续写入的最终判定，两者均保留，不覆盖早期结果。实际头字节保留在 baseline-headers.bin 与 candidate-headers.bin。工具：tools/th14-replay-entry-position-oracle-nov13.py、tools/th14-check-replay-entry-position-nov13.mjs、tools/th14-qualify-replay-entry-position-lifecycle-nov13.py。测试静音，无 GPU／音频设备或资产复制；completeGame=false。
