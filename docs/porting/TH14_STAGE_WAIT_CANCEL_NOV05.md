# TH14 首个资源阶段前的等待取消

`GameSessionResources::cancel_stage_loading()` 原来只在 `requested_phases != 0` 时调用宿主 `cancel_stage_phases`。实际 SDL 的等待代次取消位于这个回调里，而 60 ms 等待先于第一个资源阶段开始，因此在零阶段掩码时取消加载会跳过等待取消。

现在只要还有 incoming owner，就向宿主交付取消，包括零掩码；随后才清理 incoming owner。非零阶段分支沿用原有调用。没有新增计时、录像帧号、VM 身份、RNG 算法或虚函数布局变化。这个修复为独立就绪生产者接入做准备，没有把它接入普通 Application。

核验编译了当前生产 `begin_stage_loading`、`cancel_stage_loading`，以及 SDL `cancel_stage_phases` 的实际方法体，使用真实 `StageWorkerWaitTh14` 和 `StageUploadsTh14`。解码与释放是声明的记录设备依赖，没有读取资产、运行 GPU 或启动浏览器／原版进程。先在未修改源码上编译只移除错误条件的候选，然后应用源码修复，再从当前源码编译核验。

旧条件组件留下活动等待，首个宿主取消检查失败，共七项失败；修复组件 35 项检查全部通过。检查覆盖取消前尚未分发、已分发后取消、旧回调不能开始／结束新代次、重复取消，以及 owner 销毁前队列引用移除。上传引用控制由单元直接入队，不声称它是普通 GPU 流程里观察到的请求。完整生产 `GameSessionResources.cpp` 另经 TH14 WASI C++17 编译器语法检查，退出码为零。

第一版 JS 核验器把修复后新增的记录检查数误算为 12，实际为三次 release 各三项，共 9 项。错误断言和旧核验器保留；修正计数断言后，原有两份 Wasm 直接通过，没有改其结果或跳过生命周期检查。应用源码后重新编译的组件也通过。

这只关闭了“存在 incoming owner、首个资源阶段尚未请求”时的宿主取消缺口。完整 Application 对象销毁、所有错误／重启／退出路径、创建 incoming owner 之前失败的路径仍需验收。普通浏览器现有 Wasm 未替换，全部玩法回归、独立存储交付、第四次录像全局复制、原版调度及整作 1:1 均未据此通过，模式通过数不变。

工具为 `tools/th14-stage-wait-cancel-check-nov05.py --output <新证据目录>`、`tools/th14-stage-wait-cancel-run-nov05.mjs <证据目录>` 和 `tools/th14-stage-wait-cancel-evidence-nov05.py --check`。[公开统计索引](th14-stage-wait-cancel-nov05.json)只包含结果、声明范围及文件路径／哈希，不包含游戏资产或运行载荷。
