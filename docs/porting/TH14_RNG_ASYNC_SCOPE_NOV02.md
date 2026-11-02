# TH14 RNG 作用域的 Asyncify 暂停／恢复检查

2026-11-02。检查当前 `4acbbc3` 核心的 `RngBoundaryScope`，没有修改玩法源码。结果见 [JSON](th14-rng-async-scope-nov02.json)。

实际 Emscripten 编译当前 RNG 和导出的 C++ 回调，使用生产 `Th14WebGpuRuntime`、输入绑定与回调队列。80 组组合覆盖 16／32 位调用、五个语义边界、临界区开／关、script／visual RNG 和成功／失败回调。

每组在嵌套作用域内暂停，扩展 Wasm 内存 65,536 字节，同时排队输入、加载与帧回调。暂停期间这些回调均未进入 C++；恢复后的完整结果与同步运行一致，2,048 个栈保护字、外层 `running` 标记、嵌套链及析构恢复均正确。不同 RNG 的内层观察继续工作，同一 RNG 的递归观察受到抑制；失败状态保留。80 组共 320 个排队回调通过。

额外破坏控制在隔离测试中故意绕过输入队列，直接进入暂停中的 C++。测试确实检出状态变化和一次顺序错误，证明正常用例的顺序检查有效。

复现：

```powershell
python tools/th14-rng-async-scope-check-nov02.py --output artifacts/th14/rng-async-scope-fresh
```

该测试控制异步释放时机，没有创建浏览器、窗口、渲染器或音频设备。它验证 RNG 作用域与生产回调队列的组件组合；不验收完整 ANM 更新、原版线程／互斥时序、浏览器界面、帧率、持久化或整作 1:1。当前核心的完整双后端 Application 仍单独验收，旧核心的通过不继承。
