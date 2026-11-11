# TH14 自动演示的 Control 时钟

自动演示现在在实际 Control11 回调中读取速率时钟，按原版的精确相等判断在 3840 发起渐隐、在 3900 请求返回标题。判断发生在 Overlay8 和关卡激活之后、Control 时钟递增之前；停用的 Control 不消费演示退出输入。返回请求仍由下一轮 Supervisor 消费，保留当前回调轮次。普通游戏和手动录像不执行演示判断。

原实现使用 `GameSession::state.frame`，并在 Overlay8 之前判断。这个物理更新次数独立于 `GameBattle::th14_control_clock`。速率 0 或 0.5 会重复访问同一整数时钟，1.5 或 2 可以跳过整数；移植保留原版的精确相等语义，没有补帧或添加一次性触发锁。

## 对照

原版组件执行实际节点构造、有序注册、Main 遍历、完整 `436620` 控制器及 `408690` Timer。14 个声明的时钟／速率／启用／输入序列共 39 个原版快照；C++ 在请求返回之前比较 36 次 Control 轮次的全部四个 Timer 表示字，并验证 5 次下一 Supervisor 轮次返回标题。旧实现有 16 处比较失败，当前实现为零。速率覆盖 0、0.5、1、1.5、2，包含物理更新数与 Control 时钟不同，以及 Control 停用。

原版的 CRT 分配、渐隐工厂输出、记分服务和四个独立合成动画更新是声明服务边界；没有执行原版 OS 工作线程或 GPU。比较不把这些有限序列视为所有 Control 标志、完整回放或画面验收。

实际 C++ Session 还运行了六次自然演示，共 23,523 次 Player 回调：三个原始演示各一次标准速率，另对 demo0 使用 0.5、1.5、2 的初始速率。未修改录像、时钟、血量、无敌或火力。后续速率仍由原有游戏代码决定，不能将这些运行称为全程固定减速。三个标准运行均在第 3841 次 Player 回调出现渐隐，第 3901 次 Player 回调后由下一轮返回标题；其他运行也在实际 Control 时钟 3840／3900 触发。

141 个游戏单元全量编译，浏览器 146 个单元全量编译，Wasm SHA-256 为 `010d514f4e7ff2ad088d035a73a5cf2b8d3c614de83806802ef1a2a1954fdda3`。原有五例 Overlay 接入回归通过；TH12／13／16 的 GameSession 和 GameBattle 六个预处理翻译单元与修改前逐字相同。这些检查未启动其他作品。测试未打开图形或音频设备；浏览器模块完成构建，未计作浏览器运行验收。

首份夹具的 `open`／`close` 导出名与 WASI libc 冲突，原夹具及链接日志保留；更正导出名后才收集引擎失败／通过对照。旧演示夹具也显式设置两个声明时钟，独立时钟反例由本项检查承担。

## 独立复核

需要原版日文 1.00b EXE／DATA、WASI SDK、Python Unicorn／Capstone 和 Node。游戏资产不进入仓库，输出目录应新建。`--stock` 指向原版目录。

```powershell
python tools/th14-build-control-overlay-component-nov11.py --out build/demo-clock/core
python tools/th14-demo-clock-native-nov12.py --out build/demo-clock/native
python tools/th14-build-demo-clock-nov12.py --providers build/demo-clock/core --out build/demo-clock/cpp
node tools/th14-run-demo-clock-nov12.mjs --build=build/demo-clock/cpp --native=build/demo-clock/native/native.json --stock=H:/Games/th/14 --out=build/demo-clock/compare
python tools/th14-build-demo-clock-nov12.py --providers build/demo-clock/core --fixture tools/th14-demo-natural-component-nov12.cpp --out build/demo-clock/natural
node tools/th14-run-demo-natural-nov12.mjs --build=build/demo-clock/natural --stock=H:/Games/th/14 --out=build/demo-clock/natural-result
```

初始加载实际首帧的 24 次 SCRIPT RNG 调用差与 282,468 个不同像素继续保留。本修正未完成全自机／难度、严格整段录像、图形、最终 PCM、普通完整流程及浏览器发布验收，整作目标仍在进行。[结果与绑定](th14-demo-control-clock-nov12.json)。
