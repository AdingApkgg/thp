# TH14 暂停开放时机

原版 `448345` 以有符号整数比较 `Control+0x14` 与 30，条件成立后才调用 `448d80` 打开暂停。这个字段是 Control 的变速计时器当前值；它在 PauseMenu9 之后的 Control11 更新。移植版此前使用记录用的原始帧数 `GameSessionState::frame`，两者在变速时会分开。

TH14 的实际 `GameSession::update` 现在读取 `battle->control_frame() >= 30`。其他作品保留原来的判断。

验证执行原版 `448340..448367` 的未修改判断片段，将进入暂停正文作为观察边界。十例覆盖 29/30/31 边界、负时钟、时钟与原始帧数交叉，以及由真实 `Timer::tick` 在 0、0.5、1、2 倍速下累积出的值。C++ 对照执行实际 `GameSession::update`、暂停入口及原包 `front.anm` / `text.anm` 动画，不使用抽取判断表达式的替身。旧实现八例不同，修正后十例均相同。

TH12、TH13、TH16 的预处理结果与修正前逐字节一致；无握手功能的 TH14 构建通过语法检查。测试没有打开音频设备，没有运行完整录像；原版暂停正文的图像、音频和整个自然游戏流程不在该判断片段的验证范围内。[结构化验证](th14-pause-control-clock-nov11.json)

组件源码为 `tools/th14-pause-control-clock-component-nov11.cpp`。在准备好的组件构建目录中，`node tools/th14-run-pause-control-clock-component-nov11.mjs` 校验构建哈希，并分别执行旧实现和修正实现的十例。网站运行包另行构建、打包及发布，源码验证不等同于浏览器验收。
