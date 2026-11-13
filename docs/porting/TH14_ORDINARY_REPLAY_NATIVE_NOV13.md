# TH14 实际菜单录像的原版运行验收 · 2026-11-13

继普通菜单保存与重开之后，使用**同一份 535 字节录像**在原版 TH14 中实际播放。原版成功读取、执行全部 344 帧输入和终止标记，在第 345 个 Player 回调后稳定进入录像结束菜单。原版与独立 C++/Wasm 的 345 行中，所测 30 个状态字段及 HUD 分数两字全部相同，含玩法 RNG 种子和计数。

动画 script RNG 种子／计数在全部 345 行不同，原始差异保留。初始播放并不恢复该动画 RNG，菜单与加载动画历史也不同。本次不接受完整 32 字段相等、详细全部弹幕或实际 GPU／画面一致；没有通过补 RNG、改游戏状态或删失败数据制造通过。

原版运行采用已有的限定观察方法：独立、静音、隐藏的私有子进程，自动演示读取测试包中的录像；不是原版标题菜单交互。仅替换测试包的 `demo0.rpy`，其余 226 个归档项目逐项验证不变，没有重新提取素材。新归档约 90.7 MB，已解码素材和背景音乐复用，工作目录硬链接的是测试归档／不可变缓存，不链接或修改用户原版文件。

私有进程有明确声明的 6 字节 Player 入口观察跳转，以及首次回调的一次演示标志初始化；不连接调试器、不改 RNG 或计数。保存原指令并重放 displaced prologue，主线程使用观察器私有栈。三个稳定结束菜单样本确认后，由观察器结束并回收自己的子进程；**不声称原版自然退出**。这些观察和启动条件的影响不被隐藏，也不接受未经观察器干预的时序结论。

本次接受此文件的实际原版读取与短流程玩法状态对照，整作、其他机体／难度长录像、原版完整标题菜单选择、浏览器入口及持久化仍未据此完成。

本地证据：`artifacts/th14/ordinary-replay-native-nov13/qualified.json`、`end-menu-preflight/report.json`；移植端对应 `artifacts/th14/ordinary-replay-menu-nov13/reopen-v1/report.json`。完整录像、素材和原始观察字节保留本地。

工具：`tools/th14-package-ordinary-replay-menu-archive-nov13.mjs`、`tools/th14-ordinary-replay-player-native-nov13.py`、`tools/th14-qualify-ordinary-replay-native-nov13.py`。
