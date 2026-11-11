# TH14 加载动画的完整逻辑生命周期

当前 `LoadingTh14` 和 `AnmManager` 与原版加载动画在相同逻辑更新序列中一致：分别在第 40、84、120 次更新之前发送延迟 interrupt1，比较从构造到结束后 50 次更新的全部活跃 VM。397 个快照、1,328,007 个字相同，包括每个 VM 的 303 字表示、SCRIPT／游戏 RNG、原始句柄、注册表与子链，以及结束后的完整回收。没有为了通过比较重写句柄或屏蔽字段。

原版侧执行资源加载与模板解释、`47ed10` 工厂、`47aa08..47aae5` 注册片段、`401280` Main 遍历、`47e7f0`／`47e7c0` 包装、普通／覆盖动画更新、`47f140` 延迟结束与池回收。资源、纹理和 CRT 为声明服务；池预置 64 个与完整池相同的初始降序槽位，测试禁止耗尽。当前 C++ 侧执行实际资源模板、加载对象、动画解释和回收，复用哈希核对后的 141 个当前游戏对象，夹具以正常访问权限编译。

原版注册顺序为 Overlay8、Normal29。在 Normal29 中创建的覆盖粒子，下一次 Overlay8 才参与更新。将两个更新体反序调用的负对照分别出现 50、94、130 个错误快照，差异为 6,735、22,525、41,964 字。早期临时目录错误和未读全两条注册链的夹具记录保留；正式比较使用真实注册与 Main 遍历。

声明输入为速率 1、SCRIPT seed/count `12345/0`、游戏 seed/count `54321/0`，没有 Control 对象或其他动画生产者。没有将这些输入或观察结果写入生产游戏。

这项检查针对加载动画本身的逻辑语义。未运行物理线程、GPU 或音频设备，没有新增完整录像运行。当前实际 Application 首帧仍有 24 次 SCRIPT 调用差和 282,468 个不同像素。保留快照中，原版有 21 个 `ascii:16` 粒子，移植有 20 个；过场计数为 84／79。按脚本配对用于定位这些年龄和数量差异，没有用于严格验收，也未把异步耗时差认定为全部差异的原因。

## 复核

需要原版目标配置、Unicorn／Capstone、WASI SDK 和 Node。`--ascii` 指向本人原版解包得到的 `ascii.anm`，工具核对其哈希。输出目录必须新建；不上传原版资产或原始 VM 快照。

```powershell
python tools/th14-build-control-overlay-component-nov11.py --out artifacts/th14/loading-check/engine
python tools/th14-loading-family-native-nov11.py --out artifacts/th14/loading-check/native --ascii=/path/to/original/extracted/ascii.anm
python tools/th14-build-loading-family-nov11.py --providers artifacts/th14/loading-check/engine --out artifacts/th14/loading-check/cpp
node tools/th14-run-loading-family-nov11.mjs --build=artifacts/th14/loading-check/cpp --native=artifacts/th14/loading-check/native --ascii=/path/to/original/extracted/ascii.anm
```

未修改游戏实现或线上运行包。下一步继续核对独立异步发布窗口及绘制时机。[检查范围和绑定](th14-loading-family-lifecycle-nov11.json)，[原版执行摘要](th14-loading-family-native-nov11.json)。
