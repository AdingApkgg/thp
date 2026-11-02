# TH14 RNG 内部交付核心的完整双后端 Application 回归

2026-11-02。游戏核心版本固定为 `4acbbc398fe3648ca8362e4fe803f56ee87818b7`。它包含 RNG 内部的初始化轮询及两种临界区返回语义，早于随后 `2f42560` 的分阶段震屏修复。本项结果只适用于 4acbbc。[范围与哈希](th14-rng-store-boundary-application-full-nov02.json)。

GLES 和 WebGPU 均实际完成 122,622 帧、45 项断言：普通菜单进入灵梦 B Normal 完整 Replay，在第 122,562 帧自然回到结束菜单，随后稳定 60 帧。两份进程均正常退出 0，没有预算中止；实际耗时分别为 1,222.350 秒和 2,669.724 秒。独立检查器在取得两份成功终态后通过，缺少 WebGPU 终态时的拒绝记录也保留。

每后端八幅完整 BGRA、对应全部活动 VM、所选操作／状态日志、文件与录像均与封存 GLES 参考一致。离线混音得到 89,969,664 帧 PCM，SHA-256 为 `39e9d4e4c65b7dea3b259e7a83189c06b7aaf28d76ef71bf9942a5c005453b54`。实际使用生产 Application、渲染与音频实现，物理音频设备打开数为零。

检查重新绑定了实际 141 个核心对象、两份应用构建、Wasm、冻结游戏源码及头文件，以及已封存参考的版本和原始输出。长测启动后的工作区改动不会成为旧构建的源码证据；检查器读取其实际编译快照，并以明确的源码提交约束结果。

复核需保留的私有原始记录与编译产物：

```powershell
python tools/th14-rng-store-boundary-application-full-evidence-nov02.py --webgpu-home artifacts/th14/rng-store-boundary-applications-nov02/full-webgpu --gles-home artifacts/th14/rng-store-boundary-applications-nov02/full-gles --output docs/porting/th14-rng-store-boundary-application-full-nov02.json --check
```

这证明本版本、此完整用例与封存实现之间的所列双后端一致性。宿主时钟、熵、文件与异步资源交付仍是声明的平台输入；本项不证明整局原版像素／PCM、独立线程调度、浏览器表现或全部模式等价。新的 2f42560 核心已单独启动完整回归，本结果不继承给它。模式仍为 30／27，整作 1:1 未完成。
