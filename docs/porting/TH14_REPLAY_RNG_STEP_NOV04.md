# TH14 录像换关 RNG 的逐步恢复

2026-11-04，录像换关恢复和录制路径按原版写入顺序推进，并接入实际 `GameSession`、`GameBattle` 和 `StagedLoader` 的等待／失败协议。[机器复核结果](th14-replay-rng-step-nov04.json)绑定八个游戏文件、141 个核心对象、组件、留存原版对照和静音 Application 结果。

## 原版写入与实现

原版 v1.00b 的现有录像控制器先在 `45610f` 写 gameplay seed，再在 `456123` 写 script seed，最后在 `456129` 清 gameplay calls。录制路径在 `45609c` 将 gameplay seed 保存在 AX，依次在 `4560a3` 写录像头、`4560aa` 用保存的 AX 写 script seed、`4560b7` 清 gameplay calls。首次录像创建的 `454a41`／`454a47` 只恢复 gameplay seed 并清 gameplay calls，保留 script RNG。

旧 C++ 在 script seed 写入之前清 gameplay calls；当主线程在两个 worker 写入之间使用 RNG 时，计数结果会改变。`ReplayRngRestoreJobTh14` 现在逐步保留状态：主机返回 Waiting 时不执行下一次写入，Ready 后继续，Failed 终止并传回 Session。录制路径保存第一次采样值，不在恢复时重新读取已被主线程推进的 seed。完成的写入不重复执行，错误的对象／录像头身份被拒绝，重入不会推进任务。

`StagedLoader` 在 Initialize 阶段等待任务完成，既有阶段枚举值保留；前置初始化只执行一次，清理和 HUD／Scene／Timeline 请求发生在成功之后。两条下一关路径在 RNG 完成后恢复经济状态。默认主机仍立即返回 Ready；普通浏览器中各次写入的独立调度尚未验收。首次录像创建仍同步执行，录像全局快照仍作为一次操作恢复。

## 本次验证

| 范围 | 实际结果 |
| --- | --- |
| 原版指令组件 | 15,840 组：首次播放 4,320、下一关播放 5,760、录制 5,760；执行未改写的原版写入及 next16／next32，采样 43,200 次写入后状态 |
| 实际 C++ 组件 | 默认恢复、可恢复任务、生产 StagedLoader 各 15,840 组；候选最终状态及写入后状态差异均为零，旧顺序控制有 2,880 处最终差异 |
| 协议控制 | Waiting 不写、部分恢复、错误身份、失败终止、重入和完成后不重写，共六项通过 |
| 实际 Session 成功路径 | 14,303 回调并继续二面 64 回调；三个写入位于 14,104／14,106／14,108，均保持 Initialize；script seed 写入到计数清零之间实际动画消耗 24 次 script RNG |
| 实际 Session 失败路径 | 14,106 回调返回失败；仅完成第一个 seed 写入，不清计数，不请求后续资源，错误传至 Session 和 Battle |
| 当前核心留存原版对照 | 灵梦 B Normal 122,537、灵梦 A Extra 38,403、咲夜 A Extra 38,977，共 199,917 回调通过原有 v4 异常、Initialize、Scene 和独立原始载荷四项门槛 |
| 编译与 Application | 141 个核心对象全重编；TH12／13／14／16 共 12 项语法检查通过；实际 GLES Application 两关加速、换关、暂停 2,289 帧／27 断言通过，呈现 2,289 次 |
| 图像、音频与浏览器目标 | 两幅完整检查图像及 1,526,784 帧离线混音与封存参考一致；物理音频设备打开数零；146 个浏览器单元重编，尚未进行本构建的浏览器运行验收 |

指令组件使用合成输入和明确的 CPU 调度；可选锁分支经过声明的 stdcall 服务替身，不模拟 Windows 的互斥实现。旧 C++ 控制加入相同语义观察点，保留其旧写入顺序。Session 测试由测试主机主动延后 readiness 或返回失败，不向游戏注入原版 RNG 值，也不将这份改过调度的执行作为原版等价记录。

核心 Wasm：`1e15bb751d12dac304d3d48ec5f70c4a222221c6f4ce444ebb3507773e0e239d`。浏览器 Wasm：`c7b2801fb916402bfbfd4d87e4bdf706395b34e33967191cec889923514aa1c2`。图像／混音比较对象为封存 Application 参考，原版整局像素／PCM 等价另行验收。

## 复核入口

`tools/th14-replay-rng-restore-native-nov04.py` 执行原版指令组件；`tools/th14-replay-rng-step-check-nov04.mjs` 编译实际 C++ 与旧顺序控制并对照三个矩阵。三份 C++ fixture 位于 `runtimes/th12/th12_web/tests/cpp/`，两个 `th14-replay-rng-step-session-*-nov04.mjs` 驱动实际 Session 的成功和失败测试。

在保留本机原版、编译器、资产及原始证据目录的工作区中运行：

```powershell
python -X utf8 tools/th14-replay-rng-step-evidence-nov04.py --check
```

复核器检查源码、对象、Wasm、原始留存数据、测试工具和报告的哈希；公开仓库发布源码与摘要，不包含零售素材、录像、Wasm 或本机原始采样。旧录像缺失的精确线程顺序、旧 RNG／剩余弹／相机／指针 Z 失败、完整模式、原版整局画面／音频、普通游戏、存档和浏览器发布入口仍按[剩余清单](TH14_REMAINING_ACCEPTANCE.md)推进，整作 1:1 未完成。
