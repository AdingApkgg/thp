# TH14 Control 的加载分支与 Main 停止分支

Control 现在按原版区分两种提前返回。`0x04` 加载位在关卡激活判断之后被读取：写回 `flags | 0x80`，跳过 Control 自身的演示、记分、合成与时钟尾部，后续 Main 回调仍可执行。`0x10/0x20/0x40` 则在演示及记分处理之后返回 3，使本轮 Main 停在 Replay、Player 和普通动画之前。`0x04` 与后三个位同时存在时，先走加载分支。

普通游戏的累计时长也改为消费这次 Control 是否执行到计数位置的结果。它独立于速率时钟有没有改变：速率为 0、Control 正常执行时仍计一次；Control 未启用、加载提前返回或 Main 停止时不计。没有新增延时、补 RNG、改弹数或裁剪阈值。

## 验证

原版执行实际节点构造、有序注册、Main `401280`、完整 Control `436620`、Timer `408690` 和游戏时长递增。后续 Player／普通 ANM 回调正文、记分服务及四个 detached-copy 更新为声明服务边界；其调度和是否被调用由原版决定。96 个序列覆盖八种标志组合、0／0.5／1.5 速率、Control 启用／停用，以及普通游戏／演示模式，共 192 个原版快照。

C++ 使用实际 Session、Battle、资源和自机；普通路径为灵梦 B Normal 一面，演示路径使用原始 demo0。183 次 Control 轮次逐字比较 Timer、标志和累计游戏时长，另验证 9 次下一 Supervisor 轮次返回标题。转发实际 VM 更新正文的链接观察器记录四个合成 VM；Player 分派、普通自机动画指令及演示录像游标确认 Main 停止后没有继续运行。旧实现保留 360 处比较失败，当前实现为零。

首个观察夹具错将 detached-copy 的 `before_update` 回调当作直接 VM 更新入口，原始夹具及 297 处比较失败保留并拒收。第二版用链接观察器调用实际 VM 正文，在修改引擎之前完成旧实现采集；没有为凑结果修改原版或重选游戏启动样本。

141 个游戏单元全量编译；14 例演示时钟、5 例 Overlay 接入及六次自然演示回归通过。六次自然演示与上一版本的渐隐／返回边界相同，共 23,523 次 Player 回调；非标准速率是初始输入，后续仍由游戏代码决定。TH12／13／16 的 GameSession、GameBattle 六个预处理翻译单元与修改前逐字相同，不据此声称其他作品运行通过。

浏览器 146 个单元全量编译，Wasm SHA-256 为 `3adc82472741fe33fdfbc00fc5d28cb94d7cd91972726c643a5770b1ac6d7c27`。一次实际 C++ Application／ANGLE 冷启动运行到灵梦 B Normal 手动录像首个 Player／Present：510 个宿主更新，四个线程正常返回，GPU、平台及计时请求均回收，没有声音输出。145 个引擎对象按正常权限编译，现有只读 Application 观察夹具单独沿用放宽访问权限；生产浏览器构建没有该选项。原始状态和像素只在运行退役后用于比较。

这次首帧 RNG 仍为 `[39319,2588,4607,0]`，保留原版为 `[20713,2612,4607,0]`。首个 Player 的全部 32 个观测字与上一版本相同，完整图像仍有 267,510 个不同像素。旧 282,468 像素反例也保留，不能将两次物理加载调度的图像数量变化归因为此次修正。此次控制分支缺陷已修正，24 次 SCRIPT 差异及整作 1:1 仍未关闭。

## 独立复核

需要原版日文 1.00b EXE／DATA、WASI SDK、Python Unicorn／Capstone 和 Node。输出目录应新建，游戏资产不进入 Git。

```powershell
python tools/th14-build-control-overlay-component-nov11.py --out build/control-stop/core
python tools/th14-control-main-stop-native-nov12.py --out build/control-stop/native
python tools/th14-build-demo-clock-nov12.py --providers build/control-stop/core --fixture tools/th14-control-main-stop-component-nov12.cpp --wrap _ZN4th115AnmVm6updateERNS_14AnmEnvironmentE --out build/control-stop/cpp
node tools/th14-run-control-main-stop-nov12.mjs --build=build/control-stop/cpp --native=build/control-stop/native/native.json --stock=H:/Games/th/14 --out=build/control-stop/compare
```

当前模块已部署到 [测试站](https://wth.saop.cc/)，源站和公网的全部 39 个 Runtime 文件哈希均与清单相符。实际 Arch 服务经 SSH 转发的浏览器入口已观察版本更新提示、校验后重启、Normal 灵梦 B 开局／射击／Bomb、暂停恢复后再次暂停、返回标题与正常 Quit；音乐和音效均为 0。这是该生产服务的普通短流程验证，公网源直接浏览器运行及完整模式仍需验收。[发布记录](th14-control-stop-release-nov12.json)。

以上入口复核 96 个逻辑序列。实际 Application 首帧另使用保留的本地观察夹具和物理线程／GPU，不由这些组件命令冒充复现。所有 Control 标志、全部线程交错、完整录像、最终 PCM 及其余浏览器流程仍需分别验收。[结果与绑定](th14-control-main-stop-nov12.json)。
