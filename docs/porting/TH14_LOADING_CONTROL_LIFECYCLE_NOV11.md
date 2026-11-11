# TH14 加载动画的 Control 与速率边界

当前 C++ 加载对象、动画管理器与原版在 7 个声明序列中逐字一致：1,127 个快照、855,162 字，包含每个活跃 VM 的全部 303 字表示、原始句柄、注册链和两组 RNG。速率覆盖 0、0.5、1、1.5；Control 标志覆盖 0、2、3、7。第 20 次更新施加该序列的标志，第 40 次请求结束，第 60 次将标志恢复为 0。原版与 C++ 在冻结中的延迟 interrupt1、恢复和回收保持一致。速率 0 时双方均保留一个未结束 VM；其余序列在观察结束前全部回收。

原版执行实际资源、工厂、注册、Main 遍历、Control 读取、延迟中断和回收。Control 对象与其标志写入为声明输入，不执行原版 Control 生产者。C++ 使用正常访问权限和核对哈希的 141 个当前游戏对象，执行实际 LoadingTh14、AnmManager、ControlPublicationTh14 和解释器。预置 64 个原版池槽位，禁止耗尽。

负对照保持全部脚本和更新顺序，仅故意让 C++ 忽略声明 Control 标志。三个应冻结的序列各出现 141 个错误快照，分别为 9,875、9,875、8,660 个错误字；不应冻结的序列保持一致。这证明比较能够识别冻结行为差异。

## 复核

需要本人原版解包的 ascii.anm、原版目标配置、Unicorn/Capstone、WASI SDK 和 Node。工具校验输入与当前源码/对象哈希，输出目录必须新建。原始 VM 快照与游戏资源留在本地。

```powershell
python tools/th14-build-control-overlay-component-nov11.py --out artifacts/th14/control-check/engine
python tools/th14-loading-control-native-nov11.py --out artifacts/th14/control-check/native --ascii=/path/to/original/ascii.anm
python tools/th14-build-loading-control-nov11.py --providers artifacts/th14/control-check/engine --out artifacts/th14/control-check/cpp
node tools/th14-run-loading-control-nov11.mjs --build=artifacts/th14/control-check/cpp --native=artifacts/th14/control-check/native --ascii=/path/to/original/ascii.anm --output=artifacts/th14/control-check/final
```

加入 `--negative=ignore-control` 并另选输出目录可复核负对照，预期返回失败。

此项验证覆盖 Loading 的 Control 消费端与速率语义，未执行物理加载线程、浏览器减速暂停流程、GPU 或音频设备，未增加完整录像运行，也未修改游戏实现。实际首帧仍保留 24 次 SCRIPT 调用差和 282,468 个不同像素，整作 1:1 尚未完成。[摘要与绑定](th14-loading-control-lifecycle-nov11.json)。
