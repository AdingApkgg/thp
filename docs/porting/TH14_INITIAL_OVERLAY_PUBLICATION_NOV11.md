# TH14 Overlay8 后的初始 Control 数据发布

原版 Main 注册遍历在走到每个节点时读取其启用位。实际 `401280` 遍历、节点构造／有序插入以及 `41d720` 启用指令验证：在 Overlay8 中启用 Control11，本帧执行；到普通 ANM29 才启用，则下一帧执行。回调正文为声明的发布和计数服务，没有把此组件当作完整 Control 正文或物理线程调度证明。

移植版此前在 Main 资源泵阶段决定初次战斗是否就绪，然后才更新 Overlay8。现在保留这次资源泵，并在真实 Overlay8 更新之后重新读取 Control 数据发布；此处没有再做一次文件上传。`GameSession::update_after_initial_overlay` 承接已经完成的 Overlay8，避免重复更新。成功的工作线程回收留在 Main 资源轮询阶段，发布后接入不额外 join。

C++ 组件执行实际 `GameSession`、原包资源／ANM 模板和动画更新，使用与当前 Application 逐字节一致的完成轮询、资源泵包装及初始接入分支。准备与输出服务为声明边界。五例包括帧前发布、Overlay8 中发布、普通 ANM29 中发布、始终未发布，以及 Overlay8 中发布并结束的线程状态。旧读法漏掉两个 Overlay8 发布控制；修正后 Control 计数与原版注册遍历一致。每个循环恰好一次 Overlay、一次普通动画，没有第二次资源泵；线程未返回时仍可采用数据，已成功返回时也不在该接入点 join。

TH12、TH13、TH16 的 GameSession／Application 六个翻译单元预处理结果与修改前相同。浏览器模块按正常权限全量编译 146 个单元。

组件初稿缺少 Application 文件内的初始加载宏，候选分支未被编入；后续版本锁定了两边的当前头文件基线，并显式检查 `GameSession` 大小。正式版本的引擎和夹具均以正常访问权限编译。早期输出和修正过程保留，未计作正式通过。

## 独立复核入口

此项检查可以直接编译当前仓库的 141 个游戏单元，不需要历史 artifact 对象链。构建时校验夹具中的被测方法和接入分支与生产 Application 相同，记录源码、头文件、编译器和对象哈希。运行时核对原版日文 1.00b DATA 身份；原版文件不复制到 Git。需要本地 WASI SDK，以及原版目标配置和 Unicorn／Capstone。

```powershell
python tools/th14-control-overlay-publication-native-nov11.py --output artifacts/th14/overlay-check/native.json
python tools/th14-build-control-overlay-component-nov11.py --out artifacts/th14/overlay-check/core
node tools/th14-run-control-overlay-component-nov11.mjs --build=artifacts/th14/overlay-check/core --native=artifacts/th14/overlay-check/native.json --stock=H:/Games/th/14
```

静音实际 Application 新首帧只运行到一次 Player 回调：507 个宿主更新，RNG 为 `[39319,2588,4607,0]`，保留的原版为 `[20713,2612,4607,0]`，整帧有 282,468 个像素不同。与前份独立样本相比，其余 112 个非脚本 RNG 检查字相同。旧 48 次差及其他图像反例保留，不用单次物理调度的计数变化认定整体 RNG 已修复。

工作线程、GPU 和计时请求均已回收，没有打开音频设备。完整物理调度、Control11 之后的其他回调发布窗口、整段录像及整帧像素尚未完成验收。[结构化范围](th14-initial-overlay-publication-nov11.json)
